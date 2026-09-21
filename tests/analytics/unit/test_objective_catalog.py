# tests/analytics/unit/test_objective_catalog.py
"""Pruebas estructurales del catalogo de objetivos: 10_parte_operaciones.md
seccion 2, siete objetivos, cada uno con pregunta tipica y criterio de
suficiencia.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG, ObjectiveName
from querypilot.canonical_language.shared_values import AllStepsCompleted, FactValueCondition


def test_catalog_has_exactly_seven_objectives() -> None:
    assert len(OBJECTIVE_CATALOG) == 7


def test_catalog_covers_every_objective_name_exactly_once() -> None:
    names = [card.name for card in OBJECTIVE_CATALOG]
    assert set(names) == set(ObjectiveName)
    assert len(names) == len(set(names))


def test_every_card_declares_typical_question_and_sufficiency_criterion() -> None:
    for card in OBJECTIVE_CATALOG:
        assert card.typical_question
        assert card.sufficiency_criterion


def test_only_objectives_with_a_documented_threshold_declare_one() -> None:
    with_threshold = {
        card.name for card in OBJECTIVE_CATALOG if card.configurable_threshold is not None
    }
    assert with_threshold == {
        ObjectiveName.RANK,
        ObjectiveName.EXPLAIN_VARIANCE,
        ObjectiveName.DETECT_ANOMALY,
        ObjectiveName.EXPLORE,
    }


def test_only_explore_lacks_a_verifiable_sufficiency_condition() -> None:
    without_condition = {
        card.name for card in OBJECTIVE_CATALOG if card.sufficiency_condition is None
    }
    assert without_condition == {ObjectiveName.EXPLORE}


def test_five_objectives_use_all_steps_completed() -> None:
    names = {
        card.name
        for card in OBJECTIVE_CATALOG
        if isinstance(card.sufficiency_condition, AllStepsCompleted)
    }
    assert names == {
        ObjectiveName.QUERY_METRIC,
        ObjectiveName.COMPARE,
        ObjectiveName.RANK,
        ObjectiveName.DETECT_ANOMALY,
        ObjectiveName.DESCRIBE_DATASET,
    }


def test_explain_variance_compares_explained_coverage_against_the_configured_threshold() -> None:
    card = next(c for c in OBJECTIVE_CATALOG if c.name == ObjectiveName.EXPLAIN_VARIANCE)
    assert isinstance(card.sufficiency_condition, FactValueCondition)
    assert card.sufficiency_condition.condition.fact_type == "explained_coverage"
