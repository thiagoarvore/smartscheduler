from datetime import date, time

import pytest
from django.core.exceptions import ValidationError

from apps.curriculum.models import CurriculumMatrix, Subject, WorkloadItem
from apps.people.models import Teacher, TeacherQualification
from apps.scheduling.models import (
    Conflict,
    LessonAssignment,
    LessonComponent,
    Timetable,
    TimetableSlot,
    TimetableVersion,
    Validation,
)
from apps.schools.models import (
    ClassGroup,
    Period,
    SchoolYear,
    Series,
    TeachingLevel,
    Unit,
)
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestTimetableModels:
    def test_timetable_rejects_related_records_from_other_tenants(self):
        tenant_a = Tenant.objects.create(name="Tenant A", schema_name="tenant_a")
        tenant_b = Tenant.objects.create(name="Tenant B", schema_name="tenant_b")
        unit = Unit.objects.create(
            tenant=tenant_a,
            name="Unidade A",
            status=Unit.StatusChoices.ACTIVE,
            default_settings={},
        )
        period = Period.objects.create(
            tenant=tenant_a,
            unit=unit,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        school_year = SchoolYear.objects.create(
            tenant=tenant_a,
            name="2026",
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=SchoolYear.StatusChoices.ACTIVE,
            is_active=True,
        )

        timetable = Timetable(
            tenant=tenant_b,
            unit=unit,
            period=period,
            school_year=school_year,
            name="Grade 2026",
            status=Timetable.StatusChoices.DRAFT,
            current_version_number=1,
        )

        with pytest.raises(ValidationError):
            timetable.full_clean()

    def test_timetable_slot_rejects_invalid_time_window(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
        unit = Unit.objects.create(
            tenant=tenant,
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
            default_settings={},
        )
        period = Period.objects.create(
            tenant=tenant,
            unit=unit,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        school_year = SchoolYear.objects.create(
            tenant=tenant,
            name="2026",
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=SchoolYear.StatusChoices.ACTIVE,
            is_active=True,
        )
        timetable = Timetable.objects.create(
            tenant=tenant,
            unit=unit,
            period=period,
            school_year=school_year,
            name="Grade 2026",
            status=Timetable.StatusChoices.DRAFT,
            current_version_number=1,
        )

        slot = TimetableSlot(
            timetable=timetable,
            weekday=TimetableSlot.WeekdayChoices.MONDAY,
            start_time=time(10, 0),
            end_time=time(9, 0),
            order=1,
            slot_type=TimetableSlot.SlotTypeChoices.CLASS,
            accepts_double_lesson=True,
        )

        with pytest.raises(ValidationError):
            slot.full_clean()


@pytest.mark.django_db
class TestSchedulingValidationFlow:
    def test_empty_class_slots_make_version_not_ready_for_publication(self):
        version, _assignments = _build_basic_timetable_version()

        validation = version.validate()

        assert isinstance(validation, Validation)
        assert validation.status == Validation.StatusChoices.INVALID
        assert version.is_ready_for_publication() is False
        assert validation.conflicts.filter(code=Conflict.CodeChoices.MISSING_ASSIGNMENT).count() == 2

    def test_double_lessons_must_use_consecutive_slots_on_same_day(self):
        version, assignments = _build_basic_timetable_version(double_lesson=True, consecutive=True)

        validation = version.validate()

        assert validation.status == Validation.StatusChoices.VALID
        assert version.is_ready_for_publication() is True
        assert validation.conflicts.count() == 0
        assert all(assignment.pk is not None for assignment in assignments)

    def test_non_consecutive_double_lessons_are_reported_as_conflicts(self):
        version, _assignments = _build_basic_timetable_version(double_lesson=True, consecutive=False)

        validation = version.validate()

        assert validation.status == Validation.StatusChoices.INVALID
        assert validation.conflicts.filter(code=Conflict.CodeChoices.DOUBLE_LESSON_SEQUENCE).exists()

    def test_teacher_overlap_is_reported_as_conflict(self):
        version, _assignments = _build_basic_timetable_version(include_teacher_overlap=True)

        validation = version.validate()

        assert validation.status == Validation.StatusChoices.INVALID
        assert validation.conflicts.filter(code=Conflict.CodeChoices.TEACHER_OVERLAP).exists()


def _build_basic_timetable_version(double_lesson=False, consecutive=True, include_teacher_overlap=False):
    tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")
    unit = Unit.objects.create(
        tenant=tenant,
        name="Unidade Centro",
        status=Unit.StatusChoices.ACTIVE,
        default_settings={},
    )
    period = Period.objects.create(
        tenant=tenant,
        unit=unit,
        name="Manhã",
        type=Period.TypeChoices.MORNING,
        order=1,
        status=Period.StatusChoices.ACTIVE,
    )
    school_year = SchoolYear.objects.create(
        tenant=tenant,
        name="2026",
        year=2026,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        status=SchoolYear.StatusChoices.ACTIVE,
        is_active=True,
    )
    teaching_level = TeachingLevel.objects.create(
        tenant=tenant,
        name="Fundamental II",
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
        code="MAT",
        name="Matemática",
        status=Subject.StatusChoices.ACTIVE,
    )
    curriculum_matrix = CurriculumMatrix.objects.create(
        tenant=tenant,
        name="Matriz EF2",
        teaching_level=teaching_level,
        series=series,
        version="2026",
        status=CurriculumMatrix.StatusChoices.ACTIVE,
    )
    WorkloadItem.objects.create(
        tenant=tenant,
        curriculum_matrix=curriculum_matrix,
        subject=subject,
        series=series,
        class_group=class_group,
        weekly_lessons=2,
        lesson_duration_min=50,
        is_double_lesson=double_lesson,
        can_share=False,
    )

    timetable = Timetable.objects.create(
        tenant=tenant,
        unit=unit,
        period=period,
        school_year=school_year,
        name="Grade 2026",
        status=Timetable.StatusChoices.DRAFT,
        current_version_number=1,
    )
    slot_1 = TimetableSlot.objects.create(
        timetable=timetable,
        weekday=TimetableSlot.WeekdayChoices.MONDAY,
        start_time=time(8, 0),
        end_time=time(8, 50),
        order=1,
        slot_type=TimetableSlot.SlotTypeChoices.CLASS,
        accepts_double_lesson=True,
    )
    slot_2 = TimetableSlot.objects.create(
        timetable=timetable,
        weekday=TimetableSlot.WeekdayChoices.MONDAY,
        start_time=time(8, 50),
        end_time=time(9, 40),
        order=2,
        slot_type=TimetableSlot.SlotTypeChoices.CLASS,
        accepts_double_lesson=True,
    )
    slot_3 = None
    if not double_lesson or not consecutive or include_teacher_overlap:
        slot_3 = TimetableSlot.objects.create(
            timetable=timetable,
            weekday=TimetableSlot.WeekdayChoices.MONDAY,
            start_time=time(9, 40),
            end_time=time(10, 30),
            order=3,
            slot_type=TimetableSlot.SlotTypeChoices.CLASS,
            accepts_double_lesson=True,
        )

    teacher = Teacher.objects.create(
        tenant=tenant,
        name="Maria Souza",
        email="maria.souza@gradecerta.com",
        status=Teacher.StatusChoices.ACTIVE,
    )
    TeacherQualification.objects.create(
        tenant=tenant,
        teacher=teacher,
        subject=subject,
        teaching_level=teaching_level,
        series=series,
        unit=unit,
        status=TeacherQualification.StatusChoices.ACTIVE,
    )

    version = TimetableVersion.objects.create(
        tenant=tenant,
        timetable=timetable,
        version_number=1,
        name="Versão 1",
        status=TimetableVersion.StatusChoices.DRAFT,
        is_current=True,
    )

    assignments = [
        LessonAssignment.objects.create(
            tenant=tenant,
            timetable_version=version,
            class_group=class_group,
            slot=slot_1,
            subject=subject,
            teacher=teacher,
            status=LessonAssignment.StatusChoices.PLANNED,
            allocation_source_type=LessonAssignment.AllocationSourceTypeChoices.MANUAL,
            notes="Primeira aula",
        ),
    ]

    if double_lesson:
        assignments.append(
            LessonAssignment.objects.create(
                tenant=tenant,
                timetable_version=version,
                class_group=class_group,
                slot=slot_2,
                subject=subject,
                teacher=teacher,
                status=LessonAssignment.StatusChoices.PLANNED,
                allocation_source_type=LessonAssignment.AllocationSourceTypeChoices.MANUAL,
                notes="Segunda aula",
            )
        )

    if double_lesson and not consecutive:
        assignments[1].slot = slot_3
        assignments[1].save(update_fields=["slot"])

    if include_teacher_overlap:
        other_class_group = ClassGroup.objects.create(
            tenant=tenant,
            unit=unit,
            period=period,
            series=series,
            name="6º ano B",
            status=ClassGroup.StatusChoices.ACTIVE,
        )
        LessonAssignment.objects.create(
            tenant=tenant,
            timetable_version=version,
            class_group=other_class_group,
            slot=slot_1,
            subject=subject,
            teacher=teacher,
            status=LessonAssignment.StatusChoices.PLANNED,
            allocation_source_type=LessonAssignment.AllocationSourceTypeChoices.MANUAL,
            notes="Conflito de professor",
        )

    return version, assignments


@pytest.mark.django_db
class TestSchedulingAuditlogRegistration:
    def test_scheduling_models_are_registered_for_auditlog(self):
        from auditlog.registry import auditlog

        assert Timetable in auditlog._registry
        assert TimetableSlot in auditlog._registry
        assert TimetableVersion in auditlog._registry
        assert LessonAssignment in auditlog._registry
        assert LessonComponent in auditlog._registry
        assert Validation in auditlog._registry
        assert Conflict in auditlog._registry
