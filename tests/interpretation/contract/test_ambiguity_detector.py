# tests/interpretation/contract/test_ambiguity_detector.py
"""check_materiality: 07_parte_interpretacion.md seccion 5. Cuatro casos:
sin expression, sin default, con un default inequivoco, y con mas de un
default en colision -- los dos ultimos tienen que dar el mismo resultado
(sigue material) por motivos distintos.
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
from querypilot.canonical_language.shared_values import Granularity, ObjectiveName
from querypilot.interpretation.ambiguity_detector import check_materiality
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    MaterialAmbiguity,
    ObjectiveProposal,
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


def _connection() -> Connection:
    return Connection(
        id="demo",
        description="Conexion de prueba.",
        engine="postgresql",
        calendar=Calendar(type=CalendarType.CALENDAR, closing_month=12, week_start="monday"),
        thresholds=_thresholds(),
        sensitivity=[],
    )


def _metric(id_: str, synonyms: list[str], default_sense_of: list[str] | None = None) -> Metric:
    return Metric(
        id=id_,
        business_name=id_,
        definition="Definicion de prueba.",
        synonyms=synonyms,
        default_sense_of=default_sense_of,
        unit="ARS",
        aggregations=[Aggregation.SUM],
        combinable_dimensions=[],
        min_granularity=Granularity.DAY,
        physical=MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="cmp_cab.f"),
    )


def _artifact(metrics: list[Metric]) -> SemanticArtifact:
    return SemanticArtifact(connection=_connection(), dimensions=[], metrics=metrics)


def _proposal(ambiguities: tuple[MaterialAmbiguity, ...]) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=ObjectiveName.RANK,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=ambiguities,
        plan=(),
    )


def test_ambiguity_without_expression_is_never_refuted() -> None:
    artifact = _artifact([_metric("net_revenue", ["ventas"], default_sense_of=["ventas"])])
    proposal = _proposal(
        (MaterialAmbiguity(description="esos tres sin referente localizable", options=()),)
    )
    assert check_materiality(proposal, artifact) == ()


def test_ambiguity_with_no_default_sense_remains_material() -> None:
    artifact = _artifact([_metric("net_revenue", ["ventas"])])
    proposal = _proposal(
        (
            MaterialAmbiguity(
                description='criterio de "mejores"',
                options=("facturacion neta", "unidades vendidas"),
                expression="mejores",
            ),
        )
    )
    assert check_materiality(proposal, artifact) == ()


def test_ambiguity_with_exactly_one_default_sense_is_refuted() -> None:
    artifact = _artifact(
        [
            _metric("net_revenue", ["ventas", "facturacion"], default_sense_of=["ventas"]),
            _metric("units_sold", ["unidades"]),
        ]
    )
    proposal = _proposal(
        (MaterialAmbiguity(description="sentido de ventas", options=(), expression="ventas"),)
    )

    rejections = check_materiality(proposal, artifact)

    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.AMBIGUITY_HAS_DEFAULT_SENSE
    assert "net_revenue" in (rejections[0].detail or "")


def test_ambiguity_with_multiple_colliding_defaults_remains_material() -> None:
    artifact = _artifact(
        [
            _metric("net_revenue", ["ventas"], default_sense_of=["ventas"]),
            _metric("gross_revenue", ["ventas", "ventas brutas"], default_sense_of=["ventas"]),
        ]
    )
    proposal = _proposal(
        (MaterialAmbiguity(description="sentido de ventas", options=(), expression="ventas"),)
    )
    assert check_materiality(proposal, artifact) == ()
