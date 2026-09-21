# src/querypilot/interpretation/evaluation_metrics.py
"""Agrega `CaseVerdict` en el reporte del banco. Formulas acordadas para el
cierre del bloque 1.7 (01_metodo_solucion.md seccion 12,
07_parte_interpretacion.md seccion 10):

- A1 = correctas sin aclaracion / total plan_expected
- A2 = incorrectas pero con plan (silenciosas) / total plan_expected
- A4 = declinados como fuera de alcance entre los que NO son out_of_scope
  (incluye material_ambiguity) / total de esos casos
- B1 = plan valido al primer intento / total plan_expected
- B1+B2 = plan valido al primer intento o tras un unico reintento / total
  plan_expected

Diagnosticos (no son criterio de aceptacion, solo lectura fina):
objective_accuracy, concept_accuracy, clarification_rate,
out_of_scope_accuracy, inheritance_accuracy, plan_validity (alias de B1).
"""

from __future__ import annotations

from pydantic import BaseModel

from querypilot.business_knowledge.evaluation_cases import PLAN_EXPECTED_CATEGORIES, CaseCategory
from querypilot.interpretation.case_comparator import CaseVerdict, OutcomeLabel


class MetricValue(BaseModel):
    numerator: int
    denominator: int

    @property
    def ratio(self) -> float | None:
        if self.denominator == 0:
            return None
        return self.numerator / self.denominator


class EvaluationReport(BaseModel):
    semantic_version: str
    prompt_version: str
    total_cases: int

    a1_correct_without_clarification: MetricValue
    a2_silent_error: MetricValue
    a4_false_out_of_scope: MetricValue
    b1_valid_first_attempt: MetricValue
    b1_plus_b2_valid_within_retry: MetricValue

    objective_accuracy: MetricValue
    concept_accuracy: MetricValue
    clarification_rate: MetricValue
    out_of_scope_accuracy: MetricValue
    inheritance_accuracy: MetricValue
    plan_validity: MetricValue

    verdicts: tuple[CaseVerdict, ...]


def _ratio(numerator: int, denominator: int) -> MetricValue:
    return MetricValue(numerator=numerator, denominator=denominator)


# Umbrales de aceptacion del MVP 1 (01_metodo_solucion.md seccion 12).
A1_THRESHOLD = 0.80
A2_THRESHOLD = 0.05
A4_THRESHOLD = 0.05
B1_THRESHOLD = 0.90
B1_PLUS_B2_THRESHOLD = 0.98


def passes_thresholds(report: EvaluationReport) -> bool:
    """Las cinco metricas deben superar su umbral. Si A2 falla, no hay
    compensacion posible por las demas (01 seccion 12)."""
    a1 = report.a1_correct_without_clarification.ratio
    a2 = report.a2_silent_error.ratio
    a4 = report.a4_false_out_of_scope.ratio
    b1 = report.b1_valid_first_attempt.ratio
    b1_plus_b2 = report.b1_plus_b2_valid_within_retry.ratio
    if a1 is None or a2 is None or a4 is None or b1 is None or b1_plus_b2 is None:
        return False
    return (
        a1 >= A1_THRESHOLD
        and a2 <= A2_THRESHOLD
        and a4 <= A4_THRESHOLD
        and b1 >= B1_THRESHOLD
        and b1_plus_b2 >= B1_PLUS_B2_THRESHOLD
    )


def build_report(
    verdicts: tuple[CaseVerdict, ...], semantic_version: str, prompt_version: str
) -> EvaluationReport:
    plan_expected = [v for v in verdicts if v.category in PLAN_EXPECTED_CATEGORIES]
    not_out_of_scope = [v for v in verdicts if v.category is not CaseCategory.OUT_OF_SCOPE]
    out_of_scope_cases = [v for v in verdicts if v.category is CaseCategory.OUT_OF_SCOPE]
    continuation_cases = [v for v in verdicts if v.category is CaseCategory.CONTINUATION]

    a1 = _ratio(
        sum(1 for v in plan_expected if v.label is OutcomeLabel.CORRECT), len(plan_expected)
    )
    a2 = _ratio(
        sum(1 for v in plan_expected if v.label is OutcomeLabel.SILENT_ERROR), len(plan_expected)
    )
    a4 = _ratio(
        sum(1 for v in not_out_of_scope if v.declined_as_out_of_scope), len(not_out_of_scope)
    )
    b1 = _ratio(sum(1 for v in plan_expected if v.valid_first_attempt), len(plan_expected))
    b1_plus_b2 = _ratio(sum(1 for v in plan_expected if v.valid_within_retry), len(plan_expected))

    objective_accuracy = _ratio(
        sum(1 for v in plan_expected if v.plan_match is not None and v.plan_match.objective_ok),
        len(plan_expected),
    )
    concept_accuracy = _ratio(
        sum(1 for v in plan_expected if v.plan_match is not None and v.plan_match.concepts_ok),
        len(plan_expected),
    )
    clarification_rate = _ratio(
        sum(1 for v in verdicts if v.asked_for_clarification), len(verdicts)
    )
    out_of_scope_accuracy = _ratio(
        sum(1 for v in out_of_scope_cases if v.label is OutcomeLabel.CORRECT_OUT_OF_SCOPE),
        len(out_of_scope_cases),
    )
    inheritance_accuracy = _ratio(
        sum(1 for v in continuation_cases if v.plan_match is not None and v.plan_match.inherits_ok),
        len(continuation_cases),
    )

    return EvaluationReport(
        semantic_version=semantic_version,
        prompt_version=prompt_version,
        total_cases=len(verdicts),
        a1_correct_without_clarification=a1,
        a2_silent_error=a2,
        a4_false_out_of_scope=a4,
        b1_valid_first_attempt=b1,
        b1_plus_b2_valid_within_retry=b1_plus_b2,
        objective_accuracy=objective_accuracy,
        concept_accuracy=concept_accuracy,
        clarification_rate=clarification_rate,
        out_of_scope_accuracy=out_of_scope_accuracy,
        inheritance_accuracy=inheritance_accuracy,
        plan_validity=b1,
        verdicts=verdicts,
    )
