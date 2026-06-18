from django.contrib import admin

from .models import School


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "phone", "email", "active", "created_at")
    list_filter = ("active",)
    search_fields = ("name", "cnpj", "email")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("owner",)
