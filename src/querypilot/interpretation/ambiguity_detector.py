# src/querypilot/interpretation/ambiguity_detector.py
"""Refuta, cuando puede, una ambiguedad material declarada por el modelo.
07_parte_interpretacion.md seccion 5, "Verificacion determinista de la
materialidad declarada": la regla de materialidad tiene dos mitades con
duenos distintos. Que "distintas resoluciones producen respuestas
distintas" no es verificable sin ejecutar la pregunta -- esa mitad queda
confiada al modelo, este modulo no la toca. Que "no existe un valor por
defecto declarado" si es mecanico cuando `MaterialAmbiguity.expression` esta
presente: se contrasta contra `Metric.default_sense_of` del artefacto
semantico.

El sistema nunca decide materialidad de forma positiva -- solo puede
refutarla. Cuando la refuta, no modifica la propuesta ni construye un plan
en su nombre: devuelve un Rejection corregible, que consume el unico
reintento de planificacion ya existente (09_parte_ejecutor.md seccion 4).
"""

from __future__ import annotations

from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.model_port.structured_output import ObjectiveProposal


def check_materiality(
    proposal: ObjectiveProposal, artifact: SemanticArtifact
) -> tuple[Rejection, ...]:
    rejections: list[Rejection] = []
    for ambiguity in proposal.ambiguities:
        if ambiguity.expression is None:
            # No hay expresion contra la cual consultar default_sense_of.
            # No se refuta: sigue siendo material tal como la declaro el modelo.
            continue

        defaults = [
            metric.id
            for metric in artifact.metrics
            if metric.default_sense_of is not None
            and ambiguity.expression in metric.default_sense_of
        ]

        if len(defaults) != 1:
            # Cero coincidencias: no hay default, sigue material.
            # Mas de una: no hay default inequivoco, sigue material.
            continue

        rejections.append(
            Rejection(
                cause=RejectionCause.AMBIGUITY_HAS_DEFAULT_SENSE,
                action=SuggestedAction.RETRY,
                detail=(
                    f"'{ambiguity.expression}' ya tiene sentido por defecto declarado: "
                    f"'{defaults[0]}'"
                ),
            )
        )

    return tuple(rejections)
