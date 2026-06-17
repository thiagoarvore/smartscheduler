from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _
from django_base_kit.models import BaseModel

from apps.curriculum.models import Subject, WorkloadItem
from apps.people.models import Teacher, TeacherQualification
from apps.schools.models import ClassGroup, Period, SchoolYear, Unit


class Timetable(BaseModel):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _("Rascunho")
        ACTIVE = "active", _("Ativa")
        ARCHIVED = "archived", _("Arquivada")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("tenant"),
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("unidade"),
    )
    period = models.ForeignKey(
        Period,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("período"),
    )
    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="timetables",
        verbose_name=_("ano letivo"),
    )
    name = models.CharField(_("nome"), max_length=200)
    status = models.CharField(_("status"), max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    current_version_number = models.PositiveIntegerField(_("versão atual"), default=1)

    class Meta:
        verbose_name = _("grade de horários")
        verbose_name_plural = _("grades de horários")
        ordering = ["unit__name", "period__order", "name"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.unit_id and self.unit.tenant_id != self.tenant_id:
            errors["unit"] = _("A unidade deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.period_id and self.period.tenant_id != self.tenant_id:
            errors["period"] = _("O período deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.school_year_id and self.school_year.tenant_id != self.tenant_id:
            errors["school_year"] = _("O ano letivo deve pertencer ao mesmo tenant.")
        if self.unit_id and self.period_id and not self.period.units.filter(pk=self.unit_id).exists():
            errors["period"] = _("O período deve pertencer à mesma unidade da grade.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name

    def class_slots(self):
        return self.slots.filter(is_active=True, slot_type=TimetableSlot.SlotTypeChoices.CLASS)


class TimetableSlot(BaseModel):
    class WeekdayChoices(models.TextChoices):
        MONDAY = "monday", _("Segunda-feira")
        TUESDAY = "tuesday", _("Terça-feira")
        WEDNESDAY = "wednesday", _("Quarta-feira")
        THURSDAY = "thursday", _("Quinta-feira")
        FRIDAY = "friday", _("Sexta-feira")
        SATURDAY = "saturday", _("Sábado")
        SUNDAY = "sunday", _("Domingo")

    class SlotTypeChoices(models.TextChoices):
        CLASS = "class", _("Aula")
        INTERVAL = "interval", _("Intervalo")
        LUNCH = "lunch", _("Almoço")
        BLOCKED = "blocked", _("Bloqueado")

    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("grade de horários"),
    )
    weekday = models.CharField(_("dia da semana"), max_length=20, choices=WeekdayChoices.choices)
    start_time = models.TimeField(_("hora de início"))
    end_time = models.TimeField(_("hora de término"))
    order = models.PositiveIntegerField(_("ordem"))
    slot_type = models.CharField(_("tipo"), max_length=20, choices=SlotTypeChoices.choices, default=SlotTypeChoices.CLASS)
    accepts_double_lesson = models.BooleanField(_("aceita dobradinha"), default=False)
    is_active = models.BooleanField(_("ativo"), default=True)
    notes = models.TextField(_("observações"), blank=True)

    class Meta:
        verbose_name = _("slot")
        verbose_name_plural = _("slots")
        ordering = ["weekday", "order", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["timetable", "weekday", "order"],
                name="unique_timetable_weekday_slot_order",
            )
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.timetable_id and self.timetable.tenant_id is None:
            errors["timetable"] = _("A grade de horários precisa estar associada a um tenant.")
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors["end_time"] = _("O horário de término deve ser maior que o horário de início.")
        if self.slot_type in {self.SlotTypeChoices.INTERVAL, self.SlotTypeChoices.LUNCH, self.SlotTypeChoices.BLOCKED} and self.accepts_double_lesson:
            errors["accepts_double_lesson"] = _("Slots não letivos não aceitam dobradinha.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_weekday_display()} {self.order:02d}"

    def overlaps(self, other: TimetableSlot) -> bool:
        return self.weekday == other.weekday and self.start_time < other.end_time and self.end_time > other.start_time


class TimetableVersion(BaseModel):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _("Rascunho")
        VALIDATED = "validated", _("Validada")
        PUBLISHED = "published", _("Publicada")
        ARCHIVED = "archived", _("Arquivada")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="timetable_versions",
        verbose_name=_("tenant"),
    )
    timetable = models.ForeignKey(
        Timetable,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("grade de horários"),
    )
    version_number = models.PositiveIntegerField(_("número da versão"))
    name = models.CharField(_("nome"), max_length=200)
    status = models.CharField(_("status"), max_length=20, choices=StatusChoices.choices, default=StatusChoices.DRAFT)
    is_current = models.BooleanField(_("versão atual"), default=False)

    class Meta:
        verbose_name = _("versão de grade")
        verbose_name_plural = _("versões de grade")
        ordering = ["-version_number", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["timetable", "version_number"],
                name="unique_timetable_version_number",
            )
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.timetable_id and self.timetable.tenant_id != self.tenant_id:
            errors["timetable"] = _("A versão deve pertencer ao mesmo tenant da grade.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} (v{self.version_number})"

    def assignments(self):
        return self.lesson_assignments.select_related("slot", "class_group", "teacher", "subject")

    def missing_class_slots(self):
        assigned_slot_ids = set(self.assignments().values_list("slot_id", flat=True))
        return self.timetable.class_slots().exclude(id__in=assigned_slot_ids)

    def is_ready_for_publication(self):
        return not self._evaluate_publication_blockers()["conflicts"]

    def validate(self):
        evaluation = self._evaluate_publication_blockers()
        validation = Validation.objects.create(
            tenant=self.tenant,
            scope_type=Validation.ScopeTypeChoices.TIMETABLE_VERSION,
            scope_id=self.id,
            validation_type=Validation.ValidationTypeChoices.OPERATIONAL,
            status=Validation.StatusChoices.VALID if not evaluation["conflicts"] else Validation.StatusChoices.INVALID,
            message=(
                _("Grade pronta para publicação")
                if not evaluation["conflicts"]
                else _("Grade possui pendências de validação")
            ),
            details=_normalize_json_payload(evaluation),
        )
        Conflict.objects.bulk_create(
            [
                Conflict(
                    tenant=self.tenant,
                    validation=validation,
                    scope_type=conflict["scope_type"],
                    scope_id=conflict["scope_id"],
                    code=conflict["code"],
                    severity=conflict["severity"],
                    message=conflict["message"],
                    details=_normalize_json_payload(conflict["details"]),
                )
                for conflict in evaluation["conflicts"]
            ]
        )
        return validation

    def _evaluate_publication_blockers(self):
        conflicts: list[dict[str, object]] = []

        class_slots = list(self.timetable.class_slots().order_by("weekday", "order"))
        assignments = list(self.assignments())
        assignments_by_slot = defaultdict(list)
        assignments_by_teacher = defaultdict(list)
        assignments_by_class_subject = defaultdict(list)

        for assignment in assignments:
            assignments_by_slot[assignment.slot_id].append(assignment)
            if assignment.teacher_id:
                assignments_by_teacher[assignment.teacher_id].append(assignment)
            assignments_by_class_subject[(assignment.class_group_id, assignment.subject_id)].append(assignment)

        for slot in class_slots:
            if not assignments_by_slot.get(slot.id):
                conflicts.append(
                    {
                        "scope_type": Conflict.ScopeTypeChoices.TIMETABLE_SLOT,
                        "scope_id": slot.id,
                        "code": Conflict.CodeChoices.MISSING_ASSIGNMENT,
                        "severity": Conflict.SeverityChoices.ERROR,
                        "message": _("Slot sem aula alocada."),
                        "details": {"weekday": slot.weekday, "order": slot.order},
                    }
                )

        for slot_id, slot_assignments in assignments_by_slot.items():
            by_class_group = defaultdict(list)
            by_teacher = defaultdict(list)
            for assignment in slot_assignments:
                by_class_group[assignment.class_group_id].append(assignment)
                if assignment.teacher_id:
                    by_teacher[assignment.teacher_id].append(assignment)
            for class_assignments in by_class_group.values():
                if len(class_assignments) > 1:
                    conflicts.append(
                        {
                            "scope_type": Conflict.ScopeTypeChoices.LESSON_ASSIGNMENT,
                            "scope_id": class_assignments[0].id,
                            "code": Conflict.CodeChoices.DUPLICATE_CLASS_SLOT,
                            "severity": Conflict.SeverityChoices.ERROR,
                            "message": _("A turma possui mais de uma aula no mesmo slot."),
                            "details": {"slot_id": slot_id},
                        }
                    )
            for teacher_assignments in by_teacher.values():
                if len(teacher_assignments) > 1:
                    conflicts.append(
                        {
                            "scope_type": Conflict.ScopeTypeChoices.LESSON_ASSIGNMENT,
                            "scope_id": teacher_assignments[0].id,
                            "code": Conflict.CodeChoices.TEACHER_OVERLAP,
                            "severity": Conflict.SeverityChoices.ERROR,
                            "message": _("Professor alocado em mais de uma turma no mesmo slot."),
                            "details": {"slot_id": slot_id},
                        }
                    )

        for assignment in assignments:
            slot = assignment.slot
            if assignment.teacher_id and assignment.teacher.availabilities.exists() and not assignment.teacher.is_available_at(slot.weekday, slot.start_time):
                conflicts.append(
                    {
                        "scope_type": Conflict.ScopeTypeChoices.LESSON_ASSIGNMENT,
                        "scope_id": assignment.id,
                        "code": Conflict.CodeChoices.TEACHER_UNAVAILABLE,
                        "severity": Conflict.SeverityChoices.ERROR,
                        "message": _("Professor indisponível no slot."),
                        "details": {"slot_id": slot.id},
                    }
                )
            if assignment.teacher_id and not _teacher_can_teach_assignment(assignment):
                conflicts.append(
                    {
                        "scope_type": Conflict.ScopeTypeChoices.LESSON_ASSIGNMENT,
                        "scope_id": assignment.id,
                        "code": Conflict.CodeChoices.TEACHER_UNQUALIFIED,
                        "severity": Conflict.SeverityChoices.ERROR,
                        "message": _("Professor sem habilitação para a disciplina."),
                        "details": {"subject_id": assignment.subject_id},
                    }
                )

        for (class_group_id, subject_id), class_subject_assignments in assignments_by_class_subject.items():
            workload_item = (
                WorkloadItem.objects.filter(
                    class_group_id=class_group_id,
                    subject_id=subject_id,
                    is_double_lesson=True,
                    tenant_id=self.tenant_id,
                )
                .order_by("id")
                .first()
            )
            if not workload_item:
                continue

            ordered_assignments = sorted(
                class_subject_assignments,
                key=lambda assignment: (
                    _weekday_index(assignment.slot.weekday),
                    assignment.slot.order,
                ),
            )
            for left, right in _pairwise(ordered_assignments):
                if left.slot.weekday != right.slot.weekday or right.slot.order != left.slot.order + 1:
                    conflicts.append(
                        {
                            "scope_type": Conflict.ScopeTypeChoices.LESSON_ASSIGNMENT,
                            "scope_id": left.id,
                            "code": Conflict.CodeChoices.DOUBLE_LESSON_SEQUENCE,
                            "severity": Conflict.SeverityChoices.ERROR,
                            "message": _("Dobradinha exige slots consecutivos no mesmo dia."),
                            "details": {
                                "class_group_id": class_group_id,
                                "subject_id": subject_id,
                                "left_slot_id": left.slot_id,
                                "right_slot_id": right.slot_id,
                            },
                        }
                    )
                    break

        return {
            "missing_slot_count": len(list(self.missing_class_slots())),
            "conflicts": conflicts,
        }


class LessonAssignment(BaseModel):
    class StatusChoices(models.TextChoices):
        PLANNED = "planned", _("Planejada")
        FIXED = "fixed", _("Fixa")
        VALIDATED = "validated", _("Validada")
        CONFLICT = "conflict", _("Com conflito")

    class AllocationSourceTypeChoices(models.TextChoices):
        MANUAL = "manual", _("Manual")
        SUGGESTED = "suggested", _("Sugerida")
        GENERATED = "generated", _("Gerada")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("tenant"),
    )
    timetable_version = models.ForeignKey(
        TimetableVersion,
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("versão de grade"),
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("turma"),
    )
    slot = models.ForeignKey(
        TimetableSlot,
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("slot"),
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("disciplina"),
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="lesson_assignments",
        verbose_name=_("professor"),
        null=True,
        blank=True,
    )
    status = models.CharField(_("status"), max_length=20, choices=StatusChoices.choices, default=StatusChoices.PLANNED)
    allocation_source_type = models.CharField(
        _("origem da alocação"), max_length=20, choices=AllocationSourceTypeChoices.choices, default=AllocationSourceTypeChoices.MANUAL
    )
    allocation_source_id = models.UUIDField(_("origem da alocação id"), null=True, blank=True)
    notes = models.TextField(_("observações"), blank=True)

    class Meta:
        verbose_name = _("aula alocada")
        verbose_name_plural = _("aulas alocadas")
        ordering = ["slot__weekday", "slot__order", "class_group__name"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.timetable_version_id and self.timetable_version.tenant_id != self.tenant_id:
            errors["timetable_version"] = _("A versão de grade deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.class_group_id and self.class_group.tenant_id != self.tenant_id:
            errors["class_group"] = _("A turma deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.slot_id and self.slot.timetable.tenant_id != self.tenant_id:
            errors["slot"] = _("O slot deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.subject_id and self.subject.tenant_id != self.tenant_id:
            errors["subject"] = _("A disciplina deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.teacher_id and self.teacher.tenant_id != self.tenant_id:
            errors["teacher"] = _("O professor deve pertencer ao mesmo tenant.")
        if self.class_group_id and self.slot_id and self.timetable_version_id and self.slot.timetable_id != self.timetable_version.timetable_id:
            errors["slot"] = _("O slot deve pertencer à mesma grade da versão.")
        if self.class_group_id and self.timetable_version_id and self.class_group.unit_id != self.timetable_version.timetable.unit_id:
            errors["class_group"] = _("A turma deve pertencer à unidade da grade.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.class_group.name} — {self.subject.name}"


class LessonComponent(BaseModel):
    class ComponentTypeChoices(models.TextChoices):
        MAIN = "main", _("Principal")
        SUPPORT = "support", _("Apoio")
        SHARED = "shared", _("Compartilhada")
        SUBGROUP = "subgroup", _("Subgrupo")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="lesson_components",
        verbose_name=_("tenant"),
    )
    lesson_assignment = models.ForeignKey(
        LessonAssignment,
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name=_("aula alocada"),
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="lesson_components",
        verbose_name=_("professor"),
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="lesson_components",
        verbose_name=_("disciplina"),
    )
    component_type = models.CharField(_("tipo do componente"), max_length=20, choices=ComponentTypeChoices.choices)
    order = models.PositiveIntegerField(_("ordem"))
    duration_min = models.PositiveIntegerField(_("duração em minutos"))
    subgroup_label = models.CharField(_("subgrupo"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("componente de aula")
        verbose_name_plural = _("componentes de aula")
        ordering = ["lesson_assignment__slot__weekday", "lesson_assignment__slot__order", "order"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.lesson_assignment_id and self.lesson_assignment.tenant_id != self.tenant_id:
            errors["lesson_assignment"] = _("A componente deve pertencer ao mesmo tenant da aula.")
        if self.tenant_id and self.subject_id and self.subject.tenant_id != self.tenant_id:
            errors["subject"] = _("A disciplina deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.teacher_id and self.teacher.tenant_id != self.tenant_id:
            errors["teacher"] = _("O professor deve pertencer ao mesmo tenant.")
        if self.lesson_assignment_id and self.subject_id and self.lesson_assignment.subject_id != self.subject_id:
            errors["subject"] = _("O componente deve usar a mesma disciplina da aula alocada.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.lesson_assignment} — {self.get_component_type_display()}"


class Validation(BaseModel):
    class ScopeTypeChoices(models.TextChoices):
        TIMETABLE_VERSION = "timetable_version", _("Versão de grade")
        TIMETABLE = "timetable", _("Grade de horários")
        LESSON_ASSIGNMENT = "lesson_assignment", _("Aula alocada")

    class ValidationTypeChoices(models.TextChoices):
        OPERATIONAL = "operational", _("Operacional")

    class StatusChoices(models.TextChoices):
        VALID = "valid", _("Válida")
        INVALID = "invalid", _("Inválida")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="validations",
        verbose_name=_("tenant"),
    )
    scope_type = models.CharField(_("tipo de escopo"), max_length=30, choices=ScopeTypeChoices.choices)
    scope_id = models.UUIDField(_("escopo"))
    validation_type = models.CharField(_("tipo de validação"), max_length=30, choices=ValidationTypeChoices.choices)
    status = models.CharField(_("status"), max_length=20, choices=StatusChoices.choices)
    message = models.CharField(_("mensagem"), max_length=255)
    details = models.JSONField(_("detalhes"), default=dict)

    class Meta:
        verbose_name = _("validação")
        verbose_name_plural = _("validações")
        ordering = ["-created_at"]

    def __str__(self):
        return str(self.message)


class Conflict(BaseModel):
    class ScopeTypeChoices(models.TextChoices):
        TIMETABLE_VERSION = "timetable_version", _("Versão de grade")
        TIMETABLE_SLOT = "timetable_slot", _("Slot")
        LESSON_ASSIGNMENT = "lesson_assignment", _("Aula alocada")
        LESSON_COMPONENT = "lesson_component", _("Componente de aula")

    class SeverityChoices(models.TextChoices):
        ERROR = "error", _("Erro")
        WARNING = "warning", _("Aviso")

    class CodeChoices(models.TextChoices):
        MISSING_ASSIGNMENT = "missing_assignment", _("Slot vazio")
        TEACHER_OVERLAP = "teacher_overlap", _("Conflito de professor")
        DUPLICATE_CLASS_SLOT = "duplicate_class_slot", _("Turma duplicada no mesmo slot")
        TEACHER_UNAVAILABLE = "teacher_unavailable", _("Professor indisponível")
        TEACHER_UNQUALIFIED = "teacher_unqualified", _("Professor sem habilitação")
        DOUBLE_LESSON_SEQUENCE = "double_lesson_sequence", _("Dobradinha inválida")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="conflicts",
        verbose_name=_("tenant"),
    )
    validation = models.ForeignKey(
        Validation,
        on_delete=models.CASCADE,
        related_name="conflicts",
        verbose_name=_("validação"),
        null=True,
        blank=True,
    )
    scope_type = models.CharField(_("tipo de escopo"), max_length=30, choices=ScopeTypeChoices.choices)
    scope_id = models.UUIDField(_("escopo"))
    code = models.CharField(_("código"), max_length=50, choices=CodeChoices.choices)
    severity = models.CharField(_("severidade"), max_length=20, choices=SeverityChoices.choices)
    message = models.CharField(_("mensagem"), max_length=255)
    details = models.JSONField(_("detalhes"), default=dict)
    resolved_at = models.DateTimeField(_("resolvido em"), null=True, blank=True)

    class Meta:
        verbose_name = _("conflito")
        verbose_name_plural = _("conflitos")
        ordering = ["severity", "code", "created_at"]

    def __str__(self):
        return str(self.message)


def _pairwise(assignments: list[LessonAssignment]):
    for index in range(0, len(assignments), 2):
        if index + 1 >= len(assignments):
            break
        yield assignments[index], assignments[index + 1]


def _normalize_json_payload(value):
    if isinstance(value, dict):
        return {key: _normalize_json_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json_payload(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_json_payload(item) for item in value]
    if isinstance(value, Promise):
        return str(value)
    if isinstance(value, (uuid.UUID, date, datetime, time, Decimal)):
        return str(value)
    return value


def _weekday_index(weekday: str) -> int:
    order = {
        TimetableSlot.WeekdayChoices.MONDAY: 0,
        TimetableSlot.WeekdayChoices.TUESDAY: 1,
        TimetableSlot.WeekdayChoices.WEDNESDAY: 2,
        TimetableSlot.WeekdayChoices.THURSDAY: 3,
        TimetableSlot.WeekdayChoices.FRIDAY: 4,
        TimetableSlot.WeekdayChoices.SATURDAY: 5,
        TimetableSlot.WeekdayChoices.SUNDAY: 6,
    }
    return order[weekday]


def _teacher_can_teach_assignment(assignment: LessonAssignment) -> bool:
    qualifications = assignment.teacher.qualifications.filter(status=TeacherQualification.StatusChoices.ACTIVE)
    criteria = qualifications.filter(subject=assignment.subject)
    return criteria.filter(
        models.Q(unit=assignment.class_group.unit) | models.Q(unit__isnull=True)
    ).filter(
        models.Q(teaching_level=assignment.class_group.series.teaching_level) | models.Q(teaching_level__isnull=True)
    ).filter(
        models.Q(series=assignment.class_group.series) | models.Q(series__isnull=True)
    ).exists()


# Sprint 08 — Solver (SDD §22.1, §22.2.1)
# -----------------------------------------------------------------------


class SolverVariant(BaseModel):
    """Uma variante do solver (A, B ou C) que pode ser executada.

    As 3 variantes coexistem com `is_active=True` durante a fase de
    experimentação. "Melhor" não é mutação — é cálculo sobre `SolverRun`
    (menor nº de buracos, desempate por tempo total). Ver §22.1.
    """

    class NomeChoices(models.TextChoices):
        A_RESTART = "A-Restart", _("A - Restart")
        B_HILL_CLIMBING = "B-HillClimbing", _("B - Hill Climbing")
        C_HYBRID = "C-Hybrid", _("C - Híbrido")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="solver_variants",
        verbose_name=_("tenant"),
    )
    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="solver_variants",
        verbose_name=_("ano letivo"),
        null=True,
        blank=True,
        help_text=_("Se vazio, a variante é global (todos os anos letivos do tenant)."),
    )
    nome = models.CharField(
        _("nome"),
        max_length=30,
        choices=NomeChoices.choices,
    )
    descricao = models.TextField(
        _("descrição"),
        blank=True,
        default="",
    )
    is_active = models.BooleanField(
        _("ativa"),
        default=True,
        help_text=_("Variantes inativas não são executadas pelo pipeline."),
    )
    parametros = models.JSONField(
        _("parâmetros"),
        default=dict,
        blank=True,
        help_text=_(
            "Parâmetros da variante: seed, timeout, max_restarts, max_construcoes, etc."
        ),
    )

    class Meta:
        verbose_name = _("variante do solver")
        verbose_name_plural = _("variantes do solver")
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "school_year", "nome"],
                name="unique_solver_variant_per_scope",
            ),
        ]

    def __str__(self) -> str:
        scope = self.school_year.name if self.school_year_id else "global"
        return f"{self.get_nome_display()} ({scope})"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if (
            self.tenant_id
            and self.school_year_id
            and self.school_year.tenant_id != self.tenant_id
        ):
            errors["school_year"] = _("O ano letivo deve pertencer ao mesmo tenant.")
        if errors:
            raise ValidationError(errors)


class SolverRun(BaseModel):
    """Uma execução de uma variante do solver.

    Cada chamada a `Solver.solve()` gera um registro aqui. Persiste
    as 8 métricas de §22.2.9 + 2 de suggestions (Sprint 09) +
    1 de report upload (Sprint 09).
    """

    class StatusChoices(models.TextChoices):
        RUNNING = "running", _("Rodando")
        SUCCESS = "success", _("Sucesso")
        FAILED = "failed", _("Falhou")
        INTERRUPTED = "interrupted", _("Interrompida")

    class CriterioParadaChoices(models.TextChoices):
        TIMEOUT = "timeout", _("Timeout")
        ZERO_BURACOS = "zero_buracos", _("Zero buracos")
        ERRO = "erro", _("Erro")
        INTERRUPTED = "interrupted", _("Interrompido")

    class DisparadoPorChoices(models.TextChoices):
        USER = "user", _("Usuário")
        CRON = "cron", _("Cron")
        API = "api", _("API")

    class SuggestionsStatusChoices(models.TextChoices):
        NOT_RUN = "not_run", _("Não executada")
        RUNNING = "running", _("Rodando")
        DONE = "done", _("Concluída")
        TIMEOUT = "timeout", _("Timeout")
        DISABLED = "disabled", _("Desativada")
        FAILED = "failed", _("Falhou")

    class ReportUploadStatusChoices(models.TextChoices):
        PENDING = "pending", _("Pendente")
        SUCCESS = "success", _("Sucesso")
        FAILED = "failed", _("Falhou")
        DISABLED = "disabled", _("Desativada")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="solver_runs",
        verbose_name=_("tenant"),
    )
    variant = models.ForeignKey(
        SolverVariant,
        on_delete=models.PROTECT,
        related_name="runs",
        verbose_name=_("variante"),
    )
    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="solver_runs",
        verbose_name=_("ano letivo"),
    )
    started_at = models.DateTimeField(_("início"), null=True, blank=True)
    finished_at = models.DateTimeField(_("término"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.RUNNING,
    )
    # 8 métricas (§22.2.9)
    buracos = models.PositiveIntegerField(_("buracos"), null=True, blank=True)
    completude = models.FloatField(
        _("completude"),
        null=True,
        blank=True,
        help_text=_("Fração 0.0–1.0 de aulas alocadas."),
    )
    tempo_ate_1a_solucao = models.DurationField(
        _("tempo até 1ª solução"),
        null=True,
        blank=True,
    )
    tempo_total = models.DurationField(_("tempo total"), null=True, blank=True)
    iteracoes = models.PositiveIntegerField(_("iterações"), default=0)
    restarts = models.PositiveIntegerField(_("restarts"), default=0)
    criterio_parada = models.CharField(
        _("critério de parada"),
        max_length=20,
        choices=CriterioParadaChoices.choices,
        null=True,
        blank=True,
    )
    seed = models.PositiveIntegerField(_("seed"), default=0)
    solution_json = models.JSONField(
        _("solução"),
        null=True,
        blank=True,
        help_text=_("Solution serializada via to_dict(). Pode ser grande."),
    )
    error_message = models.TextField(_("mensagem de erro"), blank=True, default="")
    disparado_por = models.CharField(
        _("disparado por"),
        max_length=10,
        choices=DisparadoPorChoices.choices,
        default=DisparadoPorChoices.USER,
    )
    disparado_por_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        related_name="solver_runs",
        verbose_name=_("usuário"),
        null=True,
        blank=True,
    )
    # Suggestions layer (Sprint 09)
    suggestions_status = models.CharField(
        _("status das sugestões"),
        max_length=15,
        choices=SuggestionsStatusChoices.choices,
        default=SuggestionsStatusChoices.NOT_RUN,
    )
    suggestions_count = models.PositiveIntegerField(
        _("nº de sugestões"),
        default=0,
    )
    # Drive upload (Sprint 09)
    report_upload_status = models.CharField(
        _("status do upload do relatório"),
        max_length=10,
        choices=ReportUploadStatusChoices.choices,
        default=ReportUploadStatusChoices.PENDING,
    )

    class Meta:
        verbose_name = _("execução do solver")
        verbose_name_plural = _("execuções do solver")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["school_year", "-created_at"]),
            models.Index(fields=["variant", "-created_at"]),
            models.Index(fields=["tenant", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.variant.nome} @ {self.school_year.name} — {self.get_status_display()}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.tenant_id and self.school_year_id and self.school_year.tenant_id != self.tenant_id:
            errors["school_year"] = _("O ano letivo deve pertencer ao mesmo tenant.")
        if (
            self.tenant_id
            and self.variant_id
            and self.variant.tenant_id != self.tenant_id
        ):
            errors["variant"] = _("A variante deve pertencer ao mesmo tenant.")
        if self.completude is not None and not 0.0 <= self.completude <= 1.0:
            errors["completude"] = _("completude deve estar em [0, 1].")
        if errors:
            raise ValidationError(errors)

    @property
    def is_running(self) -> bool:
        return self.status == self.StatusChoices.RUNNING

    @property
    def is_terminal(self) -> bool:
        return self.status in {
            self.StatusChoices.SUCCESS,
            self.StatusChoices.FAILED,
            self.StatusChoices.INTERRUPTED,
        }


class Suggestion(BaseModel):
    """Sugestão de melhoria gerada pela camada de sugestões (SDD §22.4, Sprint 09)."""

    class CategoriaChoices(models.TextChoices):
        WORKLOAD_INCREASE = "workload_increase", _("Aumentar carga horária")
        TEACHER_ADD = "teacher_add", _("Adicionar professor")
        TEACHER_AVAILABILITY = "teacher_availability", _("Expandir disponibilidade")
        SUBJECT_RULE_RELAX = "subject_rule_relax", _("Relaxar regra")

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pendente")
        APPLIED = "applied", _("Aplicada")
        IGNORED = "ignored", _("Ignorada")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="suggestions",
        verbose_name=_("tenant"),
    )
    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name="suggestions",
        verbose_name=_("ano letivo"),
    )
    solver_run = models.ForeignKey(
        SolverRun,
        on_delete=models.CASCADE,
        related_name="suggestions",
        verbose_name=_("execução do solver"),
    )
    categoria = models.CharField(_("categoria"), max_length=30, choices=CategoriaChoices.choices)
    titulo = models.CharField(_("título"), max_length=200)
    descricao = models.TextField(_("descrição"), blank=True, default="")
    buracos_antes = models.PositiveIntegerField(_("buracos antes"), default=0)
    buracos_depois = models.PositiveIntegerField(_("buracos depois"), default=0)
    delta = models.IntegerField(_("delta"), default=0, help_text=_("Redução no nº de buracos (buracos_antes - buracos_depois)."))
    param_diff = models.JSONField(_("parâmetros alterados"), default=dict, blank=True)
    status = models.CharField(_("status"), max_length=10, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    aplicado_em = models.DateTimeField(_("aplicada em"), null=True, blank=True)

    class Meta:
        verbose_name = _("sugestão")
        verbose_name_plural = _("sugestões")
        ordering = ["-delta"]
        indexes = [
            models.Index(fields=["school_year", "-created_at"], name="suggestion_school_year_created"),
            models.Index(fields=["solver_run"], name="suggestion_solver_run"),
        ]

    def __str__(self) -> str:
        return f"{self.get_categoria_display()}: {self.titulo}"

    @property
    def param_diff_json(self) -> str:
        import json

        return json.dumps(self.param_diff, indent=2, ensure_ascii=False)


# Auditlog registration (Sprint 08)
# -----------------------------------------------------------------------

from auditlog.registry import auditlog  # noqa: E402

auditlog.register(SolverVariant)
auditlog.register(SolverRun)
auditlog.register(Suggestion)
