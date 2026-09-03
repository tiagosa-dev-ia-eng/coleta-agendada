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
