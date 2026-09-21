# tests/interpretation/contract/test_proposal_builder.py
"""check_objective_is_available: guarda determinista de proposal_builder
contra un objetivo sin criterio de suficiencia verificable
(07_parte_interpretacion.md seccion 10, paso 4).
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import ObjectiveName
from querypilot.interpretation.proposal_builder import check_objective_is_available
from querypilot.model_port.structured_output import Continuity, ContinuityMode, ObjectiveProposal


def _proposal(objective: ObjectiveName) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=objective,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=(),
        ambiguities=(),
        plan=(),
    )


def test_a_defined_objective_is_accepted() -> None:
    assert check_objective_is_available(_proposal(ObjectiveName.QUERY_METRIC)) == ()


def test_explore_is_rejected_as_not_available() -> None:
    rejections = check_objective_is_available(_proposal(ObjectiveName.EXPLORE))
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.OBJECTIVE_NOT_AVAILABLE
