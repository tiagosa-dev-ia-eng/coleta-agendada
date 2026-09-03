"""Configuração para a suíte de testes (rodapé rápido, sem I/O externo)."""
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# testes nunca chamam a IA real (sem chave -> mock determinístico)
DEEPSEEK_API_KEY = ""

import tempfile  # noqa: E402

# anexos de teste em diretório temporário (não poluir backend/media do dev)
MEDIA_ROOT = tempfile.mkdtemp(prefix="ca-test-media-")

# Throttles altos na suíte para não interferir (lockout testado à parte)
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_RATES": {
        **REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"],  # noqa: F405
        "anon": "100000/hour",
        "user": "100000/hour",
        "login": "1000/minute",
    },
}
