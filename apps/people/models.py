from datetime import time

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_base_kit.models import BaseModel


class Teacher(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativo")
        INACTIVE = "inactive", _("Inativo")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="teachers",
        verbose_name=_("tenant"),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    email = models.EmailField(_("e-mail"), blank=True)
    phone_number = models.CharField(_("telefone"), max_length=30, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )
    max_weekly_load = models.PositiveIntegerField(_("carga semanal máxima"), null=True, blank=True)
    notes = models.TextField(_("observações"), blank=True)

    class Meta:
        verbose_name = _("professor")
        verbose_name_plural = _("professores")
        ordering = ["name", "email"]

    def __str__(self):
        return self.name

    def is_available_at(self, weekday, moment: time) -> bool:
        windows = self.availabilities.filter(
            weekday=weekday,
            start_time__lte=moment,
            end_time__gt=moment,
        )
        if windows.filter(is_available=False).exists():
            return False
        return windows.filter(is_available=True).exists()


class TeacherQualification(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="teacher_qualifications",
        verbose_name=_("tenant"),
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="qualifications",
        verbose_name=_("professor"),
    )
    subject = models.ForeignKey(
        "curriculum.Subject",
        on_delete=models.CASCADE,
        related_name="teacher_qualifications",
        verbose_name=_("disciplina"),
        null=True,
        blank=True,
    )
    teaching_level = models.ForeignKey(
        "schools.TeachingLevel",
        on_delete=models.CASCADE,
        related_name="teacher_qualifications",
        verbose_name=_("nível de ensino"),
        null=True,
        blank=True,
    )
    series = models.ForeignKey(
        "schools.Series",
        on_delete=models.CASCADE,
        related_name="teacher_qualifications",
        verbose_name=_("série"),
        null=True,
        blank=True,
    )
    unit = models.ForeignKey(
        "schools.Unit",
        on_delete=models.CASCADE,
        related_name="teacher_qualifications",
        verbose_name=_("unidade"),
        null=True,
        blank=True,
    )
    valid_from = models.DateField(_("válida desde"), null=True, blank=True)
    valid_until = models.DateField(_("válida até"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    class Meta:
        verbose_name = _("habilitação do professor")
        verbose_name_plural = _("habilitações dos professores")
        ordering = ["teacher__name", "id"]

    def clean(self):
        super().clean()
        errors = {}

        if self.tenant_id and self.teacher_id and self.teacher.tenant_id != self.tenant_id:
            errors["teacher"] = _("O professor deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.subject_id and self.subject.tenant_id != self.tenant_id:
            errors["subject"] = _("A disciplina deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.teaching_level_id and self.teaching_level.tenant_id != self.tenant_id:
            errors["teaching_level"] = _("O nível de ensino deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.series_id and self.series.tenant_id != self.tenant_id:
            errors["series"] = _("A série deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.unit_id and self.unit.tenant_id != self.tenant_id:
            errors["unit"] = _("A unidade deve pertencer ao mesmo tenant.")
        if self.series_id and self.teaching_level_id and self.series.teaching_level_id != self.teaching_level_id:
            errors["series"] = _("A série deve pertencer ao mesmo nível de ensino da habilitação.")

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.teacher.name} — {self.get_status_display()}"


class TeacherAvailability(BaseModel):
    class WeekdayChoices(models.TextChoices):
        MONDAY = "monday", _("Segunda-feira")
        TUESDAY = "tuesday", _("Terça-feira")
        WEDNESDAY = "wednesday", _("Quarta-feira")
        THURSDAY = "thursday", _("Quinta-feira")
        FRIDAY = "friday", _("Sexta-feira")
        SATURDAY = "saturday", _("Sábado")
        SUNDAY = "sunday", _("Domingo")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="teacher_availabilities",
        verbose_name=_("tenant"),
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="availabilities",
        verbose_name=_("professor"),
    )
    weekday = models.CharField(_("dia da semana"), max_length=20, choices=WeekdayChoices.choices)
    start_time = models.TimeField(_("hora de início"))
    end_time = models.TimeField(_("hora de término"))
    is_available = models.BooleanField(_("disponível"), default=True)
    reason = models.TextField(_("motivo"), blank=True)

    class Meta:
        verbose_name = _("disponibilidade do professor")
        verbose_name_plural = _("disponibilidades dos professores")
        ordering = ["teacher__name", "weekday", "start_time"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.teacher_id and self.teacher.tenant_id != self.tenant_id:
            errors["teacher"] = _("O professor deve pertencer ao mesmo tenant.")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = _("O horário de término deve ser maior que o horário de início.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.teacher.name} — {self.get_weekday_display()}"
