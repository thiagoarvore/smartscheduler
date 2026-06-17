"""Testes da camada de sugestões (Sprint 09 §3.3, §3.4, §22.4.8).

Testa SuggestionsService, run_suggestions_layer e modelo Suggestion.
Segue o padrão de test_scheduler_tasks.py — funções puras, sem Celery.
"""
from __future__ import annotations

import uuid

import pytest

from apps.scheduling.models import SolverRun, SolverVariant, Suggestion
from apps.scheduling.services.suggestions import (
    MAX_SUGGESTIONS_PER_CATEGORY,
    SuggestionsService,
    SuggestionsServiceError,
)
from apps.scheduling.services.solver import (
    Aula,
    Disponibilidade,
    Slot,
    Timetable,
    greedy_construct,
)
from apps.scheduling.tasks import run_suggestions_layer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant(db):
    from apps.tenants.models import Tenant

    return Tenant.objects.create(schema_name="t_sug", name="Tenant Sugestões")


@pytest.fixture
def school_year(tenant, db):
    from apps.schools.models import SchoolYear

    return SchoolYear.objects.create(
        tenant=tenant,
        name="2026",
        year=2026,
        start_date="2026-02-01",
        end_date="2026-12-15",
        suggestions_enabled=True,
    )


@pytest.fixture
def school_year_disabled(tenant, db):
    from apps.schools.models import SchoolYear

    return SchoolYear.objects.create(
        tenant=tenant,
        name="2027",
        year=2027,
        start_date="2027-02-01",
        end_date="2027-12-15",
        suggestions_enabled=False,
    )


@pytest.fixture
def variant_a(tenant, db):
    return SolverVariant.objects.create(
        tenant=tenant,
        nome=SolverVariant.NomeChoices.A_RESTART,
        is_active=True,
        parametros={"max_restarts": 5},
    )


@pytest.fixture
def solver_run_with_buracos(tenant, school_year, variant_a, db):
    """SolverRun com buracos > 0, pronto para a camada de sugestões."""
    return SolverRun.objects.create(
        tenant=tenant,
        variant=variant_a,
        school_year=school_year,
        status=SolverRun.StatusChoices.SUCCESS,
        buracos=5,
        completude=0.7,
        suggestions_status=SolverRun.SuggestionsStatusChoices.NOT_RUN,
    )


@pytest.fixture
def solver_run_zero_buracos(tenant, school_year, variant_a, db):
    """SolverRun com 0 buracos — camada de sugestões desativada."""
    return SolverRun.objects.create(
        tenant=tenant,
        variant=variant_a,
        school_year=school_year,
        status=SolverRun.StatusChoices.SUCCESS,
        buracos=0,
        completude=1.0,
        suggestions_status=SolverRun.SuggestionsStatusChoices.NOT_RUN,
    )


# ---------------------------------------------------------------------------
# SuggestionsService — Validação
# ---------------------------------------------------------------------------


class TestSuggestionsServiceValidation:
    def test_raises_when_zero_buracos(self, solver_run_zero_buracos, db):
        service = SuggestionsService(solver_run_zero_buracos)
        with pytest.raises(SuggestionsServiceError, match="buracos=0"):
            service.run_all_categories()

    def test_raises_when_suggestions_disabled(
        self, tenant, school_year_disabled, variant_a, db
    ):
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year_disabled,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
            completude=0.7,
        )
        service = SuggestionsService(run)
        with pytest.raises(SuggestionsServiceError, match="suggestions_enabled=False"):
            service.run_all_categories()

    def test_raises_when_buracos_none(self, tenant, school_year, variant_a, db):
        """buracos=None é tratado como 0 via `or 0`, então dispara com buracos=0."""
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=None,
            completude=0.7,
        )
        service = SuggestionsService(run)
        # None → 0 via `buracos or 0`, então o erro fala buracos=0
        with pytest.raises(SuggestionsServiceError, match="buracos=0"):
            service.run_all_categories()


# ---------------------------------------------------------------------------
# SuggestionsService — Categoria workload_increase
# ---------------------------------------------------------------------------


class TestWorkloadIncrease:
    def test_creates_suggestion_when_improvement(
        self, tenant, school_year, variant_a, db
    ):
        """Com buracos > 0 e um WorkloadItem, verifica que não crasha."""
        from apps.curriculum.models import CurriculumMatrix, Subject, WorkloadItem
        from apps.schools.models import Series, TeachingLevel

        teaching_level = TeachingLevel.objects.create(
            tenant=tenant, name="Fundamental II", order=1
        )
        series = Series.objects.create(
            tenant=tenant,
            name="7º Ano",
            teaching_level=teaching_level,
            order=1,
        )
        subject = Subject.objects.create(tenant=tenant, name="Matemática")
        matrix = CurriculumMatrix.objects.create(
            tenant=tenant,
            name="Matriz Teste",
            teaching_level=teaching_level,
            series=series,
            version="1",
        )
        WorkloadItem.objects.create(
            tenant=tenant,
            curriculum_matrix=matrix,
            subject=subject,
            series=series,
            weekly_lessons=3,
            lesson_duration_min=45,
        )

        solver_run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=2,
            completude=0.8,
        )

        service = SuggestionsService(solver_run)
        # Com Timetable vazio (sem aulas), não há workload para aumentar.
        # Verifica que retorna vazio sem erro.
        suggestions = service._run_workload_increase()
        assert isinstance(suggestions, list)

    def test_max_5_per_category(self, db):
        """Verifica que _top_n_by_delta retorna no máximo 5."""
        service = SuggestionsService.__new__(SuggestionsService)
        service.buracos_antes = 10

        # Cria 10 candidatos com deltas variados
        candidates = [
            {"delta": i, "titulo": f"c{i}"} for i in range(1, 11)
        ]
        top = service._top_n_by_delta(candidates)
        assert len(top) == MAX_SUGGESTIONS_PER_CATEGORY
        assert top[0]["delta"] == 10  # Maior delta primeiro


# ---------------------------------------------------------------------------
# SuggestionsService — Categoria teacher_add
# ---------------------------------------------------------------------------


class TestTeacherAdd:
    def test_returns_empty_when_no_subjects_without_teacher(
        self, solver_run_with_buracos, db
    ):
        """Sem aulas sem professor, _run_teacher_add retorna vazio."""
        service = SuggestionsService(solver_run_with_buracos)
        # Timetable vazio = sem aulas = sem subjects sem teacher
        result = service._run_teacher_add()
        assert result == []


# ---------------------------------------------------------------------------
# SuggestionsService — Categoria teacher_availability
# ---------------------------------------------------------------------------


class TestTeacherAvailability:
    def test_returns_empty_when_no_unavailabilities(
        self, solver_run_with_buracos, db
    ):
        """Sem indisponibilidades, _run_teacher_availability retorna vazio."""
        service = SuggestionsService(solver_run_with_buracos)
        result = service._run_teacher_availability()
        assert result == []


# ---------------------------------------------------------------------------
# SuggestionsService — Categoria subject_rule_relax
# ---------------------------------------------------------------------------


class TestSubjectRuleRelax:
    def test_returns_empty_when_no_rules(
        self, solver_run_with_buracos, db
    ):
        """Sem SubjectRules, _run_subject_rule_relax retorna vazio."""
        service = SuggestionsService(solver_run_with_buracos)
        result = service._run_subject_rule_relax()
        assert result == []


# ---------------------------------------------------------------------------
# SuggestionsService — run_all_categories
# ---------------------------------------------------------------------------


class TestRunAllCategories:
    def test_runs_all_four_categories(
        self, solver_run_with_buracos, db
    ):
        """Com buracos > 0 e suggestions_enabled, run_all_categories roda sem erro."""
        service = SuggestionsService(solver_run_with_buracos)
        calls = {"count": 0}

        def mock_method():
            calls["count"] += 1
            return []

        service._run_workload_increase = mock_method
        service._run_teacher_add = mock_method
        service._run_teacher_availability = mock_method
        service._run_subject_rule_relax = mock_method

        result = service.run_all_categories()
        assert calls["count"] == 4
        assert result == []

    def test_returns_suggestions_from_all_categories(
        self, solver_run_with_buracos, db
    ):
        """Verifica que sugestões de todas as categorias são concatenadas."""
        service = SuggestionsService(solver_run_with_buracos)
        service._run_workload_increase = lambda: [Suggestion.CategoriaChoices.WORKLOAD_INCREASE]
        service._run_teacher_add = lambda: [Suggestion.CategoriaChoices.TEACHER_ADD]
        service._run_teacher_availability = lambda: [Suggestion.CategoriaChoices.TEACHER_AVAILABILITY]
        service._run_subject_rule_relax = lambda: [Suggestion.CategoriaChoices.SUBJECT_RULE_RELAX]

        result = service.run_all_categories()
        assert len(result) == 4


# ---------------------------------------------------------------------------
# Suggestion model
# ---------------------------------------------------------------------------


class TestSuggestionModel:
    def test_create_suggestion(self, tenant, school_year, variant_a, db):
        """Cria uma Suggestion e verifica campos."""
        solver_run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
        )
        suggestion = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
            titulo="Aumentar carga de Matemática",
            descricao="Teste",
            buracos_antes=5,
            buracos_depois=3,
            delta=2,
            param_diff={"subject": "Matemática", "weekly_lessons": {"de": 4, "para": 5}},
        )
        assert suggestion.delta == 2
        assert suggestion.categoria == Suggestion.CategoriaChoices.WORKLOAD_INCREASE
        assert suggestion.status == Suggestion.StatusChoices.PENDING
        assert suggestion.param_diff["subject"] == "Matemática"

    def test_param_diff_roundtrip_json(self, tenant, school_year, variant_a, db):
        """param_diff como JSONField faz round-trip correto."""
        solver_run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=10,
        )
        param_diff = {
            "subject": "Português",
            "series": "8ª série",
            "weekly_lessons": {"de": 4, "para": 5},
            "nested": {"a": [1, 2, 3]},
        }
        suggestion = Suggestion.objects.create(
            tenant=tenant,
            school_year=school_year,
            solver_run=solver_run,
            categoria=Suggestion.CategoriaChoices.TEACHER_ADD,
            titulo="Adicionar professor",
            descricao="Teste",
            buracos_antes=10,
            buracos_depois=7,
            delta=3,
            param_diff=param_diff,
        )
        suggestion.refresh_from_db()
        assert suggestion.param_diff == param_diff

    def test_categorias_choices(self):
        """Verifica que as 4 categorias existem."""
        expected = {
            "workload_increase",
            "teacher_add",
            "teacher_availability",
            "subject_rule_relax",
        }
        actual = {choice[0] for choice in Suggestion.CategoriaChoices.choices}
        assert actual == expected


# ---------------------------------------------------------------------------
# Task: run_suggestions_layer
# ---------------------------------------------------------------------------


class TestRunSuggestionsLayer:
    def test_disabled_when_zero_buracos(
        self, solver_run_zero_buracos, db
    ):
        """buracos=0 → suggestions_status='disabled'."""
        result = run_suggestions_layer(str(solver_run_zero_buracos.id))
        assert result["status"] == "disabled"
        solver_run_zero_buracos.refresh_from_db()
        assert solver_run_zero_buracos.suggestions_status == SolverRun.SuggestionsStatusChoices.DISABLED

    def test_disabled_when_suggestions_not_enabled(
        self, tenant, school_year_disabled, variant_a, db
    ):
        """suggestions_enabled=False → suggestions_status='disabled'."""
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year_disabled,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
        )
        result = run_suggestions_layer(str(run.id))
        assert result["status"] == "disabled"
        run.refresh_from_db()
        assert run.suggestions_status == SolverRun.SuggestionsStatusChoices.DISABLED

    def test_done_when_buracos_and_enabled(
        self, solver_run_with_buracos, db
    ):
        """buracos > 0 e suggestions_enabled=True → roda e marca done."""
        result = run_suggestions_layer(str(solver_run_with_buracos.id))
        assert result["status"] == "done"
        solver_run_with_buracos.refresh_from_db()
        assert solver_run_with_buracos.suggestions_status == SolverRun.SuggestionsStatusChoices.DONE
        assert result["suggestions_count"] >= 0

    def test_error_when_solver_run_not_found(self, db):
        """SolverRun inexistente → retorna error."""
        fake_id = str(uuid.uuid4())
        result = run_suggestions_layer(fake_id)
        assert result["status"] == "error"
        assert "não encontrado" in result["error"]

    def test_failed_status_on_exception(
        self, tenant, school_year, variant_a, db, monkeypatch
    ):
        """Se SuggestionsService.run_all_categories() levanta exceção,
        task marca suggestions_status='failed' e NÃO propaga."""
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
        )

        def mock_run_all_categories(self):
            raise RuntimeError("Erro simulado no service")

        monkeypatch.setattr(SuggestionsService, "run_all_categories", mock_run_all_categories)

        result = run_suggestions_layer(str(run.id))
        assert result["status"] == "failed"
        assert "Erro simulado" in result["error"]
        run.refresh_from_db()
        assert run.suggestions_status == SolverRun.SuggestionsStatusChoices.FAILED

    def test_timeout_status(self, tenant, school_year, variant_a, db, monkeypatch):
        """Se execução excede SUGGESTIONS_TIMEOUT_SECONDS, marca timeout."""
        import time
        import apps.scheduling.tasks as tasks_module

        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=5,
        )

        # Reduz o timeout para 0 segundos para forçar timeout
        monkeypatch.setattr(tasks_module, "SUGGESTIONS_TIMEOUT_SECONDS", 0)

        # Simula execução que demora mais que timeout
        def slow_run_all_categories(self):
            time.sleep(0.05)  # Pequeno atraso para exceder timeout de 0
            return []

        monkeypatch.setattr(SuggestionsService, "run_all_categories", slow_run_all_categories)

        result = run_suggestions_layer(str(run.id))
        assert result["status"] == "timeout"
        run.refresh_from_db()
        assert run.suggestions_status == SolverRun.SuggestionsStatusChoices.TIMEOUT

    def test_suggestions_count_persisted(
        self, solver_run_with_buracos, db
    ):
        """Ao rodar com buracos > 0 e suggestions_enabled, verifica suggestions_count."""
        result = run_suggestions_layer(str(solver_run_with_buracos.id))
        assert result["status"] == "done"
        solver_run_with_buracos.refresh_from_db()
        assert solver_run_with_buracos.suggestions_status == SolverRun.SuggestionsStatusChoices.DONE
        assert solver_run_with_buracos.suggestions_count >= 0
        assert result["suggestions_count"] == solver_run_with_buracos.suggestions_count

    def test_disabled_when_buracos_none(
        self, tenant, school_year, variant_a, db
    ):
        """buracos=None é tratado como desabilitado."""
        run = SolverRun.objects.create(
            tenant=tenant,
            variant=variant_a,
            school_year=school_year,
            status=SolverRun.StatusChoices.SUCCESS,
            buracos=None,
        )
        result = run_suggestions_layer(str(run.id))
        assert result["status"] == "disabled"
        run.refresh_from_db()
        assert run.suggestions_status == SolverRun.SuggestionsStatusChoices.DISABLED


# ---------------------------------------------------------------------------
# SuggestionsService — _solve_rapido integration
# ---------------------------------------------------------------------------


class TestSolveRapido:
    def test_solve_rapido_with_minimal_timetable(self, db):
        """Verifica que greedy_construct retorna int (buracos) corretamente."""
        # Timetable com 1 slot e 1 aula — deve resolver sem buracos
        slot = Slot(
            id=uuid.uuid4(),
            class_group_id=uuid.uuid4(),
            weekday="monday",
            order=1,
        )
        aula = Aula(
            id=uuid.uuid4(),
            class_group_id=slot.class_group_id,
            subject_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            weekly_hours=1,
        )
        tt = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=(aula,),
            slots=(slot,),
        )
        result = greedy_construct(tt, seed=0)
        assert isinstance(result.total_buracos, int)

    def test_solve_rapido_with_empty_timetable(self, db):
        """Timetable vazio tem 0 buracos (0 aulas para alocar)."""
        tt = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=(),
            slots=(),
        )
        result = greedy_construct(tt, seed=0)
        assert result.total_buracos == 0

    def test_solve_rapido_detects_buracos(self, db):
        """Timetable com mais slots que aulas gera buracos."""
        cg_id = uuid.uuid4()

        slots = tuple(
            Slot(
                id=uuid.uuid4(),
                class_group_id=cg_id,
                weekday="monday",
                order=i,
            )
            for i in range(1, 6)
        )

        # Apenas 2 aulas para 5 slots
        aulas = (
            Aula(
                id=uuid.uuid4(),
                class_group_id=cg_id,
                subject_id=uuid.uuid4(),
                teacher_id=uuid.uuid4(),
                weekly_hours=1,
            ),
            Aula(
                id=uuid.uuid4(),
                class_group_id=cg_id,
                subject_id=uuid.uuid4(),
                teacher_id=uuid.uuid4(),
                weekly_hours=1,
            ),
        )
        tt = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=aulas,
            slots=slots,
        )
        result = greedy_construct(tt, seed=0)
        # 5 slots, 2 aulas → pelo menos 3 buracos
        assert result.total_buracos >= 3