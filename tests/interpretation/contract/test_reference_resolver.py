# tests/interpretation/contract/test_reference_resolver.py
"""check_references_have_context: 07_parte_interpretacion.md seccion 10,
paso 6. Solo verifica que exista contexto (estado o historial), nunca que
la resolucion del modelo sea correcta.
"""

from __future__ import annotations

from querypilot.canonical_language.rejection import RejectionCause
from querypilot.canonical_language.shared_values import AnalyticalState, ObjectiveName
from querypilot.interpretation.reference_resolver import check_references_have_context
from querypilot.model_port.structured_output import (
    Continuity,
    ContinuityMode,
    ObjectiveProposal,
    ResolvedReference,
)


def _proposal(references: tuple[ResolvedReference, ...]) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id="p1",
        objective=ObjectiveName.COMPARE,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(),
        time_expressions=(),
        filters=(),
        premises=(),
        references=references,
        ambiguities=(),
        plan=(),
    )


_A_REFERENCE = (
    ResolvedReference(
        expression="esos tres",
        resolution="los tres contribuyentes principales del turno anterior",
    ),
)


def test_proposal_without_references_is_never_checked() -> None:
    assert (
        check_references_have_context(_proposal(()), analytical_state=None, conversation_history=())
        == ()
    )


def test_reference_resolved_against_analytical_state_is_accepted() -> None:
    state = AnalyticalState(
        period="junio y julio de 2026",
        last_reference="ds_301, con sus tres contribuyentes principales",
        semantic_version="sem_v7",
    )
    result = check_references_have_context(
        _proposal(_A_REFERENCE), analytical_state=state, conversation_history=()
    )
    assert result == ()


def test_reference_resolved_against_conversation_history_is_accepted() -> None:
    result = check_references_have_context(
        _proposal(_A_REFERENCE),
        analytical_state=None,
        conversation_history=("Turno anterior: los tres contribuyentes fueron...",),
    )
    assert result == ()


def test_reference_without_any_context_is_rejected() -> None:
    rejections = check_references_have_context(
        _proposal(_A_REFERENCE), analytical_state=None, conversation_history=()
    )
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.REFERENCE_WITHOUT_CONTEXT


def test_reference_with_state_but_no_last_reference_and_no_history_is_rejected() -> None:
    state = AnalyticalState(period="junio y julio de 2026", semantic_version="sem_v7")
    rejections = check_references_have_context(
        _proposal(_A_REFERENCE), analytical_state=state, conversation_history=()
    )
    assert len(rejections) == 1
    assert rejections[0].cause == RejectionCause.REFERENCE_WITHOUT_CONTEXT
