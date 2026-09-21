# src/querypilot/interpretation/interpretation_validator.py
"""Orquesta la validacion determinista completa de un InterpretationOutput.
07_parte_interpretacion.md seccion 10 (pasos 4-6) y 09_parte_ejecutor.md
seccion 5. Solo valida -- nunca transforma la propuesta ni construye nada.
Una InterpretationOutput sin rechazos es la unica entrada valida para
`plan_builder.build_analysis_plan`.
"""

from __future__ import annotations

from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.rejection import Rejection
from querypilot.canonical_language.shared_values import AnalyticalState
from querypilot.interpretation import (
    ambiguity_detector,
    dependency_graph,
    plan_builder,
    proposal_builder,
    reference_resolver,
)
from querypilot.model_port.structured_output import InterpretationOutput


def validate_interpretation(
    output: InterpretationOutput,
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
) -> tuple[Rejection, ...]:
    rejections: list[Rejection] = []

    for proposal in output.objective_proposals:
        rejections.extend(proposal_builder.check_objective_is_available(proposal))
        rejections.extend(proposal_builder.check_concepts_exist(proposal, artifact))
        rejections.extend(proposal_builder.check_continuity_is_coherent(proposal, analytical_state))
        rejections.extend(ambiguity_detector.check_materiality(proposal, artifact))
        rejections.extend(
            reference_resolver.check_references_have_context(
                proposal, analytical_state, conversation_history
            )
        )
        rejections.extend(plan_builder.validate_plan_steps(proposal))
        rejections.extend(plan_builder.check_ambiguity_excludes_plan(proposal))

    rejections.extend(dependency_graph.check_for_cycles(output.objective_proposals))

    return tuple(rejections)
