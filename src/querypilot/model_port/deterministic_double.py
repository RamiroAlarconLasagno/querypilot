# src/querypilot/model_port/deterministic_double.py
"""Doble determinista del puerto del modelo. 07_parte_interpretacion.md
seccion 10 y 08_parte_sintesis.md seccion 11: la verificacion de contrato de
Interpretacion y Sintesis corre entera con dobles que devuelven salidas fijas,
sin tocar ningun proveedor ni requerir su clave (02_vision_arquitectura.md
seccion 8; 16_instrucciones_ia.md seccion 6). No hereda de ModelPort -- es un
Protocol, la conformidad se verifica estructuralmente.
"""

from __future__ import annotations

from querypilot.model_port.structured_output import InterpretationOutput, SynthesisOutput


class DeterministicModelPort:
    def __init__(
        self,
        interpretation_output: InterpretationOutput | None = None,
        synthesis_output: SynthesisOutput | None = None,
    ) -> None:
        self._interpretation_output = interpretation_output
        self._synthesis_output = synthesis_output

    async def interpret(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> InterpretationOutput:
        if self._interpretation_output is None:
            raise RuntimeError(
                "DeterministicModelPort no fue configurado con un InterpretationOutput fijo"
            )
        return self._interpretation_output.model_copy(update={"prompt_version": prompt_version})

    async def synthesize(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> SynthesisOutput:
        if self._synthesis_output is None:
            raise RuntimeError(
                "DeterministicModelPort no fue configurado con un SynthesisOutput fijo"
            )
        return self._synthesis_output.model_copy(update={"prompt_version": prompt_version})
