# src/querypilot/interpretation/evaluation_cli.py
"""Comando de evaluacion: corre el banco de casos contra Interpretacion.
06_parte_conocimiento_negocio.md, modulo `commands`: "evaluar" tiene su
propio punto de entrada aca porque depende del banco de casos (bloque 1.7,
`business_knowledge/evaluation_cases.py`) e Interpretacion (bloque 1.6) --
no de `business_knowledge/commands.py`, que solo valida y publica.

Uso (16_instrucciones_ia.md seccion 9):
  uv run querypilot-eval run demo

Bloque 1.7 entrega el instrumento completo -- carga del banco, comparador
semantico, metricas A1/A2/A4/B1/B2 y diagnosticos -- probado entero con
`DeterministicModelPort` (`tests/interpretation/evaluation/`). Lo unico que
falta es una implementacion real de `ModelPort` con proveedor y clave: eso es
bloque 1.8 (`02_vision_arquitectura.md` seccion 10). Por eso `run` carga y
valida todo lo que puede cargar y validar sin modelo, y se detiene con un
mensaje explicito en el paso que si lo necesita, en vez de simular una
corrida o importar un proveedor que todavia no existe.
"""

from __future__ import annotations

from pathlib import Path

import typer

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

app = typer.Typer(help="Correr el banco de evaluacion de Interpretacion.")


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
        f"Casos: {report.total_cases}",
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


@app.command()
def run(
    connection: str = typer.Argument(help="Nombre de la conexion (subcarpeta de semantic/)."),
    semantic_dir: Path = typer.Option(Path("semantic"), help="Directorio base de conexiones."),
    prompt_version: str = typer.Option("v1", help="Version de prompt a auditar junto al reporte."),
) -> None:
    """Carga artefacto y banco, y corre la evaluacion si hay un ModelPort real disponible."""
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

    typer.echo(
        "No hay todavia una implementacion real de ModelPort (bloque 1.8, "
        "02_vision_arquitectura.md seccion 10). El instrumento de evaluacion "
        "-- este comando, el comparador semantico y las metricas -- esta "
        "completo y probado con DeterministicModelPort. Falta unicamente el "
        "proveedor real para correr esta conexion de verdad."
    )
    raise typer.Exit(code=2)
