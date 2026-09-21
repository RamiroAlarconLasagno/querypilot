# tests/interpretation/contract/test_build_analysis_plan.py
"""build_analysis_plan: transforma una InterpretationOutput ya validada en
AnalysisPlan. No vuelve a validar -- solo asigna ids durables, reescribe
derives_from, traduce ObjectiveDependency y toma sufficiency del catalogo.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.business_knowledge.semantic_artifact import Thresholds
from querypilot.canonical_language.plan import AnalysisPlan, PlannedObjectiveDependency, StepState
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import (
    AllStepsCompleted,
    Binding,
    FilterOperator,
    ObjectiveName,
    OperationName,
)
from querypilot.interpretation.plan_builder import build_analysis_plan
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    InterpretationOutput,
    ObjectiveDependency,
    ObjectiveProposal,
    ProposedPlanStep,
)


def _thresholds() -> Thresholds:
    return Thresholds(
        context_rows=20,
        preview_rows=100,
        preview_columns=20,
        materialization_rows=50000,
        active_datasets_per_session=5,
        active_datasets_mb=50,
        decompose_variance_max_dimension_cardinality=5000,
        min_explanation_coverage=Decimal("0.70"),
        closed_period_freshness_hours=24,
        open_period_freshness_minutes=15,
        query_time_limit_seconds=30,
        turn_budget_seconds=90,
        model_calls_budget=5,
        rows_examined_to_confirm=1_000_000,
    )


def _proposal(
    proposal_id: str,
    objective: ObjectiveName,
    plan: tuple[ProposedPlanStep, ...] = (),
    dependency: ObjectiveDependency | None = None,
) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id=proposal_id,
        objective=objective,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=plan,
        dependency=dependency,
    )


def test_a_single_objective_plan_gets_durable_ids_and_pending_steps() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=(),
    )
    proposal = _proposal("p1", ObjectiveName.QUERY_METRIC, plan=(step,))
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )

    plan = build_analysis_plan(output, turn_id="t_1", plan_id="plan_1", thresholds=_thresholds())

    assert isinstance(plan, AnalysisPlan)
    assert len(plan.objectives) == 1
    objective = plan.objectives[0]
    assert objective.objective_id == "obj_1"
    assert objective.sufficiency == AllStepsCompleted()
    assert len(objective.steps) == 1
    assert objective.steps[0].step_id == "step_1"
    assert objective.steps[0].state == StepState.PENDING
    assert objective.steps[0].attempt_id is None


def test_derives_from_is_rewritten_to_durable_step_ids() -> None:
    step_1 = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.COMPARE_PERIODS,
        arguments={
            "metric": "net_revenue",
            "current_period": "julio",
            "comparison_period": "junio",
        },
        derives_from=(),
    )
    step_2 = ProposedPlanStep(
        step_id="s2",
        operation=OperationName.DECOMPOSE_VARIANCE,
        arguments={
            "metric": "net_revenue",
            "current_period": "julio",
            "comparison_period": "junio",
            "dimension": "customer",
        },
        derives_from=("s1",),
    )
    proposal = _proposal("p1", ObjectiveName.EXPLAIN_VARIANCE, plan=(step_1, step_2))
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )

    plan = build_analysis_plan(output, turn_id="t_1", plan_id="plan_1", thresholds=_thresholds())

    assert isinstance(plan, AnalysisPlan)
    steps = plan.objectives[0].steps
    assert steps[0].step_id == "step_1"
    assert steps[1].step_id == "step_2"
    assert steps[1].derives_from == ("step_1",)


def test_dependency_is_translated_to_durable_objective_ids_with_binding_intact() -> None:
    binding = Binding(
        source_fact_type="main_contributor",
        target_dimension="customer",
        operator=FilterOperator.NOT_IN,
    )
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.RANK,
        arguments={"metric": "net_revenue", "dimension": "customer", "period": "julio"},
        derives_from=(),
    )
    p1 = _proposal("p1", ObjectiveName.EXPLAIN_VARIANCE, plan=(step,))
    p2 = _proposal(
        "p2",
        ObjectiveName.RANK,
        plan=(step,),
        dependency=ObjectiveDependency(source_proposal_id="p1", binding=binding),
    )
    output = InterpretationOutput(
        objective_proposals=(p1, p2), out_of_scope=(), prompt_version="v1"
    )

    plan = build_analysis_plan(output, turn_id="t_1", plan_id="plan_1", thresholds=_thresholds())

    assert isinstance(plan, AnalysisPlan)
    dependency = plan.objectives[1].dependency
    assert dependency == PlannedObjectiveDependency(source_objective_id="obj_1", binding=binding)


def test_an_objective_without_sufficiency_condition_is_rejected_before_building() -> None:
    proposal = _proposal("p1", ObjectiveName.EXPLORE, plan=())
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )

    result = build_analysis_plan(output, turn_id="t_1", plan_id="plan_1", thresholds=_thresholds())

    assert not isinstance(result, AnalysisPlan)
    assert len(result) == 1
    assert result[0].cause == RejectionCause.OBJECTIVE_NOT_AVAILABLE


def test_budget_is_taken_from_thresholds() -> None:
    proposal = _proposal("p1", ObjectiveName.QUERY_METRIC, plan=())
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )

    plan = build_analysis_plan(output, turn_id="t_1", plan_id="plan_1", thresholds=_thresholds())

    assert isinstance(plan, AnalysisPlan)
    assert plan.budget.total_time_seconds == 90
    assert plan.budget.max_model_calls == 5
