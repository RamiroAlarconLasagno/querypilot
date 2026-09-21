# src/querypilot/interpretation/dependency_graph.py
"""Valida el grafo de dependencias entre las ObjectiveProposal de un mismo
turno. 07_parte_interpretacion.md seccion 6bis: una dependencia declarada
ordena la ejecucion entre objetivos. Funcion separada de plan_builder a
proposito -- valida entre propuestas, no dentro de una sola.

Cada propuesta tiene a lo sumo una dependencia (ObjectiveDependency es un
campo opcional, no una lista), asi que el grafo es funcional: a lo sumo un
borde saliente por nodo. Eso permite detectar ciclos siguiendo la cadena de
cada propuesta sin visitar dos veces la misma, marcando como resueltas las
que ya se recorrieron.
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import Rejection, RejectionCause, SuggestedAction
from querypilot.model_port.structured_output import ObjectiveProposal


def check_for_cycles(proposals: tuple[ObjectiveProposal, ...]) -> tuple[Rejection, ...]:
    proposal_ids = {proposal.proposal_id for proposal in proposals}
    rejections: list[Rejection] = []
    valid_edges: dict[str, str] = {}

    for proposal in proposals:
        dependency = proposal.dependency
        if dependency is None:
            continue
        source = dependency.source_proposal_id
        if source == proposal.proposal_id:
            rejections.append(
                Rejection(
                    cause=RejectionCause.SELF_DEPENDENCY,
                    action=SuggestedAction.RETRY,
                    detail=f"{proposal.proposal_id} depende de si misma",
                )
            )
        elif source not in proposal_ids:
            rejections.append(
                Rejection(
                    cause=RejectionCause.DEPENDENCY_TARGET_NOT_FOUND,
                    action=SuggestedAction.RETRY,
                    detail=f"{proposal.proposal_id} depende de '{source}', "
                    "que no existe en este turno",
                )
            )
        else:
            valid_edges[proposal.proposal_id] = source

    resolved: set[str] = set()
    for start in valid_edges:
        if start in resolved:
            continue
        path: list[str] = []
        current: str | None = start
        while current is not None and current not in resolved:
            if current in path:
                cycle = [*path[path.index(current) :], current]
                rejections.append(
                    Rejection(
                        cause=RejectionCause.DEPENDENCY_CYCLE,
                        action=SuggestedAction.RETRY,
                        detail=f"Ciclo de dependencias: {' -> '.join(cycle)}",
                    )
                )
                break
            path.append(current)
            current = valid_edges.get(current)
        resolved.update(path)

    return tuple(rejections)
