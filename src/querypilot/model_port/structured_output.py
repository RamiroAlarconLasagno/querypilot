# src/querypilot/model_port/structured_output.py
"""Salida estructurada del puerto del modelo. 14_contratos_formato.md seccion
8: un solo esquema valida la salida y restringe la generacion; no puede haber
dos definiciones que diverjan. Interpretacion y Sintesis nunca se comunican
entre si (07_parte_interpretacion.md seccion 1): InterpretationOutput y
SynthesisOutput son el unico contrato que comparten con el resto del sistema.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from querypilot.analytics.objective_catalog import ObjectiveName
from querypilot.analytics.operation_catalog import OperationName
from querypilot.business_knowledge.semantic_artifact import Granularity


class FactType(StrEnum):
    """Tipos de hecho declarados por las diez fichas de 10_parte_operaciones.md
    seccion 8. Cada operacion es duena de los suyos; este enum solo los reune
    para poder tiparlos en Condition y Binding.
    """

    PERIOD_VALUE = "period_value"
    ABSOLUTE_VARIANCE = "absolute_variance"
    RELATIVE_VARIANCE = "relative_variance"
    MAIN_CONTRIBUTOR = "main_contributor"
    EXPLAINED_COVERAGE = "explained_coverage"
    DIMENSION_CARDINALITY = "dimension_cardinality"
    RANKING_ELEMENT = "ranking_element"
    UNIVERSE_TOTAL = "universe_total"
    UNIVERSE_SCOPE = "universe_scope"
    METRIC_VALUE = "metric_value"
    VALUE_PER_ELEMENT = "value_per_element"
    SERIES_POINT = "series_point"
    COUNT = "count"
    AVAILABLE_COLUMNS = "available_columns"
    ANOMALOUS_POINT = "anomalous_point"
    APPLIED_CRITERION = "applied_criterion"
    SHARE = "share"


class ConditionOperator(StrEnum):
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    EQ = "eq"
    NEQ = "neq"


class ThresholdName(StrEnum):
    """Umbrales configurados que una Condition puede citar en vez de un valor
    literal. Acotado a los dos umbrales de connection.yaml que se comparan
    contra hechos (09_parte_ejecutor.md seccion 5): el resto de los campos de
    Thresholds son limites operativos (filas, segundos, MB), no criterios de
    suficiencia.
    """

    MIN_EXPLANATION_COVERAGE = "min_explanation_coverage"
    DECOMPOSE_VARIANCE_MAX_DIMENSION_CARDINALITY = "decompose_variance_max_dimension_cardinality"


class Condition(BaseModel):
    fact_type: FactType
    operator: ConditionOperator
    value: Decimal | ThresholdName


class FilterOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"


class Filter(BaseModel):
    dimension: str
    operator: FilterOperator
    values: tuple[str, ...]


class SortDirection(StrEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


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


class Binding(BaseModel):
    source_fact_type: FactType
    target_dimension: str
    operator: FilterOperator


class ObjectiveDependency(BaseModel):
    source_proposal_id: str
    binding: Binding


DomainValue = str | int | Granularity | SortDirection


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
