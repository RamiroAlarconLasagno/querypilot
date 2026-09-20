# tests/analytics/unit/test_operation_catalog.py
"""Pruebas estructurales del catalogo de operaciones: 10_parte_operaciones.md
seccion 3 (trece campos por ficha) y seccion 8 (diez operaciones).
"""

from __future__ import annotations

from querypilot.analytics.operation_catalog import (
    OPERATION_CATALOG,
    OperationCard,
    OperationName,
    Parameter,
    UniverseRequirement,
)

THIRTEEN_FIELDS = tuple(OperationCard.model_fields)


def _card(name: OperationName) -> OperationCard:
    return next(card for card in OPERATION_CATALOG if card.name == name)


def test_catalog_has_exactly_ten_operations() -> None:
    assert len(OPERATION_CATALOG) == 10


def test_catalog_covers_every_operation_name_exactly_once() -> None:
    names = [card.name for card in OPERATION_CATALOG]
    assert set(names) == set(OperationName)
    assert len(names) == len(set(names))


def test_every_card_declares_the_thirteen_fields() -> None:
    assert len(THIRTEEN_FIELDS) == 13
    for card in OPERATION_CATALOG:
        for field in THIRTEEN_FIELDS:
            value = getattr(card, field)
            assert value not in (None, ""), f"{card.name}: campo {field} vacio"
        assert len(card.parameters) >= 1


def test_universe_requirement_matches_the_classification_in_section_4() -> None:
    complete_universe = {OperationName.CALCULATE_SHARE}
    for card in OPERATION_CATALOG:
        expected = (
            UniverseRequirement.COMPLETE
            if card.name in complete_universe
            else UniverseRequirement.AUTHORIZED
        )
        assert card.universe_requirement == expected


def test_only_calculate_share_costs_two_accesses() -> None:
    for card in OPERATION_CATALOG:
        expected_cost = 2 if card.name == OperationName.CALCULATE_SHARE else 1
        assert card.cost == expected_cost


def test_calculate_share_declares_element_separate_from_filters() -> None:
    card = _card(OperationName.CALCULATE_SHARE)
    names = [parameter.name for parameter in card.parameters]
    assert "element" in names
    assert "filters" in names

    element = next(p for p in card.parameters if p.name == "element")
    filters = next(p for p in card.parameters if p.name == "filters")
    assert element.required is True
    assert filters.required is False


def test_calculate_share_request_construction_is_documented_in_data_requests() -> None:
    card = _card(OperationName.CALCULATE_SHARE)
    assert "dimension = element" in card.data_requests
    assert "solo filters" in card.data_requests


def test_detect_anomaly_sensitivity_defaults_to_the_objective_and_is_optional() -> None:
    card = _card(OperationName.DETECT_ANOMALY)
    sensitivity = next(p for p in card.parameters if p.name == "sensitivity")
    assert sensitivity.required is False
    assert sensitivity.default == "valor configurado del objetivo"


def test_detect_anomaly_does_not_commit_to_a_statistical_method() -> None:
    card = _card(OperationName.DETECT_ANOMALY)
    calculation_lower = card.calculation.lower()
    for forbidden_term in ("z-score", "iqr", "desviacion estandar", "percentil"):
        assert forbidden_term not in calculation_lower


def test_excessive_cardinality_is_scoped_to_decompose_variance_only() -> None:
    decompose_variance = _card(OperationName.DECOMPOSE_VARIANCE)
    breakdown = _card(OperationName.BREAKDOWN)
    assert "excessive_cardinality" in decompose_variance.rejection_conditions
    assert "No comparte excessive_cardinality" in breakdown.rejection_conditions


def test_time_series_granularity_is_required_and_no_trend_is_published() -> None:
    card = _card(OperationName.TIME_SERIES)
    granularity = next(p for p in card.parameters if p.name == "granularity")
    assert granularity.required is True
    assert "trend" not in card.published_facts.lower()


def test_parameter_model_accepts_only_documented_fields() -> None:
    parameter = Parameter(name="metric", domain_type="metric_reference", required=True)
    assert parameter.default is None
