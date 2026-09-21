# tests/interpretation/contract/test_service.py
"""Flujo completo de Interpretacion con DeterministicModelPort:
pregunta + contexto -> build_material -> ModelPort.interpret ->
validate_interpretation -> build_analysis_plan. 07_parte_interpretacion.md
seccion 10. Sin proveedor real, sin ejecucion de operaciones.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.analytics.operation_catalog import OPERATION_CATALOG
from querypilot.business_knowledge.semantic_artifact import (
    Calendar,
    CalendarType,
    Connection,
    Metric,
    MetricPhysical,
    SemanticArtifact,
    Thresholds,
)
from querypilot.canonical_language.plan import AnalysisPlan
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import (
    Binding,
    FilterOperator,
    Granularity,
    ObjectiveName,
)
from querypilot.interpretation.service import (
    NeedsClarification,
    PlanReady,
    Rejected,
    run_interpretation,
    run_replanning,
)
from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.structured_output import (
    ConceptMapping,
    Continuity,
    ContinuityMode,
    InterpretationOutput,
    MaterialAmbiguity,
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
        aggregations=[],
        combinable_dimensions=[],
        min_granularity=Granularity.DAY,
        physical=MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="cmp_cab.f"),
    )
    return SemanticArtifact(connection=connection, dimensions=[], metrics=[metric])


def _proposal(
    proposal_id: str = "p1",
    objective: ObjectiveName = ObjectiveName.QUERY_METRIC,
    plan: tuple[ProposedPlanStep, ...] = (),
    continuity: Continuity | None = None,
    ambiguities: tuple[MaterialAmbiguity, ...] = (),
    dependency: ObjectiveDependency | None = None,
) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id=proposal_id,
        objective=objective,
        continuity=continuity or Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(ConceptMapping(canonical="net_revenue", original_expression="facturacion"),),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=ambiguities,
        plan=plan,
        dependency=dependency,
    )


async def test_a_simple_valid_question_produces_an_analysis_plan() -> None:
    proposal = _proposal(
        plan=(
            ProposedPlanStep(
                step_id="s1",
                operation="query_metric",
                arguments={"metric": "net_revenue", "period": "julio"},
                derives_from=(),
            ),
        )
    )
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, PlanReady)
    assert isinstance(outcome.plan, AnalysisPlan)
    assert len(outcome.plan.objectives) == 1


async def test_an_invalid_argument_is_rejected() -> None:
    proposal = _proposal(
        plan=(
            ProposedPlanStep(
                step_id="s1",
                operation="query_metric",
                arguments={"metric": "net_revenue", "period": "julio", "bogus": "x"},
                derives_from=(),
            ),
        )
    )
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, Rejected)
    assert any(r.cause == RejectionCause.INVALID_PARAMETERS for r in outcome.rejections)


async def test_material_ambiguity_does_not_build_a_plan() -> None:
    ambiguity = MaterialAmbiguity(description='criterio de "mejores"', options=())
    proposal = _proposal(objective=ObjectiveName.RANK, ambiguities=(ambiguity,), plan=())
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="¿Los mejores clientes?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, NeedsClarification)
    assert len(outcome.ambiguities) == 1


async def test_explore_is_rejected() -> None:
    proposal = _proposal(objective=ObjectiveName.EXPLORE, plan=())
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="¿Como viene el negocio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, Rejected)
    assert any(r.cause == RejectionCause.OBJECTIVE_NOT_AVAILABLE for r in outcome.rejections)


async def test_continuation_without_state_is_rejected() -> None:
    proposal = _proposal(
        continuity=Continuity(mode=ContinuityMode.CONTINUATION, inherits=()), plan=()
    )
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="Segui con lo mismo",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, Rejected)
    assert any(r.cause == RejectionCause.CONTINUATION_WITHOUT_STATE for r in outcome.rejections)


async def test_a_valid_dependency_between_two_objectives_translates_ephemeral_ids() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation="query_metric",
        arguments={"metric": "net_revenue", "period": "julio"},
        derives_from=(),
    )
    binding = Binding(
        source_fact_type="main_contributor",
        target_dimension="customer",
        operator=FilterOperator.NOT_IN,
    )
    p1 = _proposal(proposal_id="p1", objective=ObjectiveName.QUERY_METRIC, plan=(step,))
    p2 = _proposal(
        proposal_id="p2",
        objective=ObjectiveName.COMPARE,
        plan=(step,),
        dependency=ObjectiveDependency(source_proposal_id="p1", binding=binding),
    )
    output = InterpretationOutput(
        objective_proposals=(p1, p2), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_interpretation(
        model_port=double,
        prompt_version="v1",
        question="Compara julio contra junio para esos mismos clientes",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, PlanReady)
    dependency = outcome.plan.objectives[1].dependency
    assert dependency is not None
    assert dependency.source_objective_id == "obj_1"


async def test_replanning_that_conserves_the_objective_can_produce_a_plan() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation="query_metric",
        arguments={"metric": "net_revenue", "period": "junio"},
        derives_from=(),
    )
    proposal = _proposal(objective=ObjectiveName.QUERY_METRIC, plan=(step,))
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_replanning(
        model_port=double,
        prompt_version="v1",
        original_objective=ObjectiveName.QUERY_METRIC,
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        previous_plan_summary="paso 1: query_metric(net_revenue, julio)",
        insufficiency_cause="dato no obtenido en la primera ronda",
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, PlanReady)


async def test_replanning_that_changes_the_objective_is_rejected() -> None:
    proposal = _proposal(objective=ObjectiveName.RANK, plan=())
    output = InterpretationOutput(
        objective_proposals=(proposal,), out_of_scope=(), prompt_version="fixture"
    )
    double = DeterministicModelPort(interpretation_output=output)

    outcome = await run_replanning(
        model_port=double,
        prompt_version="v1",
        original_objective=ObjectiveName.QUERY_METRIC,
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        previous_plan_summary="paso 1: query_metric(net_revenue, julio)",
        insufficiency_cause="dato no obtenido en la primera ronda",
        turn_id="t_1",
        plan_id="plan_1",
    )

    assert isinstance(outcome, Rejected)
    assert any(r.cause == RejectionCause.REPLAN_CHANGED_OBJECTIVE for r in outcome.rejections)
