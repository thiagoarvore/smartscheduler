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
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    timezone = models.CharField(_("fuso horário"), max_length=64, blank=True)
    default_settings = models.JSONField(_("configurações padrão"), default=dict, blank=True)

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
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="periods",
        verbose_name=_("unidade"),
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
        ordering = ["unit__name", "order", "name"]

    def clean(self):
        super().clean()
        if self.tenant_id and self.unit_id and self.unit.tenant_id != self.tenant_id:
            raise ValidationError({"unit": _("A unidade deve pertencer ao mesmo tenant.")})

    def __str__(self):
        return self.name


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
    teaching_level = models.ForeignKey(
        TeachingLevel,
        on_delete=models.CASCADE,
        related_name="series",
        verbose_name=_("nível de ensino"),
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
        if self.unit_id and self.period_id and self.period.unit_id != self.unit_id:
            errors["period"] = _("O período deve pertencer à mesma unidade da turma.")
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
    status = models.CharField(_("status"), max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    is_active = models.BooleanField(_("ativo"), default=False)

    class Meta:
        verbose_name = _("ano letivo")
        verbose_name_plural = _("anos letivos")
        ordering = ["-year", "name"]

    def clean(self):
        super().clean()
        errors = {}
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["end_date"] = _("A data de término deve ser maior que a data de início.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name
