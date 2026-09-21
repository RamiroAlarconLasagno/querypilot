# tests/canonical_language/unit/test_plan.py
"""AnalysisPlan y familia: 14_contratos_formato.md seccion 6. Fixture con las
dos variantes de SufficiencyCriterion y una PlannedObjectiveDependency real,
para confirmar que la union discriminada y el plan completo redondean por JSON.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.canonical_language.identifiers import AttemptId, ObjectiveId, TurnId
from querypilot.canonical_language.plan import (
    AnalysisPlan,
    PlannedObjective,
    PlannedObjectiveDependency,
    PlanStep,
    StepId,
    StepState,
    TurnBudget,
)
from querypilot.canonical_language.shared_values import (
    AllStepsCompleted,
    Binding,
    Condition,
    ConditionOperator,
    FactValueCondition,
    FilterOperator,
    ObjectiveName,
    OperationName,
    ThresholdName,
)


def _plan() -> AnalysisPlan:
    obj_1 = PlannedObjective(
        objective_id=ObjectiveId("obj_1"),
        objective=ObjectiveName.EXPLAIN_VARIANCE,
        sufficiency=FactValueCondition(
            condition=Condition(
                fact_type="explained_coverage",
                operator=ConditionOperator.GTE,
                value=ThresholdName.MIN_EXPLANATION_COVERAGE,
            )
        ),
        steps=(
            PlanStep(
                step_id=StepId("s1"),
                operation=OperationName.COMPARE_PERIODS,
                arguments={"metric": "net_revenue"},
                derives_from=(),
                state=StepState.COMPLETED,
                attempt_id=AttemptId("att_1"),
            ),
            PlanStep(
                step_id=StepId("s2"),
                operation=OperationName.DECOMPOSE_VARIANCE,
                arguments={"metric": "net_revenue", "dimension": "customer"},
                condition=Condition(
                    fact_type="relative_variance", operator=ConditionOperator.LT, value=Decimal(0)
                ),
                derives_from=(StepId("s1"),),
                state=StepState.COMPLETED,
                attempt_id=AttemptId("att_1"),
            ),
        ),
    )
    obj_2 = PlannedObjective(
        objective_id=ObjectiveId("obj_2"),
        objective=ObjectiveName.RANK,
        sufficiency=AllStepsCompleted(),
        dependency=PlannedObjectiveDependency(
            source_objective_id=ObjectiveId("obj_1"),
            binding=Binding(
                source_fact_type="main_contributor",
                target_dimension="customer",
                operator=FilterOperator.NOT_IN,
            ),
        ),
        steps=(
            PlanStep(
                step_id=StepId("s1"),
                operation=OperationName.RANK,
                arguments={"metric": "net_revenue", "dimension": "customer", "n": 10},
                derives_from=(),
                state=StepState.PENDING,
            ),
        ),
    )
    return AnalysisPlan(
        id="plan_1",
        turn_id=TurnId("t_58"),
        objectives=(obj_1, obj_2),
        budget=TurnBudget(total_time_seconds=90, max_model_calls=5),
    )


def test_analysis_plan_round_trips_through_json() -> None:
    plan = _plan()
    restored = AnalysisPlan.model_validate_json(plan.model_dump_json())
    assert restored == plan


def test_both_sufficiency_variants_are_distinguishable_after_round_trip() -> None:
    plan = _plan()
    restored = AnalysisPlan.model_validate_json(plan.model_dump_json())
    assert isinstance(restored.objectives[0].sufficiency, FactValueCondition)
    assert isinstance(restored.objectives[1].sufficiency, AllStepsCompleted)


def test_planned_objective_dependency_uses_durable_objective_id_not_proposal_id() -> None:
    plan = _plan()
    dependency = plan.objectives[1].dependency
    assert dependency is not None
    assert dependency.source_objective_id == "obj_1"


def test_plan_step_derives_from_references_a_step_in_the_same_plan() -> None:
    plan = _plan()
    steps = plan.objectives[0].steps
    assert steps[1].derives_from == (steps[0].step_id,)
