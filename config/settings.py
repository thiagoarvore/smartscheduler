"""
Django settings for SmartSchedule (Grade Certa).

Multi-tenant SaaS for school timetabling.
Uses django-tenants for schema-based isolation.

This configuration always requires PostgreSQL.
For Docker development, use: docker compose up
"""

import os
import sys
from pathlib import Path

from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENVIRONMENT = os.getenv("ENVIRONMENT", config("ENVIRONMENT", default="local")).strip()
DEVELOPMENT_ENVIRONMENTS = {"local", "dev"}


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-smartschedule-dev-key-change-in-production",
)

# SECURITY WARNING: don't run with debug turned on in production!
debug_value = os.getenv("DEBUG")
if debug_value is None:
    DEBUG = ENVIRONMENT in DEVELOPMENT_ENVIRONMENTS
else:
    DEBUG = debug_value.strip().lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,.localhost",
).split(",")

# Application definition
# ---------------------------------------------------------------

SHARED_APPS = [
    "django_tenants",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "auditlog",
    "django_base_kit",
    "apps.tenants.apps.TenantsConfig",
    "apps.accounts.apps.AccountsConfig",
]

TENANT_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.schools.apps.SchoolsConfig",
    "apps.curriculum.apps.CurriculumConfig",
    "apps.people.apps.PeopleConfig",
    "apps.scheduling.apps.SchedulingConfig",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

MIDDLEWARE = [
    "django_tenants.middleware.default.DefaultTenantMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# Database — always PostgreSQL for django-tenants
# ---------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("DB_NAME", default="smartschedule"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="postgres"),
        "HOST": config("DB_HOST", default="db"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

DATABASE_ROUTERS = (
    "django_tenants.routers.TenantSyncRouter",
)

# Tenant configuration
# ---------------------------------------------------------------

TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"

DEMO_TENANT_ENABLED = env_bool(
    "DEMO_TENANT_ENABLED",
    default=ENVIRONMENT in DEVELOPMENT_ENVIRONMENTS,
)
DEMO_TENANT_NAME = config("DEMO_TENANT_NAME", default="Colegio Objetivo")
DEMO_TENANT_SCHEMA_NAME = config(
    "DEMO_TENANT_SCHEMA_NAME",
    default="colegioobjetivo",
)
DEMO_TENANT_DOMAIN = config("DEMO_TENANT_DOMAIN", default="localhost")

TENANT_APPS_DIR = BASE_DIR / "apps"

# Public schema URL prefix
PUBLIC_SCHEMA_URL_PREFIX = ""

# Authentication
# ---------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = LOGIN_URL

# Password validation
# ---------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# django-base-kit configuration
# ---------------------------------------------------------------

BASE_KIT = {
    "login_template": "accounts/login.html",
    "login_success_url": LOGIN_REDIRECT_URL,
    "logout_success_url": LOGIN_URL,
}

# Internationalization
# ---------------------------------------------------------------

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True

# Static files
# ---------------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

IS_TEST_ENV = "test" in sys.argv or os.getenv("PYTEST_CURRENT_TEST") is not None
if IS_TEST_ENV:
    STORAGES["staticfiles"] = {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
    }

# Default primary key type
# ---------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auditlog
# ---------------------------------------------------------------

AUDITLOG_INCLUDE_ALL_MODELS = False
