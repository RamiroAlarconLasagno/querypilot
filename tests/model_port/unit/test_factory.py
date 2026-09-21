# tests/model_port/unit/test_factory.py
"""build_model_port: seleccion de proveedor por QP_MODEL_PROVIDER. Bloque 1.8."""

from __future__ import annotations

import pytest

from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.factory import build_model_port
from querypilot.model_port.openai_adapter import OpenAIModelPort


def test_defaults_to_the_double_when_the_provider_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("QP_MODEL_PROVIDER", raising=False)
    assert isinstance(build_model_port(), DeterministicModelPort)


def test_doble_provider_never_needs_a_key(sin_claves_de_modelo: None) -> None:
    port = build_model_port()
    assert isinstance(port, DeterministicModelPort)


def test_openai_provider_requires_a_model_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QP_MODEL_PROVIDER", "openai")
    monkeypatch.delenv("QP_MODEL_NAME", raising=False)
    with pytest.raises(RuntimeError, match="QP_MODEL_NAME"):
        build_model_port()


def test_openai_provider_builds_the_real_adapter_without_touching_the_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QP_MODEL_PROVIDER", "openai")
    monkeypatch.setenv("QP_MODEL_NAME", "gpt-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    port = build_model_port()
    assert isinstance(port, OpenAIModelPort)
    assert port._client is None  # construccion perezosa: nada toco la clave todavia


def test_unknown_provider_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("QP_MODEL_PROVIDER", "algo-inexistente")
    with pytest.raises(RuntimeError, match="algo-inexistente"):
        build_model_port()
