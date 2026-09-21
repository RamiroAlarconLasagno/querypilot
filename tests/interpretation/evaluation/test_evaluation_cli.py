# tests/interpretation/evaluation/test_evaluation_cli.py
"""`querypilot-eval run demo`: carga el artefacto y el banco reales, corre la
evaluacion contra el `ModelPort` que resuelva `factory.build_model_port()`, y
escribe el reporte. Bloque 1.8. Estos tests fuerzan `QP_MODEL_PROVIDER=doble`
explicitamente -- nunca dependen del entorno ambiente -- asi que no requieren
`OPENAI_API_KEY` en ningun caso: con el doble sin configurar, los 60 casos
terminan en falla operativa, lo cual es un resultado real y verificable, no
un simulacro.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from querypilot.interpretation.evaluation_cli import app, format_report
from querypilot.interpretation.evaluation_metrics import MetricValue, build_report

runner = CliRunner()
_DOBLE_ENV = {"QP_MODEL_PROVIDER": "doble"}


def test_run_with_the_unconfigured_double_reports_every_case_as_an_operational_failure() -> None:
    result = runner.invoke(app, ["run", "demo"], env=_DOBLE_ENV)
    assert result.exit_code == 1
    assert "60 casos" in result.output
    assert "Fallas operativas: 60" in result.output
    assert "Casos evaluados: 0" in result.output
    assert "NO ACEPTADO" in result.output


def test_run_writes_the_report_to_the_requested_path(tmp_path: Path) -> None:
    report_path = tmp_path / "reporte.md"
    result = runner.invoke(app, ["run", "demo", "--report", str(report_path)], env=_DOBLE_ENV)
    assert result.exit_code == 1
    assert report_path.exists()
    assert "Fallas operativas: 60" in report_path.read_text(encoding="utf-8")


def test_run_saves_history_and_warns_at_the_iteration_limit(tmp_path: Path) -> None:
    history_dir = tmp_path / "runs"
    for _ in range(2):
        runner.invoke(app, ["run", "demo", "--history-dir", str(history_dir)], env=_DOBLE_ENV)

    result = runner.invoke(app, ["run", "demo", "--history-dir", str(history_dir)], env=_DOBLE_ENV)

    saved_files = list((history_dir / "demo").glob("*.md"))
    assert len(saved_files) == 3  # misma semantic_version, tres corridas distintas
    assert "1/3" in result.output or "3/3" in result.output


def test_run_reports_invalid_artifacts_before_trying_to_evaluate(tmp_path: Path) -> None:
    (tmp_path / "broken").mkdir()
    result = runner.invoke(app, ["run", "broken", "--semantic-dir", str(tmp_path)], env=_DOBLE_ENV)
    assert result.exit_code != 0


def test_run_requires_a_model_name_for_the_openai_provider() -> None:
    result = runner.invoke(app, ["run", "demo"], env={"QP_MODEL_PROVIDER": "openai"})
    assert result.exit_code != 0
    assert "QP_MODEL_NAME" in str(result.exception)


def test_format_report_includes_the_acceptance_verdict() -> None:
    report = build_report(
        (), semantic_version="v1", prompt_version="p1", provider="doble", model="-"
    )
    text = format_report(report)
    assert "Veredicto:" in text
    assert "s/d" in text  # sin casos, los ratios no estan definidos


def test_format_report_shows_percentages_when_there_is_data() -> None:
    report = build_report(
        (), semantic_version="v1", prompt_version="p1", provider="doble", model="-"
    ).model_copy(
        update={"a1_correct_without_clarification": MetricValue(numerator=45, denominator=50)}
    )
    text = format_report(report)
    assert "90.0%" in text


def test_format_report_lists_operational_failure_case_ids() -> None:
    report = build_report(
        (),
        semantic_version="v1",
        prompt_version="p1",
        provider="openai",
        model="gpt-test",
        operational_failure_case_ids=("c001", "c002"),
    )
    text = format_report(report)
    assert "c001, c002" in text
