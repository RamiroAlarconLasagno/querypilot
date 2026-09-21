# tests/interpretation/contract/test_material_builder.py
"""available_objectives y build_material: 10_parte_operaciones.md seccion 2
(diferimiento de explore) y 07_parte_interpretacion.md seccion 2 (entradas
de Interpretacion). build_material es un renderizado simple y determinista
-- estas pruebas verifican que cada pieza aparece cuando corresponde, no la
calidad del texto.
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
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.canonical_language.shared_values import AnalyticalState, ObjectiveName
from querypilot.interpretation.material_builder import available_objectives, build_material


def test_available_objectives_excludes_only_explore() -> None:
    excluded = {card.name for card in OBJECTIVE_CATALOG} - {
        card.name for card in available_objectives(OBJECTIVE_CATALOG)
    }
    assert excluded == {ObjectiveName.EXPLORE}


def test_available_objectives_keeps_the_six_defined_objectives() -> None:
    assert len(available_objectives(OBJECTIVE_CATALOG)) == 6


def test_available_objectives_never_returns_a_card_without_sufficiency_condition() -> None:
    for card in available_objectives(OBJECTIVE_CATALOG):
        assert card.sufficiency_condition is not None


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


def test_system_prompt_excludes_explore_and_lists_operations() -> None:
    system_prompt, _ = build_material(
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
    )
    assert "explore" not in system_prompt
    assert "query_metric" in system_prompt
    assert "compare_periods" in system_prompt


def test_user_prompt_includes_the_question_and_a_fresh_turn_marker() -> None:
    _, user_prompt = build_material(
        question="¿Cuanto vendimos en julio?",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
    )
    assert "¿Cuanto vendimos en julio?" in user_prompt
    assert "turno nuevo" in user_prompt


def test_user_prompt_includes_analytical_state_when_present() -> None:
    state = AnalyticalState(period="junio y julio de 2026", semantic_version="sem_v7")
    _, user_prompt = build_material(
        question="Segui con lo mismo",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=state,
        conversation_history=(),
    )
    assert "junio y julio de 2026" in user_prompt
    assert "sem_v7" in user_prompt


def test_optional_fields_only_appear_when_provided() -> None:
    _, user_prompt_without = build_material(
        question="q",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
    )
    assert "Aclaracion previa" not in user_prompt_without
    assert "Causa de rechazo" not in user_prompt_without
    assert "Replanificacion" not in user_prompt_without

    _, user_prompt_with = build_material(
        question="q",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        analytical_state=None,
        conversation_history=(),
        prior_clarification="por facturacion neta",
        retry_cause=Rejection(
            cause=RejectionCause.INVALID_PARAMETERS, action=SuggestedAction.RETRY
        ),
        fixed_objective="rank",
        previous_plan_summary="paso 1: rank(...)",
        insufficiency_cause="cobertura insuficiente",
        available_facts=("explained_coverage = 40%",),
    )
    assert "por facturacion neta" in user_prompt_with
    assert "invalid_parameters" in user_prompt_with
    assert "rank" in user_prompt_with
    assert "paso 1: rank(...)" in user_prompt_with
    assert "cobertura insuficiente" in user_prompt_with
    assert "explained_coverage = 40%" in user_prompt_with
