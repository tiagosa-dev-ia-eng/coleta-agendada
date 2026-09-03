"""Padroniza erros da API no formato do doc 07 §11:

    { "error": { "code": ..., "message": ..., "details": {} } }
"""
from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = getattr(response, "data", None)
    code = getattr(exc, "default_code", None) or "error"

    message = ""
    if isinstance(detail, dict):
        parts = []
        for value in detail.values():
            if isinstance(value, (list, tuple)) and value:
                parts.append(str(value[0]))
            elif isinstance(value, str):
                parts.append(value)
        message = "; ".join(parts)
    elif isinstance(detail, (list, tuple)) and detail:
        message = str(detail[0])
    elif detail is not None:
        message = str(detail)

    response.data = {
        "error": {
            "code": code,
            "message": message or "Requisição inválida.",
            "details": detail if isinstance(detail, dict) else {},
        }
    }
    return response
