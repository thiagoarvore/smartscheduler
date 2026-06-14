from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_base_kit.models import BaseModel


class Unit(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="units",
        verbose_name=_("tenant"),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    address = models.TextField(_("endereço"), blank=True, default="")
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    timezone = models.CharField(_("fuso horário"), max_length=64, blank=True, default="America/Sao_Paulo")

    class Meta:
        verbose_name = _("unidade")
        verbose_name_plural = _("unidades")
        ordering = ["name"]

    def __str__(self):
        return self.name


class TeachingLevel(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativo")
        INACTIVE = "inactive", _("Inativo")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="teaching_levels",
        verbose_name=_("tenant"),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    order = models.PositiveIntegerField(_("ordem"))
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    class Meta:
        verbose_name = _("nível de ensino")
        verbose_name_plural = _("níveis de ensino")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Period(BaseModel):
    class TypeChoices(models.TextChoices):
        MORNING = "morning", _("Manhã")
        AFTERNOON = "afternoon", _("Tarde")
        EVENING = "evening", _("Noite")

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativo")
        INACTIVE = "inactive", _("Inativo")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="periods",
        verbose_name=_("tenant"),
    )
    is_tenant_default = models.BooleanField(
        _("padrão do tenant"),
        default=False,
        help_text=_("Se marcado, este período se aplica a todas as unidades do tenant."),
    )
    units = models.ManyToManyField(
        Unit,
        blank=True,
        related_name="periods",
        verbose_name=_("unidades"),
        help_text=_("Unidades específicas associadas a este período. Deixe vazio se for padrão do tenant."),
    )
    name = models.CharField(_("nome"), max_length=200)
    type = models.CharField(_("tipo"), max_length=20, choices=TypeChoices.choices)
    order = models.PositiveIntegerField(_("ordem"))
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    start_time = models.TimeField(_("hora de início"), null=True, blank=True)
    end_time = models.TimeField(_("hora de término"), null=True, blank=True)

    class Meta:
        verbose_name = _("período")
        verbose_name_plural = _("períodos")
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.is_tenant_default and self.units.exists():
            raise ValidationError(
                {"units": _("Períodos padrão do tenant não devem ter unidades específicas.")}
            )


class Series(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="series_set",
        verbose_name=_("tenant"),
    )
    is_tenant_default = models.BooleanField(
        _("padrão do tenant"),
        default=False,
        help_text=_("Se marcado, esta série se aplica a todas as unidades do tenant."),
    )
    teaching_level = models.ForeignKey(
        TeachingLevel,
        on_delete=models.CASCADE,
        related_name="series",
        verbose_name=_("nível de ensino"),
    )
    units = models.ManyToManyField(
        Unit,
        blank=True,
        related_name="series_set",
        verbose_name=_("unidades"),
        help_text=_("Unidades específicas associadas a esta série. Deixe vazio se for padrão do tenant."),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    order = models.PositiveIntegerField(_("ordem"))
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    class Meta:
        verbose_name = _("série")
        verbose_name_plural = _("séries")
        ordering = ["teaching_level__order", "order", "name"]

    def clean(self):
        super().clean()
        if self.tenant_id and self.teaching_level_id and self.teaching_level.tenant_id != self.tenant_id:
            raise ValidationError({"teaching_level": _("O nível de ensino deve pertencer ao mesmo tenant.")})
        if self.is_tenant_default and self.units.exists():
            raise ValidationError(
                {"units": _("Séries padrão do tenant não devem ter unidades específicas.")}
            )

    def __str__(self):
        return self.name


class ClassGroup(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="class_groups",
        verbose_name=_("tenant"),
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="class_groups",
        verbose_name=_("unidade"),
    )
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name="class_groups",
        verbose_name=_("período"),
    )
    series = models.ForeignKey(
        Series,
        on_delete=models.CASCADE,
        related_name="class_groups",
        verbose_name=_("série"),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    class Meta:
        verbose_name = _("turma")
        verbose_name_plural = _("turmas")
        ordering = ["name"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.unit_id and self.unit.tenant_id != self.tenant_id:
            errors["unit"] = _("A unidade deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.period_id and self.period.tenant_id != self.tenant_id:
            errors["period"] = _("O período deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.series_id and self.series.tenant_id != self.tenant_id:
            errors["series"] = _("A série deve pertencer ao mesmo tenant.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class SchoolYear(BaseModel):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _("Rascunho")
        ACTIVE = "active", _("Ativo")
        ARCHIVED = "archived", _("Arquivado")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="school_years",
        verbose_name=_("tenant"),
    )
    name = models.CharField(_("nome"), max_length=200)
    year = models.PositiveIntegerField(_("ano"))
    start_date = models.DateField(_("data de início"))
    end_date = models.DateField(_("data de término"))
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    is_active = models.BooleanField(_("ativo"), default=False)
    last_solver_run_at = models.DateTimeField(
        _("última execução do solver"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_(
            "Cooldown: 1 execução por hora (desativado em local/dev/test). Ver SDD §22.2.4."
        ),
    )

    class Meta:
        verbose_name = _("ano letivo")
        verbose_name_plural = _("anos letivos")
        ordering = ["-year", "name"]

    def __str__(self):
        return self.name


# Auditlog registration — moved from signals.py
from auditlog.registry import auditlog  # noqa: E402

auditlog.register(Unit)
auditlog.register(TeachingLevel)
auditlog.register(Period)
auditlog.register(Series)
auditlog.register(ClassGroup)
auditlog.register(SchoolYear)