# tests/structural/test_canonical_language_identifiers.py
"""Que garantiza (y que no) TurnId/ObjectiveId/AttemptId, definidos como
NewType sobre str en canonical_language/identifiers.py.

No viven en tests/canonical_language/unit/ porque canonical_language/ no es
una de las diez cajas del diagrama y 02_vision_arquitectura.md seccion 8 solo
asigna tests/<parte>/ a esas diez; se decidio mantener sus pruebas en
tests/structural/ junto con la de "sin comportamiento".
"""

from __future__ import annotations

from querypilot.canonical_language.identifiers import (
    AttemptId,
    ObjectiveId,
    TurnId,
)


def test_the_three_identifiers_exist_and_are_distinct() -> None:
    """NewType dedicado por identificador: mypy no deja confundir uno con otro."""
    assert TurnId is not ObjectiveId
    assert TurnId is not AttemptId
    assert ObjectiveId is not AttemptId


def test_identifiers_remain_str_at_runtime() -> None:
    """NewType no envuelve nada: en runtime es la funcion identidad.

    La distincion entre TurnId, ObjectiveId y AttemptId existe solo para
    mypy. En runtime, TurnId("t_58") devuelve el mismo str que recibio.
    """
    turn = TurnId("t_58")
    objective = ObjectiveId("obj_1")
    attempt = AttemptId("att_2")

    assert type(turn) is str
    assert type(objective) is str
    assert type(attempt) is str
    assert turn == "t_58"
    assert objective == "obj_1"
    assert attempt == "att_2"


def test_does_not_validate_format_or_prefix() -> None:
    """Decision explicita: el prefijo no se valida aqui.

    14_contratos_formato.md seccion 2 dice que el sistema no interpreta el
    prefijo. Validarlo en canonical_language/ violaria la regla dura de
    02_vision_arquitectura.md seccion 6 ("nada de logica ni validaciones").
    La garantia del prefijo queda para la funcion que genere cada
    identificador, en la parte duena (analysis_session/, executor/), cuando
    se implemente ese bloque. Esta prueba documenta el estado actual para
    que un cambio futuro sea deliberado, no accidental.
    """
    assert TurnId("sin-prefijo-de-turno") == "sin-prefijo-de-turno"
    assert TurnId("") == ""
