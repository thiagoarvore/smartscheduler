from django.urls import path

from . import views

app_name = "schools"

urlpatterns = [
    path("", views.SchoolRedirectView.as_view(), name="redirect"),
    path("schools/<uuid:pk>/", views.SchoolDetailView.as_view(), name="detail"),
    path(
        "schools/<uuid:pk>/edit/",
        views.SchoolUpdateView.as_view(),
        name="update",
    ),
]
