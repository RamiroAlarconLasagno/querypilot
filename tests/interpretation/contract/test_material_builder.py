# tests/interpretation/contract/test_material_builder.py
"""available_objectives: 10_parte_operaciones.md seccion 2, nota de
diferimiento de explore en el MVP 1. material_builder no decide visibilidad
por permisos -- esto es la unica exclusion que le corresponde.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.canonical_language.shared_values import ObjectiveName
from querypilot.interpretation.material_builder import available_objectives


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
