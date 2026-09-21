# src/querypilot/interpretation/replanner.py
"""Entrada acotada para una segunda ronda de planificacion.
07_parte_interpretacion.md seccion 7: puede proponer otra dimension de
descomposicion u operaciones adicionales del catalogo; no puede cambiar el
objetivo. Reutiliza `build_material` (no hay un segundo renderizador de
prompt) y deja que el llamador aplique las mismas validaciones
deterministas del camino normal (`interpretation_validator`,
`plan_builder.build_analysis_plan`) -- este modulo no valida nada mas alla
de la regla dura del objetivo fijo.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import ObjectiveCard
from querypilot.analytics.operation_catalog import OperationCard
from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.canonical_language.shared_values import AnalyticalState, ObjectiveName
from querypilot.interpretation.material_builder import build_material
from querypilot.model_port.port import ModelPort
from querypilot.model_port.structured_output import InterpretationOutput


async def replan(
    original_objective: ObjectiveName,
    model_port: ModelPort,
    prompt_version: str,
    question: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
    previous_plan_summary: str,
    insufficiency_cause: str,
    available_facts: tuple[str, ...] = (),
) -> InterpretationOutput | tuple[Rejection, ...]:
    system_prompt, user_prompt = build_material(
        question=question,
        objective_catalog=objective_catalog,
        operation_catalog=operation_catalog,
        artifact=artifact,
        analytical_state=analytical_state,
        conversation_history=conversation_history,
        fixed_objective=original_objective,
        previous_plan_summary=previous_plan_summary,
        insufficiency_cause=insufficiency_cause,
        available_facts=available_facts,
    )
    output = await model_port.interpret(prompt_version, system_prompt, user_prompt)

    changed = tuple(
        Rejection(
            cause=RejectionCause.REPLAN_CHANGED_OBJECTIVE,
            action=SuggestedAction.INFORM,
            detail=f"{proposal.proposal_id}: propuso {proposal.objective}, "
            f"el objetivo fijo es {original_objective}",
        )
        for proposal in output.objective_proposals
        if proposal.objective != original_objective
    )
    if changed:
        return changed

    return output
