# tests/interpretation/evaluation/test_evaluation_cli.py
"""`querypilot-eval run demo`: carga y valida el artefacto y el banco reales
sin modelo, y se detiene con un mensaje explicito porque bloque 1.7 no
incluye un ModelPort real (eso es 1.8). No requiere clave de proveedor.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from querypilot.interpretation.evaluation_cli import app, format_report
from querypilot.interpretation.evaluation_metrics import MetricValue, build_report

runner = CliRunner()


def test_run_loads_the_real_bank_and_stops_without_a_real_provider() -> None:
    result = runner.invoke(app, ["run", "demo"])
    assert result.exit_code == 2
    assert "60 casos" in result.output
    assert "bloque 1.8" in result.output


def test_run_reports_invalid_artifacts_before_trying_to_evaluate(tmp_path: Path) -> None:
    (tmp_path / "broken").mkdir()
    result = runner.invoke(app, ["run", "broken", "--semantic-dir", str(tmp_path)])
    assert result.exit_code != 0


def test_format_report_includes_the_acceptance_verdict() -> None:
    report = build_report((), semantic_version="v1", prompt_version="p1")
    text = format_report(report)
    assert "Veredicto:" in text
    assert "s/d" in text  # sin casos, los ratios no estan definidos


def test_format_report_shows_percentages_when_there_is_data() -> None:
    report = build_report((), semantic_version="v1", prompt_version="p1").model_copy(
        update={"a1_correct_without_clarification": MetricValue(numerator=45, denominator=50)}
    )
    text = format_report(report)
    assert "90.0%" in text
