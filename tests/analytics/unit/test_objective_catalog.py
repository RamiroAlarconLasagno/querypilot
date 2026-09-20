# tests/analytics/unit/test_objective_catalog.py
"""Pruebas estructurales del catalogo de objetivos: 10_parte_operaciones.md
seccion 2, siete objetivos, cada uno con pregunta tipica y criterio de
suficiencia.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG, ObjectiveName


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
