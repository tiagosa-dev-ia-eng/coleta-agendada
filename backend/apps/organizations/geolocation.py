"""Geolocalização da rede de farmácias (demanda D-01, docs/demandas.md).

Decisão de domínio (usuário, 04/09/2026): o paciente envia a localização pelo
chat e o chatbot devolve a farmácia mais próxima da rede do laboratório do
canal. As coordenadas das farmácias são cadastradas em
Pharmacy.latitude/longitude (cadastro/API/admin).
"""
import math
import re

from apps.organizations.models import STATUS_ACTIVE, Pharmacy

_EARTH_RADIUS_KM = 6371.0088
_COORD_PAIR_RE = re.compile(
    r"(-?\d{1,3}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)"
)


def haversine_km(lat1, lon1, lat2, lon2):
    """Distância aproximada (km) entre dois pontos, fórmula de Haversine."""
    lat1, lon1, lat2, lon2 = map(math.radians, (float(lat1), float(lon1), float(lat2), float(lon2)))
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
    """Extrai um par \"latitude, longitude\" de um texto (fallback do simulador).

    Exige que ao menos um número tenha casas decimais ou sinal negativo, para
    não confundir com frases comuns (ex.: \"às 10, 30\"). Valida faixas.
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


def nearest_pharmacies(laboratory_id, latitude, longitude, *, limit=1):
    """Farmácias ativas com coordenadas da rede, ordenadas por proximidade.

    Retorna lista de tuplas (distancia_km, Pharmacy). A distância é calculada
    em memória (Haversine) sobre a rede do laboratório.
    """
    if not valid_coordinates(latitude, longitude):
        return []
    qs = (
        Pharmacy.objects.filter(
            laboratory_id=laboratory_id,
            status=STATUS_ACTIVE,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .order_by("name")
        .only("name", "address", "city", "state", "latitude", "longitude")
    )
    ranked = []
    for pharmacy in qs:
        d = haversine_km(
            latitude, longitude, float(pharmacy.latitude), float(pharmacy.longitude)
        )
        ranked.append((d, pharmacy))
    ranked.sort(key=lambda item: item[0])
    return ranked[: max(1, int(limit))]


def nearest_collection_points(laboratory_id, latitude, longitude, *, limit=1):
    """Locais de coleta mais próximos da rede (D-01: farmácia OU laboratório).

    Candidatos: o laboratório do canal (se tiver coordenadas) e as farmácias
    ativas com coordenadas da rede. Retorna lista de tuplas
    (distancia_km, kind, objeto), ordenada por proximidade; kind é
    "laboratory" ou "pharmacy".
    """
    from apps.organizations.models import Laboratory

    if not valid_coordinates(latitude, longitude):
        return []
    candidates = []
    lab = (
        Laboratory.objects.filter(pk=laboratory_id).first()
        if laboratory_id is not None
        else None
    )
    if (
        lab is not None
        and lab.latitude is not None
        and lab.longitude is not None
    ):
        candidates.append(("laboratory", lab))
    for pharmacy in (
        Pharmacy.objects.filter(
            laboratory_id=laboratory_id,
            status=STATUS_ACTIVE,
            latitude__isnull=False,
            longitude__isnull=False,
        )
        .order_by("name")
        .only("name", "address", "city", "state", "latitude", "longitude")
    ):
        candidates.append(("pharmacy", pharmacy))
    ranked = []
    for kind, obj in candidates:
        d = haversine_km(
            latitude, longitude, float(obj.latitude), float(obj.longitude)
        )
        ranked.append((d, kind, obj))
    ranked.sort(key=lambda item: item[0])
    return ranked[: max(1, int(limit))]
