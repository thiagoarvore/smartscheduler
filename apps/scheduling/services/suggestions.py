"""Camada de sugestões — SDD §22.4, Sprint 09 §3.3.

Heurística leve que roda *depois* do solver, tentando 4 categorias
de mudanças paramétricas para reduzir buracos. Cada categoria gera
no máximo 5 sugestões (pick das que mais reduzem buracos).

Não é parte do solver (§22.4.1) — mora em services/suggestions.py,
separada de services/solver.py.
"""
from __future__ import annotations

import logging
import uuid
from copy import copy
from dataclasses import replace
from datetime import timedelta
from typing import Any

from apps.curriculum.models import Subject, SubjectRule, WorkloadItem
from apps.people.models import TeacherAvailability
from apps.scheduling.models import Suggestion, SolverRun
from apps.scheduling.services.solver import (
    Aula,
    Disponibilidade,
    Restricao,
    RestricaoTipo,
    Slot,
    Timetable,
    greedy_construct,
)
from apps.schools.models import SchoolYear

logger = logging.getLogger(__name__)

# Orçamento de tempo para solve_rapido por tentativa (§22.4.4)
SOLVE_RAPIDO_DEADLINE = timedelta(seconds=60)

# Máximo de sugestões por categoria
MAX_SUGGESTIONS_PER_CATEGORY = 5


class SuggestionsServiceError(Exception):
    """Erro na camada de sugestões."""


class SuggestionsService:
    """Recebe um SolverRun, valida pré-condições e executa as 4 categorias.

    Uso:
        suggestions = SuggestionsService(solver_run).run_all_categories()
    """

    def __init__(self, solver_run: SolverRun) -> None:
        self.solver_run = solver_run
        self.school_year: SchoolYear = solver_run.school_year
        self.buracos_antes: int = solver_run.buracos or 0

    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        """Levanta erro se a camada não deve rodar."""
        if self.buracos_antes <= 0:
            raise SuggestionsServiceError(
                f"SolverRun {self.solver_run.id} tem buracos={self.buracos_antes}; "
                "camada de sugestões desativada."
            )
        if not self.school_year.suggestions_enabled:
            raise SuggestionsServiceError(
                f"SchoolYear {self.school_year.id} tem suggestions_enabled=False; "
                "camada de sugestões desativada."
            )

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------

    def run_all_categories(self) -> list[Suggestion]:
        """Executa as 4 categorias e retorna todas as sugestões criadas."""
        self._validate()
        suggestions: list[Suggestion] = []
        suggestions.extend(self._run_workload_increase())
        suggestions.extend(self._run_teacher_add())
        suggestions.extend(self._run_teacher_availability())
        suggestions.extend(self._run_subject_rule_relax())
        return suggestions

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _load_timetable(self) -> Timetable:
        """Carrega o Timetable (dataclass) a partir do SolverRun."""
        from apps.scheduling.tasks import build_timetable_from_run

        return build_timetable_from_run(self.solver_run)

    def _solve_rapido(self, timetable: Timetable) -> int:
        """Roda greedy_construct e retorna o número de buracos."""
        solution = greedy_construct(timetable, seed=0)
        return solution.total_buracos

    def _create_suggestion(
        self,
        *,
        categoria: str,
        titulo: str,
        descricao: str,
        buracos_depois: int,
        param_diff: dict[str, Any],
    ) -> Suggestion:
        """Cria e retorna um objeto Suggestion persistido."""
        delta = self.buracos_antes - buracos_depois
        return Suggestion.objects.create(
            tenant_id=self.solver_run.tenant_id,
            school_year=self.school_year,
            solver_run=self.solver_run,
            categoria=categoria,
            titulo=titulo,
            descricao=descricao,
            buracos_antes=self.buracos_antes,
            buracos_depois=buracos_depois,
            delta=delta,
            param_diff=param_diff,
        )

    def _top_n_by_delta(
        self, candidates: list[dict], n: int = MAX_SUGGESTIONS_PER_CATEGORY
    ) -> list[dict]:
        """Ordena candidatos por delta desc e retorna os top-N."""
        candidates.sort(key=lambda c: c["delta"], reverse=True)
        return candidates[:n]

    # ------------------------------------------------------------------
    # Categoria 1: workload_increase
    # ------------------------------------------------------------------

    def _run_workload_increase(self) -> list[Suggestion]:
        """Aumenta weekly_hours de WorkloadItems, testa se reduz buracos."""
        timetable = self._load_timetable()
        items = list(
            WorkloadItem.objects.filter(
                tenant_id=self.solver_run.tenant_id,
                curriculum_matrix__series__isnull=False,
                weekly_lessons__lt=6,
            ).select_related("subject", "series", "class_group")[
                :20
            ]  # limita iteração
        )
        candidates: list[dict] = []

        for item in items:
            # Constrói Timetable modificado: aumenta weekly_hours das aulas deste item
            modified_aulas: list[Aula] = []
            found = False
            for aula in timetable.aulas:
                if aula.subject_id == item.subject_id and (
                    item.class_group_id is None
                    or aula.class_group_id == item.class_group_id
                ):
                    modified_aulas.append(
                        replace(aula, weekly_hours=aula.weekly_hours + 1)
                    )
                    found = True
                else:
                    modified_aulas.append(aula)

            if not found:
                continue

            modified_tt = replace(timetable, aulas=tuple(modified_aulas))
            buracos_depois = self._solve_rapido(modified_tt)

            if buracos_depois < self.buracos_antes:
                candidates.append(
                    {
                        "categoria": Suggestion.CategoriaChoices.WORKLOAD_INCREASE,
                        "titulo": (
                            f"Aumentar carga de {item.subject.name}"
                            f" na série {item.series.name}"
                            f" de {item.weekly_lessons} para {item.weekly_lessons + 1} aulas/semana"
                        ),
                        "descricao": (
                            f"Aumentar weekly_lessons de {item.weekly_lessons} para "
                            f"{item.weekly_lessons + 1} pode reduzir buracos de "
                            f"{self.buracos_antes} para {buracos_depois}."
                        ),
                        "buracos_depois": buracos_depois,
                        "param_diff": {
                            "subject": item.subject.name,
                            "series": item.series.name,
                            "weekly_lessons": {
                                "de": item.weekly_lessons,
                                "para": item.weekly_lessons + 1,
                            },
                        },
                        "delta": self.buracos_antes - buracos_depois,
                    }
                )

        suggestions: list[Suggestion] = []
        for c in self._top_n_by_delta(candidates):
            suggestions.append(
                self._create_suggestion(
                    categoria=c["categoria"],
                    titulo=c["titulo"],
                    descricao=c["descricao"],
                    buracos_depois=c["buracos_depois"],
                    param_diff=c["param_diff"],
                )
            )
        return suggestions

    # ------------------------------------------------------------------
    # Categoria 2: teacher_add
    # ------------------------------------------------------------------

    def _run_teacher_add(self) -> list[Suggestion]:
        """Simula adicionar um professor habilitado, testa se reduz buracos."""
        timetable = self._load_timetable()

        # Identifica subjects com aulas sem professor no timetable
        buraco_subject_ids: set[uuid.UUID] = set()
        for aula in timetable.aulas:
            if aula.teacher_id is None:
                buraco_subject_ids.add(aula.subject_id)

        if not buraco_subject_ids:
            return []

        subjects = Subject.objects.filter(
            tenant_id=self.solver_run.tenant_id,
            id__in=buraco_subject_ids,
        )[:10]

        candidates: list[dict] = []

        for subject in subjects:
            # Simula adicionar um professor genérico habilitado para este subject
            # em todas as aulas onde subject_id == subject.id e teacher_id is None
            teacher_id_fake = uuid.uuid4()
            modified_aulas: list[Aula] = []
            for aula in timetable.aulas:
                if aula.subject_id == subject.id and aula.teacher_id is None:
                    modified_aulas.append(replace(aula, teacher_id=teacher_id_fake))
                else:
                    modified_aulas.append(aula)

            if modified_aulas == list(timetable.aulas):
                continue

            # Adiciona disponibilidade total para o professor fictício
            new_disponibilidades = list(timetable.disponibilidades)
            unique_weekdays: set[str] = set()
            for slot in timetable.slots:
                if slot.weekday not in unique_weekdays:
                    new_disponibilidades.append(
                        Disponibilidade(
                            teacher_id=teacher_id_fake,
                            weekday=slot.weekday,
                            start_order=1,
                            end_order=99,
                        )
                    )
                    unique_weekdays.add(slot.weekday)

            modified_tt = replace(
                timetable,
                aulas=tuple(modified_aulas),
                disponibilidades=tuple(new_disponibilidades),
            )
            buracos_depois = self._solve_rapido(modified_tt)

            if buracos_depois < self.buracos_antes:
                candidates.append(
                    {
                        "categoria": Suggestion.CategoriaChoices.TEACHER_ADD,
                        "titulo": f"Adicionar professor habilitado em {subject.name}",
                        "descricao": (
                            f"Adicionar 1 professor habilitado em {subject.name} "
                            f"pode reduzir buracos de {self.buracos_antes} para {buracos_depois}."
                        ),
                        "buracos_depois": buracos_depois,
                        "param_diff": {
                            "subject": subject.name,
                            "acao": "adicionar_professor",
                        },
                        "delta": self.buracos_antes - buracos_depois,
                    }
                )

        suggestions: list[Suggestion] = []
        for c in self._top_n_by_delta(candidates):
            suggestions.append(
                self._create_suggestion(
                    categoria=c["categoria"],
                    titulo=c["titulo"],
                    descricao=c["descricao"],
                    buracos_depois=c["buracos_depois"],
                    param_diff=c["param_diff"],
                )
            )
        return suggestions

    # ------------------------------------------------------------------
    # Categoria 3: teacher_availability
    # ------------------------------------------------------------------

    def _run_teacher_availability(self) -> list[Suggestion]:
        """Simula expandir a janela de disponibilidade de professores."""
        timetable = self._load_timetable()

        # Busca entradas de indisponibilidade (is_available=False)
        unavailable = list(
            TeacherAvailability.objects.filter(
                tenant_id=self.solver_run.tenant_id,
                is_available=False,
            ).select_related("teacher")[:10]
        )

        candidates: list[dict] = []

        for avail in unavailable:
            teacher_id = avail.teacher_id

            # Simula: remove indisponibilidades deste professor (marca como disponível)
            modified_disponibilidades: list[Disponibilidade] = []
            found_teacher = False
            for d in timetable.disponibilidades:
                if d.teacher_id == teacher_id:
                    found_teacher = True
                    continue  # remove indisponibilidades do professor
                modified_disponibilidades.append(d)

            # Se o professor não estava no timetable como indisponível,
            # não há o que simular
            if not found_teacher:
                continue

            modified_tt = replace(
                timetable,
                disponibilidades=tuple(modified_disponibilidades),
            )
            buracos_depois = self._solve_rapido(modified_tt)

            if buracos_depois < self.buracos_antes:
                candidates.append(
                    {
                        "categoria": Suggestion.CategoriaChoices.TEACHER_AVAILABILITY,
                        "titulo": (
                            f"Liberar {avail.teacher.name} no "
                            f"{avail.get_weekday_display()} "
                            f"{avail.start_time}–{avail.end_time}"
                        ),
                        "descricao": (
                            f"Marcar {avail.teacher.name} como disponível no "
                            f"{avail.get_weekday_display()} "
                            f"{avail.start_time}–{avail.end_time} "
                            f"pode reduzir buracos de {self.buracos_antes} para {buracos_depois}."
                        ),
                        "buracos_depois": buracos_depois,
                        "param_diff": {
                            "teacher": avail.teacher.name,
                            "weekday": avail.weekday,
                            "start_time": str(avail.start_time),
                            "end_time": str(avail.end_time),
                            "acao": "marcar_disponível",
                        },
                        "delta": self.buracos_antes - buracos_depois,
                    }
                )

        suggestions: list[Suggestion] = []
        for c in self._top_n_by_delta(candidates):
            suggestions.append(
                self._create_suggestion(
                    categoria=c["categoria"],
                    titulo=c["titulo"],
                    descricao=c["descricao"],
                    buracos_depois=c["buracos_depois"],
                    param_diff=c["param_diff"],
                )
            )
        return suggestions

    # ------------------------------------------------------------------
    # Categoria 4: subject_rule_relax
    # ------------------------------------------------------------------

    def _run_subject_rule_relax(self) -> list[Suggestion]:
        """Simula relaxar SubjectRule constraints, testa se reduz buracos."""
        timetable = self._load_timetable()

        rules = list(
            SubjectRule.objects.filter(
                tenant_id=self.solver_run.tenant_id,
                is_active=True,
            )[:10]
        )

        candidates: list[dict] = []

        for rule in rules:
            # Simula: marca regra como flexível (relaxada)
            modified_restricoes: list[Restricao] = []
            found_rule = False
            for r in timetable.restricoes:
                if r.descricao == rule.rule_type:
                    modified_restricoes.append(
                        replace(r, tipo=RestricaoTipo.FLEXIVEL)
                    )
                    found_rule = True
                else:
                    modified_restricoes.append(r)

            if not found_rule:
                # Regra não estava no timetable — adiciona como flexível
                modified_restricoes = list(timetable.restricoes) + [
                    Restricao(
                        tipo=RestricaoTipo.FLEXIVEL,
                        descricao=rule.rule_type,
                    )
                ]

            modified_tt = replace(
                timetable,
                restricoes=tuple(modified_restricoes),
            )
            buracos_depois = self._solve_rapido(modified_tt)

            if buracos_depois < self.buracos_antes:
                candidates.append(
                    {
                        "categoria": Suggestion.CategoriaChoices.SUBJECT_RULE_RELAX,
                        "titulo": f"Relaxar regra '{rule.get_rule_type_display()}'",
                        "descricao": (
                            f"Relaxar a regra '{rule.get_rule_type_display()}' "
                            f"pode reduzir buracos de {self.buracos_antes} para {buracos_depois}."
                        ),
                        "buracos_depois": buracos_depois,
                        "param_diff": {
                            "rule_type": rule.rule_type,
                            "rule_id": str(rule.id),
                            "acao": "relaxar_regra",
                        },
                        "delta": self.buracos_antes - buracos_depois,
                    }
                )

        suggestions: list[Suggestion] = []
        for c in self._top_n_by_delta(candidates):
            suggestions.append(
                self._create_suggestion(
                    categoria=c["categoria"],
                    titulo=c["titulo"],
                    descricao=c["descricao"],
                    buracos_depois=c["buracos_depois"],
                    param_diff=c["param_diff"],
                )
            )
        return suggestions