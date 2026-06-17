"""Testes do campo suggestions_enabled em SchoolYear (Sprint 09).

Como o settings_test.py usa SQLite sem django-tenants, montamos
um schema isolado com `Tenant` via `Tenant.objects.create`.
"""
from __future__ import annotations

import pytest

from apps.schools.models import SchoolYear
from apps.tenants.models import Tenant


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(
        schema_name="test_schema_sug",
        name="Test Tenant Sug",
    )


@pytest.fixture
def school_year(tenant, db):
    return SchoolYear.objects.create(
        tenant=tenant,
        name="2026 Sug",
        year=2026,
        start_date="2026-02-01",
        end_date="2026-12-15",
    )


class TestSchoolYearSuggestionsEnabled:
    def test_default_is_true(self, school_year) -> None:
        """O campo suggestions_enabled deve ter default=True."""
        assert school_year.suggestions_enabled is True

    def test_can_set_to_false(self, school_year, db) -> None:
        """É possível desativar sugestões para o ano letivo."""
        school_year.suggestions_enabled = False
        school_year.save()
        school_year.refresh_from_db()
        assert school_year.suggestions_enabled is False

    def test_can_toggle_back_to_true(self, school_year, db) -> None:
        """É possível reativar sugestões após desativar."""
        school_year.suggestions_enabled = False
        school_year.save()
        school_year.suggestions_enabled = True
        school_year.save()
        school_year.refresh_from_db()
        assert school_year.suggestions_enabled is True

    def test_new_school_year_has_suggestions_enabled(self, tenant, db) -> None:
        """Novos SchoolYears: sugestões ativadas por padrão."""
        sy = SchoolYear.objects.create(
            tenant=tenant,
            name="2027",
            year=2027,
            start_date="2027-02-01",
            end_date="2027-12-15",
        )
        assert sy.suggestions_enabled is True

    def test_multiple_school_years_independent(self, tenant, db) -> None:
        """Cada SchoolYear tem seu próprio suggestions_enabled."""
        sy_on = SchoolYear.objects.create(
            tenant=tenant,
            name="2026 ON",
            year=2026,
            start_date="2026-02-01",
            end_date="2026-12-15",
            suggestions_enabled=True,
        )
        sy_off = SchoolYear.objects.create(
            tenant=tenant,
            name="2026 OFF",
            year=2026,
            start_date="2026-02-01",
            end_date="2026-12-15",
            suggestions_enabled=False,
        )
        assert sy_on.suggestions_enabled is True
        assert sy_off.suggestions_enabled is False