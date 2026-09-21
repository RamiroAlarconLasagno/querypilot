# src/querypilot/canonical_language/rejection.py
"""Rechazo, como valor de retorno. 14_contratos_formato.md seccion 7 y
16_instrucciones_ia.md seccion 7: las autoridades devuelven Rejection, nunca
lanzan excepciones -- un rechazo es un resultado normal del dominio, no una
falla operativa.

RejectionCause transcribe hoy las diez causas genericas ya cerradas de
10_parte_operaciones.md seccion 7, mas las causas propias de Interpretacion
(07_parte_interpretacion.md) que cada validador fue necesitando:

- `objective_not_available` (proposal_builder).
- `ambiguity_has_default_sense` (ambiguity_detector, seccion 5: refutacion
  deterministica de una ambiguedad material declarada por el modelo cuando
  el artefacto semantico ya tiene una acepcion por defecto inequivoca).
- `reference_without_context` (reference_resolver: una referencia resuelta
  sin ningun estado analitico ni historial del cual pudiera haberse resuelto).
- `condition_references_unpublished_fact` (plan_builder.validate_plan_steps,
  09_parte_ejecutor.md seccion 5: la condicion de un paso cita un tipo de
  hecho que ningun paso anterior del mismo plan declara publicar).
- `invalid_derives_from` (plan_builder.validate_plan_steps: `derives_from`
  referencia un `step_id` inexistente, futuro, o a si mismo).
- `ambiguity_with_plan` (plan_builder.check_ambiguity_excludes_plan,
  07_parte_interpretacion.md seccion 5: una ambiguedad material nunca viaja
  junto con un plan propuesto).
- `self_dependency`, `dependency_target_not_found`, `dependency_cycle`
  (dependency_graph.check_for_cycles: un ObjectiveDependency.source_proposal_id
  invalido o un ciclo entre las propuestas del mismo turno).
- `continuity_new_declares_inherits`, `continuation_without_state`,
  `inherited_field_unavailable` (proposal_builder.check_continuity_is_coherent).
- `replan_changed_objective` (replanner: la replanificacion no puede cambiar
  el objetivo, 07_parte_interpretacion.md seccion 7).

Los argumentos de operacion (desconocidos o faltantes) reusan la causa
generica `invalid_parameters` ya cerrada -- son exactamente el caso que esa
causa describe, no ameritan una causa nueva. Las causas propias de cada
operacion (overlapping_periods, excessive_cardinality, zero_variance,
excessive_n, nonexistent_filter_value...) se agregan cuando el validador
que las produce se implemente -- no se listan de antemano.
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
    CONDITION_REFERENCES_UNPUBLISHED_FACT = "condition_references_unpublished_fact"
    INVALID_DERIVES_FROM = "invalid_derives_from"
    AMBIGUITY_WITH_PLAN = "ambiguity_with_plan"
    SELF_DEPENDENCY = "self_dependency"
    DEPENDENCY_TARGET_NOT_FOUND = "dependency_target_not_found"
    DEPENDENCY_CYCLE = "dependency_cycle"
    CONTINUITY_NEW_DECLARES_INHERITS = "continuity_new_declares_inherits"
    CONTINUATION_WITHOUT_STATE = "continuation_without_state"
    INHERITED_FIELD_UNAVAILABLE = "inherited_field_unavailable"
    REPLAN_CHANGED_OBJECTIVE = "replan_changed_objective"


class Rejection(BaseModel):
    cause: RejectionCause
    action: SuggestedAction
    options: tuple[str, ...] = ()
    detail: str | None = None
