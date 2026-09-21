# tests/interpretation/contract/test_proposal_builder.py
"""check_objective_is_available, check_concepts_exist y
check_continuity_is_coherent: 07_parte_interpretacion.md seccion 10, paso 4.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.business_knowledge.semantic_artifact import (
    Calendar,
    CalendarType,
    Connection,
    Dimension,
    DimensionPhysical,
    Metric,
    MetricPhysical,
    SemanticArtifact,
    Thresholds,
)
from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import AnalyticalState, Granularity, ObjectiveName
from querypilot.interpretation.proposal_builder import (
    check_concepts_exist,
    check_continuity_is_coherent,
    check_objective_is_available,
)
from querypilot.model_port.structured_output import (
    ConceptMapping,
    Continuity,
    ContinuityMode,
    InheritedField,
    ObjectiveProposal,
)


def _proposal(
    objective: ObjectiveName = ObjectiveName.QUERY_METRIC,
    concepts: tuple[ConceptMapping, ...] = (),
    continuity: Continuity | None = None,
) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=objective,
        continuity=continuity or Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=concepts,
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=(),
    )


def test_a_defined_objective_is_accepted() -> None:
    assert check_objective_is_available(_proposal(ObjectiveName.QUERY_METRIC)) == ()


def test_explore_is_rejected_as_not_available() -> None:
    rejections = check_objective_is_available(_proposal(ObjectiveName.EXPLORE))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.OBJECTIVE_NOT_AVAILABLE


def _metric(id_: str) -> Metric:
    return Metric(
        id=id_,
        business_name=id_,
        definition="Definicion de prueba.",
        synonyms=[],
        unit="ARS",
        aggregations=[],
        combinable_dimensions=[],
        min_granularity=Granularity.DAY,
        physical=MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="cmp_cab.f"),
    )


def _dimension(id_: str) -> Dimension:
    return Dimension(
        id=id_,
        business_name=id_,
        synonyms=[],
        expected_cardinality=10,
        physical=DimensionPhysical(source="ent_com", attribute="nombre", key="id", relation="x=y"),
    )


def _artifact(metrics: list[Metric], dimensions: list[Dimension]) -> SemanticArtifact:
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
    return SemanticArtifact(connection=connection, dimensions=dimensions, metrics=metrics)


def test_known_concepts_are_accepted() -> None:
    artifact = _artifact(metrics=[_metric("net_revenue")], dimensions=[_dimension("customer")])
    proposal = _proposal(
        concepts=(
            ConceptMapping(canonical="net_revenue", original_expression="facturacion"),
            ConceptMapping(canonical="customer", original_expression="clientes"),
        )
    )
    assert check_concepts_exist(proposal, artifact) == ()


def test_unknown_concept_is_rejected() -> None:
    artifact = _artifact(metrics=[_metric("net_revenue")], dimensions=[])
    proposal = _proposal(
        concepts=(ConceptMapping(canonical="profit_margin", original_expression="margen"),)
    )
    rejections = check_concepts_exist(proposal, artifact)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.NONEXISTENT_CONCEPT


def test_new_continuity_with_empty_inherits_is_accepted() -> None:
    proposal = _proposal(continuity=Continuity(mode=ContinuityMode.NEW, inherits=()))
    assert check_continuity_is_coherent(proposal, analytical_state=None) == ()


def test_new_continuity_declaring_inherits_is_rejected() -> None:
    proposal = _proposal(
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=(InheritedField.METRIC,))
    )
    rejections = check_continuity_is_coherent(proposal, analytical_state=None)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.CONTINUITY_NEW_DECLARES_INHERITS


def test_continuation_without_analytical_state_is_rejected() -> None:
    proposal = _proposal(
        continuity=Continuity(mode=ContinuityMode.CONTINUATION, inherits=(InheritedField.PERIOD,))
    )
    rejections = check_continuity_is_coherent(proposal, analytical_state=None)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.CONTINUATION_WITHOUT_STATE


def test_continuation_inheriting_an_unavailable_field_is_rejected() -> None:
    state = AnalyticalState(period="julio", metric=None, semantic_version="sem_v7")
    proposal = _proposal(
        continuity=Continuity(mode=ContinuityMode.CONTINUATION, inherits=(InheritedField.METRIC,))
    )
    rejections = check_continuity_is_coherent(proposal, analytical_state=state)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.INHERITED_FIELD_UNAVAILABLE


def test_continuation_inheriting_available_fields_is_accepted() -> None:
    state = AnalyticalState(
        period="julio", metric="net_revenue", dimension="customer", semantic_version="sem_v7"
    )
    proposal = _proposal(
        continuity=Continuity(
            mode=ContinuityMode.CONTINUATION,
            inherits=(InheritedField.PERIOD, InheritedField.METRIC, InheritedField.DIMENSION),
        )
    )
    assert check_continuity_is_coherent(proposal, analytical_state=state) == ()
