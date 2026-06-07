from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("schools/", include("apps.schools.urls")),
    path("pessoas/", include("apps.people.urls")),
    path("curriculo/", include("apps.curriculum.urls")),
    path("grade/", include("apps.scheduling.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)