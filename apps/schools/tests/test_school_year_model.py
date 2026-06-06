from datetime import date

import pytest

from apps.schools.models import SchoolYear
from apps.tenants.models import Tenant


@pytest.mark.django_db
class TestSchoolYearModel:
    def test_school_year_can_be_created_for_a_tenant(self):
        tenant = Tenant.objects.create(name="Escola Teste", schema_name="escola_teste")

        school_year = SchoolYear.objects.create(
            tenant=tenant,
            name="Ano Letivo 2026",
            year=2026,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            status=SchoolYear.StatusChoices.ACTIVE,
            is_active=True,
        )

        assert school_year.pk is not None
        assert school_year.tenant == tenant
        assert school_year.year == 2026
        assert str(school_year) == "Ano Letivo 2026"
