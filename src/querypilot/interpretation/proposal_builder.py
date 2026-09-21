# src/querypilot/interpretation/proposal_builder.py
"""Valida el objetivo, los conceptos, la continuidad y las premisas de cada
ObjectiveProposal. 07_parte_interpretacion.md seccion 10 (paso 4). Nunca
transforma la propuesta -- devuelve rechazos, nunca excepciones
(16_instrucciones_ia.md seccion 7).
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.model_port.structured_output import ObjectiveProposal


def check_objective_is_available(proposal: ObjectiveProposal) -> tuple[Rejection, ...]:
    """Un objetivo sin criterio de suficiencia verificable no puede
    proponerse (10_parte_operaciones.md seccion 2). En operacion normal esto
    nunca deberia disparar: material_builder ya excluye esos objetivos del
    catalogo que el modelo recibe. Esta es una defensa ante una propuesta
    que de algun modo eludio esa exclusion, no un camino esperado.
    """
    card = next(c for c in OBJECTIVE_CATALOG if c.name == proposal.objective)
    if card.sufficiency_condition is not None:
        return ()
    return (
        Rejection(
            cause=RejectionCause.OBJECTIVE_NOT_AVAILABLE,
            action=SuggestedAction.INFORM,
        ),
    )
