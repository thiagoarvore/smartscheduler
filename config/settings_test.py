"""
Test settings for SmartSchedule — uses SQLite without django-tenants.

These settings are used for running unit tests quickly without PostgreSQL.
Multi-tenant schema tests require PostgreSQL and run in Docker.
"""

from config.settings import *  # noqa: F401, F403

# Override database to SQLite for fast local testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# Remove django-tenants from the test configuration since SQLite
# doesn't support schemas
DATABASE_ROUTERS = ()

# Remove django_tenants from INSTALLED_APPS for SQLite tests
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_tenants"]  # noqa: F405

# Remove TenantMiddleware for SQLite tests
MIDDLEWARE = [  # noqa: F405
    m
    for m in MIDDLEWARE  # noqa: F405
    if m not in {
        "django_tenants.middleware.default.DefaultTenantMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    }
]

# Add test middleware that injects request.tenant (simulates django-tenants in SQLite)
MIDDLEWARE.insert(0, "conftest.SetTenantMiddleware")

# Avoid WhiteNoise manifest lookups in SQLite tests
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}
