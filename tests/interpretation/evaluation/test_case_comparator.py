# tests/interpretation/evaluation/test_case_comparator.py
"""Clasificacion de un InterpretationOutcome real contra el `expected` de un
EvaluationCase. Reglas acordadas para el cierre de 1.7 -- ver el docstring
de interpretation/case_comparator.py.
"""

from __future__ import annotations

from querypilot.business_knowledge.evaluation_cases import (
    CaseCategory,
    EvaluationCase,
    ExpectedAmbiguity,
    ExpectedObjective,
    ExpectedOutOfScope,
    ExpectedPlan,
)
from querypilot.canonical_language.plan import AnalysisPlan, TurnBudget
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.canonical_language.shared_values import ObjectiveName, OperationName
from querypilot.interpretation.case_comparator import OutcomeLabel, classify_case
from querypilot.interpretation.service import NeedsClarification, PlanReady, Rejected
from querypilot.model_port.structured_output import (
    ConceptMapping,
    Continuity,
    ContinuityMode,
    InheritedField,
    InterpretationOutput,
    MaterialAmbiguity,
    ObjectiveDependency,
    ObjectiveProposal,
    OutOfScope,
    ProposedPlanStep,
)


def _dummy_plan() -> AnalysisPlan:
    return AnalysisPlan(
        id="plan",
        turn_id="t_1",
        objectives=(),
        budget=TurnBudget(total_time_seconds=90, max_model_calls=5),
    )


def _proposal(
    objective: ObjectiveName,
    metric: str | None = None,
    dimension: str | None = None,
    temporal: tuple[str, ...] = (),
    premises: tuple[str, ...] = (),
    plan: tuple[ProposedPlanStep, ...] = (),
    continuity: Continuity | None = None,
    dependency: ObjectiveDependency | None = None,
) -> ObjectiveProposal:
    concepts = tuple(
        ConceptMapping(canonical=c, original_expression=c) for c in (metric, dimension) if c
    )
    return ObjectiveProposal(
        proposal_id="p1",
        objective=objective,
        continuity=continuity or Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=concepts,
        time_expressions=temporal,
        filters=(),
        premises=premises,
        references=(),
        ambiguities=(),
        plan=plan,
        dependency=dependency,
    )


def _plan_ready(*proposals: ObjectiveProposal) -> PlanReady:
    output = InterpretationOutput(
        objective_proposals=proposals, out_of_scope=(), prompt_version="fixture"
    )
    return PlanReady(plan=_dummy_plan(), output=output)


def _direct_case(temporal: tuple[str, ...] = ()) -> EvaluationCase:
    expected = ExpectedObjective(
        objective=ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=temporal
    )
    return EvaluationCase(
        id="c1",
        category=CaseCategory.DIRECT,
        question="¿Cuanto facturamos en julio?",
        expected=ExpectedPlan(objectives=(expected,)),
    )


def test_matching_plan_is_correct() -> None:
    case = _direct_case(temporal=("julio",))
    outcome = _plan_ready(
        _proposal(ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",))
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.CORRECT
    assert verdict.valid_first_attempt is True


def test_wrong_metric_is_silent_error() -> None:
    case = _direct_case(temporal=("julio",))
    outcome = _plan_ready(
        _proposal(ObjectiveName.QUERY_METRIC, metric="units_sold", temporal=("julio",))
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.SILENT_ERROR
    assert verdict.plan_match is not None
    assert verdict.plan_match.concepts_ok is False


def test_wrong_objective_count_is_silent_error() -> None:
    case = _direct_case(temporal=("julio",))
    outcome = _plan_ready(
        _proposal(ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",)),
        _proposal(ObjectiveName.RANK, metric="net_revenue", dimension="customer"),
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.SILENT_ERROR
    assert verdict.plan_match is not None
    assert verdict.plan_match.same_objective_count is False


def test_unnecessary_clarification_on_a_plan_expected_case() -> None:
    case = _direct_case(temporal=("julio",))
    outcome = NeedsClarification(
        ambiguities=(MaterialAmbiguity(description="x", options=()),), out_of_scope=()
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.UNNECESSARY_CLARIFICATION
    assert verdict.declined_as_out_of_scope is False
    assert verdict.asked_for_clarification is True


def test_generic_rejection_on_a_plan_expected_case_is_not_out_of_scope() -> None:
    case = _direct_case(temporal=("julio",))
    outcome = Rejected(
        rejections=(
            Rejection(cause=RejectionCause.INVALID_PARAMETERS, action=SuggestedAction.RETRY),
        )
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.REJECTED
    assert verdict.declined_as_out_of_scope is False


def test_rejection_becomes_valid_within_retry() -> None:
    case = _direct_case(temporal=("julio",))
    first = Rejected(
        rejections=(
            Rejection(cause=RejectionCause.INVALID_PARAMETERS, action=SuggestedAction.RETRY),
        )
    )
    retry = _plan_ready(
        _proposal(ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",))
    )
    verdict = classify_case(case, first, retry)
    assert verdict.valid_first_attempt is False
    assert verdict.valid_within_retry is True


def test_material_ambiguity_correctly_flagged() -> None:
    case = EvaluationCase(
        id="c2",
        category=CaseCategory.MATERIAL_AMBIGUITY,
        question="¿Los mejores clientes?",
        expected=ExpectedAmbiguity(description='criterio de "mejores"', options=()),
    )
    outcome = NeedsClarification(
        ambiguities=(MaterialAmbiguity(description="x", options=()),), out_of_scope=()
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.CORRECT_AMBIGUITY


def test_material_ambiguity_missed_when_a_plan_is_built() -> None:
    case = EvaluationCase(
        id="c2",
        category=CaseCategory.MATERIAL_AMBIGUITY,
        question="¿Los mejores clientes?",
        expected=ExpectedAmbiguity(description='criterio de "mejores"', options=()),
    )
    outcome = _plan_ready(_proposal(ObjectiveName.RANK, metric="net_revenue", dimension="customer"))
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.MISSED_AMBIGUITY


def test_out_of_scope_correctly_declined_by_the_model() -> None:
    case = EvaluationCase(
        id="c3",
        category=CaseCategory.OUT_OF_SCOPE,
        question="¿Nos conviene abrir una sucursal?",
        expected=ExpectedOutOfScope(reason="requiere proyeccion"),
    )
    outcome = NeedsClarification(
        ambiguities=(), out_of_scope=(OutOfScope(reason="requiere proyeccion", alternatives=()),)
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.CORRECT_OUT_OF_SCOPE
    assert verdict.declined_as_out_of_scope is True


def test_out_of_scope_correctly_declined_by_a_deterministic_rejection() -> None:
    case = EvaluationCase(
        id="c4",
        category=CaseCategory.OUT_OF_SCOPE,
        question="¿Cual fue el margen?",
        expected=ExpectedOutOfScope(
            reason="concepto inexistente", rejection_cause=RejectionCause.NONEXISTENT_CONCEPT
        ),
    )
    outcome = Rejected(
        rejections=(
            Rejection(cause=RejectionCause.NONEXISTENT_CONCEPT, action=SuggestedAction.INFORM),
        )
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.CORRECT_OUT_OF_SCOPE


def test_out_of_scope_missed_when_a_plan_is_built() -> None:
    case = EvaluationCase(
        id="c3",
        category=CaseCategory.OUT_OF_SCOPE,
        question="¿Nos conviene abrir una sucursal?",
        expected=ExpectedOutOfScope(reason="requiere proyeccion"),
    )
    outcome = _plan_ready(_proposal(ObjectiveName.QUERY_METRIC, metric="net_revenue"))
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.MISSED_OUT_OF_SCOPE


def test_dependency_expected_but_missing_is_silent_error() -> None:
    case = EvaluationCase(
        id="c5",
        category=CaseCategory.MULTIPLE_OBJECTIVES,
        question="x",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(objective=ObjectiveName.COMPARE, metric="net_revenue"),
                ExpectedObjective(
                    objective=ObjectiveName.COMPARE, metric="net_revenue", depends_on_previous=True
                ),
            )
        ),
    )
    outcome = _plan_ready(
        _proposal(ObjectiveName.COMPARE, metric="net_revenue"),
        _proposal(ObjectiveName.COMPARE, metric="net_revenue"),  # sin dependency
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.SILENT_ERROR
    assert verdict.plan_match is not None
    assert verdict.plan_match.dependency_ok is False


def test_breakdown_operation_expected_and_present() -> None:
    case = EvaluationCase(
        id="c6",
        category=CaseCategory.DIRECT,
        question="Facturacion por region",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.QUERY_METRIC,
                    metric="net_revenue",
                    dimension="region",
                    operations=(OperationName.BREAKDOWN,),
                ),
            )
        ),
    )
    outcome = _plan_ready(
        _proposal(
            ObjectiveName.QUERY_METRIC,
            metric="net_revenue",
            dimension="region",
            plan=(
                ProposedPlanStep(
                    step_id="s1",
                    operation=OperationName.BREAKDOWN,
                    arguments={"metric": "net_revenue", "dimension": "region", "period": "el ano"},
                    derives_from=(),
                ),
            ),
        )
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.CORRECT


def test_continuation_with_inherits_mismatch_is_silent_error() -> None:
    case = EvaluationCase(
        id="c7",
        category=CaseCategory.CONTINUATION,
        question="¿Y en junio?",
        previous_context="Facturacion de julio.",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(objective=ObjectiveName.QUERY_METRIC, metric="net_revenue"),
            ),
            inherits=(InheritedField.METRIC,),
        ),
    )
    outcome = _plan_ready(
        _proposal(ObjectiveName.QUERY_METRIC, metric="net_revenue")  # continuity=NEW por defecto
    )
    verdict = classify_case(case, outcome, None)
    assert verdict.label is OutcomeLabel.SILENT_ERROR
    assert verdict.plan_match is not None
    assert verdict.plan_match.inherits_ok is False
