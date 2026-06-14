"""Testes do solver consolidado (SDD §22.1, Sprint 08).

Tipos de domínio, construtor greedy, 3 variantes e retry.
Tudo importa de `apps.scheduling.services.solver`.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest
from django.db.utils import OperationalError

from apps.scheduling.services.solver import (
    Assignment,
    Aula,
    Buraco,
    Slot,
    Solution,
    SolverError,
    Timetable,
    UnsatisfiableError,
    VariantARestart,
    VariantBHillClimbing,
    VariantCHybrid,
    greedy_construct,
    transient_retry,
)

# ---- Fixtures sintéticas --------------------------------------------------


def _make_slot(
    slot_id=None,
    class_group_id=None,
    weekday="monday",
    order=1,
    accepts_double_lesson=False,
) -> Slot:
    return Slot(
        id=slot_id or uuid.uuid4(),
        class_group_id=class_group_id or uuid.uuid4(),
        weekday=weekday,
        order=order,
        accepts_double_lesson=accepts_double_lesson,
    )


def _make_timetable_min() -> Timetable:
    """Timetable mínimo com 1 turma, 2 slots, 2 aulas."""
    cg_id = uuid.uuid4()
    slots = (
        _make_slot(class_group_id=cg_id, weekday="monday", order=1),
        _make_slot(class_group_id=cg_id, weekday="monday", order=2),
    )
    aulas = (
        Aula(id=uuid.uuid4(), class_group_id=cg_id, subject_id=uuid.uuid4(), weekly_hours=1),
        Aula(id=uuid.uuid4(), class_group_id=cg_id, subject_id=uuid.uuid4(), weekly_hours=1),
    )
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=aulas,
        slots=slots,
    )


# ---- Testes dos tipos de domínio (§22.1) ----------------------------------


class TestSlot:
    def test_construction(self):
        s = _make_slot()
        assert s.id is not None
        assert s.order >= 1

    def test_order_must_be_positive(self):
        with pytest.raises(ValueError):
            _make_slot(order=0)


class TestAula:
    def test_construction(self):
        a = Aula(id=uuid.uuid4(), class_group_id=uuid.uuid4(), subject_id=uuid.uuid4())
        assert a.weekly_hours == 1

    def test_weekly_hours_negative_raises(self):
        with pytest.raises(ValueError):
            Aula(id=uuid.uuid4(), class_group_id=uuid.uuid4(), subject_id=uuid.uuid4(), weekly_hours=-1)


class TestSolution:
    def test_completude_range(self):
        sol = Solution(
            assignments=[],
            buracos=[],
            completude=0.5,
            criterio_parada=Solution.CriterioParada.ZERO_BURACOS,
        )
        assert sol.completude == 0.5

    def test_completude_out_of_range_raises(self):
        with pytest.raises(ValueError):
            Solution(
                assignments=[],
                buracos=[],
                completude=1.5,
                criterio_parada=Solution.CriterioParada.ZERO_BURACOS,
            )

    def test_to_dict_roundtrip(self):
        aula_id = uuid.uuid4()
        slot_id = uuid.uuid4()
        cg_id = uuid.uuid4()
        subj_id = uuid.uuid4()
        sol = Solution(
            assignments=[
                Assignment(
                    aula_id=aula_id,
                    slot_id=slot_id,
                    class_group_id=cg_id,
                    subject_id=subj_id,
                    teacher_id=None,
                )
            ],
            buracos=[
                Buraco(
                    slot_id=uuid.uuid4(),
                    class_group_id=cg_id,
                    weekday="tuesday",
                    order=3,
                )
            ],
            completude=0.75,
            criterio_parada=Solution.CriterioParada.TIMEOUT,
            iteracoes=42,
            restarts=3,
        )
        data = sol.to_dict()
        restored = Solution.from_dict(data)
        assert restored.assignments[0].aula_id == aula_id
        assert restored.buracos[0].weekday == "tuesday"
        assert restored.completude == 0.75
        assert restored.iteracoes == 42


class TestSolverError:
    def test_hierarchy(self):
        assert issubclass(UnsatisfiableError, SolverError)


# ---- Testes do construtor greedy (§22.2.3) --------------------------------


class TestGreedyConstruct:
    def test_basic(self):
        tt = _make_timetable_min()
        sol = greedy_construct(tt, seed=42)
        assert sol.completude > 0
        assert sol.total_buracos >= 0

    def test_seed_reproducible(self):
        tt = _make_timetable_min()
        sol1 = greedy_construct(tt, seed=123)
        sol2 = greedy_construct(tt, seed=123)
        assert len(sol1.assignments) == len(sol2.assignments)
        assert sol1.total_buracos == sol2.total_buracos

    def test_empty_timetable(self):
        tt = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
        )
        sol = greedy_construct(tt)
        assert sol.completude == 1.0
        assert sol.total_buracos == 0


# ---- Testes das 3 variantes (§22.2.3-22.2.5) ------------------------------


class TestVariantARestart:
    def test_solve(self):
        tt = _make_timetable_min()
        sol = VariantARestart().solve(tt, timedelta(minutes=5))
        assert sol is not None
        assert sol.completude >= 0

    def test_solve_max_restarts(self):
        tt = _make_timetable_min()
        object.__setattr__(tt, "_params", {"max_restarts": 10, "seed_base": 0})
        sol = VariantARestart().solve(tt, timedelta(minutes=5))
        assert sol.restarts <= 10


class TestVariantBHillClimbing:
    def test_solve(self):
        tt = _make_timetable_min()
        sol = VariantBHillClimbing().solve(tt, timedelta(minutes=5))
        assert sol is not None

    def test_params_propagation(self):
        tt = _make_timetable_min()
        object.__setattr__(tt, "_params", {"seed_base": 99, "max_iteracoes": 50, "vizinhos_por_iteracao": 5})
        sol = VariantBHillClimbing().solve(tt, timedelta(minutes=5))
        assert sol is not None


class TestVariantCHybrid:
    def test_solve(self):
        tt = _make_timetable_min()
        sol = VariantCHybrid().solve(tt, timedelta(minutes=5))
        assert sol is not None


# ---- Testes do retry transiente (§22.2.6) ---------------------------------


class TestTransientRetry:
    def test_sucesso_na_primeira_tentativa(self):
        calls: list[int] = []

        @transient_retry
        def func() -> str:
            calls.append(1)
            return "ok"

        assert func() == "ok"
        assert len(calls) == 1

    def test_retry_em_erro_transiente(self):
        calls: list[int] = []

        @transient_retry
        def func() -> str:
            calls.append(1)
            if len(calls) == 1:
                raise OperationalError("connection lost")
            return "ok"

        assert func() == "ok"
        assert len(calls) == 2

    def test_exaustao_de_tentativas(self):
        calls: list[int] = []

        @transient_retry(max_attempts=2)
        def func() -> str:
            calls.append(1)
            raise OperationalError("connection lost")

        with pytest.raises(OperationalError):
            func()
        assert len(calls) == 2

    def test_erro_nao_transiente_sem_retry(self):
        calls: list[int] = []

        @transient_retry
        def func() -> str:
            calls.append(1)
            raise ValueError("not transient")

        with pytest.raises(ValueError):
            func()
        assert len(calls) == 1

    def test_decorator_com_args(self):
        calls: list[int] = []

        @transient_retry(max_attempts=3)
        def func() -> str:
            calls.append(1)
            if len(calls) < 2:
                raise OperationalError("retry me")
            return "ok"

        assert func() == "ok"
        assert len(calls) == 2
