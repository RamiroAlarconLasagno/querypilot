# tests/interpretation/contract/test_dependency_graph.py
"""check_for_cycles: 07_parte_interpretacion.md seccion 6bis. Tres reglas:
source_proposal_id existe, no apunta a si mismo, no hay ciclos entre
propuestas del mismo turno.
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import Binding, FilterOperator, ObjectiveName
from querypilot.interpretation.dependency_graph import check_for_cycles
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    ObjectiveDependency,
    ObjectiveProposal,
)

_BINDING = Binding(
    source_fact_type="main_contributor", target_dimension="customer", operator=FilterOperator.NOT_IN
)


def _proposal(proposal_id: str, source_proposal_id: str | None = None) -> ObjectiveProposal:
    dependency = (
        ObjectiveDependency(source_proposal_id=source_proposal_id, binding=_BINDING)
        if source_proposal_id is not None
        else None
    )
    return ObjectiveProposal(
        proposal_id=proposal_id,
        objective=ObjectiveName.RANK,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=(),
        dependency=dependency,
    )


def test_no_dependencies_has_no_rejections() -> None:
    proposals = (_proposal("p1"), _proposal("p2"))
    assert check_for_cycles(proposals) == ()


def test_a_valid_dependency_on_another_proposal_has_no_rejections() -> None:
    proposals = (_proposal("p1"), _proposal("p2", source_proposal_id="p1"))
    assert check_for_cycles(proposals) == ()


def test_dependency_on_a_nonexistent_proposal_is_rejected() -> None:
    proposals = (_proposal("p1", source_proposal_id="p99"),)
    rejections = check_for_cycles(proposals)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.DEPENDENCY_TARGET_NOT_FOUND


def test_self_dependency_is_rejected() -> None:
    proposals = (_proposal("p1", source_proposal_id="p1"),)
    rejections = check_for_cycles(proposals)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.SELF_DEPENDENCY


def test_a_two_proposal_cycle_is_rejected_exactly_once() -> None:
    proposals = (
        _proposal("p1", source_proposal_id="p2"),
        _proposal("p2", source_proposal_id="p1"),
    )
    rejections = check_for_cycles(proposals)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.DEPENDENCY_CYCLE


def test_a_three_proposal_cycle_is_rejected_exactly_once() -> None:
    proposals = (
        _proposal("p1", source_proposal_id="p2"),
        _proposal("p2", source_proposal_id="p3"),
        _proposal("p3", source_proposal_id="p1"),
    )
    rejections = check_for_cycles(proposals)
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.DEPENDENCY_CYCLE
