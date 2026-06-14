"""Admin do app scheduling (Sprint 08).

SolverVariant e SolverRun são readonly no admin — execuções
finalizadas não devem ser editadas. Variantes podem ser
ativadas/desativadas e os parâmetros editados.
"""
from __future__ import annotations

from django.contrib import admin

from .models import SolverRun, SolverVariant


@admin.register(SolverVariant)
class SolverVariantAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "school_year",
        "is_active",
        "updated_at",
    )
    list_filter = ("nome", "is_active", "school_year")
    search_fields = ("nome", "descricao")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("tenant", "school_year", "nome", "is_active")}),
        ("Detalhes", {"fields": ("descricao", "parametros")}),
        ("Auditoria", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(SolverRun)
class SolverRunAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "school_year",
        "status",
        "buracos",
        "completude",
        "tempo_total",
        "created_at",
    )
    list_filter = ("status", "variant", "school_year", "criterio_parada")
    search_fields = ("variant__nome", "error_message")
    readonly_fields = (
        "tenant",
        "variant",
        "school_year",
        "started_at",
        "finished_at",
        "status",
        "buracos",
        "completude",
        "tempo_ate_1a_solucao",
        "tempo_total",
        "iteracoes",
        "restarts",
        "criterio_parada",
        "seed",
        "solution_json",
        "error_message",
        "disparado_por",
        "disparado_por_user",
        "suggestions_status",
        "suggestions_count",
        "report_upload_status",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request) -> bool:
        # Runs são criados pelo solver, não manualmente.
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
