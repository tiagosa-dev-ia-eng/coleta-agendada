"""Configurações base do projeto (compartilhadas por todos os ambientes)."""
import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes", "on"}

_allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
ALLOWED_HOSTS = [h for h in _allowed_hosts.split(",") if h]

# Aplicativos
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # terceiros
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # apps do domínio (monolito modular — doc 03 §3)
    "apps.accounts",
    "apps.organizations",
    "apps.technicians",
    "apps.patients",
    "apps.requests",
    "apps.scheduling",
    "apps.payments",
    "apps.catalog",
    "apps.quotations",
    "apps.core",
    "apps.audit",
]

# Usuário customizado do domínio (doc 06 — User com email/phone/document/role)
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Banco de dados (doc 13 §4 — DATABASE_URL; default local SQLite para dev rápido)
_DATABASE_URL = os.getenv("DATABASE_URL")
if _DATABASE_URL:
    DATABASES = {"default": dj_database_url.parse(_DATABASE_URL, conn_max_age=60)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
# Anexos — storage LOCAL por decisão G-07 (03/09/2026).
# Evolução futura: object storage S3-compatible via django-storages em produção
# (trocar DEFAULT_FILE_STORAGE; os upload_to relativos permanecem).
MAX_MEDICAL_UPLOAD_BYTES = int(os.getenv("MAX_MEDICAL_UPLOAD_MB", "10")) * 1024 * 1024

# Pagamentos (doc 10/13): gateway via adapter (R-006) — MVP usa fake (gate G-02)
PAYMENT_GATEWAY = os.getenv("PAYMENT_GATEWAY", "fake")
PAYMENT_WEBHOOK_SECRET = os.getenv("PAYMENT_WEBHOOK_SECRET", "")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Segurança parametrizada (doc 11 §2)
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("LOCKOUT_MINUTES", "15")) * 60
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
LOGIN_RATE_PER_MINUTE = int(os.getenv("LOGIN_RATE_PER_MINUTE", "10"))

# DRF — JWT + RBAC no backend (doc 11; ADR-009: frontend nunca é fonte de verdade)
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": f"{RATE_LIMIT_PER_HOUR}/hour",
        "user": f"{RATE_LIMIT_PER_HOUR}/hour",
        "login": f"{LOGIN_RATE_PER_MINUTE}/minute",
    },
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# JWT (simplejwt) — doc 11 §1/§3: refresh com rotação e blacklist
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "UPDATE_LAST_LOGIN": True,
}

# CORS (doc 13 §4)
_CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
CORS_ALLOWED_ORIGINS = [o for o in _CORS_ORIGINS.split(",") if o]
