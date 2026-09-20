# tests/business_knowledge/unit/test_semantic_artifact.py
"""Carga del artefacto semantico real y tipado de sus campos.

min_explanation_coverage se prueba explicitamente como Decimal, nunca float:
16_instrucciones_ia.md seccion 7 exige Decimal de punta a punta, y un YAML
sin comillas alrededor de "0.70" pasaria por float antes de llegar a Pydantic.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from querypilot.business_knowledge.semantic_artifact import (
    Metric,
    load_semantic_artifact,
)

DEMO_DIR = Path(__file__).resolve().parents[3] / "semantic" / "demo"


def test_loads_the_real_demo_artifact_without_errors() -> None:
    artifact = load_semantic_artifact(DEMO_DIR)

    assert artifact.connection.id == "demo"
    assert len(artifact.dimensions) == 5
    assert len(artifact.metrics) == 4


def test_min_explanation_coverage_is_decimal_not_float() -> None:
    artifact = load_semantic_artifact(DEMO_DIR)
    coverage = artifact.connection.thresholds.min_explanation_coverage

    assert coverage == Decimal("0.70")
    assert type(coverage) is Decimal
    assert type(coverage) is not float


def test_a_metric_missing_a_required_field_fails_validation() -> None:
    incomplete_metric = {
        "business_name": "Facturacion",
        "definition": "Ventas menos notas de credito.",
        "synonyms": ["ventas"],
        "unit": "ARS",
        "aggregations": ["sum"],
        "combinable_dimensions": ["customer"],
        "min_granularity": "day",
        "physical": {
            "source": "cmp_cab",
            "measure": "sum(cmp_det.imp_neto)",
            "temporal_field": "cmp_cab.f_emis",
        },
    }

    with pytest.raises(ValidationError):
        Metric.model_validate(incomplete_metric)
