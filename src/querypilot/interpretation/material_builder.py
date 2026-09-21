# src/querypilot/interpretation/material_builder.py
"""Filtra que ObjectiveCard ofrecer al modelo. 07_parte_interpretacion.md
seccion 2: Interpretacion recibe los catalogos ya filtrados por Contexto de
acceso -- material_builder nunca decide visibilidad por permisos, esa parte
no existe todavia en este MVP (02_vision_arquitectura.md seccion 9); los
tests le dan directamente catalogos ya filtrados.

La unica exclusion que aplica aqui es estructural, no de permisos: un
objetivo sin criterio de suficiencia verificable no puede ofrecerse, porque
el Ejecutor nunca sabria cuando darlo por satisfecho. Hoy es solo `explore`
(10_parte_operaciones.md seccion 2, nota de diferimiento en el MVP 1).
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import ObjectiveCard


def available_objectives(
    objective_catalog: tuple[ObjectiveCard, ...],
) -> tuple[ObjectiveCard, ...]:
    return tuple(card for card in objective_catalog if card.sufficiency_condition is not None)
