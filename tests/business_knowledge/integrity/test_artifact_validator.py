# tests/business_knowledge/integrity/test_artifact_validator.py
"""Un caso positivo y uno negativo por cada comprobacion de
06_parte_conocimiento_negocio.md seccion 6, mas el artefacto real de
semantic/demo/ pasando las 8 sin hallazgos.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from querypilot.business_knowledge.artifact_validator import (
    check_combinable_dimensions_exist,
    check_default_sense_points_to_existing_concept,
    check_metrics_have_complete_physical_mapping,
    check_min_granularity_has_temporal_field,
    check_source_relations_have_no_path_ambiguity,
    check_synonyms_do_not_collide,
    check_thresholds_are_coherent,
    validate_artifact,
)
from querypilot.business_knowledge.semantic_artifact import (
    Aggregation,
    Calendar,
    CalendarType,
    Connection,
    Dimension,
    DimensionPhysical,
    Granularity,
    Metric,
    MetricPhysical,
    SemanticArtifact,
    Thresholds,
    load_semantic_artifact,
)

DEMO_DIR = Path(__file__).resolve().parents[3] / "semantic" / "demo"


def _thresholds(**overrides: object) -> Thresholds:
    base: dict[str, object] = {
        "context_rows": 20,
        "preview_rows": 100,
        "preview_columns": 20,
        "materialization_rows": 50000,
        "active_datasets_per_session": 5,
        "active_datasets_mb": 50,
        "decompose_variance_max_dimension_cardinality": 5000,
        "min_explanation_coverage": Decimal("0.70"),
        "closed_period_freshness_hours": 24,
        "open_period_freshness_minutes": 15,
        "query_time_limit_seconds": 30,
        "turn_budget_seconds": 90,
        "model_calls_budget": 5,
        "rows_examined_to_confirm": 1_000_000,
    }
    base.update(overrides)
    return Thresholds.model_validate(base)


def _connection(**overrides: object) -> Connection:
    base: dict[str, object] = {
        "id": "demo",
        "description": "Conexion de prueba.",
        "engine": "postgresql",
        "calendar": Calendar(type=CalendarType.CALENDAR, closing_month=12, week_start="monday"),
        "thresholds": _thresholds(),
        "sensitivity": [],
    }
    base.update(overrides)
    return Connection.model_validate(base)


def _dimension(
    id_: str = "customer",
    relation: str = "cmp_cab.ent_id = ent_com.ent_id",
    source: str = "ent_com",
    **overrides: object,
) -> Dimension:
    base: dict[str, object] = {
        "id": id_,
        "business_name": "Cliente",
        "synonyms": ["clientes"],
        "expected_cardinality": 100,
        "physical": DimensionPhysical(
            source=source, attribute=f"{source}.nombre", key=f"{source}.id", relation=relation
        ),
    }
    base.update(overrides)
    return Dimension.model_validate(base)


def _metric(
    id_: str = "net_revenue",
    physical: MetricPhysical | None = None,
    **overrides: object,
) -> Metric:
    base: dict[str, object] = {
        "id": id_,
        "business_name": "Facturacion",
        "definition": "Ventas menos notas de credito.",
        "synonyms": ["ventas"],
        "default_sense_of": None,
        "unit": "ARS",
        "aggregations": [Aggregation.SUM],
        "combinable_dimensions": ["customer"],
        "min_granularity": Granularity.DAY,
        "physical": physical
        or MetricPhysical(
            source="cmp_cab", measure="sum(cmp_det.imp_neto)", temporal_field="cmp_cab.f_emis"
        ),
    }
    base.update(overrides)
    return Metric.model_validate(base)


def _artifact(
    dimensions: list[Dimension] | None = None,
    metrics: list[Metric] | None = None,
    connection: Connection | None = None,
) -> SemanticArtifact:
    return SemanticArtifact(
        connection=connection or _connection(),
        dimensions=dimensions if dimensions is not None else [_dimension()],
        metrics=metrics if metrics is not None else [_metric()],
    )


def test_the_real_demo_artifact_passes_all_eight_checks() -> None:
    artifact = load_semantic_artifact(DEMO_DIR)
    assert validate_artifact(artifact) == []


def test_complete_physical_mapping_passes_when_all_fields_present() -> None:
    assert check_metrics_have_complete_physical_mapping(_artifact()) == []


def test_complete_physical_mapping_fails_when_source_is_blank() -> None:
    incomplete = MetricPhysical(source="", measure="sum(x)", temporal_field="cmp_cab.f_emis")
    artifact = _artifact(metrics=[_metric(physical=incomplete)])
    assert check_metrics_have_complete_physical_mapping(artifact) != []


def test_combinable_dimensions_pass_when_dimension_exists() -> None:
    artifact = _artifact(
        dimensions=[_dimension(id_="customer")],
        metrics=[_metric(combinable_dimensions=["customer"])],
    )
    assert check_combinable_dimensions_exist(artifact) == []


def test_combinable_dimensions_fail_when_dimension_is_missing() -> None:
    artifact = _artifact(
        dimensions=[_dimension(id_="customer")],
        metrics=[_metric(combinable_dimensions=["nonexistent"])],
    )
    assert check_combinable_dimensions_exist(artifact) != []


def test_min_granularity_passes_with_temporal_field() -> None:
    assert check_min_granularity_has_temporal_field(_artifact()) == []


def test_min_granularity_fails_without_temporal_field() -> None:
    physical = MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="")
    artifact = _artifact(metrics=[_metric(physical=physical)])
    assert check_min_granularity_has_temporal_field(artifact) != []


def test_aggregations_outside_the_closed_catalog_are_rejected_at_load_time() -> None:
    """El chequeo de 06 §6 lo hace cumplir Pydantic (Aggregation es StrEnum),
    no una funcion de artifact_validator: si el YAML llega hasta aca, ya paso.
    """
    with pytest.raises(ValidationError):
        _metric(aggregations=["no_es_una_agregacion_valida"])


def test_synonyms_do_not_collide_across_distinct_concepts() -> None:
    artifact = _artifact(
        dimensions=[_dimension(id_="customer", synonyms=["clientes"])],
        metrics=[_metric(id_="net_revenue", synonyms=["ventas"])],
    )
    assert check_synonyms_do_not_collide(artifact) == []


def test_synonyms_collide_when_two_concepts_share_one() -> None:
    artifact = _artifact(
        dimensions=[_dimension(id_="customer", synonyms=["ventas"])],
        metrics=[_metric(id_="net_revenue", synonyms=["ventas"])],
    )
    assert check_synonyms_do_not_collide(artifact) != []


def test_default_sense_passes_when_listed_in_its_own_synonyms() -> None:
    metric = _metric(synonyms=["ventas", "ingresos"], default_sense_of=["ventas"])
    assert check_default_sense_points_to_existing_concept(_artifact(metrics=[metric])) == []


def test_default_sense_fails_when_not_in_its_own_synonyms() -> None:
    metric = _metric(synonyms=["ventas"], default_sense_of=["palabra_no_declarada"])
    assert check_default_sense_points_to_existing_concept(_artifact(metrics=[metric])) != []


def test_source_relations_pass_with_a_single_path_per_pair() -> None:
    assert check_source_relations_have_no_path_ambiguity(_artifact()) == []


def test_source_relations_fail_with_two_different_paths_for_the_same_pair() -> None:
    region = _dimension(id_="region", source="geo_ref", relation="ent_com.geo_id = geo_ref.geo_id")
    region_alt = _dimension(
        id_="region_alt", source="geo_ref", relation="ent_com.other_id = geo_ref.other_id"
    )
    artifact = _artifact(dimensions=[region, region_alt], metrics=[])
    assert check_source_relations_have_no_path_ambiguity(artifact) != []


def test_thresholds_pass_when_ordered_correctly() -> None:
    assert check_thresholds_are_coherent(_artifact()) == []


def test_thresholds_fail_when_context_exceeds_preview() -> None:
    connection = _connection(thresholds=_thresholds(context_rows=200, preview_rows=100))
    assert check_thresholds_are_coherent(_artifact(connection=connection)) != []
