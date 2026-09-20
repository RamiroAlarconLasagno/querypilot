# tests/structural/test_canonical_language_no_behavior.py
"""Regla dura de canonical_language/: solo definiciones, nunca comportamiento.

02_vision_arquitectura.md seccion 6: "Es la carpeta con mas riesgo de
degenerar en el cajon generico que el metodo prohibe... no contiene
comportamiento." Esta prueba lo hace ejercitable: recorre cada modulo de
canonical_language/ y falla si aparece una funcion o un metodo, sin importar
si es logica de negocio, un validador o una conversion.
"""

from __future__ import annotations

import ast
from pathlib import Path

CANONICAL_LANGUAGE_DIR = (
    Path(__file__).resolve().parents[2] / "src" / "querypilot" / "canonical_language"
)


def _python_modules() -> list[Path]:
    return sorted(CANONICAL_LANGUAGE_DIR.glob("*.py"))


def test_at_least_one_module_exists() -> None:
    """Si la carpeta queda vacia, la prueba de abajo pasaria en falso."""
    assert _python_modules(), f"No hay modulos .py en {CANONICAL_LANGUAGE_DIR}"


def test_no_module_defines_functions_or_methods() -> None:
    forbidden_definitions: list[str] = []

    for module in _python_modules():
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                forbidden_definitions.append(f"{module.name}:{node.lineno} {node.name}")

    assert not forbidden_definitions, (
        "canonical_language/ solo admite definiciones; se encontraron funciones "
        f"o metodos: {forbidden_definitions}"
    )
