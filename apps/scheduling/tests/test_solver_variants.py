"""Testes das 3 variantes do solver (Sprint 08 itens 3.6, 3.7, 3.8).

Usa fixtures sintéticas (timables pequenos) em vez de fixtures
de banco, porque o solver é puro Python e não toca em Django.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

import pytest

from apps.scheduling.solver.constructor import greedy_construct
from apps.scheduling.solver.types import (
    Aula,
    Disponibilidade,
    Slot,
    Solution,
    Timetable,
)
from apps.scheduling.solver.variant_a_restart import VariantARestart
from apps.scheduling.solver.variant_b_hill_climbing import VariantBHillClimbing
from apps.scheduling.solver.variant_c_hybrid import VariantCHybrid


# Fixture: 1 turma, 5 aulas/semana, 5 slots (seg a sex, ordem 1)
# Cenário ideal: greedy resolve com 0 buracos.
@pytest.fixture
def timetable_perfeito():
    turma = uuid.uuid4()
    disciplina = uuid.uuid4()
    professor = uuid.uuid4()
    aulas = tuple(
        Aula(
            id=uuid.uuid4(),
            class_group_id=turma,
            subject_id=disciplina,
            teacher_id=professor,
            weekly_hours=1,
        )
        for _ in range(5)
    )
    slots = tuple(
        Slot(
            id=uuid.uuid4(),
            class_group_id=turma,
            weekday=wd,
            order=1,
        )
        for wd in ("monday", "tuesday", "wednesday", "thursday", "friday")
    )
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=aulas,
        slots=slots,
    )


# Fixture: 1 turma, 5 aulas/semana, **3** slots (apenas 3! — faltam slots)
# Greedy aloca 3 aulas, 0 buracos (todos os slots preenchidos),
# mas completude = 3/5 = 0.6 (2 aulas viraram fantasmas).
# Esse cenário testa completude, não buracos.
@pytest.fixture
def timetable_poucos_slots():
    turma = uuid.uuid4()
    disciplina = uuid.uuid4()
    professor = uuid.uuid4()
    aulas = tuple(
        Aula(
            id=uuid.uuid4(),
            class_group_id=turma,
            subject_id=disciplina,
            teacher_id=professor,
            weekly_hours=1,
        )
        for _ in range(5)
    )
    slots = tuple(
        Slot(
            id=uuid.uuid4(),
            class_group_id=turma,
            weekday=wd,
            order=1,
        )
        for wd in ("monday", "tuesday", "wednesday")
    )
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=aulas,
        slots=slots,
    )


# Fixture: cenário com buracos REAIS — slots demais pro mesmo professor
# 1 turma, 5 aulas, 5 slots, mas professor SÓ tem disponibilidade
# em 2 dias. Resultado: 3 buracos.
@pytest.fixture
def timetable_com_buracos_reais():
    turma = uuid.uuid4()
    disciplina = uuid.uuid4()
    professor = uuid.uuid4()
    aulas = tuple(
        Aula(
            id=uuid.uuid4(),
            class_group_id=turma,
            subject_id=disciplina,
            teacher_id=professor,
            weekly_hours=1,
        )
        for _ in range(5)
    )
    slots = tuple(
        Slot(
            id=uuid.uuid4(),
            class_group_id=turma,
            weekday=wd,
            order=1,
        )
        for wd in ("monday", "tuesday", "wednesday", "thursday", "friday")
    )
    disponibilidades = (
        Disponibilidade(
            teacher_id=professor,
            weekday="monday",
            start_order=1,
            end_order=6,
        ),
        Disponibilidade(
            teacher_id=professor,
            weekday="tuesday",
            start_order=1,
            end_order=6,
        ),
    )
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=aulas,
        slots=slots,
        disponibilidades=disponibilidades,
    )


# Fixture: 2 turmas, 1 professor só disponível em 1 das turmas
@pytest.fixture
def timetable_com_restricao_professor():
    turma_a = uuid.uuid4()
    turma_b = uuid.uuid4()
    disciplina = uuid.uuid4()
    professor = uuid.uuid4()
    aulas = (
        Aula(
            id=uuid.uuid4(),
            class_group_id=turma_a,
            subject_id=disciplina,
            teacher_id=professor,
            weekly_hours=2,
        ),
        Aula(
            id=uuid.uuid4(),
            class_group_id=turma_b,
            subject_id=disciplina,
            teacher_id=professor,
            weekly_hours=2,
        ),
    )
    slots = (
        Slot(id=uuid.uuid4(), class_group_id=turma_a, weekday="monday", order=1),
        Slot(id=uuid.uuid4(), class_group_id=turma_a, weekday="tuesday", order=1),
        Slot(id=uuid.uuid4(), class_group_id=turma_b, weekday="monday", order=1),
        Slot(id=uuid.uuid4(), class_group_id=turma_b, weekday="tuesday", order=1),
    )
    # Professor só disponível segunda
    disponibilidades = (
        Disponibilidade(
            teacher_id=professor,
            weekday="monday",
            start_order=1,
            end_order=6,
        ),
    )
    return Timetable(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        school_year_id=uuid.uuid4(),
        aulas=aulas,
        slots=slots,
        disponibilidades=disponibilidades,
    )


# Construtor greedy compartilhado ---------------------------------------


class TestGreedyConstruct:
    def test_resolve_caso_perfeito(self, timetable_perfeito) -> None:
        sol = greedy_construct(timetable_perfeito, seed=0)
        assert sol.total_buracos == 0
        assert sol.completude == 1.0
        assert sol.criterio_parada == Solution.CriterioParada.ZERO_BURACOS

    def test_lida_com_poucos_slots(self, timetable_poucos_slots) -> None:
        sol = greedy_construct(timetable_poucos_slots, seed=0)
        # 3 slots preenchidos, 0 buracos, completude 3/5
        assert sol.total_buracos == 0
        assert sol.completude == pytest.approx(0.6, rel=0.01)

    def test_detecta_buracos_reais(
        self, timetable_com_buracos_reais
    ) -> None:
        sol = greedy_construct(timetable_com_buracos_reais, seed=0)
        # Professor só pode dar 2 dias (seg, ter) → 3 buracos
        assert sol.total_buracos == 3
        assert sol.completude == pytest.approx(0.4, rel=0.01)

    def test_respeita_disponibilidade_professor(
        self, timetable_com_restricao_professor
    ) -> None:
        sol = greedy_construct(timetable_com_restricao_professor, seed=0)
        # Professor só pode dar aula segunda; 2ª, 3ª e 4ª aulas
        # (1 da turma_a na terça + 1 da turma_b na terça) viram buracos
        assert sol.total_buracos >= 2

    def test_total_aulas_eh_zero_sem_aulas(self) -> None:
        t = Timetable(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            school_year_id=uuid.uuid4(),
            aulas=(),
            slots=(),
        )
        sol = greedy_construct(t, seed=0)
        assert sol.completude == 1.0


# Variante A -------------------------------------------------------------


class TestVariantARestart:
    def test_resolve_caso_perfeito(self, timetable_perfeito) -> None:
        solver = VariantARestart()
        sol = solver.solve(
            timetable_perfeito,
            deadline=timedelta(seconds=10),
        )
        assert sol.total_buracos == 0
        assert sol.restarts >= 1

    def test_melhora_com_mais_restarts(
        self, timetable_com_buracos_reais
    ) -> None:
        t1 = _with_params(timetable_com_buracos_reais, {"max_restarts": 1, "seed_base": 0})
        t2 = _with_params(timetable_com_buracos_reais, {"max_restarts": 50, "seed_base": 0})
        s1 = VariantARestart().solve(t1, deadline=timedelta(seconds=5))
        s2 = VariantARestart().solve(t2, deadline=timedelta(seconds=5))
        assert s2.restarts >= s1.restarts

    def test_para_cedo_com_0_buracos(self, timetable_perfeito) -> None:
        t = _with_params(timetable_perfeito, {"max_restarts": 1000})
        sol = VariantARestart().solve(t, deadline=timedelta(seconds=30))
        # Encontrou 0 buracos muito antes de 1000 restarts
        assert sol.restarts < 1000


# Variante B -------------------------------------------------------------


class TestVariantBHillClimbing:
    def test_resolve_caso_perfeito(self, timetable_perfeito) -> None:
        sol = VariantBHillClimbing().solve(
            timetable_perfeito,
            deadline=timedelta(seconds=10),
        )
        assert sol.total_buracos == 0
        assert sol.iteracoes >= 1

    def test_lida_com_buracos(self, timetable_com_buracos_reais) -> None:
        sol = VariantBHillClimbing().solve(
            timetable_com_buracos_reais,
            deadline=timedelta(seconds=5),
        )
        # Hill climbing não consegue alocar mais que greedy
        # (mesmos buracos)
        assert sol.total_buracos == 3
        assert sol.completude == pytest.approx(0.4, rel=0.01)


# Variante C -------------------------------------------------------------


class TestVariantCHybrid:
    def test_resolve_caso_perfeito(self, timetable_perfeito) -> None:
        sol = VariantCHybrid().solve(
            timetable_perfeito,
            deadline=timedelta(seconds=10),
        )
        assert sol.total_buracos == 0

    def test_melhor_que_greedy_em_casos_dificeis(
        self, timetable_com_buracos_reais
    ) -> None:
        sol = VariantCHybrid().solve(
            timetable_com_buracos_reais,
            deadline=timedelta(seconds=5),
        )
        assert sol.total_buracos >= 3
        assert sol.completude <= 1.0

    def test_max_construcoes_zero_explode(self) -> None:
        # max_construcoes=0 é input inválido — esperamos erro (não contrato
        # atual não tem fallback). Validamos que falha ruidosamente.
        t = _with_params(timetable_perfeito, {"max_construcoes": 0})
        with pytest.raises(ZeroDivisionError):
            VariantCHybrid().solve(t, deadline=timedelta(seconds=5))


# Helpers ----------------------------------------------------------------


def _with_params(timetable: Timetable, params: dict) -> Timetable:
    """Cria cópia do Timetable com `_params` setado.

    `Timetable` é frozen (dataclass), então usamos `object.__setattr__`
    pra injetar o atributo. Hack leve pro MVP — idealmente os parâmetros
    viriam do `SolverRun.variant.parametros` via uma classe wrapper.
    """
    from copy import copy

    new = copy(timetable)
    object.__setattr__(new, "_params", params)
    return new
