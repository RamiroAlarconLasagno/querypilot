# tests/structural/test_model_port_without_provider_key.py
"""Ejercita la propiedad declarada en `ci.yml`/`13_decisiones_tecnicas.md`
seccion 8: el CI no tiene ninguna clave de proveedor. Bloque 1.8: hasta ahora
la regla estaba solo en la configuracion del workflow; esto la convierte en
algo que una corrida de pytest verifica.
"""

from __future__ import annotations

import importlib

from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.factory import build_model_port


def test_importing_model_port_modules_never_requires_a_key(sin_claves_de_modelo: None) -> None:
    for module_name in (
        "querypilot.model_port.port",
        "querypilot.model_port.deterministic_double",
        "querypilot.model_port.openai_adapter",
        "querypilot.model_port.factory",
    ):
        importlib.import_module(module_name)


def test_the_provider_selected_by_ci_never_touches_a_key(sin_claves_de_modelo: None) -> None:
    port = build_model_port()
    assert isinstance(port, DeterministicModelPort)
