import pytest
from django.core.exceptions import ValidationError

from apps.schools.models import ClassGroup, Period, Series, TeachingLevel, Unit
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestSchoolStructureModels:
    def test_school_structure_models_can_be_created_and_linked(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        unit = Unit.objects.create(
            tenant=tenant,
            code="UN-01",
            name="Unidade Centro",
            status=Unit.StatusChoices.ACTIVE,
        )
        teaching_level = TeachingLevel.objects.create(
            tenant=tenant,
            code="EF2",
            name="Ensino Fundamental II",
            order=1,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        period = Period.objects.create(
            tenant=tenant,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        period.units.add(unit)
        series = Series.objects.create(
            tenant=tenant,
            teaching_level=teaching_level,
            code="6ANO",
            name="6º ano",
            order=6,
            status=Series.StatusChoices.ACTIVE,
        )
        class_group = ClassGroup.objects.create(
            tenant=tenant,
            unit=unit,
            period=period,
            series=series,
            code="6A",
            name="6º ano A",
            status=ClassGroup.StatusChoices.ACTIVE,
        )

        assert unit.tenant == tenant
        assert str(unit) == "Unidade Centro"
        assert unit in period.units.all()
        assert period.tenant == tenant
        assert str(period) == "Manhã"
        assert series.teaching_level == teaching_level
        assert str(series) == "6º ano"
        assert class_group.unit == unit
        assert class_group.period == period
        assert class_group.series == series
        assert str(class_group) == "6º ano A"

    def test_period_units_m2m_links_to_units(self):
        """Period → units is M2M; a period can belong to multiple units."""
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste2")
        unit_a = Unit.objects.create(
            tenant=tenant, name="Unidade A", status=Unit.StatusChoices.ACTIVE
        )
        unit_b = Unit.objects.create(
            tenant=tenant, name="Unidade B", status=Unit.StatusChoices.ACTIVE
        )
        period = Period.objects.create(
            tenant=tenant,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        period.units.add(unit_a, unit_b)

        assert unit_a in period.units.all()
        assert unit_b in period.units.all()
        assert period.units.count() == 2

    def test_class_group_rejects_related_records_from_other_tenants(self):
        tenant_a = Tenant.objects.create(name="Tenant A", schema_name="tenant_a")
        tenant_b = Tenant.objects.create(name="Tenant B", schema_name="tenant_b")

        unit = Unit.objects.create(
            tenant=tenant_a,
            name="Unidade A",
            status=Unit.StatusChoices.ACTIVE,
        )
        period = Period.objects.create(
            tenant=tenant_a,
            name="Manhã",
            type=Period.TypeChoices.MORNING,
            order=1,
            status=Period.StatusChoices.ACTIVE,
        )
        period.units.add(unit)
        teaching_level = TeachingLevel.objects.create(
            tenant=tenant_b,
            name="Ensino Médio",
            order=1,
            status=TeachingLevel.StatusChoices.ACTIVE,
        )
        series = Series(
            tenant=tenant_a,
            teaching_level=teaching_level,
            name="1ª série",
            order=1,
            status=Series.StatusChoices.ACTIVE,
        )

        with pytest.raises(ValidationError):
            series.full_clean()


@pytest.mark.django_db
class TestSchoolsAuditlogRegistration:
    def test_school_models_are_registered_for_auditlog(self):
        from auditlog.registry import auditlog

        assert Unit in auditlog._registry
        assert TeachingLevel in auditlog._registry
        assert Period in auditlog._registry
        assert Series in auditlog._registry
        assert ClassGroup in auditlog._registry