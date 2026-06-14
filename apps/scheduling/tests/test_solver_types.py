"""Testes dos tipos de domínio do solver (SDD §22.1, Sprint 08 item 3.1).

Foco: garantir que os dataclasses são construíveis, validam-se,
e que `Solution.to_dict` / `from_dict` fazem round-trip sem perda.
"""
from __future__ import annotations

import uuid

import pytest

from apps.scheduling.solver.types import (
    Assignment,
    Aula,
    Buraco,
    Disponibilidade,
    Restricao,
    RestricaoTipo,
    Slot,
    Solution,
    SolverError,
    Timetable,
    UnsatisfiableError,
)

# Fixtures ---------------------------------------------------------------


@pytest.fixture
def slot_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def class_group_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def subject_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def teacher_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def slot(slot_id: uuid.UUID, class_group_id: uuid.UUID) -> Slot:
    return Slot(
        id=slot_id,
        class_group_id=class_group_id,
        weekday="monday",
        order=1,
    )


@pytest.fixture
def aula(teacher_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID) -> Aula:
    return Aula(
        id=uuid.uuid4(),
        class_group_id=class_group_id,
        subject_id=subject_id,
        teacher_id=teacher_id,
        weekly_hours=4,
    )


@pytest.fixture
def timetable(aula: Aula, slot: Slot) -> Timetable:
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=(aula,),
        slots=(slot,),
    )


# Slot -------------------------------------------------------------------


class TestSlot:
    def test_cria_com_campos_minimos(self, slot_id: uuid.UUID, class_group_id: uuid.UUID) -> None:
        slot = Slot(id=slot_id, class_group_id=class_group_id, weekday="tuesday", order=3)
        assert slot.weekday == "tuesday"
        assert slot.order == 3
        assert slot.accepts_double_lesson is False

    def test_rejeita_id_none(self, class_group_id: uuid.UUID) -> None:
        with pytest.raises(ValueError, match="Slot.id"):
            Slot(id=None, class_group_id=class_group_id, weekday="monday", order=1)  # type: ignore[arg-type]

    def test_rejeita_order_zero(self, slot_id: uuid.UUID, class_group_id: uuid.UUID) -> None:
        with pytest.raises(ValueError, match="Slot.order"):
            Slot(id=slot_id, class_group_id=class_group_id, weekday="monday", order=0)

    def test_rejeita_order_negativo(self, slot_id: uuid.UUID, class_group_id: uuid.UUID) -> None:
        with pytest.raises(ValueError, match="Slot.order"):
            Slot(id=slot_id, class_group_id=class_group_id, weekday="monday", order=-1)

    def test_eh_imutavel(self, slot: Slot) -> None:
        import dataclasses

        with pytest.raises(dataclasses.FrozenInstanceError):
            slot.order = 5  # type: ignore[misc]


# Aula -------------------------------------------------------------------


class TestAula:
    def test_cria_com_campos_minimos(
        self, teacher_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID
    ) -> None:
        aula = Aula(
            id=uuid.uuid4(),
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            weekly_hours=5,
        )
        assert aula.weekly_hours == 5
        assert aula.is_double_lesson is False

    def test_aceita_teacher_none(self, class_group_id: uuid.UUID, subject_id: uuid.UUID) -> None:
        aula = Aula(
            id=uuid.uuid4(),
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=None,
            weekly_hours=3,
        )
        assert aula.teacher_id is None

    def test_rejeita_weekly_hours_negativo(
        self, teacher_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID
    ) -> None:
        with pytest.raises(ValueError, match="weekly_hours"):
            Aula(
                id=uuid.uuid4(),
                class_group_id=class_group_id,
                subject_id=subject_id,
                teacher_id=teacher_id,
                weekly_hours=-1,
            )

    def test_double_lesson_default_false(
        self, teacher_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID
    ) -> None:
        aula = Aula(
            id=uuid.uuid4(),
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            weekly_hours=2,
        )
        assert aula.is_double_lesson is False


# Timetable --------------------------------------------------------------


class TestTimetable:
    def test_total_aulas_soma_weekly_hours(self, timetable: Timetable, aula: Aula) -> None:
        assert timetable.total_aulas == aula.weekly_hours

    def test_total_aulas_zero_sem_aulas(self) -> None:
        t = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=(),
            slots=(),
        )
        assert t.total_aulas == 0

    def test_total_aulas_soma_multiplas(self) -> None:
        a1 = Aula(
            id=uuid.uuid4(),
            class_group_id=uuid.uuid4(),
            subject_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            weekly_hours=3,
        )
        a2 = Aula(
            id=uuid.uuid4(),
            class_group_id=uuid.uuid4(),
            subject_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
            weekly_hours=5,
        )
        t = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=(a1, a2),
            slots=(),
        )
        assert t.total_aulas == 8

    def test_rejeita_sem_tenant(self) -> None:
        with pytest.raises(ValueError, match="tenant_id"):
            Timetable(
                id=uuid.uuid4(),
                tenant_id=None,  # type: ignore[arg-type]
                school_year_id=uuid.uuid4(),
                aulas=(),
                slots=(),
            )

    def test_rejeita_sem_school_year(self) -> None:
        with pytest.raises(ValueError, match="school_year_id"):
            Timetable(
                id=uuid.uuid4(),
                tenant_id=uuid.uuid4(),
                school_year_id=None,  # type: ignore[arg-type]
                aulas=(),
                slots=(),
            )

    def test_restricoes_e_disponibilidades_default_vazias(self, timetable: Timetable) -> None:
        assert timetable.restricoes == ()
        assert timetable.disponibilidades == ()


# Solution ---------------------------------------------------------------


class TestSolution:
    def _make_assignment(
        self, slot_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID
    ) -> Assignment:
        return Assignment(
            aula_id=uuid.uuid4(),
            slot_id=slot_id,
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=uuid.uuid4(),
        )

    def test_cria_solution_valida(self) -> None:
        sol = Solution(
            assignments=[],
            buracos=[],
            completude=1.0,
            criterio_parada=Solution.CriterioParada.ZERO_BURACOS,
        )
        assert sol.completude == 1.0
        assert sol.total_buracos == 0

    def test_rejeita_completude_acima_de_1(self) -> None:
        with pytest.raises(ValueError, match="completude"):
            Solution(
                assignments=[],
                buracos=[],
                completude=1.5,
                criterio_parada=Solution.CriterioParada.TIMEOUT,
            )

    def test_rejeita_completude_abaixo_de_0(self) -> None:
        with pytest.raises(ValueError, match="completude"):
            Solution(
                assignments=[],
                buracos=[],
                completude=-0.1,
                criterio_parada=Solution.CriterioParada.TIMEOUT,
            )

    def test_total_buracos_conta_lista(self) -> None:
        b1 = Buraco(slot_id=uuid.uuid4(), class_group_id=uuid.uuid4(), weekday="monday", order=1)
        b2 = Buraco(slot_id=uuid.uuid4(), class_group_id=uuid.uuid4(), weekday="monday", order=2)
        sol = Solution(
            assignments=[],
            buracos=[b1, b2],
            completude=0.5,
            criterio_parada=Solution.CriterioParada.TIMEOUT,
        )
        assert sol.total_buracos == 2

    def test_to_dict_serializa_campos_basicos(self) -> None:
        sol = Solution(
            assignments=[],
            buracos=[],
            completude=1.0,
            criterio_parada=Solution.CriterioParada.ZERO_BURACOS,
            iteracoes=42,
            restarts=3,
        )
        d = sol.to_dict()
        assert d["completude"] == 1.0
        assert d["criterio_parada"] == "zero_buracos"
        assert d["iteracoes"] == 42
        assert d["restarts"] == 3
        assert d["assignments"] == []
        assert d["buracos"] == []

    def test_round_trip_to_from_dict(self, slot_id: uuid.UUID, class_group_id: uuid.UUID) -> None:
        subject_id = uuid.uuid4()
        teacher_id = uuid.uuid4()
        aula_id = uuid.uuid4()
        assignment = Assignment(
            aula_id=aula_id,
            slot_id=slot_id,
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
        )
        buraco = Buraco(
            slot_id=uuid.uuid4(),
            class_group_id=uuid.uuid4(),
            weekday="wednesday",
            order=5,
        )
        sol = Solution(
            assignments=[assignment],
            buracos=[buraco],
            completude=0.85,
            criterio_parada=Solution.CriterioParada.TIMEOUT,
            iteracoes=100,
            restarts=2,
        )

        d = sol.to_dict()
        sol2 = Solution.from_dict(d)

        assert sol2.completude == sol.completude
        assert sol2.criterio_parada == sol.criterio_parada
        assert sol2.iteracoes == sol.iteracoes
        assert sol2.restarts == sol.restarts
        assert sol2.total_buracos == sol.total_buracos
        assert len(sol2.assignments) == len(sol.assignments)
        a_round = sol2.assignments[0]
        assert a_round.aula_id == aula_id
        assert a_round.slot_id == slot_id
        assert a_round.teacher_id == teacher_id

    def test_round_trip_preserva_teacher_none(
        self, slot_id: uuid.UUID, class_group_id: uuid.UUID, subject_id: uuid.UUID
    ) -> None:
        assignment = Assignment(
            aula_id=uuid.uuid4(),
            slot_id=slot_id,
            class_group_id=class_group_id,
            subject_id=subject_id,
            teacher_id=None,
        )
        sol = Solution(
            assignments=[assignment],
            buracos=[],
            completude=1.0,
            criterio_parada=Solution.CriterioParada.ZERO_BURACOS,
        )
        sol2 = Solution.from_dict(sol.to_dict())
        assert sol2.assignments[0].teacher_id is None


# Disponibilidade e Restricao --------------------------------------------


class TestDisponibilidade:
    def test_cria_basica(self, teacher_id: uuid.UUID) -> None:
        d = Disponibilidade(teacher_id=teacher_id, weekday="friday", start_order=1, end_order=6)
        assert d.start_order == 1
        assert d.end_order == 6


class TestRestricao:
    def test_cria_rigida(self) -> None:
        r = Restricao(tipo=RestricaoTipo.RIGIDA, descricao="X")
        assert r.tipo == RestricaoTipo.RIGIDA

    def test_cria_flexivel(self) -> None:
        r = Restricao(tipo=RestricaoTipo.FLEXIVEL, descricao="Y")
        assert r.tipo == RestricaoTipo.FLEXIVEL


# Exceções ---------------------------------------------------------------


class TestExceptions:
    def test_solver_error_eh_exception(self) -> None:
        assert issubclass(SolverError, Exception)

    def test_unsatisfiable_eh_solver_error(self) -> None:
        assert issubclass(UnsatisfiableError, SolverError)
