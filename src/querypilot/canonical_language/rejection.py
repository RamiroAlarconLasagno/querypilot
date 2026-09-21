# src/querypilot/canonical_language/rejection.py
"""Rechazo, como valor de retorno. 14_contratos_formato.md seccion 7 y
16_instrucciones_ia.md seccion 7: las autoridades devuelven Rejection, nunca
lanzan excepciones -- un rechazo es un resultado normal del dominio, no una
falla operativa.

RejectionCause transcribe hoy las diez causas genericas ya cerradas de
10_parte_operaciones.md seccion 7, mas tres causas propias de Interpretacion
(07_parte_interpretacion.md): objective_not_available (proposal_builder),
ambiguity_has_default_sense (ambiguity_detector, seccion 5: refutacion
deterministica de una ambiguedad material declarada por el modelo cuando el
artefacto semantico ya tiene una acepcion por defecto inequivoca) y
reference_without_context (reference_resolver: una referencia resuelta sin
ningun estado analitico ni historial del cual pudiera haberse resuelto).
Las causas propias de cada operacion (overlapping_periods,
excessive_cardinality, zero_variance, excessive_n, nonexistent_filter_value...)
se agregan cuando el validador que las produce se implemente -- no se listan
de antemano.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class SuggestedAction(StrEnum):
    INFORM = "inform"
    CLARIFY = "clarify"
    NARROW = "narrow"
    RETRY = "retry"
    RE_EXECUTE = "re_execute"


class RejectionCause(StrEnum):
    NONEXISTENT_CONCEPT = "nonexistent_concept"
    UNAUTHORIZED_CONCEPT = "unauthorized_concept"
    INCOMPATIBLE_DIMENSION = "incompatible_dimension"
    GRANULARITY_NOT_AVAILABLE = "granularity_not_available"
    INVALID_PARAMETERS = "invalid_parameters"
    INSUFFICIENT_UNIVERSE = "insufficient_universe"
    ROW_LIMIT_EXCEEDED = "row_limit_exceeded"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    PERIOD_WITHOUT_DATA = "period_without_data"
    SOURCE_NOT_AVAILABLE = "source_not_available"
    OBJECTIVE_NOT_AVAILABLE = "objective_not_available"
    AMBIGUITY_HAS_DEFAULT_SENSE = "ambiguity_has_default_sense"
    REFERENCE_WITHOUT_CONTEXT = "reference_without_context"


class Rejection(BaseModel):
    cause: RejectionCause
    action: SuggestedAction
    options: tuple[str, ...] = ()
    detail: str | None = None
