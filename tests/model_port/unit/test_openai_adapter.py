# tests/model_port/unit/test_openai_adapter.py
"""OpenAIModelPort, con un cliente OpenAI falso -- sin red, sin clave.
Bloque 1.8. Decision B (docs/13_decisiones_tecnicas.md seccion 6bis): modo
JSON simple + `model_validate_json`, no Structured Outputs estricto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from querypilot.model_port.openai_adapter import ModelOutputParseError, OpenAIModelPort


@dataclass
class _FakeResponse:
    output_text: str


@dataclass
class _FakeResponses:
    output_text: str
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(output_text=self.output_text)


@dataclass
class _FakeClient:
    responses: _FakeResponses


def _adapter_with(output_text: str) -> tuple[OpenAIModelPort, _FakeResponses]:
    adapter = OpenAIModelPort(model="gpt-test")
    responses = _FakeResponses(output_text=output_text)
    adapter._client = _FakeClient(responses=responses)  # type: ignore[assignment]
    return adapter, responses


def test_the_client_is_never_built_at_construction() -> None:
    adapter = OpenAIModelPort(model="gpt-test")
    assert adapter._client is None


async def test_interpret_parses_valid_json_into_interpretation_output() -> None:
    adapter, _responses = _adapter_with(
        '{"objective_proposals": [], "out_of_scope": [], "prompt_version": "ignored"}'
    )
    output = await adapter.interpret("v7", "system", "pregunta")
    assert output.objective_proposals == ()
    assert output.prompt_version == "v7"  # el adaptador lo re-estampa, como el doble


async def test_synthesize_parses_valid_json_into_synthesis_output() -> None:
    adapter, _responses = _adapter_with(
        '{"sections": [], "cross_objective": null, "suggestions": [], "prompt_version": "ignored"}'
    )
    output = await adapter.synthesize("v7", "system", "pregunta")
    assert output.sections == ()
    assert output.prompt_version == "v7"


async def test_invalid_json_raises_model_output_parse_error() -> None:
    adapter, _ = _adapter_with("esto no es json")
    with pytest.raises(ModelOutputParseError):
        await adapter.interpret("v1", "system", "pregunta")


async def test_well_formed_json_that_violates_the_schema_raises_model_output_parse_error() -> None:
    adapter, _ = _adapter_with('{"objective_proposals": "no deberia ser un string"}')
    with pytest.raises(ModelOutputParseError):
        await adapter.interpret("v1", "system", "pregunta")


async def test_the_request_asks_for_json_object_format_and_the_right_model() -> None:
    adapter, responses = _adapter_with(
        '{"objective_proposals": [], "out_of_scope": [], "prompt_version": "x"}'
    )
    await adapter.interpret("v1", "sistema", "usuario")

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call["model"] == "gpt-test"
    assert call["input"] == "usuario"
    assert call["text"] == {"format": {"type": "json_object"}}
    assert "sistema" in call["instructions"]


async def test_client_is_built_once_and_reused_across_calls() -> None:
    adapter, _ = _adapter_with(
        '{"objective_proposals": [], "out_of_scope": [], "prompt_version": "x"}'
    )
    client_after_construction = adapter._client
    await adapter.interpret("v1", "s", "u")
    await adapter.interpret("v1", "s", "u")
    assert adapter._client is client_after_construction
