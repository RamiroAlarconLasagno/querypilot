# src/querypilot/model_port/port.py
"""Puerto del modelo: dos operaciones de dominio, nunca un cliente generico de
"completar texto" (02_vision_arquitectura.md seccion 6). El dominio no conoce
proveedor, modelo ni prompts -- solo estas dos firmas. Las llamadas reales son
E/S de red, por eso el puerto es async desde el inicio.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from querypilot.model_port.structured_output import InterpretationOutput, SynthesisOutput


@runtime_checkable
class ModelPort(Protocol):
    async def interpret(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> InterpretationOutput: ...

    async def synthesize(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> SynthesisOutput: ...
