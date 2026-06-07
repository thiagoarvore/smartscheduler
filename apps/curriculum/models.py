from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_base_kit.models import BaseModel


class Subject(BaseModel):
    class StatusChoices(models.TextChoices):
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subjects",
        verbose_name=_("tenant"),
    )
    code = models.CharField(_("código"), max_length=50, blank=True)
    name = models.CharField(_("nome"), max_length=200)
    slug = models.SlugField(_("slug"), blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
    )

    class Meta:
        verbose_name = _("disciplina")
        verbose_name_plural = _("disciplinas")
        ordering = ["name"]

    def __str__(self):
        return self.name


class CurriculumMatrix(BaseModel):
    class StatusChoices(models.TextChoices):
        DRAFT = "draft", _("Rascunho")
        ACTIVE = "active", _("Ativa")
        INACTIVE = "inactive", _("Inativa")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="curriculum_matrices",
        verbose_name=_("tenant"),
    )
    name = models.CharField(_("nome"), max_length=200)
    teaching_level = models.ForeignKey(
        "schools.TeachingLevel",
        on_delete=models.CASCADE,
        related_name="curriculum_matrices",
        verbose_name=_("nível de ensino"),
    )
    series = models.ForeignKey(
        "schools.Series",
        on_delete=models.CASCADE,
        related_name="curriculum_matrices",
        verbose_name=_("série"),
        null=True,
        blank=True,
    )
    version = models.CharField(_("versão"), max_length=50)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )
    effective_from = models.DateField(_("vigente desde"), null=True, blank=True)
    effective_to = models.DateField(_("vigente até"), null=True, blank=True)

    class Meta:
        verbose_name = _("matriz curricular")
        verbose_name_plural = _("matrizes curriculares")
        ordering = ["name", "version"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.teaching_level_id and self.teaching_level.tenant_id != self.tenant_id:
            errors["teaching_level"] = _("O nível de ensino deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.series_id and self.series.tenant_id != self.tenant_id:
            errors["series"] = _("A série deve pertencer ao mesmo tenant.")
        if self.series_id and self.teaching_level_id and self.series.teaching_level_id != self.teaching_level_id:
            errors["series"] = _("A série deve pertencer ao mesmo nível de ensino da matriz.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} v{self.version}"


class WorkloadItem(BaseModel):
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="workload_items",
        verbose_name=_("tenant"),
    )
    curriculum_matrix = models.ForeignKey(
        CurriculumMatrix,
        on_delete=models.CASCADE,
        related_name="workload_items",
        verbose_name=_("matriz curricular"),
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="workload_items",
        verbose_name=_("disciplina"),
    )
    series = models.ForeignKey(
        "schools.Series",
        on_delete=models.CASCADE,
        related_name="workload_items",
        verbose_name=_("série"),
    )
    class_group = models.ForeignKey(
        "schools.ClassGroup",
        on_delete=models.CASCADE,
        related_name="workload_items",
        verbose_name=_("turma"),
        null=True,
        blank=True,
    )
    weekly_lessons = models.PositiveIntegerField(_("aulas semanais"))
    lesson_duration_min = models.PositiveIntegerField(_("duração da aula em minutos"))
    is_double_lesson = models.BooleanField(_("aula dupla"), default=False)
    can_share = models.BooleanField(_("pode compartilhar horário"), default=False)
    notes = models.TextField(_("observações"), blank=True)

    class Meta:
        verbose_name = _("item de carga horária")
        verbose_name_plural = _("itens de carga horária")
        ordering = ["curriculum_matrix__name", "subject__name"]

    def clean(self):
        super().clean()
        errors = {}
        if self.tenant_id and self.curriculum_matrix_id and self.curriculum_matrix.tenant_id != self.tenant_id:
            errors["curriculum_matrix"] = _("A matriz curricular deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.subject_id and self.subject.tenant_id != self.tenant_id:
            errors["subject"] = _("A disciplina deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.series_id and self.series.tenant_id != self.tenant_id:
            errors["series"] = _("A série deve pertencer ao mesmo tenant.")
        if self.tenant_id and self.class_group_id and self.class_group.tenant_id != self.tenant_id:
            errors["class_group"] = _("A turma deve pertencer ao mesmo tenant.")
        if self.class_group_id and self.series_id and self.class_group.series_id != self.series_id:
            errors["class_group"] = _("A turma deve pertencer à mesma série do item de carga horária.")
        if self.curriculum_matrix_id and self.series_id and self.curriculum_matrix.series_id and self.curriculum_matrix.series_id != self.series_id:
            errors["series"] = _("A série deve coincidir com a série da matriz curricular.")
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.subject.name} — {self.weekly_lessons} aulas"


class SubjectRule(BaseModel):
    class RuleTypeChoices(models.TextChoices):
        WEEKLY_LOAD = "weekly_load", _("Carga semanal")
        DOUBLE_LESSON = "double_lesson", _("Aula dupla")
        SHARE_ALLOWED = "share_allowed", _("Compartilhamento")
        DISTRIBUTION = "distribution", _("Distribuição semanal")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="subject_rules",
        verbose_name=_("tenant"),
    )
    rule_type = models.CharField(_("tipo da regra"), max_length=50, choices=RuleTypeChoices.choices)
    payload = models.JSONField(_("payload"), default=dict)
    is_active = models.BooleanField(_("ativo"), default=True)
    notes = models.TextField(_("observações"), blank=True)

    class Meta:
        verbose_name = _("regra de disciplina")
        verbose_name_plural = _("regras de disciplina")
        ordering = ["rule_type", "id"]

    def __str__(self):
        return self.get_rule_type_display()


class InheritanceRule(BaseModel):
    class SourceTargetChoices(models.TextChoices):
        TENANT = "tenant", _("Tenant")
        TEACHING_LEVEL = "teaching_level", _("Nível de ensino")
        SERIES = "series", _("Série")
        UNIT = "unit", _("Unidade")
        CLASS_GROUP = "class_group", _("Turma")
        CURRICULUM_MATRIX = "curriculum_matrix", _("Matriz curricular")
        WORKLOAD_ITEM = "workload_item", _("Item de carga horária")
        SUBJECT = "subject", _("Disciplina")

    class RuleTypeChoices(models.TextChoices):
        WEEKLY_LOAD = "weekly_load", _("Carga semanal")
        SUBJECT = "subject", _("Disciplina")
        DOUBLE_LESSON = "double_lesson", _("Aula dupla")
        SHARE_ALLOWED = "share_allowed", _("Compartilhamento")
        CURRICULUM_SCOPE = "curriculum_scope", _("Escopo curricular")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="inheritance_rules",
        verbose_name=_("tenant"),
    )
    source_type = models.CharField(_("tipo de origem"), max_length=50, choices=SourceTargetChoices.choices)
    source_id = models.UUIDField(_("origem"))
    target_type = models.CharField(_("tipo de destino"), max_length=50, choices=SourceTargetChoices.choices)
    target_id = models.UUIDField(_("destino"))
    rule_type = models.CharField(_("tipo da regra"), max_length=50, choices=RuleTypeChoices.choices)
    priority = models.IntegerField(_("prioridade"), default=0)
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("regra de herança")
        verbose_name_plural = _("regras de herança")
        ordering = ["-priority", "id"]

    def __str__(self):
        return f"{self.get_rule_type_display()} ({self.source_type}→{self.target_type})"


class LocalException(BaseModel):
    class ScopeChoices(models.TextChoices):
        TEACHING_LEVEL = "teaching_level", _("Nível de ensino")
        SERIES = "series", _("Série")
        UNIT = "unit", _("Unidade")
        CLASS_GROUP = "class_group", _("Turma")
        CURRICULUM_MATRIX = "curriculum_matrix", _("Matriz curricular")
        WORKLOAD_ITEM = "workload_item", _("Item de carga horária")
        SUBJECT = "subject", _("Disciplina")

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="local_exceptions",
        verbose_name=_("tenant"),
    )
    inheritance_rule = models.ForeignKey(
        InheritanceRule,
        on_delete=models.CASCADE,
        related_name="local_exceptions",
        verbose_name=_("regra de herança"),
    )
    scope_type = models.CharField(_("tipo de escopo"), max_length=50, choices=ScopeChoices.choices)
    scope_id = models.UUIDField(_("escopo"))
    original_value = models.JSONField(_("valor original"), default=dict)
    override_value = models.JSONField(_("valor sobrescrito"), default=dict)
    reason = models.TextField(_("motivo"))
    is_active = models.BooleanField(_("ativo"), default=True)

    class Meta:
        verbose_name = _("exceção local")
        verbose_name_plural = _("exceções locais")
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.tenant_id and self.inheritance_rule_id and self.inheritance_rule.tenant_id != self.tenant_id:
            raise ValidationError({"inheritance_rule": _("A regra de herança deve pertencer ao mesmo tenant.")})

    def __str__(self):
        return self.reason
