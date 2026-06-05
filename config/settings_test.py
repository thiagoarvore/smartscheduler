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
MIDDLEWARE = [m for m in MIDDLEWARE if m != "django_tenants.middleware.default.TenantMiddleware"]  # noqa: F405
