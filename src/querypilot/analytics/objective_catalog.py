# src/querypilot/analytics/objective_catalog.py
"""Catalogo cerrado de objetivos. 10_parte_operaciones.md seccion 2: el
criterio de suficiencia lo declara el objetivo, no la operacion ni el
modelo -- es lo que evita que el sistema entre en bucle o se rinda antes
de tiempo. Dato, no logica: el catalogo se recorre, nunca se calcula.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ObjectiveName(StrEnum):
    QUERY_METRIC = "query_metric"
    COMPARE = "compare"
    RANK = "rank"
    EXPLAIN_VARIANCE = "explain_variance"
    DETECT_ANOMALY = "detect_anomaly"
    DESCRIBE_DATASET = "describe_dataset"
    EXPLORE = "explore"


class ObjectiveCard(BaseModel):
    name: ObjectiveName
    typical_question: str
    sufficiency_criterion: str
    configurable_threshold: str | None = None


OBJECTIVE_CATALOG: tuple[ObjectiveCard, ...] = (
    ObjectiveCard(
        name=ObjectiveName.QUERY_METRIC,
        typical_question="¿Cuanto vendimos en julio?",
        sufficiency_criterion="La metrica se obtuvo para el alcance completo pedido",
    ),
    ObjectiveCard(
        name=ObjectiveName.COMPARE,
        typical_question="¿Julio contra junio?",
        sufficiency_criterion="Ambos terminos obtenidos, comparables y con igual definicion",
    ),
    ObjectiveCard(
        name=ObjectiveName.RANK,
        typical_question="¿Los diez mejores clientes?",
        sufficiency_criterion=(
            "Se obtuvieron N elementos ordenados sobre el universo autorizado completo"
        ),
        configurable_threshold="N por defecto = 10",
    ),
    ObjectiveCard(
        name=ObjectiveName.EXPLAIN_VARIANCE,
        typical_question="¿Por que cayo la facturacion?",
        sufficiency_criterion=(
            "La contribucion acumulada de los factores identificados alcanza el umbral"
        ),
        configurable_threshold="70 % por defecto",
    ),
    ObjectiveCard(
        name=ObjectiveName.DETECT_ANOMALY,
        typical_question="¿Hay algo raro esta semana?",
        sufficiency_criterion=("Se evaluo la serie completa del periodo con el criterio declarado"),
        configurable_threshold="Sensibilidad",
    ),
    ObjectiveCard(
        name=ObjectiveName.DESCRIBE_DATASET,
        typical_question="¿Quienes fueron los invitados?",
        sufficiency_criterion=(
            "Se obtuvo el conteo total y una vista previa determinista y acotada"
        ),
    ),
    ObjectiveCard(
        name=ObjectiveName.EXPLORE,
        typical_question="¿Como viene el negocio?",
        sufficiency_criterion="Se cubrieron todas las dimensiones declaradas del panorama",
        configurable_threshold="Dimensiones del panorama",
    ),
)
