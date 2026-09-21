# src/querypilot/interpretation/case_comparator.py
"""Compara un `InterpretationOutcome` real contra el `expected` declarado por
un `EvaluationCase`. 07_parte_interpretacion.md seccion 10 y la definicion de
metricas acordada para el bloque 1.7.

Reglas de clasificacion (decision registrada con el usuario, no inferida):

- Categorias `direct`, `premise`, `continuation`, `multiple_objectives` son
  "plan_expected": el turno debe terminar en un `AnalysisPlan`.
- Sobre esas categorias: `PlanReady` que coincide semanticamente con
  `expected` -> CORRECT (A1). `PlanReady` que no coincide -> SILENT_ERROR
  (A2, el desenlace que el umbral duro no tolera). `NeedsClarification` ->
  UNNECESSARY_CLARIFICATION (resta A1, no es A2). `Rejected` -> REJECTED
  (tampoco A2: un rechazo lleva causa y accion, no es silencioso).
- `material_ambiguity`: `NeedsClarification` con `ambiguities` no vacio ->
  CORRECT_AMBIGUITY. Cualquier otro desenlace -> MISSED_AMBIGUITY.
- `out_of_scope`: declinado (ver `_is_declined`) -> CORRECT_OUT_OF_SCOPE.
  Si no -> MISSED_OUT_OF_SCOPE.
- A4 (falsos fuera de alcance) se calcula aparte, en evaluation_metrics.py,
  sobre cualquier caso no-out_of_scope (incluido material_ambiguity) que
  resulto declinado.

"Declinado" cubre dos caminos deterministas distintos, ambos validos: el
modelo declara `out_of_scope` (`NeedsClarification.out_of_scope` no vacio), o
un validador rechaza por una causa de alcance/existencia del concepto
(`_SCOPE_REJECTION_CAUSES`). `invalid_parameters`, los ciclos de dependencia
y demas causas estructurales NO son "declinar por alcance": son un plan mal
formado, y quedan en REJECTED/MISSED segun la categoria.

El comparador semantico (`_plan_matches`) solo verifica lo que el caso
declaro en `ExpectedObjective`: nunca proposal_id, step_id ni ids durables.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from querypilot.business_knowledge.evaluation_cases import (
    PLAN_EXPECTED_CATEGORIES,
    CaseCategory,
    EvaluationCase,
    ExpectedAmbiguity,
    ExpectedObjective,
    ExpectedOutOfScope,
    ExpectedPlan,
)
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.interpretation.service import (
    InterpretationOutcome,
    NeedsClarification,
    PlanReady,
    Rejected,
)
from querypilot.model_port.structured_output import (
    ContinuityMode,
    InterpretationOutput,
    ObjectiveProposal,
)

_SCOPE_REJECTION_CAUSES = frozenset(
    {
        RejectionCause.NONEXISTENT_CONCEPT,
        RejectionCause.UNAUTHORIZED_CONCEPT,
        RejectionCause.OBJECTIVE_NOT_AVAILABLE,
    }
)


class OutcomeLabel(StrEnum):
    CORRECT = "correct"
    SILENT_ERROR = "silent_error"
    UNNECESSARY_CLARIFICATION = "unnecessary_clarification"
    REJECTED = "rejected"
    CORRECT_AMBIGUITY = "correct_ambiguity"
    MISSED_AMBIGUITY = "missed_ambiguity"
    CORRECT_OUT_OF_SCOPE = "correct_out_of_scope"
    MISSED_OUT_OF_SCOPE = "missed_out_of_scope"


class PlanMatch(BaseModel):
    """Sub-chequeos de un `ExpectedPlan` contra un `InterpretationOutput`
    real. Cada campo es independiente para poder componer los diagnosticos
    (objective_accuracy, concept_accuracy, inheritance_accuracy) sin repetir
    la comparacion.
    """

    same_objective_count: bool
    objective_ok: bool
    concepts_ok: bool
    temporal_ok: bool
    premises_ok: bool
    dependency_ok: bool
    inherits_ok: bool

    @property
    def fully_correct(self) -> bool:
        return all(
            (
                self.same_objective_count,
                self.objective_ok,
                self.concepts_ok,
                self.temporal_ok,
                self.premises_ok,
                self.dependency_ok,
                self.inherits_ok,
            )
        )


class CaseVerdict(BaseModel):
    case_id: str
    category: CaseCategory
    label: OutcomeLabel
    plan_match: PlanMatch | None = None
    valid_first_attempt: bool
    valid_within_retry: bool
    # Independiente de `label`: cualquier caso (de cualquier categoria) cuyo
    # primer intento termino declinado por alcance. A4 se calcula sobre este
    # campo, no sobre `label` -- un caso plan_expected declinado por error
    # queda con label=REJECTED (no es "silencioso") y este campo en True.
    declined_as_out_of_scope: bool
    # Idem para la tasa de aclaracion (07 seccion 10): independiente de la
    # categoria, para poder medirla sobre el banco entero.
    asked_for_clarification: bool


def _is_declined(outcome: InterpretationOutcome) -> bool:
    if isinstance(outcome, NeedsClarification):
        return bool(outcome.out_of_scope)
    if isinstance(outcome, Rejected):
        return bool(outcome.rejections) and all(
            r.cause in _SCOPE_REJECTION_CAUSES for r in outcome.rejections
        )
    return False


def _objective_matches(expected: ExpectedObjective, actual: ObjectiveProposal) -> PlanMatch:
    objective_ok = expected.objective == actual.objective

    concepts = {mapping.canonical for mapping in actual.concepts}
    concepts_ok = (expected.metric is None or expected.metric in concepts) and (
        expected.dimension is None or expected.dimension in concepts
    )

    normalized_expected_temporal = {t.strip().lower() for t in expected.temporal}
    normalized_actual_temporal = {t.strip().lower() for t in actual.time_expressions}
    temporal_ok = normalized_expected_temporal <= normalized_actual_temporal

    premises_ok = not expected.premises or bool(actual.premises)

    operations_ok = not expected.operations or any(
        step.operation in expected.operations for step in actual.plan
    )

    dependency_ok = (actual.dependency is not None) == expected.depends_on_previous

    return PlanMatch(
        same_objective_count=True,
        objective_ok=objective_ok,
        concepts_ok=concepts_ok and operations_ok,
        temporal_ok=temporal_ok,
        premises_ok=premises_ok,
        dependency_ok=dependency_ok,
        inherits_ok=True,
    )


def _plan_matches(expected: ExpectedPlan, output: InterpretationOutput) -> PlanMatch:
    if len(expected.objectives) != len(output.objective_proposals):
        return PlanMatch(
            same_objective_count=False,
            objective_ok=False,
            concepts_ok=False,
            temporal_ok=False,
            premises_ok=False,
            dependency_ok=False,
            inherits_ok=False,
        )

    per_objective = [
        _objective_matches(expected_objective, actual_objective)
        for expected_objective, actual_objective in zip(
            expected.objectives, output.objective_proposals, strict=True
        )
    ]

    inherits_ok = True
    if expected.inherits:
        first_proposal = output.objective_proposals[0]
        inherits_ok = first_proposal.continuity.mode == ContinuityMode.CONTINUATION and set(
            expected.inherits
        ) <= set(first_proposal.continuity.inherits)

    return PlanMatch(
        same_objective_count=True,
        objective_ok=all(m.objective_ok for m in per_objective),
        concepts_ok=all(m.concepts_ok for m in per_objective),
        temporal_ok=all(m.temporal_ok for m in per_objective),
        premises_ok=all(m.premises_ok for m in per_objective),
        dependency_ok=all(m.dependency_ok for m in per_objective),
        inherits_ok=inherits_ok,
    )


def classify_case(
    case: EvaluationCase,
    first_attempt: InterpretationOutcome,
    retry_attempt: InterpretationOutcome | None,
) -> CaseVerdict:
    expected = case.expected
    valid_first_attempt = isinstance(first_attempt, PlanReady)
    valid_within_retry = valid_first_attempt or isinstance(retry_attempt, PlanReady)
    declined = _is_declined(first_attempt)
    asked_for_clarification = isinstance(first_attempt, NeedsClarification) and bool(
        first_attempt.ambiguities
    )

    if isinstance(expected, ExpectedAmbiguity):
        label = (
            OutcomeLabel.CORRECT_AMBIGUITY
            if asked_for_clarification
            else OutcomeLabel.MISSED_AMBIGUITY
        )
        return CaseVerdict(
            case_id=case.id,
            category=case.category,
            label=label,
            valid_first_attempt=valid_first_attempt,
            valid_within_retry=valid_within_retry,
            declined_as_out_of_scope=declined,
            asked_for_clarification=asked_for_clarification,
        )

    if isinstance(expected, ExpectedOutOfScope):
        label = OutcomeLabel.CORRECT_OUT_OF_SCOPE if declined else OutcomeLabel.MISSED_OUT_OF_SCOPE
        return CaseVerdict(
            case_id=case.id,
            category=case.category,
            label=label,
            valid_first_attempt=valid_first_attempt,
            valid_within_retry=valid_within_retry,
            declined_as_out_of_scope=declined,
            asked_for_clarification=asked_for_clarification,
        )

    assert isinstance(expected, ExpectedPlan)
    assert case.category in PLAN_EXPECTED_CATEGORIES

    if isinstance(first_attempt, PlanReady):
        plan_match = _plan_matches(expected, first_attempt.output)
        label = OutcomeLabel.CORRECT if plan_match.fully_correct else OutcomeLabel.SILENT_ERROR
    elif isinstance(first_attempt, NeedsClarification):
        plan_match = None
        label = OutcomeLabel.UNNECESSARY_CLARIFICATION
    else:
        plan_match = None
        label = OutcomeLabel.REJECTED

    return CaseVerdict(
        case_id=case.id,
        category=case.category,
        label=label,
        plan_match=plan_match,
        valid_first_attempt=valid_first_attempt,
        valid_within_retry=valid_within_retry,
        declined_as_out_of_scope=declined,
        asked_for_clarification=asked_for_clarification,
    )
