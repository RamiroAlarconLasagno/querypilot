# src/querypilot/model_port/openai_adapter.py
"""Adaptador real de `ModelPort` sobre OpenAI. Bloque 1.8.

Decision de 1.8 (ver `docs/13_decisiones_tecnicas.md` seccion 6bis): Structured
Outputs **estricto** queda degradado para el MVP 1. `ProposedPlanStep.arguments:
dict[str, DomainValue]` (dentro de `InterpretationOutput`) es un diccionario de
claves libres, y el modo estricto de OpenAI exige que todo objeto declare sus
propiedades de antemano (`additionalProperties: false`) -- no admite eso. En vez
de reabrir `model_port/structured_output.py` (contrato cerrado de 1.5/1.6) para
acomodar una limitacion del proveedor, este adaptador usa el modo JSON simple:

    modelo -> texto/JSON -> Pydantic -> validacion deterministica

El esquema (`model_json_schema()` del tipo Pydantic esperado) viaja como texto
dentro de las instrucciones -- OpenAI no genera JSON sin que se le pida
explicitamente, ni siquiera en modo `json_object`. Lo que se pierde es la
garantia de forma **a nivel de API**; lo que no cambia es que la forma nunca
garantizo verdad (`13` seccion 6, `14` seccion 8): la validacion real sigue
ocurriendo despues, en Pydantic primero y en los validadores deterministas de
Interpretacion despues, exactamente como si la API hubiera devuelto la forma
correcta de entrada.

Un fallo de parseo (JSON invalido, o JSON valido que no cumple el esquema) es
una **falla operativa** de este adaptador -- se propaga como excepcion
(`ModelOutputParseError`), nunca como `Rejection`: un rechazo es un resultado de
dominio sobre una propuesta bien formada, y esto no llega a serlo.

Reintentos de transporte (limite de tasa, 5xx, timeout) los maneja el propio
cliente de OpenAI via `max_retries` -- una capa separada del unico reintento de
dominio que ya implementa `interpretation/evaluation_runner.py` sobre
`retry_cause`. No se reimplementa aca ni se mezclan ambas cosas.

Construccion perezosa: el cliente de OpenAI se crea recien en el primer uso, no
en `__init__` ni al importar este modulo -- instanciar `OpenAIModelPort` o
importar este archivo nunca requiere `OPENAI_API_KEY`.
"""

from __future__ import annotations

from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from querypilot.model_port.structured_output import InterpretationOutput, SynthesisOutput

DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_TRANSPORT_RETRIES = 2

ModelT = TypeVar("ModelT", bound=BaseModel)


class ModelOutputParseError(RuntimeError):
    """El modelo respondio, pero el texto no es JSON valido o no cumple el
    esquema esperado. No hay `Rejection` posible sobre una salida que ni
    siquiera alcanza la forma minima para interpretarse.
    """


class OpenAIModelPort:
    """Implementa el `Protocol` `ModelPort` (`model_port/port.py`) contra la
    Responses API de OpenAI. `model` es obligatorio y sin valor por defecto:
    usar un modelo silenciosamente distinto del pedido invalidaria la
    comparabilidad de la corrida (`14_contratos_formato.md` seccion 11).
    """

    def __init__(
        self,
        model: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_TRANSPORT_RETRIES,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(timeout=self._timeout, max_retries=self._max_retries)
        return self._client

    async def _complete(self, system_prompt: str, user_prompt: str, shape: type[ModelT]) -> ModelT:
        instructions = (
            f"{system_prompt}\n\n"
            "Responde UNICAMENTE con un objeto JSON que cumpla exactamente este "
            "JSON Schema, sin texto adicional ni bloques de codigo:\n"
            f"{shape.model_json_schema()}"
        )
        client = self._get_client()
        response = await client.responses.create(
            model=self._model,
            instructions=instructions,
            input=user_prompt,
            text={"format": {"type": "json_object"}},
        )
        raw = response.output_text
        try:
            return shape.model_validate_json(raw)
        except ValidationError as exc:
            raise ModelOutputParseError(
                f"la respuesta del modelo no cumple el esquema de {shape.__name__}: {exc}"
            ) from exc

    async def interpret(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> InterpretationOutput:
        output = await self._complete(system_prompt, user_prompt, InterpretationOutput)
        return output.model_copy(update={"prompt_version": prompt_version})

    async def synthesize(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> SynthesisOutput:
        output = await self._complete(system_prompt, user_prompt, SynthesisOutput)
        return output.model_copy(update={"prompt_version": prompt_version})
