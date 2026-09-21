# src/querypilot/model_port/factory.py
"""Selecciona la implementacion de `ModelPort` segun el entorno. Bloque 1.8.

`QP_MODEL_PROVIDER` (`ci.yml`, `evaluacion.yml`) decide entre:

- `openai`: `OpenAIModelPort` real. Exige `QP_MODEL_NAME` -- sin default
  silencioso, para que una corrida nunca use un modelo distinto del pedido sin
  que quede a la vista. La clave (`OPENAI_API_KEY`) la lee el propio SDK de
  OpenAI si no se pasa explicita; este modulo no la toca.
- `doble` (o ausente): `DeterministicModelPort` sin salida configurada. Nunca
  requiere clave -- es el valor que fija `ci.yml`.

Vive en `model_port/` (16_instrucciones_ia.md seccion 4: caja habilitada para
esto) para que `interpretation/` siga sin conocer proveedores.
"""

from __future__ import annotations

import os

from querypilot.model_port.deterministic_double import DeterministicModelPort
from querypilot.model_port.openai_adapter import OpenAIModelPort
from querypilot.model_port.port import ModelPort

_OPENAI = "openai"
_DOUBLE = "doble"


def build_model_port() -> ModelPort:
    provider = os.environ.get("QP_MODEL_PROVIDER", _DOUBLE)

    if provider == _OPENAI:
        model = os.environ.get("QP_MODEL_NAME")
        if not model:
            raise RuntimeError(
                "QP_MODEL_NAME es obligatoria para QP_MODEL_PROVIDER=openai -- "
                "no hay modelo por defecto: una corrida real nunca debe usar "
                "silenciosamente un modelo distinto del pedido."
            )
        return OpenAIModelPort(model=model)

    if provider == _DOUBLE:
        return DeterministicModelPort()

    raise RuntimeError(
        f"QP_MODEL_PROVIDER desconocido: {provider!r} (valores validos: openai, doble)"
    )
