# src/querypilot/canonical_language/plan.py
"""Plan de analisis durable. 14_contratos_formato.md seccion 6: el lenguaje
cerrado de condiciones y el plan que el sistema ejecuta y persiste -- distinto
de InterpretationOutput (model_port), que es la propuesta cruda del modelo
antes de validarse. `step_id` es local a este modulo porque, a diferencia de
`TurnId`/`ObjectiveId`/`AttemptId` (identificadores.py, bloque 1.1), no es un
eje de aislamiento de evidencia: es solo una referencia dentro de un plan.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NewType

from pydantic import BaseModel

from querypilot.canonical_language.identifiers import AttemptId, ObjectiveId, TurnId
from querypilot.canonical_language.shared_values import (
    Binding,
    Condition,
    DomainValue,
    ObjectiveName,
    OperationName,
    SufficiencyCriterion,
)

StepId = NewType("StepId", str)


class StepState(StrEnum):
    PENDING = "pending"
    SKIPPED = "skipped"
    STARTED = "started"
    COMPLETED = "completed"
    REJECTED = "rejected"
    NOT_EXECUTED = "not_executed"


class TurnBudget(BaseModel):
    total_time_seconds: int
    max_model_calls: int


class PlanStep(BaseModel):
    step_id: StepId
    operation: OperationName
    arguments: dict[str, DomainValue]
    condition: Condition | None = None
    derives_from: tuple[StepId, ...]
    state: StepState
    attempt_id: AttemptId | None = None


class PlannedObjectiveDependency(BaseModel):
    source_objective_id: ObjectiveId
    binding: Binding


class PlannedObjective(BaseModel):
    objective_id: ObjectiveId
    objective: ObjectiveName
    sufficiency: SufficiencyCriterion
    dependency: PlannedObjectiveDependency | None = None
    steps: tuple[PlanStep, ...]


class AnalysisPlan(BaseModel):
    id: str
    turn_id: TurnId
    objectives: tuple[PlannedObjective, ...]
    budget: TurnBudget
