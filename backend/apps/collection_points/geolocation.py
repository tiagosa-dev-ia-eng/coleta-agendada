"""Geolocalização dos locais de coleta (D-01/D-03).

O "local de coleta" é a entidade CollectionPoint (farmácia OU laboratório) e a
localização pertence ao ponto. Candidatos: pontos ATIVOS com coordenadas da
rede do laboratório; distância Haversine (km).
"""
import math
import re

from apps.collection_points.models import STATUS_ACTIVE, CollectionPoint

_EARTH_RADIUS_KM = 6371.0088
_COORD_PAIR_RE = re.compile(
    r"(-?\d{1,3}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)"
)


def haversine_km(lat1, lon1, lat2, lon2):
    """Distância aproximada (km) entre dois pontos, fórmula de Haversine."""
    lat1, lon1, lat2, lon2 = map(
        math.radians, (float(lat1), float(lon1), float(lat2), float(lon2))
    )
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return _EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def valid_coordinates(latitude, longitude):
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError):
        return False
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0


def parse_coordinates(text):
    """Extrai um par "latitude, longitude" de um texto (fallback do simulador).

    Exige que ao menos um número tenha casas decimais ou sinal negativo, para
    não confundir com frases comuns (ex.: "às 10, 30"). Valida faixas.
    """
    if not text:
        return None
    for m in _COORD_PAIR_RE.finditer(str(text)):
        a, b = m.group(1), m.group(2)
        if not (("." in a) or ("-" in a) or ("." in b) or ("-" in b)):
            continue
        try:
            lat, lon = float(a), float(b)
        except ValueError:
            continue
        if valid_coordinates(lat, lon):
            return (lat, lon)
    return None


def nearest_collection_points(laboratory_id, latitude, longitude, *, limit=1):
    """Locais de coleta (CollectionPoint) mais próximos da rede do laboratório.

    Pontos ATIVOS com coordenadas cadastradas, de qualquer tipo (farmácia ou
    laboratório). Retorna lista de tuplas (distancia_km, kind, CollectionPoint)
    ordenada por proximidade.
    """
    if not valid_coordinates(latitude, longitude):
        return []
    qs = (
        CollectionPoint.objects.filter(
            laboratory_id=laboratory_id,
            status=STATUS_ACTIVE,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .order_by("name")
        .select_related("pharmacy", "laboratory")
    )
    ranked = []
    for point in qs:
        d = haversine_km(
            latitude, longitude, float(point.latitude), float(point.longitude)
        )
        ranked.append((d, point.kind, point))
    ranked.sort(key=lambda item: item[0])
    return ranked[: max(1, int(limit))]
