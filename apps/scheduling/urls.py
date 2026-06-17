from django.urls import path

from .views import (
    RunProgressView,
    RunResultViewActual,
    RunTimetableView,
    SchedulingIndexView,
    SchoolYearCreateView,
    SchoolYearDeleteView,
    SchoolYearListView,
    SchoolYearUpdateView,
    suggestion_detail_view,
    suggestion_ignore_view,
)

app_name = "scheduling"

urlpatterns = [
    path("", SchedulingIndexView.as_view(), name="index"),
    path("anos-letivos/", SchoolYearListView.as_view(), name="schoolyear-list"),
    path("anos-letivos/novo/", SchoolYearCreateView.as_view(), name="schoolyear-create"),
    path(
        "anos-letivos/<uuid:pk>/editar/",
        SchoolYearUpdateView.as_view(),
        name="schoolyear-update",
    ),
    path(
        "anos-letivos/<uuid:pk>/excluir/",
        SchoolYearDeleteView.as_view(),
        name="schoolyear-delete",
    ),
    # Sprint 08 — solver UI
    path(
        "run/<uuid:school_year_id>/",
        RunTimetableView.as_view(),
        name="run-timetable",
    ),
    path(
        "run/<uuid:school_year_id>/progress/",
        RunProgressView.as_view(),
        name="run-progress",
    ),
    path(
        "run/<uuid:school_year_id>/result/",
        RunResultViewActual.as_view(),
        name="run-result",
    ),
    # Sprint 09 — Sugestões
    path(
        "suggestion/<uuid:pk>/",
        suggestion_detail_view,
        name="suggestion-detail",
    ),
    path(
        "suggestion/<uuid:pk>/ignore/",
        suggestion_ignore_view,
        name="suggestion-ignore",
    ),
]
