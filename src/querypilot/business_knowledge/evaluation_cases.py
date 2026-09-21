# src/querypilot/business_knowledge/evaluation_cases.py
"""Banco de casos de evaluacion: pregunta -> interpretacion esperada.

06_parte_conocimiento_negocio.md seccion "Modulos que la componen":
"evaluation_cases | Banco de casos, versionado con el artefacto" -- vive aca,
no en interpretation/, porque los casos dependen del vocabulario (metricas,
dimensiones, sinonimos) igual que concept_resolver o context_filter. Lo que
si vive en interpretation/ es el comando que corre el banco contra
Interpretacion (evaluation_cli.py), porque ese es el consumidor.

01_metodo_solucion.md seccion 12 y 07_parte_interpretacion.md seccion 10: un
caso NO declara cifras -- la interpretacion esperada depende solo de la capa
semantica, nunca de los datos. `expected` es una union discriminada, simetrica
a `InterpretationOutcome` (interpretation/service.py): un caso espera
exactamente uno de tres desenlaces -- un plan, una ambiguedad material, o una
razon de fuera de alcance.

El comparador semantico (interpretation/case_comparator.py) solo verifica lo
declarado aca -- nunca proposal_id, step_id, ni ningun identificador durable,
que son accidentes de una corrida y no parte de la interpretacion esperada.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, Field

from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import ObjectiveName, OperationName
from querypilot.model_port.structured_output import InheritedField


class CaseCategory(StrEnum):
    """Composicion fija del banco (60 casos): 40% direct, 15% material_ambiguity,
    15% continuation, 10% premise, 10% multiple_objectives, 10% out_of_scope.
    """

    DIRECT = "direct"
    PREMISE = "premise"
    CONTINUATION = "continuation"
    MULTIPLE_OBJECTIVES = "multiple_objectives"
    MATERIAL_AMBIGUITY = "material_ambiguity"
    OUT_OF_SCOPE = "out_of_scope"


BANK_SIZE = 60

CATEGORY_SHARE: dict[CaseCategory, float] = {
    CaseCategory.DIRECT: 0.40,
    CaseCategory.MATERIAL_AMBIGUITY: 0.15,
    CaseCategory.CONTINUATION: 0.15,
    CaseCategory.PREMISE: 0.10,
    CaseCategory.MULTIPLE_OBJECTIVES: 0.10,
    CaseCategory.OUT_OF_SCOPE: 0.10,
}

# "plan_expected": categorias donde el turno debe terminar en un AnalysisPlan.
# Decision registrada con el usuario (cierre de 1.6 -> alcance de 1.7): las
# metricas A1/A2/B1/B2 se miden sobre este subconjunto; A4 se mide sobre todo
# menos out_of_scope (incluye material_ambiguity).
PLAN_EXPECTED_CATEGORIES = frozenset(
    {
        CaseCategory.DIRECT,
        CaseCategory.PREMISE,
        CaseCategory.CONTINUATION,
        CaseCategory.MULTIPLE_OBJECTIVES,
    }
)


class ExpectedKind(StrEnum):
    PLAN = "plan"
    AMBIGUITY = "ambiguity"
    OUT_OF_SCOPE = "out_of_scope"


class ExpectedObjective(BaseModel):
    """Lo esperable de un `ObjectiveProposal`. Todo lo no declarado (metric,
    dimension, temporal...) queda fuera de la comparacion -- no es "debe
    estar vacio", es "no se verifica".
    """

    objective: ObjectiveName
    metric: str | None = None
    dimension: str | None = None
    temporal: tuple[str, ...] = ()
    premises: tuple[str, ...] = ()
    operations: tuple[OperationName, ...] = ()
    depends_on_previous: bool = False


class ExpectedPlan(BaseModel):
    kind: Literal[ExpectedKind.PLAN] = ExpectedKind.PLAN
    objectives: tuple[ExpectedObjective, ...]
    inherits: tuple[InheritedField, ...] = ()


class ExpectedAmbiguity(BaseModel):
    kind: Literal[ExpectedKind.AMBIGUITY] = ExpectedKind.AMBIGUITY
    description: str
    options: tuple[str, ...] = ()


class ExpectedOutOfScope(BaseModel):
    kind: Literal[ExpectedKind.OUT_OF_SCOPE] = ExpectedKind.OUT_OF_SCOPE
    reason: str
    offered_alternatives: tuple[str, ...] = ()
    # Cuando el rechazo lo produce un validador deterministico (p. ej. un
    # concepto inexistente) en vez de que el modelo declare `out_of_scope`
    # por su cuenta.
    rejection_cause: RejectionCause | None = None
    must_not_name: tuple[str, ...] = ()


ExpectedOutcome = Annotated[
    ExpectedPlan | ExpectedAmbiguity | ExpectedOutOfScope, Field(discriminator="kind")
]


class EvaluationCase(BaseModel):
    id: str
    category: CaseCategory
    question: str
    previous_context: str | None = None
    expected: ExpectedOutcome


def load_evaluation_cases(connection_dir: Path) -> tuple[EvaluationCase, ...]:
    """Carga `evaluation/cases.yaml` de una conexion (p. ej. `semantic/demo`)."""
    raw = yaml.safe_load((connection_dir / "evaluation" / "cases.yaml").read_text(encoding="utf-8"))
    return tuple(EvaluationCase.model_validate(case) for case in raw["cases"])
