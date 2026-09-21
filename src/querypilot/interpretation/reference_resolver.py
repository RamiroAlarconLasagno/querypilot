# src/querypilot/interpretation/reference_resolver.py
"""Valida que una ResolvedReference tenga de donde salir. 07_parte_interpretacion.md
seccion 10 (paso 6). No puede confirmar que la resolucion del modelo sea
correcta -- comparar el texto de `resolution` contra el estado o el
historial es exactamente el tipo de heuristica de texto que este proyecto
evita (ver la misma decision en ambiguity_detector). Lo unico verificable
sin heuristicas es que exista *algun* contexto del cual una referencia
pudiera haberse resuelto: si no hay ninguno, la referencia es imposible por
construccion, no una cuestion de si el modelo acerto o no.

Si no hay contexto, la salida es aclaracion, no reintento -- coherente con
la fila de 07_parte_interpretacion.md seccion 5: "esos tres" sin referente
localizable en el historial -> aclaracion.
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.canonical_language.shared_values import AnalyticalState
from querypilot.model_port.structured_output import ObjectiveProposal


def check_references_have_context(
    proposal: ObjectiveProposal,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
) -> tuple[Rejection, ...]:
    if not proposal.references:
        return ()

    has_state_reference = (
        analytical_state is not None and analytical_state.last_reference is not None
    )
    has_history = len(conversation_history) > 0
    if has_state_reference or has_history:
        return ()

    return (
        Rejection(
            cause=RejectionCause.REFERENCE_WITHOUT_CONTEXT,
            action=SuggestedAction.CLARIFY,
        ),
    )
