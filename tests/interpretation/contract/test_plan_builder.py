# tests/interpretation/contract/test_plan_builder.py
"""validate_plan_steps y check_ambiguity_excludes_plan: 07_parte_interpretacion.md
seccion 10 (paso 5) y 09_parte_ejecutor.md seccion 5.
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import (
    Condition,
    ConditionOperator,
    ObjectiveName,
    OperationName,
)
from querypilot.interpretation.plan_builder import (
    check_ambiguity_excludes_plan,
    validate_plan_steps,
)
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    MaterialAmbiguity,
    ObjectiveProposal,
    ProposedPlanStep,
)


def _proposal(
    plan: tuple[ProposedPlanStep, ...], ambiguities: tuple[MaterialAmbiguity, ...] = ()
) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=ObjectiveName.EXPLAIN_VARIANCE,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=ambiguities,
        plan=plan,
    )


def test_unknown_argument_is_rejected() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio", "bogus_arg": "x"},
        derives_from=(),
    )
    rejections = validate_plan_steps(_proposal((step,)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INVALID_PARAMETERS


def test_missing_required_argument_is_rejected() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue"},
        derives_from=(),
    )
    rejections = validate_plan_steps(_proposal((step,)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INVALID_PARAMETERS


def test_condition_referencing_an_unpublished_fact_is_rejected() -> None:
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
        condition=Condition(
            fact_type="explained_coverage", operator=ConditionOperator.GTE, value=1
        ),
        derives_from=("s1",),
    )
    rejections = validate_plan_steps(_proposal((step_1, step_2)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.CONDITION_REFERENCES_UNPUBLISHED_FACT


def test_derives_from_a_nonexistent_step_is_rejected() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=("s99",),
    )
    rejections = validate_plan_steps(_proposal((step,)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INVALID_DERIVES_FROM


def test_derives_from_a_future_step_is_rejected() -> None:
    step_1 = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=("s2",),
    )
    step_2 = ProposedPlanStep(
        step_id="s2",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "junio"},
        derives_from=(),
    )
    rejections = validate_plan_steps(_proposal((step_1, step_2)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INVALID_DERIVES_FROM


def test_derives_from_self_reference_is_rejected() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=("s1",),
    )
    rejections = validate_plan_steps(_proposal((step,)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INVALID_DERIVES_FROM


def test_valid_plan_with_condition_and_derives_from_has_no_rejections() -> None:
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
        condition=Condition(fact_type="relative_variance", operator=ConditionOperator.LT, value=0),
        derives_from=("s1",),
    )
    assert validate_plan_steps(_proposal((step_1, step_2))) == ()


def test_ambiguity_with_nonempty_plan_is_rejected() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=(),
    )
    ambiguity = MaterialAmbiguity(description='criterio de "mejores"', options=())
    rejections = check_ambiguity_excludes_plan(_proposal((step,), ambiguities=(ambiguity,)))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.AMBIGUITY_WITH_PLAN


def test_ambiguity_with_empty_plan_has_no_rejections() -> None:
    ambiguity = MaterialAmbiguity(description='criterio de "mejores"', options=())
    assert check_ambiguity_excludes_plan(_proposal((), ambiguities=(ambiguity,))) == ()
