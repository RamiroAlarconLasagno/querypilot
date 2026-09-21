# tests/interpretation/contract/test_interpretation_validator.py
"""validate_interpretation: orquesta proposal_builder, ambiguity_detector,
reference_resolver, plan_builder (las dos funciones) y dependency_graph, en
ese orden, sin transformar nada. 07_parte_interpretacion.md seccion 10.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.business_knowledge.semantic_artifact import (
    Aggregation,
    Calendar,
    CalendarType,
    Connection,
    Metric,
    MetricPhysical,
    SemanticArtifact,
    Thresholds,
)
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import (
    Binding,
    FilterOperator,
    Granularity,
    ObjectiveName,
    OperationName,
)
from querypilot.interpretation.interpretation_validator import validate_interpretation
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    InterpretationOutput,
    ObjectiveDependency,
    ObjectiveProposal,
    ProposedPlanStep,
)


def _artifact() -> SemanticArtifact:
    thresholds = Thresholds(
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
    connection = Connection(
        id="demo",
        description="Conexion de prueba.",
        engine="postgresql",
        calendar=Calendar(type=CalendarType.CALENDAR, closing_month=12, week_start="monday"),
        thresholds=thresholds,
        sensitivity=[],
    )
    metric = Metric(
        id="net_revenue",
        business_name="Facturacion",
        definition="Definicion de prueba.",
        synonyms=["ventas"],
        unit="ARS",
        aggregations=[Aggregation.SUM],
        combinable_dimensions=[],
        min_granularity=Granularity.DAY,
        physical=MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="cmp_cab.f"),
    )
    return SemanticArtifact(connection=connection, dimensions=[], metrics=[metric])


def _valid_proposal() -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=ObjectiveName.QUERY_METRIC,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=(
            ProposedPlanStep(
                step_id="s1",
                operation=OperationName.QUERY_METRIC,
                arguments={"metric": "net_revenue", "period": "julio"},
                derives_from=(),
            ),
        ),
    )


def test_a_fully_valid_output_has_no_rejections() -> None:
    output = InterpretationOutput(
        objective_proposals=(_valid_proposal(),), out_of_scope=(), prompt_version="v1"
    )
    assert validate_interpretation(output, _artifact(), None, ()) == ()


def test_an_unavailable_objective_is_reported_through_the_orchestrator() -> None:
    proposal = _valid_proposal().model_copy(update={"objective": ObjectiveName.EXPLORE, "plan": ()})
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )
    rejections = validate_interpretation(output, _artifact(), None, ())
    assert any(r.cause == RejectionCause.OBJECTIVE_NOT_AVAILABLE for r in rejections)


def test_a_broken_plan_step_is_reported_through_the_orchestrator() -> None:
    bad_step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio", "bogus_arg": "x"},
        derives_from=(),
    )
    proposal = _valid_proposal().model_copy(update={"plan": (bad_step,)})
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="v1"
    )
    rejections = validate_interpretation(output, _artifact(), None, ())
    assert any(r.cause == RejectionCause.INVALID_PARAMETERS for r in rejections)


def test_a_dependency_cycle_across_proposals_is_reported_through_the_orchestrator() -> None:
    binding_source = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.QUERY_METRIC,
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=(),
    )
    binding = Binding(
        source_fact_type="metric_value", target_dimension="customer", operator=FilterOperator.EQ
    )
    p1 = _valid_proposal().model_copy(
        update={
            "proposal_id": "p1",
            "plan": (binding_source,),
            "dependency": ObjectiveDependency(source_proposal_id="p2", binding=binding),
        }
    )
    p2 = _valid_proposal().model_copy(
        update={
            "proposal_id": "p2",
            "plan": (binding_source,),
            "dependency": ObjectiveDependency(source_proposal_id="p1", binding=binding),
        }
    )
    output = InterpretationOutput(
        objective_proposals=(p1, p2), out_of_scope=(), prompt_version="v1"
    )
    rejections = validate_interpretation(output, _artifact(), None, ())
    assert any(r.cause == RejectionCause.DEPENDENCY_CYCLE for r in rejections)
