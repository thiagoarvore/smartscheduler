import uuid
from datetime import time

import pytest
from django.core.exceptions import ValidationError

from apps.people.models import Teacher, TeacherAvailability, TeacherQualification
from apps.schools.models import Series, TeachingLevel, Unit
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestTeacherModel:
    def test_teacher_can_be_created_for_a_tenant(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        teacher = Teacher.objects.create(
            tenant=tenant,
            code="PROF-01",
            name="Maria Souza",
            email="maria.souza@gradecerta.com",
            phone_number="(11) 99999-0000",
            status=Teacher.StatusChoices.ACTIVE,
            max_weekly_load=20,
            notes="Disponível apenas no período da manhã.",
        )

        assert teacher.pk is not None
        assert isinstance(teacher.pk, uuid.UUID)
        assert teacher.tenant == tenant
        assert teacher.name == "Maria Souza"
        assert str(teacher) == "Maria Souza"
        assert teacher.max_weekly_load == 20
        assert teacher.active is True

    def test_teacher_is_unavailable_when_no_availability_is_registered(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        teacher = Teacher.objects.create(
            tenant=tenant,
            name="Maria Souza",
            status=Teacher.StatusChoices.ACTIVE,
        )

        assert teacher.is_available_at(TeacherAvailability.WeekdayChoices.MONDAY, time(8, 0)) is False

    def test_teacher_uses_explicit_availability_and_blocks_unavailable_windows(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        teacher = Teacher.objects.create(
            tenant=tenant,
            name="Maria Souza",
            status=Teacher.StatusChoices.ACTIVE,
        )
        TeacherAvailability.objects.create(
            tenant=tenant,
            teacher=teacher,
            weekday=TeacherAvailability.WeekdayChoices.MONDAY,
            start_time=time(7, 0),
            end_time=time(12, 0),
            is_available=True,
        )
        TeacherAvailability.objects.create(
            tenant=tenant,
            teacher=teacher,
            weekday=TeacherAvailability.WeekdayChoices.MONDAY,
            start_time=time(9, 0),
            end_time=time(10, 0),
            is_available=False,
            reason="Reunião pedagógica.",
        )

        assert teacher.is_available_at(TeacherAvailability.WeekdayChoices.MONDAY, time(8, 0)) is True
        assert teacher.is_available_at(TeacherAvailability.WeekdayChoices.MONDAY, time(9, 30)) is False
        assert teacher.is_available_at(TeacherAvailability.WeekdayChoices.MONDAY, time(12, 30)) is False


@pytest.mark.django_db
class TestTeacherQualificationAndAvailabilityModels:
    def test_teacher_qualification_rejects_related_entities_from_other_tenants(self):
        tenant_a = Tenant.objects.create(name="Tenant A", schema_name="tenant_a")
        tenant_b = Tenant.objects.create(name="Tenant B", schema_name="tenant_b")
        teacher = Teacher.objects.create(
            tenant=tenant_a,
            name="Maria Souza",
            status=Teacher.StatusChoices.ACTIVE,
        )
        subject = Unit.objects.create(
            tenant=tenant_b,
            name="Unidade B",
            status=Unit.StatusChoices.ACTIVE,
            default_settings={},
        )

        qualification = TeacherQualification(
            tenant=tenant_a,
            teacher=teacher,
            unit=subject,
            status=TeacherQualification.StatusChoices.ACTIVE,
        )

        with pytest.raises(ValidationError):
            qualification.full_clean()

    def test_teacher_availability_rejects_invalid_time_window(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        teacher = Teacher.objects.create(
            tenant=tenant,
            name="Maria Souza",
            status=Teacher.StatusChoices.ACTIVE,
        )

        availability = TeacherAvailability(
            tenant=tenant,
            teacher=teacher,
            weekday=TeacherAvailability.WeekdayChoices.MONDAY,
            start_time=time(12, 0),
            end_time=time(11, 0),
            is_available=True,
        )

        with pytest.raises(ValidationError):
            availability.full_clean()

    def test_teacher_qualification_accepts_matching_tenant_scope(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        teacher = Teacher.objects.create(
            tenant=tenant,
            name="Maria Souza",
            status=Teacher.StatusChoices.ACTIVE,
        )
        unit = Unit.objects.create(
            tenant=tenant,
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
            default_settings={},
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

        qualification = TeacherQualification(
            tenant=tenant,
            teacher=teacher,
            unit=unit,
            teaching_level=teaching_level,
            series=series,
            status=TeacherQualification.StatusChoices.ACTIVE,
        )
        qualification.full_clean()
        qualification.save()

        assert qualification.pk is not None
        assert qualification.teacher == teacher
        assert qualification.unit == unit
        assert qualification.teaching_level == teaching_level
        assert qualification.series == series


@pytest.mark.django_db
class TestPeopleAuditlogRegistration:
    def test_people_models_are_registered_for_auditlog(self):
        from auditlog.registry import auditlog

        assert Teacher in auditlog._registry
        assert TeacherQualification in auditlog._registry
        assert TeacherAvailability in auditlog._registry
