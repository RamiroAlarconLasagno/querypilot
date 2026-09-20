# src/querypilot/canonical_language/identifiers.py
"""Identificadores de aislamiento: turno, objetivo e intento.

Cadenas opacas (14_contratos_formato.md seccion 2): un prefijo legible como
"t_58" ayuda a quien lee un registro de auditoria, pero el sistema no lo
interpreta ni lo valida. Cada tipo distinto evita que turno, objetivo e
intento se confundan entre si en las firmas de funciones y modelos futuros,
que es la fuga que describe 01_metodo_solucion.md seccion 11.3: sin
distincion de turno, una afirmacion podria citar evidencia de otro turno,
producida bajo otro contexto de acceso.

Que un modelo los declare sin valor por defecto -- la parte de "obligatorio"
de 16_instrucciones_ia.md seccion 7 -- es responsabilidad de cada modelo que
los use, no de este archivo: aqui solo se definen los tipos.
"""

from __future__ import annotations

from typing import NewType

TurnId = NewType("TurnId", str)
ObjectiveId = NewType("ObjectiveId", str)
AttemptId = NewType("AttemptId", str)
