# src/querypilot/model_port/structured_output.py
"""Salida estructurada del puerto del modelo. 14_contratos_formato.md seccion
8: un solo esquema valida la salida y restringe la generacion; no puede haber
dos definiciones que diverjan. Interpretacion y Sintesis nunca se comunican
entre si (07_parte_interpretacion.md seccion 1): InterpretationOutput y
SynthesisOutput son el unico contrato que comparten con el resto del sistema.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from querypilot.analytics.objective_catalog import ObjectiveName
from querypilot.analytics.operation_catalog import OperationName
from querypilot.canonical_language.shared_values import (
    Binding,
    Condition,
    DomainValue,
    Filter,
)


class InheritedField(StrEnum):
    PERIOD = "period"
    FILTERS = "filters"
    METRIC = "metric"
    DIMENSION = "dimension"


class ContinuityMode(StrEnum):
    NEW = "new"
    CONTINUATION = "continuation"


class Continuity(BaseModel):
    mode: ContinuityMode
    inherits: tuple[InheritedField, ...]


class ConceptMapping(BaseModel):
    canonical: str
    original_expression: str


class ResolvedReference(BaseModel):
    expression: str
    resolution: str


class MaterialAmbiguity(BaseModel):
    description: str
    options: tuple[str, ...]


class OutOfScope(BaseModel):
    reason: str
    alternatives: tuple[str, ...]


class ObjectiveDependency(BaseModel):
    source_proposal_id: str
    binding: Binding


class ProposedPlanStep(BaseModel):
    step_id: str
    operation: OperationName
    arguments: dict[str, DomainValue]
    condition: Condition | None = None
    derives_from: tuple[str, ...]


class ObjectiveProposal(BaseModel):
    proposal_id: str
    objective: ObjectiveName
    continuity: Continuity
    concepts: tuple[ConceptMapping, ...]
    time_expressions: tuple[str, ...]
    filters: tuple[Filter, ...]
    premises: tuple[str, ...]
    references: tuple[ResolvedReference, ...]
    ambiguities: tuple[MaterialAmbiguity, ...]
    plan: tuple[ProposedPlanStep, ...]
    dependency: ObjectiveDependency | None = None


class InterpretationOutput(BaseModel):
    objective_proposals: tuple[ObjectiveProposal, ...]
    out_of_scope: tuple[OutOfScope, ...]
    prompt_version: str


class AssertionKind(StrEnum):
    DATA = "data"
    INTERPRETATION = "interpretation"
    HYPOTHESIS = "hypothesis"


class Assertion(BaseModel):
    id: str
    objective_id: str
    turn_id: str
    kind: AssertionKind
    text: str
    evidence: tuple[str, ...]


class CrossObjectiveAssertion(BaseModel):
    turn_id: str
    objective_ids: tuple[str, ...]
    kind: AssertionKind
    text: str
    evidence: tuple[str, ...]


class AnswerSection(BaseModel):
    objective_id: str
    assertions: tuple[Assertion, ...]


class ResearchSuggestion(BaseModel):
    question: str


class SynthesisOutput(BaseModel):
    sections: tuple[AnswerSection, ...]
    cross_objective: CrossObjectiveAssertion | None = None
    suggestions: tuple[ResearchSuggestion, ...]
    prompt_version: str
