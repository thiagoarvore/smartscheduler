from django.contrib import admin
from django.urls import path
from django_base_kit.urls import user_urlpatterns

from . import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("admin/", admin.site.urls),
] + user_urlpatterns
