"""Data migration: cria as 3 variantes padrão (A, B, C) do solver.

Cada tenant recebe as 3 variantes com `school_year=None` (globais).
Ver SDD §22.1 e Sprint 08 item 3.2.
"""
from __future__ import annotations

from django.db import migrations

VARIANTES_PADRAO = [
    {
        "nome": "A-Restart",
        "descricao": "N tentativas independentes do construtor; fica com a melhor.",
        "parametros": {
            "max_restarts": 100,
            "tempo_por_tentativa_seg": 18,
        },
    },
    {
        "nome": "B-HillClimbing",
        "descricao": "1 construção inicial + hill climbing até bater timeout.",
        "parametros": {
            "vizinhos_por_iteracao": 10,
        },
    },
    {
        "nome": "C-Hybrid",
        "descricao": "Várias construções com seeds diferentes + hill climbing em cada.",
        "parametros": {
            "max_construcoes": 5,
            "tempo_por_construcao_seg": 120,
        },
    },
]


def criar_variantes(apps, schema_editor) -> None:
    SolverVariant = apps.get_model("scheduling", "SolverVariant")
    Tenant = apps.get_model("tenants", "Tenant")
    for tenant in Tenant.objects.all():
        for v in VARIANTES_PADRAO:
            SolverVariant.objects.get_or_create(
                tenant=tenant,
                school_year=None,
                nome=v["nome"],
                defaults={
                    "descricao": v["descricao"],
                    "parametros": v["parametros"],
                    "is_active": True,
                },
            )


def reverter_variantes(apps, schema_editor) -> None:
    SolverVariant = apps.get_model("scheduling", "SolverVariant")
    SolverVariant.objects.filter(
        school_year__isnull=True,
        nome__in=[v["nome"] for v in VARIANTES_PADRAO],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0003_solvervariant_solverrun_and_more"),
    ]

    operations = [
        migrations.RunPython(criar_variantes, reverter_variantes),
    ]
