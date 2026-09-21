# src/querypilot/interpretation/material_builder.py
"""Arma el material que se envia al modelo. 07_parte_interpretacion.md
seccion 2: Interpretacion recibe los catalogos ya filtrados por Contexto de
acceso -- material_builder nunca decide visibilidad por permisos, esa parte
no existe todavia en este MVP (02_vision_arquitectura.md seccion 9); los
llamadores le dan directamente catalogos ya filtrados/autorizados.

La unica exclusion que aplica aqui es estructural, no de permisos: un
objetivo sin criterio de suficiencia verificable no puede ofrecerse, porque
el Ejecutor nunca sabria cuando darlo por satisfecho. Hoy es solo `explore`
(10_parte_operaciones.md seccion 2, nota de diferimiento en el MVP 1).

`build_material` es deliberadamente simple: un renderizado legible y
determinista, no una pieza de ingenieria de prompt afinada. El refinamiento
real ocurre con el banco de evaluacion (bloque 1.7), no aqui.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import ObjectiveCard
from querypilot.analytics.operation_catalog import OperationCard
from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.rejection import Rejection
from querypilot.canonical_language.shared_values import AnalyticalState


def available_objectives(
    objective_catalog: tuple[ObjectiveCard, ...],
) -> tuple[ObjectiveCard, ...]:
    return tuple(card for card in objective_catalog if card.sufficiency_condition is not None)


def _render_objectives(objective_catalog: tuple[ObjectiveCard, ...]) -> str:
    lines = [
        f"- {card.name}: {card.typical_question} (suficiencia: {card.sufficiency_criterion})"
        for card in available_objectives(objective_catalog)
    ]
    return "\n".join(lines) if lines else "(ninguno disponible)"


def _render_operations(operation_catalog: tuple[OperationCard, ...]) -> str:
    lines = [
        f"- {card.name}: {card.purpose}. "
        f"Parametros: {', '.join(p.name for p in card.parameters)}. "
        f"Hechos publicados: {card.published_facts}"
        for card in operation_catalog
    ]
    return "\n".join(lines) if lines else "(ninguna disponible)"


def _render_concepts(artifact: SemanticArtifact) -> str:
    metrics = [
        f"- {metric.id} ({metric.business_name}): sinonimos {metric.synonyms}"
        for metric in artifact.metrics
    ]
    dimensions = [
        f"- {dimension.id} ({dimension.business_name}): sinonimos {dimension.synonyms}"
        for dimension in artifact.dimensions
    ]
    return (
        "Metricas:\n" + ("\n".join(metrics) if metrics else "(ninguna)") + "\n\n"
        "Dimensiones:\n" + ("\n".join(dimensions) if dimensions else "(ninguna)")
    )


def _render_state(analytical_state: AnalyticalState | None) -> str:
    if analytical_state is None:
        return "Sin estado analitico vigente (turno nuevo)."
    return (
        f"Periodo: {analytical_state.period}\n"
        f"Metrica: {analytical_state.metric}\n"
        f"Dimension: {analytical_state.dimension}\n"
        f"Filtros: {analytical_state.filters}\n"
        f"Definiciones aplicadas: {analytical_state.applied_definitions}\n"
        f"Ultima referencia: {analytical_state.last_reference}\n"
        f"Version semantica: {analytical_state.semantic_version}"
    )


def _render_history(conversation_history: tuple[str, ...]) -> str:
    return "\n".join(conversation_history) if conversation_history else "(sin historial previo)"


def build_material(
    question: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    analytical_state: AnalyticalState | None,
    conversation_history: tuple[str, ...],
    prior_clarification: str | None = None,
    retry_cause: Rejection | None = None,
    fixed_objective: str | None = None,
    previous_plan_summary: str | None = None,
    insufficiency_cause: str | None = None,
    available_facts: tuple[str, ...] = (),
) -> tuple[str, str]:
    """Arma (system_prompt, user_prompt). Los ultimos cuatro parametros solo
    los usa `replanner` -- se reutiliza la misma funcion en vez de mantener
    un segundo renderizador para replanificacion.
    """
    system_prompt = (
        "Objetivos disponibles:\n"
        f"{_render_objectives(objective_catalog)}\n\n"
        "Operaciones disponibles:\n"
        f"{_render_operations(operation_catalog)}\n\n"
        "Conceptos disponibles:\n"
        f"{_render_concepts(artifact)}"
    )

    user_sections = [
        f"Pregunta: {question}",
        f"Estado analitico:\n{_render_state(analytical_state)}",
        f"Historial:\n{_render_history(conversation_history)}",
    ]
    if prior_clarification is not None:
        user_sections.append(f"Aclaracion previa: {prior_clarification}")
    if retry_cause is not None:
        user_sections.append(
            f"Causa de rechazo del intento anterior: {retry_cause.cause} -- "
            f"{retry_cause.detail or ''}"
        )
    if fixed_objective is not None:
        user_sections.append(
            f"Replanificacion: el objetivo es fijo y no puede cambiar: {fixed_objective}"
        )
    if previous_plan_summary is not None:
        user_sections.append(f"Plan anterior:\n{previous_plan_summary}")
    if insufficiency_cause is not None:
        user_sections.append(f"Causa de insuficiencia: {insufficiency_cause}")
    if available_facts:
        user_sections.append("Hechos disponibles:\n" + "\n".join(available_facts))

    user_prompt = "\n\n".join(user_sections)

    return system_prompt, user_prompt
