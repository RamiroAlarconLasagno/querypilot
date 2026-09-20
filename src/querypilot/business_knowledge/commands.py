# src/querypilot/business_knowledge/commands.py
"""Comandos de linea de ordenes: validar y publicar el artefacto semantico.

06_parte_conocimiento_negocio.md, modulo `commands`. "Evaluar" no vive aca:
depende del banco de casos (bloque 1.7) e Interpretacion (bloque 1.6), y
tiene su propio punto de entrada -- querypilot-eval, en
interpretation/evaluation_cli.py -- declarado aparte en pyproject.toml.

Uso (16_instrucciones_ia.md seccion 9):
  uv run querypilot-semantic validate demo
  uv run querypilot-semantic publish demo
"validate"/"publish" reciben el NOMBRE de la conexion (subcarpeta de
semantic/), no una ruta completa.
"""

from __future__ import annotations

from pathlib import Path

import typer

from querypilot.business_knowledge.artifact_validator import (
    ArtifactValidationIssue,
    validate_artifact,
)
from querypilot.business_knowledge.semantic_artifact import (
    SemanticArtifact,
    derive_semantic_version,
    load_semantic_artifact,
)

app = typer.Typer(help="Validar y publicar el artefacto semantico de una conexion.")

PUBLISHED_VERSION_FILENAME = ".published_version"


def _report_issues(issues: list[ArtifactValidationIssue]) -> None:
    typer.echo(f"Artefacto invalido: {len(issues)} hallazgo(s).")
    for issue in issues:
        typer.echo(f"  - {issue.check}: {issue.detail}")


def _load_and_validate(
    semantic_dir: Path, connection: str
) -> tuple[SemanticArtifact, list[ArtifactValidationIssue]]:
    artifact = load_semantic_artifact(semantic_dir / connection)
    return artifact, validate_artifact(artifact)


@app.command()
def validate(
    connection: str = typer.Argument(help="Nombre de la conexion (subcarpeta de semantic/)."),
    semantic_dir: Path = typer.Option(Path("semantic"), help="Directorio base de conexiones."),
) -> None:
    """Carga el artefacto y corre las 8 comprobaciones de integridad."""
    _artifact, issues = _load_and_validate(semantic_dir, connection)
    if issues:
        _report_issues(issues)
        raise typer.Exit(code=1)
    typer.echo("Artefacto valido.")


@app.command()
def publish(
    connection: str = typer.Argument(help="Nombre de la conexion (subcarpeta de semantic/)."),
    semantic_dir: Path = typer.Option(Path("semantic"), help="Directorio base de conexiones."),
) -> None:
    """Valida y, si es valido, publica una nueva version derivada del contenido.

    Un artefacto que no valida no se publica: la version vigente anterior
    sigue sirviendo, sin tocar el marcador de version (06 seccion 6).
    """
    artifact, issues = _load_and_validate(semantic_dir, connection)
    if issues:
        _report_issues(issues)
        typer.echo("No se publica: la version vigente anterior sigue sirviendo.")
        raise typer.Exit(code=1)

    version = derive_semantic_version(artifact)
    marker = semantic_dir / connection / PUBLISHED_VERSION_FILENAME
    marker.write_text(version, encoding="utf-8")
    typer.echo(f"Version publicada: {version}")
