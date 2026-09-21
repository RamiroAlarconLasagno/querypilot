# tests/business_knowledge/unit/test_evaluation_cases.py
"""Carga del banco real de `semantic/demo/evaluation/cases.yaml` y validacion
de su composicion. 01_metodo_solucion.md seccion 12: banco minimo de 60
casos, congelado, con la distribucion 40/15/15/10/10/10 declarada en el
propio archivo.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from querypilot.business_knowledge.evaluation_cases import (
    BANK_SIZE,
    CATEGORY_SHARE,
    CaseCategory,
    ExpectedAmbiguity,
    ExpectedOutOfScope,
    ExpectedPlan,
    load_evaluation_cases,
)

DEMO_DIR = Path(__file__).resolve().parents[3] / "semantic" / "demo"


def test_the_real_demo_bank_has_sixty_cases() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    assert len(cases) == BANK_SIZE


def test_case_ids_are_unique() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    ids = [case.id for case in cases]
    assert len(ids) == len(set(ids))


def test_category_distribution_matches_the_declared_composition() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    counts = Counter(case.category for case in cases)
    for category, share in CATEGORY_SHARE.items():
        assert counts[category] == round(share * BANK_SIZE), (
            f"{category}: {counts[category]} casos, se esperaban {round(share * BANK_SIZE)}"
        )


def test_every_category_is_present_in_the_share_table() -> None:
    assert set(CATEGORY_SHARE) == set(CaseCategory)


def test_plan_expected_categories_declare_at_least_one_objective() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    for case in cases:
        if isinstance(case.expected, ExpectedPlan):
            assert len(case.expected.objectives) >= 1, case.id


def test_material_ambiguity_cases_declare_a_description() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    for case in cases:
        if case.category is CaseCategory.MATERIAL_AMBIGUITY:
            assert isinstance(case.expected, ExpectedAmbiguity)
            assert case.expected.description


def test_out_of_scope_cases_declare_a_reason() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    for case in cases:
        if case.category is CaseCategory.OUT_OF_SCOPE:
            assert isinstance(case.expected, ExpectedOutOfScope)
            assert case.expected.reason


def test_continuation_cases_declare_inherited_fields() -> None:
    cases = load_evaluation_cases(DEMO_DIR)
    for case in cases:
        if case.category is CaseCategory.CONTINUATION:
            assert isinstance(case.expected, ExpectedPlan)
            assert case.expected.inherits
            assert case.previous_context
