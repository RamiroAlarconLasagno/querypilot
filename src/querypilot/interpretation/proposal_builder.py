# src/querypilot/interpretation/proposal_builder.py
"""Valida el objetivo, los conceptos, la continuidad y las premisas de cada
ObjectiveProposal. 07_parte_interpretacion.md seccion 10 (paso 4). Nunca
transforma la propuesta -- devuelve rechazos, nunca excepciones
(16_instrucciones_ia.md seccion 7).
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.canonical_language.shared_values import AnalyticalState
from querypilot.model_port.structured_output import (
    ContinuityMode,
    InheritedField,
    ObjectiveProposal,
)


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


def check_concepts_exist(
    proposal: ObjectiveProposal, artifact: SemanticArtifact
) -> tuple[Rejection, ...]:
    """Cada ConceptMapping.canonical debe ser un id real del artefacto
    semantico -- metrica o dimension. No corrige ni descarta el concepto
    inventado: lo rechaza.
    """
    known_ids = {metric.id for metric in artifact.metrics} | {
        dimension.id for dimension in artifact.dimensions
    }
    unknown = sorted({concept.canonical for concept in proposal.concepts} - known_ids)
    if not unknown:
        return ()
    return (
        Rejection(
            cause=RejectionCause.NONEXISTENT_CONCEPT,
            action=SuggestedAction.RETRY,
            options=tuple(sorted(known_ids)),
            detail=f"Conceptos inexistentes: {unknown}",
        ),
    )


def check_continuity_is_coherent(
    proposal: ObjectiveProposal, analytical_state: AnalyticalState | None
) -> tuple[Rejection, ...]:
    """07_parte_interpretacion.md seccion 3, "Continuidad explicita":
    `new` nunca declara que hereda algo; `continuation` exige un estado del
    cual heredar, y cada campo que declara heredar debe existir en ese
    estado -- heredar en silencio, o heredar algo que no esta, produce
    respuestas sobre un alcance que no es el que el usuario cree.
    """
    continuity = proposal.continuity

    if continuity.mode == ContinuityMode.NEW:
        if continuity.inherits:
            return (
                Rejection(
                    cause=RejectionCause.CONTINUITY_NEW_DECLARES_INHERITS,
                    action=SuggestedAction.RETRY,
                    detail=f"continuity.mode=new no puede declarar inherits={continuity.inherits}",
                ),
            )
        return ()

    # continuity.mode == CONTINUATION
    if analytical_state is None:
        return (
            Rejection(
                cause=RejectionCause.CONTINUATION_WITHOUT_STATE,
                action=SuggestedAction.RETRY,
                detail="continuity.mode=continuation sin estado analitico vigente",
            ),
        )

    unavailable = sorted(
        field.value
        for field in continuity.inherits
        if (field == InheritedField.METRIC and analytical_state.metric is None)
        or (field == InheritedField.DIMENSION and analytical_state.dimension is None)
    )
    if unavailable:
        return (
            Rejection(
                cause=RejectionCause.INHERITED_FIELD_UNAVAILABLE,
                action=SuggestedAction.RETRY,
                detail=f"El estado analitico no tiene: {unavailable}",
            ),
        )
    return ()
