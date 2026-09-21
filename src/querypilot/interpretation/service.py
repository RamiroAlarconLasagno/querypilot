# src/querypilot/interpretation/service.py
"""Orquesta el flujo completo de Interpretacion: pregunta + contexto ->
build_material -> ModelPort.interpret -> validate_interpretation ->
build_analysis_plan. 07_parte_interpretacion.md seccion 10.

`InterpretationOutcome` es una union discriminada chica y local (no vive en
canonical_language: nada mas la consume todavia, y Ejecutor -- bloque muy
posterior -- decidira su propia representacion cuando exista). Separa los
tres resultados que le importan a quien llama:

- `PlanReady`: hay un AnalysisPlan listo.
- `Rejected`: la validacion determinista encontro algo invalido.
- `NeedsClarification`: no hay nada invalido, pero tampoco hay plan --
  ambiguedad material o intencion fuera de alcance. No se fabrica un plan
  en ninguno de los dos casos.

Simplificacion deliberada de este cierre de 1.6: si *cualquier* propuesta
del turno trae ambiguedad, o si `out_of_scope` no esta vacio, el turno
completo se resuelve como `NeedsClarification`, aunque otras propuestas del
mismo turno tuvieran plan valido. Manejar turnos mixtos (algunos objetivos
listos, otros no) con precision es un caso mas rico que ningun test de
cierre ejercita todavia -- queda anotado para revisar en 1.7 si el banco de
casos lo necesita.

Ajuste de 1.7: `PlanReady` ahora conserva tambien el `InterpretationOutput`
crudo, ademas del `AnalysisPlan` construido. `AnalysisPlan` (canonical_language,
durable) deliberadamente no lleva premisas ni concepts -- son insumos de
Interpretacion, no del plan que el Ejecutor persiste. El comparador semantico
del banco de evaluacion (business_knowledge/evaluation_cases.py,
interpretation/case_comparator.py) necesita verificar exactamente eso, asi
que en vez de agregar campos ajenos a `AnalysisPlan`, `PlanReady` -- que ya es
un tipo local, chico, no durable -- lleva ambos. Cambio aditivo, sin tocar
ningun campo existente.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from querypilot.analytics.objective_catalog import ObjectiveCard
from querypilot.analytics.operation_catalog import OperationCard
from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.plan import AnalysisPlan
from querypilot.canonical_language.rejection import Rejection
from querypilot.canonical_language.shared_values import AnalyticalState, ObjectiveName
from querypilot.interpretation import plan_builder, replanner
from querypilot.interpretation.interpretation_validator import validate_interpretation
from querypilot.interpretation.material_builder import build_material
from querypilot.model_port.port import ModelPort
from querypilot.model_port.structured_output import (
    InterpretationOutput,
    MaterialAmbiguity,
    OutOfScope,
)


class PlanReady(BaseModel):
    kind: Literal["plan_ready"] = "plan_ready"
    plan: AnalysisPlan
    output: InterpretationOutput


class Rejected(BaseModel):
    kind: Literal["rejected"] = "rejected"
    rejections: tuple[Rejection, ...]


class NeedsClarification(BaseModel):
    kind: Literal["needs_clarification"] = "needs_clarification"
    ambiguities: tuple[MaterialAmbiguity, ...]
    out_of_scope: tuple[OutOfScope, ...]


InterpretationOutcome = PlanReady | Rejected | NeedsClarification


def _finish(
    output: InterpretationOutput,
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
    turn_id: str,
    plan_id: str,
) -> InterpretationOutcome:
    rejections = validate_interpretation(output, artifact, analytical_state, conversation_history)
    if rejections:
        return Rejected(rejections=rejections)

    ambiguities = tuple(
        ambiguity for proposal in output.objective_proposals for ambiguity in proposal.ambiguities
    )
    if ambiguities or output.out_of_scope:
        return NeedsClarification(ambiguities=ambiguities, out_of_scope=output.out_of_scope)

    result = plan_builder.build_analysis_plan(
        output, turn_id=turn_id, plan_id=plan_id, thresholds=artifact.connection.thresholds
    )
    if isinstance(result, AnalysisPlan):
        return PlanReady(plan=result, output=output)
    return Rejected(rejections=result)


async def run_interpretation(
    model_port: ModelPort,
    prompt_version: str,
    question: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
    turn_id: str,
    plan_id: str,
    prior_clarification: str | None = None,
    retry_cause: Rejection | None = None,
) -> InterpretationOutcome:
    system_prompt, user_prompt = build_material(
        question=question,
        objective_catalog=objective_catalog,
        operation_catalog=operation_catalog,
        artifact=artifact,
        analytical_state=analytical_state,
        conversation_history=conversation_history,
        prior_clarification=prior_clarification,
        retry_cause=retry_cause,
    )
    output = await model_port.interpret(prompt_version, system_prompt, user_prompt)
    return _finish(output, artifact, analytical_state, conversation_history, turn_id, plan_id)


async def run_replanning(
    model_port: ModelPort,
    prompt_version: str,
    original_objective: ObjectiveName,
    question: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
    previous_plan_summary: str,
    insufficiency_cause: str,
    turn_id: str,
    plan_id: str,
    available_facts: tuple[str, ...] = (),
) -> InterpretationOutcome:
    result = await replanner.replan(
        original_objective=original_objective,
        model_port=model_port,
        prompt_version=prompt_version,
        question=question,
        objective_catalog=objective_catalog,
        operation_catalog=operation_catalog,
        artifact=artifact,
        analytical_state=analytical_state,
        conversation_history=conversation_history,
        previous_plan_summary=previous_plan_summary,
        insufficiency_cause=insufficiency_cause,
        available_facts=available_facts,
    )
    if not isinstance(result, InterpretationOutput):
        return Rejected(rejections=result)
    return _finish(result, artifact, analytical_state, conversation_history, turn_id, plan_id)
