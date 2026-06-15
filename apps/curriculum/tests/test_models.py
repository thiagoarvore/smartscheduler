import pytest
from django.apps import apps
from django.core.exceptions import ValidationError

from apps.curriculum.models import (
    CurriculumMatrix,
    InheritanceRule,
    LocalException,
    Subject,
    SubjectRule,
    WorkloadItem,
)
from apps.schools.models import ClassGroup, Period, Series, TeachingLevel, Unit
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestCurriculumSubjectModel:
    def test_subject_model_can_be_loaded_and_created(self):
        subject_model = apps.get_model("curriculum", "Subject")
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        subject = subject_model.objects.create(
            tenant=tenant,
            code="MAT",
            name="Matemática",
            slug="matematica",
            status=subject_model.StatusChoices.ACTIVE,
        )

        assert subject.pk is not None
        assert subject.tenant == tenant
        assert str(subject) == "Matemática"


@pytest.mark.django_db
class TestCurriculumMatrixAndWorkloadModels:
    def test_curriculum_matrix_rejects_series_from_other_teaching_level(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        teaching_level = TeachingLevel.objects.create(
            tenant=tenant,
            name="Ensino Fundamental II",
            order=1,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        other_teaching_level = TeachingLevel.objects.create(
            tenant=tenant,
            name="Ensino Médio",
            order=2,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        series = Series.objects.create(
            tenant=tenant,
            teaching_level=other_teaching_level,
            name="1ª série EM",
            order=1,
            status=Series.StatusChoices.ACTIVE,
        )

        matrix = CurriculumMatrix(
            tenant=tenant,
            name="Matriz EF2",
            teaching_level=teaching_level,
            series=series,
            version="2026",
            status=CurriculumMatrix.StatusChoices.ACTIVE,
        )

        with pytest.raises(ValidationError):
            matrix.full_clean()

    def test_workload_item_requires_consistent_tenant_and_series(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        unit = Unit.objects.create(
            tenant=tenant,
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
        )
        teaching_level = TeachingLevel.objects.create(
            tenant=tenant,
            name="Ensino Fundamental II",
            order=1,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        series = Series.objects.create(
            tenant=tenant,
            teaching_level=teaching_level,
            name="6º ano",
            order=6,
            status=Series.StatusChoices.ACTIVE,
        )
        period = Period.objects.create(
            tenant=tenant,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        period.units.add(unit)
        class_group = ClassGroup.objects.create(
            tenant=tenant,
            unit=unit,
            period=period,
            series=series,
            name="6º ano A",
            status=ClassGroup.StatusChoices.ACTIVE,
        )
        subject = Subject.objects.create(
            tenant=tenant,
            name="Matemática",
            status=Subject.StatusChoices.ACTIVE,
        )
        matrix = CurriculumMatrix.objects.create(
            tenant=tenant,
            name="Matriz EF2",
            teaching_level=teaching_level,
            series=series,
            version="2026",
            status=CurriculumMatrix.StatusChoices.ACTIVE,
        )

        item = WorkloadItem(
            tenant=tenant,
            curriculum_matrix=matrix,
            subject=subject,
            series=series,
            class_group=class_group,
            weekly_lessons=5,
            lesson_duration_min=50,
            is_double_lesson=False,
            can_share=False,
        )

        item.full_clean()
        item.save()

        assert item.pk is not None
        assert str(item) == "Matemática — 5 aulas"

    def test_workload_item_rejects_series_mismatch_with_class_group(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        unit = Unit.objects.create(
            tenant=tenant,
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
        )
        teaching_level = TeachingLevel.objects.create(
            tenant=tenant,
            name="Ensino Fundamental II",
            order=1,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        series_a = Series.objects.create(
            tenant=tenant,
            teaching_level=teaching_level,
            name="6º ano",
            order=6,
            status=Series.StatusChoices.ACTIVE,
        )
        series_b = Series.objects.create(
            tenant=tenant,
            teaching_level=teaching_level,
            name="7º ano",
            order=7,
            status=Series.StatusChoices.ACTIVE,
        )
        period = Period.objects.create(
            tenant=tenant,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        period.units.add(unit)
        class_group = ClassGroup.objects.create(
            tenant=tenant,
            unit=unit,
            period=period,
            series=series_a,
            name="6º ano A",
            status=ClassGroup.StatusChoices.ACTIVE,
        )
        subject = Subject.objects.create(
            tenant=tenant,
            name="História",
            status=Subject.StatusChoices.ACTIVE,
        )
        matrix = CurriculumMatrix.objects.create(
            tenant=tenant,
            name="Matriz EF2",
            teaching_level=teaching_level,
            version="2026",
            status=CurriculumMatrix.StatusChoices.ACTIVE,
        )

        item = WorkloadItem(
            tenant=tenant,
            curriculum_matrix=matrix,
            subject=subject,
            series=series_b,
            class_group=class_group,
            weekly_lessons=2,
            lesson_duration_min=50,
            is_double_lesson=False,
            can_share=False,
        )

        with pytest.raises(ValidationError):
            item.full_clean()


@pytest.mark.django_db
class TestCurriculumInheritanceModels:
    def test_local_exception_requires_rule_from_same_tenant(self):
        tenant_a = Tenant.objects.create(name="Tenant A", schema_name="tenant_a")
        tenant_b = Tenant.objects.create(name="Tenant B", schema_name="tenant_b")

        inheritance_rule = InheritanceRule.objects.create(
            tenant=tenant_a,
            source_type=InheritanceRule.SourceTargetChoices.TEACHING_LEVEL,
            source_id="11111111-1111-1111-1111-111111111111",
            target_type=InheritanceRule.SourceTargetChoices.SERIES,
            target_id="22222222-2222-2222-2222-222222222222",
            rule_type=InheritanceRule.RuleTypeChoices.CURRICULUM_SCOPE,
            priority=10,
            is_active=True,
        )
        exception = LocalException(
            tenant=tenant_b,
            inheritance_rule=inheritance_rule,
            scope_type=LocalException.ScopeChoices.SERIES,
            scope_id="33333333-3333-3333-3333-333333333333",
            original_value={"weekly_lessons": 5},
            override_value={"weekly_lessons": 6},
            reason="Ajuste local",
            is_active=True,
        )

        with pytest.raises(ValidationError):
            exception.full_clean()

    def test_subject_rule_is_creatable(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        rule = SubjectRule.objects.create(
            tenant=tenant,
            rule_type=SubjectRule.RuleTypeChoices.DOUBLE_LESSON,
            payload={"preferred": True},
            is_active=True,
            notes="Preferir blocos duplos em laboratório",
        )

        assert rule.pk is not None
        assert rule.payload == {"preferred": True}


@pytest.mark.django_db
class TestCurriculumAuditlogRegistration:
    def test_curriculum_models_are_registered_for_auditlog(self):
        from auditlog.registry import auditlog

        assert Subject in auditlog._registry
        assert CurriculumMatrix in auditlog._registry
        assert WorkloadItem in auditlog._registry
        assert SubjectRule in auditlog._registry
        assert InheritanceRule in auditlog._registry
        assert LocalException in auditlog._registry
