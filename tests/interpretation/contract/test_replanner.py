# tests/interpretation/contract/test_replanner.py
"""replan: 07_parte_interpretacion.md seccion 7. Regla dura: no puede
cambiar el objetivo. No valida nada mas -- eso lo hace el camino normal
(interpretation_validator, build_analysis_plan) sobre lo que replan()
devuelve.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.analytics.operation_catalog import OPERATION_CATALOG
from querypilot.business_knowledge.semantic_artifact import (
    Calendar,
    CalendarType,
    Connection,
    SemanticArtifact,
    Thresholds,
)
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import ObjectiveName
from querypilot.interpretation.replanner import replan
from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    InterpretationOutput,
    ObjectiveProposal,
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
    return SemanticArtifact(connection=connection, dimensions=[], metrics=[])


def _proposal(objective: ObjectiveName) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=objective,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=(),
    )


async def test_replan_returns_the_output_when_the_objective_is_conserved() -> None:
    fixture = InterpretationOutput(
        objective_proposals=(_proposal(ObjectiveName.EXPLAIN_VARIANCE),),
        out_of_scope=(),
        prompt_version="fixture",
    )
    double = DeterministicModelPort(interpretation_output=fixture)

    result = await replan(
        original_objective=ObjectiveName.EXPLAIN_VARIANCE,
        model_port=double,
        prompt_version="v1",
        question="¿Por que cayo la facturacion?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        previous_plan_summary="paso 1: compare_periods(...)",
        insufficiency_cause="explained_coverage = 40% < 70%",
    )

    assert isinstance(result, InterpretationOutput)
    assert result.objective_proposals[0].objective == ObjectiveName.EXPLAIN_VARIANCE


async def test_replan_rejects_when_the_objective_changes() -> None:
    fixture = InterpretationOutput(
        objective_proposals=(_proposal(ObjectiveName.RANK),),
        out_of_scope=(),
        prompt_version="fixture",
    )
    double = DeterministicModelPort(interpretation_output=fixture)

    result = await replan(
        original_objective=ObjectiveName.EXPLAIN_VARIANCE,
        model_port=double,
        prompt_version="v1",
        question="¿Por que cayo la facturacion?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        previous_plan_summary="paso 1: compare_periods(...)",
        insufficiency_cause="explained_coverage = 40% < 70%",
    )

    assert not isinstance(result, InterpretationOutput)
    assert len(result) == 1
    assert result[0].cause == RejectionCause.REPLAN_CHANGED_OBJECTIVE
