# Sprint 07 — Model changes: Unit, Period, Series, Teacher


from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("schools", "0002_schoolyear"),
    ]

    operations = [
        # ── Unit ──────────────────────────────────────────────────
        # Add address field
        migrations.AddField(
            model_name="unit",
            name="address",
            field=models.TextField(blank=True, default="", verbose_name="endereço"),
        ),
        # Remove default_settings (JSONField — internal, not for UI)
        migrations.RemoveField(
            model_name="unit",
            name="default_settings",
        ),
        # Change timezone to use Brazil timezone select with default
        migrations.AlterField(
            model_name="unit",
            name="timezone",
            field=models.CharField(
                blank=True,
                default="America/Sao_Paulo",
                max_length=64,
                verbose_name="fuso horário",
            ),
        ),

        # ── Period ────────────────────────────────────────────────
        # Add is_tenant_default flag
        migrations.AddField(
            model_name="period",
            name="is_tenant_default",
            field=models.BooleanField(
                default=False,
                help_text="Se marcado, este período se aplica a todas as unidades do tenant.",
                verbose_name="padrão do tenant",
            ),
        ),
        # Add M2M field for units (blank=True, allows tenant-default periods)
        migrations.AddField(
            model_name="period",
            name="units",
            field=models.ManyToManyField(
                blank=True,
                related_name="periods",
                to="schools.unit",
                verbose_name="unidades",
                help_text="Unidades específicas associadas a este período. Deixe vazio se for padrão do tenant.",
            ),
        ),
        # Remove old FK to unit
        migrations.RemoveField(
            model_name="period",
            name="unit",
        ),
        # Remove old ordering that references unit
        migrations.AlterModelOptions(
            name="period",
            options={"ordering": ["order", "name"], "verbose_name": "período", "verbose_name_plural": "períodos"},
        ),

        # ── Series ────────────────────────────────────────────────
        # Add is_tenant_default flag
        migrations.AddField(
            model_name="series",
            name="is_tenant_default",
            field=models.BooleanField(
                default=False,
                help_text="Se marcado, esta série se aplica a todas as unidades do tenant.",
                verbose_name="padrão do tenant",
            ),
        ),
        # Add M2M field for units
        migrations.AddField(
            model_name="series",
            name="units",
            field=models.ManyToManyField(
                blank=True,
                related_name="series_set",
                to="schools.unit",
                verbose_name="unidades",
                help_text="Unidades específicas associadas a esta série. Deixe vazio se for padrão do tenant.",
            ),
        ),
    ]