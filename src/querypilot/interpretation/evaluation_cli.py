# src/querypilot/interpretation/evaluation_cli.py
"""Comando de evaluacion: corre el banco de casos contra Interpretacion.
06_parte_conocimiento_negocio.md, modulo `commands`: "evaluar" tiene su
propio punto de entrada aca porque depende del banco de casos (bloque 1.7,
`business_knowledge/evaluation_cases.py`) e Interpretacion (bloque 1.6) --
no de `business_knowledge/commands.py`, que solo valida y publica.

Uso (16_instrucciones_ia.md seccion 9, `evaluacion.yml`):
  uv run querypilot-eval run demo --prompt-version v1 --report reporte.md

Bloque 1.8: el proveedor real (`model_port/factory.py`) se selecciona por
`QP_MODEL_PROVIDER`/`QP_MODEL_NAME`/`OPENAI_API_KEY` -- ningun valor por
defecto silencioso para el modelo. Con `QP_MODEL_PROVIDER=doble` (el valor
que fija `ci.yml`), `run` nunca necesita una clave: se construye un
`DeterministicModelPort` sin salida configurada, que solo fallaria si algo
intentara usarlo de verdad, cosa que el CI no hace (nunca invoca este
comando).
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path

import typer

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.analytics.operation_catalog import OPERATION_CATALOG
from querypilot.business_knowledge.artifact_validator import validate_artifact
from querypilot.business_knowledge.evaluation_cases import load_evaluation_cases
from querypilot.business_knowledge.semantic_artifact import (
    derive_semantic_version,
    load_semantic_artifact,
)
from querypilot.interpretation.evaluation_metrics import (
    EvaluationReport,
    MetricValue,
    passes_thresholds,
)
from querypilot.interpretation.evaluation_runner import run_bank_evaluation
from querypilot.model_port.factory import build_model_port

app = typer.Typer(help="Correr el banco de evaluacion de Interpretacion.")

MAX_SEMANTIC_ITERATIONS = 3


@app.callback()
def _cli() -> None:
    """Con un solo comando registrado, Typer lo aplana y deja de exigir su
    nombre (`querypilot-eval demo` en vez de `querypilot-eval run demo`).
    Este callback fuerza el modo grupo para que `run` siga siendo explicito,
    igual que `validate`/`publish` en `business_knowledge/commands.py` --
    y para que agregar un segundo comando mas adelante no cambie la forma
    de invocar los que ya existen.
    """


def format_report(report: EvaluationReport) -> str:
    def line(label: str, value: MetricValue) -> str:
        ratio = value.ratio
        shown = "s/d" if ratio is None else f"{ratio:.1%} ({value.numerator}/{value.denominator})"
        return f"  {label}: {shown}"

    lines = [
        f"Version semantica: {report.semantic_version}",
        f"Version de prompt: {report.prompt_version}",
        f"Proveedor: {report.provider}",
        f"Modelo: {report.model}",
        f"Casos totales: {report.total_cases}",
        f"Casos evaluados: {report.evaluated_cases}",
        f"Fallas operativas: {report.operational_failures}",
    ]
    if report.operational_failure_case_ids:
        lines.append(
            f"  casos con falla operativa: {', '.join(report.operational_failure_case_ids)}"
        )
    lines += [
        "Metricas de aceptacion:",
        line("A1 (correctas sin aclaracion, >= 80%)", report.a1_correct_without_clarification),
        line("A2 (error silencioso, <= 5%)", report.a2_silent_error),
        line("A4 (falsos fuera de alcance, <= 5%)", report.a4_false_out_of_scope),
        line("B1 (plan valido al primer intento, >= 90%)", report.b1_valid_first_attempt),
        line("B1+B2 (valido tras un reintento, >= 98%)", report.b1_plus_b2_valid_within_retry),
        "Diagnosticos:",
        line("Acierto de objetivo", report.objective_accuracy),
        line("Acierto de conceptos", report.concept_accuracy),
        line("Tasa de aclaracion", report.clarification_rate),
        line("Acierto fuera de alcance", report.out_of_scope_accuracy),
        line("Herencia correcta", report.inheritance_accuracy),
        line("Validez de plan", report.plan_validity),
        f"Veredicto: {'ACEPTADO' if passes_thresholds(report) else 'NO ACEPTADO'}",
    ]
    return "\n".join(lines)


def _history_semantic_versions(history_dir: Path, connection: str) -> set[str]:
    """Versiones semanticas distintas ya evaluadas para esta conexion, segun
    los reportes previos guardados en `history_dir`. Cada archivo se nombra
    `<semantic_version>__<prompt_version>__<timestamp>.md`: contar
    iteraciones es contar prefijos distintos, sin parsear contenido.
    """
    connection_dir = history_dir / connection
    if not connection_dir.exists():
        return set()
    return {path.stem.split("__")[0] for path in connection_dir.glob("*.md")}


def _save_to_history(
    history_dir: Path, connection: str, report: EvaluationReport, text: str
) -> Path:
    connection_dir = history_dir / connection
    connection_dir.mkdir(parents=True, exist_ok=True)
    # Microsegundos: una corrida real tarda de sobra para no colisionar, pero
    # nada obliga a que dos corridas (p. ej. de prueba) no caigan en el mismo
    # segundo.
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    path = connection_dir / f"{report.semantic_version}__{report.prompt_version}__{timestamp}.md"
    path.write_text(text, encoding="utf-8")
    return path


def _warn_about_iteration_limit(
    history_dir: Path, connection: str, report: EvaluationReport
) -> None:
    prior_versions = _history_semantic_versions(history_dir, connection)
    all_versions = prior_versions | {report.semantic_version}
    typer.echo(
        f"Versiones semanticas distintas evaluadas hasta ahora "
        f"(incluyendo esta corrida): {len(all_versions)}/{MAX_SEMANTIC_ITERATIONS}."
    )
    if len(all_versions) >= MAX_SEMANTIC_ITERATIONS:
        typer.echo(
            "Limite de 01_metodo_solucion.md seccion 12: tres iteraciones de mejora del "
            "artefacto semantico. Si esta corrida no alcanza los umbrales, el supuesto "
            "queda refutado -- la decision se registra a mano, este aviso no bloquea nada."
        )


@app.command()
def run(
    connection: str = typer.Argument(help="Nombre de la conexion (subcarpeta de semantic/)."),
    semantic_dir: Path = typer.Option(Path("semantic"), help="Directorio base de conexiones."),
    prompt_version: str = typer.Option("v1", help="Version de prompt a auditar junto al reporte."),
    report: Path | None = typer.Option(
        None, "--report", help="Ruta donde escribir el reporte en Markdown."
    ),
    history_dir: Path | None = typer.Option(
        None,
        "--history-dir",
        help="Directorio con corridas anteriores (para contar iteraciones sobre el artefacto).",
    ),
) -> None:
    """Carga artefacto y banco, y corre la evaluacion contra el ModelPort real."""
    connection_dir = semantic_dir / connection
    artifact = load_semantic_artifact(connection_dir)
    issues = validate_artifact(artifact)
    if issues:
        typer.echo(f"Artefacto invalido: {len(issues)} hallazgo(s). No se puede evaluar.")
        for issue in issues:
            typer.echo(f"  - {issue.check}: {issue.detail}")
        raise typer.Exit(code=1)

    cases = load_evaluation_cases(connection_dir)
    semantic_version = derive_semantic_version(artifact)
    typer.echo(f"Banco cargado: {len(cases)} casos. Version semantica: {semantic_version}.")

    model_port = build_model_port()
    provider = os.environ.get("QP_MODEL_PROVIDER", "doble")
    model = os.environ.get("QP_MODEL_NAME", "-")

    evaluation_report = asyncio.run(
        run_bank_evaluation(
            model_port=model_port,
            cases=cases,
            prompt_version=prompt_version,
            objective_catalog=OBJECTIVE_CATALOG,
            operation_catalog=OPERATION_CATALOG,
            artifact=artifact,
            semantic_version=semantic_version,
            provider=provider,
            model=model,
        )
    )

    text = format_report(evaluation_report)
    typer.echo(text)

    if report is not None:
        report.write_text(text, encoding="utf-8")
        typer.echo(f"Reporte escrito en {report}.")

    if history_dir is not None:
        saved_at = _save_to_history(history_dir, connection, evaluation_report, text)
        typer.echo(f"Copia guardada en el historial: {saved_at}.")
        _warn_about_iteration_limit(history_dir, connection, evaluation_report)

    if not passes_thresholds(evaluation_report):
        raise typer.Exit(code=1)
