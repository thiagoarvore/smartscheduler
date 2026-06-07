from django.urls import path

from .views import (
    SchoolYearCreateView,
    SchoolYearDeleteView,
    SchoolYearListView,
    SchoolYearUpdateView,
    SchedulingIndexView,
)

app_name = "scheduling"

urlpatterns = [
    path("", SchedulingIndexView.as_view(), name="index"),
    path("anos-letivos/", SchoolYearListView.as_view(), name="schoolyear-list"),
    path("anos-letivos/novo/", SchoolYearCreateView.as_view(), name="schoolyear-create"),
    path("anos-letivos/<uuid:pk>/editar/", SchoolYearUpdateView.as_view(), name="schoolyear-update"),
    path("anos-letivos/<uuid:pk>/excluir/", SchoolYearDeleteView.as_view(), name="schoolyear-delete"),
]