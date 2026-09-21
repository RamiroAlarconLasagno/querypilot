# tests/model_port/unit/test_deterministic_double.py
"""DeterministicModelPort: 07_parte_interpretacion.md seccion 10 y
08_parte_sintesis.md seccion 11 exigen un doble que devuelva salidas fijas sin
tocar ningun proveedor. La prueba central es estructural: cualquier funcion
tipada contra ModelPort debe aceptar el doble sin conversion explicita.
"""

from __future__ import annotations

import pytest

from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.port import ModelPort
from querypilot.model_port.structured_output import InterpretationOutput, SynthesisOutput

_INTERPRETATION_FIXTURE = InterpretationOutput(
    objective_proposals=(),
    out_of_scope=(),
    prompt_version="fixture_interpretation_v1",
)

_SYNTHESIS_FIXTURE = SynthesisOutput(
    sections=(),
    suggestions=(),
    prompt_version="fixture_synthesis_v1",
)


async def _interpret_through_the_port(port: ModelPort) -> InterpretationOutput:
    """Tipada contra ModelPort, no contra DeterministicModelPort: si el doble
    no cumpliera el protocolo estructuralmente, mypy rechazaria la llamada de
    test_deterministic_double_satisfies_the_model_port_protocol.
    """
    return await port.interpret("v2", "system prompt", "user prompt")


async def test_deterministic_double_satisfies_the_model_port_protocol() -> None:
    double = DeterministicModelPort(interpretation_output=_INTERPRETATION_FIXTURE)
    assert isinstance(double, ModelPort)
    result = await _interpret_through_the_port(double)
    assert result.prompt_version == "v2"


async def test_interpret_restamps_the_requested_prompt_version() -> None:
    double = DeterministicModelPort(interpretation_output=_INTERPRETATION_FIXTURE)
    result = await double.interpret("requested_v3", "system", "user")
    assert result.prompt_version == "requested_v3"
    assert result.model_copy(update={"prompt_version": "fixture_interpretation_v1"}) == (
        _INTERPRETATION_FIXTURE
    )


async def test_synthesize_restamps_the_requested_prompt_version() -> None:
    double = DeterministicModelPort(synthesis_output=_SYNTHESIS_FIXTURE)
    result = await double.synthesize("requested_v9", "system", "user")
    assert result.prompt_version == "requested_v9"
    assert result.model_copy(update={"prompt_version": "fixture_synthesis_v1"}) == (
        _SYNTHESIS_FIXTURE
    )


async def test_interpret_raises_when_not_configured() -> None:
    double = DeterministicModelPort()
    with pytest.raises(RuntimeError):
        await double.interpret("v1", "system", "user")


async def test_synthesize_raises_when_not_configured() -> None:
    double = DeterministicModelPort()
    with pytest.raises(RuntimeError):
        await double.synthesize("v1", "system", "user")
