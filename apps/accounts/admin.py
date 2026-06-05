from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


class CustomUserAdmin(UserAdmin):
    """Admin interface for the custom User model."""

    model = User
    list_display = (
        "email",
        "username",
        "active",
        "first_name",
        "last_name",
        "is_staff",
    )
    list_filter = ("is_staff", "active")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Informacoes pessoais"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissoes"),
            {
                "fields": (
                    "username",
                    "active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Datas importantes"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "is_staff",
                    "active",
                ),
            },
        ),
    )


admin.site.register(User, CustomUserAdmin)
