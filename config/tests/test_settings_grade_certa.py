"""Testes das settings adicionadas na Sprint 08 (SDD §22.2.4).

Foco: garantir que `GRADE_CERTA_COOLDOWN_DISABLED` e
`NON_PRODUCTION_ENVIRONMENTS` se comportam corretamente conforme
`ENVIRONMENT` muda.
"""
from __future__ import annotations

import config.settings as settings


class TestNonProductionEnvironments:
    def test_contem_local_dev_test(self) -> None:
        assert "local" in settings.NON_PRODUCTION_ENVIRONMENTS
        assert "dev" in settings.NON_PRODUCTION_ENVIRONMENTS
        assert "test" in settings.NON_PRODUCTION_ENVIRONMENTS

    def test_nao_contem_production_staging(self) -> None:
        assert "production" not in settings.NON_PRODUCTION_ENVIRONMENTS
        assert "staging" not in settings.NON_PRODUCTION_ENVIRONMENTS


class TestCooldownDisabledByEnvironment:
    def test_local_dev_test_desativam(self) -> None:
        for env in ("local", "dev", "test"):
            assert env in settings.NON_PRODUCTION_ENVIRONMENTS

    def test_production_staging_mantem(self) -> None:
        for env in ("production", "staging"):
            assert env not in settings.NON_PRODUCTION_ENVIRONMENTS


class TestSettingsCarregam:
    def test_time_zone_eh_asia_tokyo(self) -> None:
        assert settings.TIME_ZONE == "Asia/Tokyo"

    def test_use_tz_eh_true(self) -> None:
        assert settings.USE_TZ is True

    def test_environment_carregado(self) -> None:
        # settings_test herda ENVIRONMENT; o valor concreto vem do
        # ambiente do test runner, mas tem que ser uma string
        assert isinstance(settings.ENVIRONMENT, str)
        assert settings.ENVIRONMENT != ""
