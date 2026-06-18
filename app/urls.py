from django.contrib import admin
from django.urls import include, path
from django_base_kit.urls import user_urlpatterns

from . import views

# Sem signup — user é criado pelo admin Django.
auth_urlpatterns = [p for p in user_urlpatterns if p.name != "signup"]

urlpatterns = [
    path("health/", views.health, name="health"),
    path("admin/", admin.site.urls),
    path("", include("schools.urls", namespace="schools")),
] + auth_urlpatterns
