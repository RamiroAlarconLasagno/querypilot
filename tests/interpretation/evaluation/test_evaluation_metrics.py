# tests/interpretation/evaluation/test_evaluation_metrics.py
"""Agregacion de CaseVerdict en EvaluationReport. Formulas acordadas para el
cierre de 1.7 -- ver el docstring de interpretation/evaluation_metrics.py.
Verdicts sinteticos, sin pasar por classify_case: prueba la agregacion sola.
"""

from __future__ import annotations

from querypilot.business_knowledge.evaluation_cases import CaseCategory
from querypilot.interpretation.case_comparator import CaseVerdict, OutcomeLabel, PlanMatch
from querypilot.interpretation.evaluation_metrics import (
    EvaluationReport,
    MetricValue,
    build_report,
    passes_thresholds,
)

_FULL_MATCH = PlanMatch(
    same_objective_count=True,
    objective_ok=True,
    concepts_ok=True,
    temporal_ok=True,
    premises_ok=True,
    dependency_ok=True,
    inherits_ok=True,
)
_WRONG_CONCEPT = _FULL_MATCH.model_copy(update={"concepts_ok": False})


def _synthetic_verdicts() -> tuple[CaseVerdict, ...]:
    return (
        CaseVerdict(
            case_id="d1",
            category=CaseCategory.DIRECT,
            label=OutcomeLabel.CORRECT,
            plan_match=_FULL_MATCH,
            valid_first_attempt=True,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="d2",
            category=CaseCategory.DIRECT,
            label=OutcomeLabel.SILENT_ERROR,
            plan_match=_WRONG_CONCEPT,
            valid_first_attempt=True,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="p1",
            category=CaseCategory.PREMISE,
            label=OutcomeLabel.REJECTED,
            plan_match=None,
            valid_first_attempt=False,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="ct1",
            category=CaseCategory.CONTINUATION,
            label=OutcomeLabel.CORRECT,
            plan_match=_FULL_MATCH,
            valid_first_attempt=True,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="m1",
            category=CaseCategory.MULTIPLE_OBJECTIVES,
            label=OutcomeLabel.UNNECESSARY_CLARIFICATION,
            plan_match=None,
            valid_first_attempt=False,
            valid_within_retry=False,
            declined_as_out_of_scope=False,
            asked_for_clarification=True,
        ),
        CaseVerdict(
            case_id="a1",
            category=CaseCategory.MATERIAL_AMBIGUITY,
            label=OutcomeLabel.CORRECT_AMBIGUITY,
            plan_match=None,
            valid_first_attempt=False,
            valid_within_retry=False,
            declined_as_out_of_scope=False,
            asked_for_clarification=True,
        ),
        CaseVerdict(
            case_id="a2",
            category=CaseCategory.MATERIAL_AMBIGUITY,
            label=OutcomeLabel.MISSED_AMBIGUITY,
            plan_match=None,
            valid_first_attempt=True,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="o1",
            category=CaseCategory.OUT_OF_SCOPE,
            label=OutcomeLabel.CORRECT_OUT_OF_SCOPE,
            plan_match=None,
            valid_first_attempt=False,
            valid_within_retry=False,
            declined_as_out_of_scope=True,
            asked_for_clarification=False,
        ),
        CaseVerdict(
            case_id="o2",
            category=CaseCategory.OUT_OF_SCOPE,
            label=OutcomeLabel.MISSED_OUT_OF_SCOPE,
            plan_match=None,
            valid_first_attempt=True,
            valid_within_retry=True,
            declined_as_out_of_scope=False,
            asked_for_clarification=False,
        ),
    )


def _build_report(**overrides: object) -> EvaluationReport:
    kwargs: dict[str, object] = {
        "verdicts": _synthetic_verdicts(),
        "semantic_version": "v1",
        "prompt_version": "p1",
        "provider": "doble",
        "model": "-",
    }
    kwargs.update(overrides)
    return build_report(**kwargs)  # type: ignore[arg-type]


def test_report_computes_a1_a2_over_plan_expected_only() -> None:
    report = _build_report()
    # plan_expected = d1, d2, p1, ct1, m1 (5 casos)
    assert report.a1_correct_without_clarification == MetricValue(numerator=2, denominator=5)
    assert report.a2_silent_error == MetricValue(numerator=1, denominator=5)


def test_report_computes_a4_over_every_non_out_of_scope_case() -> None:
    report = _build_report()
    # not_out_of_scope = 7 casos (incluye los 2 de material_ambiguity); ninguno declinado
    assert report.a4_false_out_of_scope == MetricValue(numerator=0, denominator=7)


def test_report_computes_b1_and_b1_plus_b2() -> None:
    report = _build_report()
    assert report.b1_valid_first_attempt == MetricValue(numerator=3, denominator=5)
    assert report.b1_plus_b2_valid_within_retry == MetricValue(numerator=4, denominator=5)


def test_report_diagnostics() -> None:
    report = _build_report()
    assert report.objective_accuracy == MetricValue(numerator=3, denominator=5)
    assert report.concept_accuracy == MetricValue(numerator=2, denominator=5)
    assert report.clarification_rate == MetricValue(numerator=2, denominator=9)
    assert report.out_of_scope_accuracy == MetricValue(numerator=1, denominator=2)
    assert report.inheritance_accuracy == MetricValue(numerator=1, denominator=1)
    assert report.plan_validity == report.b1_valid_first_attempt


def test_report_counts_total_evaluated_and_operational_failures() -> None:
    report = _build_report(operational_failure_case_ids=("x1", "x2"))
    assert report.total_cases == 11  # 9 verdicts + 2 fallas operativas
    assert report.evaluated_cases == 9
    assert report.operational_failures == 2
    assert report.operational_failure_case_ids == ("x1", "x2")


def test_report_carries_provider_and_model() -> None:
    report = _build_report(provider="openai", model="gpt-test")
    assert report.provider == "openai"
    assert report.model == "gpt-test"


def test_metric_value_ratio_is_none_with_empty_denominator() -> None:
    assert MetricValue(numerator=0, denominator=0).ratio is None


def _report_with(
    a1: MetricValue | None = None,
    a2: MetricValue | None = None,
    a4: MetricValue | None = None,
    b1: MetricValue | None = None,
    b1_plus_b2: MetricValue | None = None,
    operational_failures: int = 0,
) -> EvaluationReport:
    ok = MetricValue(numerator=54, denominator=54)
    resolved_b1 = b1 or MetricValue(numerator=49, denominator=54)
    return EvaluationReport(
        semantic_version="v1",
        prompt_version="p1",
        provider="openai",
        model="gpt-test",
        total_cases=60,
        evaluated_cases=60 - operational_failures,
        operational_failures=operational_failures,
        a1_correct_without_clarification=a1 or MetricValue(numerator=48, denominator=54),
        a2_silent_error=a2 or MetricValue(numerator=1, denominator=54),
        a4_false_out_of_scope=a4 or MetricValue(numerator=1, denominator=54),
        b1_valid_first_attempt=resolved_b1,
        b1_plus_b2_valid_within_retry=b1_plus_b2 or MetricValue(numerator=53, denominator=54),
        objective_accuracy=ok,
        concept_accuracy=ok,
        clarification_rate=MetricValue(numerator=9, denominator=60),
        out_of_scope_accuracy=MetricValue(numerator=6, denominator=6),
        inheritance_accuracy=MetricValue(numerator=9, denominator=9),
        plan_validity=resolved_b1,
        verdicts=(),
    )


def test_passes_thresholds_when_all_five_metrics_meet_their_bound() -> None:
    assert passes_thresholds(_report_with())


def test_a2_failure_is_not_compensated_by_a_high_a1() -> None:
    report = _report_with(
        a1=MetricValue(numerator=54, denominator=54),
        a2=MetricValue(numerator=3, denominator=54),  # 5.5 % > 5 %
    )
    assert not passes_thresholds(report)


def test_operational_failures_block_acceptance_even_with_perfect_metrics() -> None:
    report = _report_with(
        a1=MetricValue(numerator=54, denominator=54),
        a2=MetricValue(numerator=0, denominator=54),
        a4=MetricValue(numerator=0, denominator=54),
        b1=MetricValue(numerator=54, denominator=54),
        b1_plus_b2=MetricValue(numerator=54, denominator=54),
        operational_failures=1,
    )
    assert not passes_thresholds(report)
