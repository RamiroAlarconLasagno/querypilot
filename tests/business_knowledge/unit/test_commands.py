# tests/business_knowledge/unit/test_commands.py
"""Comandos validate y publish, via CliRunner.

publish se prueba siempre sobre una copia en tmp_path, nunca sobre
semantic/demo/: escribe un marcador de version y no debe mutar el fixture
que usan los demas tests de este bloque.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from querypilot.business_knowledge.commands import PUBLISHED_VERSION_FILENAME, app

REPO_ROOT = Path(__file__).resolve().parents[3]
DEMO_DIR = REPO_ROOT / "semantic" / "demo"

BROKEN_COMBINABLE_DIMENSIONS = (
    "    combinable_dimensions: [customer, region, product, salesperson, category]"
)

runner = CliRunner()


def _copy_demo_connection(destination_semantic_dir: Path, connection: str = "demo") -> Path:
    connection_dir = destination_semantic_dir / connection
    connection_dir.mkdir(parents=True)
    for filename in ("connection.yaml", "dimensions.yaml", "metrics.yaml"):
        shutil.copy(DEMO_DIR / filename, connection_dir / filename)
    return connection_dir


def _break_combinable_dimensions(connection_dir: Path) -> None:
    metrics_path = connection_dir / "metrics.yaml"
    content = metrics_path.read_text(encoding="utf-8")
    broken = content.replace(
        BROKEN_COMBINABLE_DIMENSIONS, "    combinable_dimensions: [does_not_exist]", 1
    )
    assert broken != content, "el texto a reemplazar no aparecio en metrics.yaml"
    metrics_path.write_text(broken, encoding="utf-8")


def test_validate_the_real_demo_connection_succeeds() -> None:
    result = runner.invoke(app, ["validate", "demo", "--semantic-dir", str(REPO_ROOT / "semantic")])

    assert result.exit_code == 0
    assert "valido" in result.stdout.lower()


def test_validate_reports_a_broken_connection(tmp_path: Path) -> None:
    connection_dir = _copy_demo_connection(tmp_path)
    _break_combinable_dimensions(connection_dir)

    result = runner.invoke(app, ["validate", "demo", "--semantic-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "combinable_dimensions_exist" in result.stdout


def test_publish_a_valid_connection_writes_a_deterministic_version(tmp_path: Path) -> None:
    connection_dir = _copy_demo_connection(tmp_path)
    marker = connection_dir / PUBLISHED_VERSION_FILENAME

    first = runner.invoke(app, ["publish", "demo", "--semantic-dir", str(tmp_path)])
    first_version = marker.read_text(encoding="utf-8")

    marker.unlink()
    second = runner.invoke(app, ["publish", "demo", "--semantic-dir", str(tmp_path)])
    second_version = marker.read_text(encoding="utf-8")

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert first_version == second_version
    assert first_version.startswith("sem_v")


def test_publish_an_invalid_connection_does_not_touch_the_marker(tmp_path: Path) -> None:
    connection_dir = _copy_demo_connection(tmp_path)
    marker = connection_dir / PUBLISHED_VERSION_FILENAME
    marker.write_text("sem_v_previous", encoding="utf-8")
    _break_combinable_dimensions(connection_dir)

    result = runner.invoke(app, ["publish", "demo", "--semantic-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert marker.read_text(encoding="utf-8") == "sem_v_previous"
