from django.urls import path

from .views import (
    CurriculumMatrixCreateView,
    CurriculumMatrixDeleteView,
    CurriculumMatrixListView,
    CurriculumMatrixUpdateView,
    CurriculumIndexView,
    SubjectCreateView,
    SubjectDeleteView,
    SubjectListView,
    SubjectUpdateView,
)

app_name = "curriculum"

urlpatterns = [
    path("", CurriculumIndexView.as_view(), name="index"),
    path("disciplinas/", SubjectListView.as_view(), name="subject-list"),
    path("disciplinas/nova/", SubjectCreateView.as_view(), name="subject-create"),
    path("disciplinas/<uuid:pk>/editar/", SubjectUpdateView.as_view(), name="subject-update"),
    path("disciplinas/<uuid:pk>/excluir/", SubjectDeleteView.as_view(), name="subject-delete"),
    path("matrizes/", CurriculumMatrixListView.as_view(), name="curriculummatrix-list"),
    path("matrizes/nova/", CurriculumMatrixCreateView.as_view(), name="curriculummatrix-create"),
    path("matrizes/<uuid:pk>/editar/", CurriculumMatrixUpdateView.as_view(), name="curriculummatrix-update"),
    path("matrizes/<uuid:pk>/excluir/", CurriculumMatrixDeleteView.as_view(), name="curriculummatrix-delete"),
]