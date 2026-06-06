from django.urls import path

from .views import (
    PeopleIndexView,
    TeacherAvailabilityCreateView,
    TeacherAvailabilityDeleteView,
    TeacherAvailabilityListView,
    TeacherAvailabilityUpdateView,
    TeacherCreateView,
    TeacherDeleteView,
    TeacherListView,
    TeacherQualificationCreateView,
    TeacherQualificationDeleteView,
    TeacherQualificationListView,
    TeacherQualificationUpdateView,
    TeacherUpdateView,
)

app_name = "people"

urlpatterns = [
    path("", PeopleIndexView.as_view(), name="index"),
    path("professores/", TeacherListView.as_view(), name="teacher-list"),
    path("professores/novo/", TeacherCreateView.as_view(), name="teacher-create"),
    path("professores/<uuid:pk>/editar/", TeacherUpdateView.as_view(), name="teacher-update"),
    path("professores/<uuid:pk>/excluir/", TeacherDeleteView.as_view(), name="teacher-delete"),
    path(
        "habilitacoes/",
        TeacherQualificationListView.as_view(),
        name="teacherqualification-list",
    ),
    path(
        "habilitacoes/nova/",
        TeacherQualificationCreateView.as_view(),
        name="teacherqualification-create",
    ),
    path(
        "habilitacoes/<uuid:pk>/editar/",
        TeacherQualificationUpdateView.as_view(),
        name="teacherqualification-update",
    ),
    path(
        "habilitacoes/<uuid:pk>/excluir/",
        TeacherQualificationDeleteView.as_view(),
        name="teacherqualification-delete",
    ),
    path("disponibilidades/", TeacherAvailabilityListView.as_view(), name="teacheravailability-list"),
    path(
        "disponibilidades/nova/",
        TeacherAvailabilityCreateView.as_view(),
        name="teacheravailability-create",
    ),
    path(
        "disponibilidades/<uuid:pk>/editar/",
        TeacherAvailabilityUpdateView.as_view(),
        name="teacheravailability-update",
    ),
    path(
        "disponibilidades/<uuid:pk>/excluir/",
        TeacherAvailabilityDeleteView.as_view(),
        name="teacheravailability-delete",
    ),
]
