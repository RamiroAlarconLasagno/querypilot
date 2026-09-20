# tests/conftest.py
"""Configuracion compartida de pruebas.

Frontera que sostiene el diseno del CI:

  CI          -> prueba que el sistema es correcto. Determinista, sin secretos.
  Evaluacion  -> prueba que el modelo es bueno. Manual, con clave real.

Si un test necesita una clave de proveedor, esta mal categorizado: pertenece a
la marca `evaluation`, que el CI excluye.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest


@pytest.fixture(scope="session")
def system_db_url() -> str:
    """URL de la base propia del sistema, para pruebas de integracion."""
    url = os.getenv("QP_SYSTEM_DB_URL")
    if not url:
        pytest.skip("QP_SYSTEM_DB_URL no definida: se omiten pruebas de integracion")
    return url


@pytest.fixture
def sin_claves_de_modelo(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Elimina toda credencial de proveedor del entorno.

    Se usa en la prueba estructural que verifica que la suite de contrato pasa
    sin claves. Convierte la regla en una propiedad ejercitada en vez de una
    intencion declarada.
    """
    for var in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "QP_MODEL_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("QP_MODEL_PROVIDER", "doble")
    yield


@pytest.fixture
def modelo_doble() -> object:
    """Doble determinista del puerto del modelo.

    Devuelve salidas fijas. Permite verificar el contrato entero de
    Interpretacion y Sintesis sin red, sin coste y sin variabilidad.
    """
    pytest.skip("Se implementa en el sub-peldano 5.1")
