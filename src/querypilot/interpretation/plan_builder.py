# src/querypilot/interpretation/plan_builder.py
"""Valida los pasos propuestos de un ObjectiveProposal. 07_parte_interpretacion.md
seccion 10 (paso 5) y 09_parte_ejecutor.md seccion 5: "cada condicion es
satisfacible con los hechos que los pasos previos declaran publicar" se
comprueba antes de ejecutar, sin tocar la fuente. `build_analysis_plan` (la
transformacion hacia AnalysisPlan) vive aparte, en un modulo propio, para no
mezclar validacion con construccion.

`_publishes` busca el tipo de hecho como palabra completa dentro de
`OperationCard.published_facts` -- ese campo es texto libre (bloque 1.4,
hueco de cardinalidad ya registrado, no resuelto aqui); la busqueda por
palabra completa evita colisiones de subcadena entre los 17 FactType.
"""

from __future__ import annotations

import re

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG, ObjectiveCard
from querypilot.analytics.operation_catalog import OPERATION_CATALOG, OperationCard
from querypilot.business_knowledge.semantic_artifact import Thresholds
from querypilot.canonical_language.identifiers import ObjectiveId, TurnId
from querypilot.canonical_language.plan import (
    AnalysisPlan,
    PlannedObjective,
    PlannedObjectiveDependency,
    PlanStep,
    StepId,
    StepState,
    TurnBudget,
)
from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.model_port.structured_output import (
    InterpretationOutput,
    ObjectiveProposal,
    ProposedPlanStep,
)


def _operation_card(step: ProposedPlanStep) -> OperationCard:
    return next(card for card in OPERATION_CATALOG if card.name == step.operation)


def _publishes(card: OperationCard, fact_type_value: str) -> bool:
    return re.search(rf"\b{re.escape(fact_type_value)}\b", card.published_facts) is not None


def _check_arguments(step: ProposedPlanStep) -> tuple[Rejection, ...]:
    card = _operation_card(step)
    declared = {parameter.name: parameter for parameter in card.parameters}

    unknown = sorted(set(step.arguments) - set(declared))
    if unknown:
        return (
            Rejection(
                cause=RejectionCause.INVALID_PARAMETERS,
                action=SuggestedAction.RETRY,
                detail=f"{step.operation}: argumentos no declarados {unknown}",
            ),
        )

    missing = sorted(
        name
        for name, parameter in declared.items()
        if parameter.required and name not in step.arguments
    )
    if missing:
        return (
            Rejection(
                cause=RejectionCause.INVALID_PARAMETERS,
                action=SuggestedAction.RETRY,
                detail=f"{step.operation}: faltan argumentos obligatorios {missing}",
            ),
        )
    return ()


def _check_condition(
    step: ProposedPlanStep, previous_steps: tuple[ProposedPlanStep, ...]
) -> tuple[Rejection, ...]:
    if step.condition is None:
        return ()

    fact_type_value = step.condition.fact_type.value
    if any(_publishes(_operation_card(previous), fact_type_value) for previous in previous_steps):
        return ()

    return (
        Rejection(
            cause=RejectionCause.CONDITION_REFERENCES_UNPUBLISHED_FACT,
            action=SuggestedAction.RETRY,
            detail=f"{step.step_id}: ningun paso anterior publica '{fact_type_value}'",
        ),
    )


def _check_derives_from(
    step: ProposedPlanStep, previous_step_ids: tuple[str, ...]
) -> tuple[Rejection, ...]:
    invalid = [
        ref for ref in step.derives_from if ref == step.step_id or ref not in previous_step_ids
    ]
    if not invalid:
        return ()
    return (
        Rejection(
            cause=RejectionCause.INVALID_DERIVES_FROM,
            action=SuggestedAction.RETRY,
            detail=f"{step.step_id}: derives_from invalido {invalid}",
        ),
    )


def validate_plan_steps(proposal: ObjectiveProposal) -> tuple[Rejection, ...]:
    rejections: list[Rejection] = []
    previous_steps: tuple[ProposedPlanStep, ...] = ()
    previous_step_ids: tuple[str, ...] = ()

    for step in proposal.plan:
        rejections.extend(_check_arguments(step))
        rejections.extend(_check_condition(step, previous_steps))
        rejections.extend(_check_derives_from(step, previous_step_ids))
        previous_steps = (*previous_steps, step)
        previous_step_ids = (*previous_step_ids, step.step_id)

    return tuple(rejections)


def check_ambiguity_excludes_plan(proposal: ObjectiveProposal) -> tuple[Rejection, ...]:
    """07_parte_interpretacion.md seccion 5: una ambiguedad material nunca
    viaja junto con un plan propuesto. No vacia el plan ni descarta la
    ambiguedad -- devuelve el rechazo y deja que el modelo reintente.
    """
    if proposal.ambiguities and proposal.plan:
        return (Rejection(cause=RejectionCause.AMBIGUITY_WITH_PLAN, action=SuggestedAction.RETRY),)
    return ()


def build_analysis_plan(
    output: InterpretationOutput,
    turn_id: str,
    plan_id: str,
    thresholds: Thresholds,
) -> AnalysisPlan | tuple[Rejection, ...]:
    """Transforma una InterpretationOutput ya validada (interpretation_validator
    devolvio () ) en un AnalysisPlan durable. No vuelve a validar conceptos,
    argumentos, condiciones ni dependencias -- eso ya paso. Su unico trabajo
    propio es la transformacion de identificadores efimeros a durables y la
    incorporacion del criterio de suficiencia del catalogo.

    Igual se defiende contra un objetivo sin sufficiency_condition (hoy,
    explore): construir un PlannedObjective sin criterio no es posible --
    PlannedObjective.sufficiency es obligatorio -- asi que ante ese caso
    rechaza antes de construir nada, en vez de fallar a mitad de camino.
    """
    unavailable = tuple(
        Rejection(
            cause=RejectionCause.OBJECTIVE_NOT_AVAILABLE,
            action=SuggestedAction.INFORM,
            detail=f"{proposal.proposal_id}: {proposal.objective} sin criterio de suficiencia",
        )
        for proposal in output.objective_proposals
        if _objective_card(proposal).sufficiency_condition is None
    )
    if unavailable:
        return unavailable

    proposal_to_objective_id = {
        proposal.proposal_id: ObjectiveId(f"obj_{index}")
        for index, proposal in enumerate(output.objective_proposals, start=1)
    }

    planned_objectives = tuple(
        _build_planned_objective(proposal, proposal_to_objective_id)
        for proposal in output.objective_proposals
    )

    return AnalysisPlan(
        id=plan_id,
        turn_id=TurnId(turn_id),
        objectives=planned_objectives,
        budget=TurnBudget(
            total_time_seconds=thresholds.turn_budget_seconds,
            max_model_calls=thresholds.model_calls_budget,
        ),
    )


def _objective_card(proposal: ObjectiveProposal) -> ObjectiveCard:
    return next(card for card in OBJECTIVE_CATALOG if card.name == proposal.objective)


def _build_planned_objective(
    proposal: ObjectiveProposal,
    proposal_to_objective_id: dict[str, ObjectiveId],
) -> PlannedObjective:
    card = _objective_card(proposal)
    sufficiency = card.sufficiency_condition
    assert sufficiency is not None  # ya se descarto en build_analysis_plan

    local_to_durable_step_id: dict[str, StepId] = {
        step.step_id: StepId(f"step_{index}") for index, step in enumerate(proposal.plan, start=1)
    }

    steps = tuple(
        PlanStep(
            step_id=local_to_durable_step_id[step.step_id],
            operation=step.operation,
            arguments=step.arguments,
            condition=step.condition,
            derives_from=tuple(local_to_durable_step_id[ref] for ref in step.derives_from),
            state=StepState.PENDING,
            attempt_id=None,
        )
        for step in proposal.plan
    )

    dependency = None
    if proposal.dependency is not None:
        dependency = PlannedObjectiveDependency(
            source_objective_id=proposal_to_objective_id[proposal.dependency.source_proposal_id],
            binding=proposal.dependency.binding,
        )

    return PlannedObjective(
        objective_id=proposal_to_objective_id[proposal.proposal_id],
        objective=proposal.objective,
        sufficiency=sufficiency,
        dependency=dependency,
        steps=steps,
    )
