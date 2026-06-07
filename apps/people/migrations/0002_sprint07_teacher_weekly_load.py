# Sprint 07 — Teacher: rename max_weekly_load → weekly_load

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("people", "0001_initial"),
    ]

    operations = [
        # Rename field max_weekly_load → weekly_load with updated semantics
        migrations.RenameField(
            model_name="teacher",
            old_name="max_weekly_load",
            new_name="weekly_load",
        ),
        migrations.AlterField(
            model_name="teacher",
            name="weekly_load",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="carga semanal",
                help_text="Carga horária semanal exata do professor (em aulas).",
            ),
        ),
    ]