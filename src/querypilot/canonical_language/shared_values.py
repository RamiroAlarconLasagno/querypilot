# src/querypilot/canonical_language/shared_values.py
"""Vocabulario canonico compartido por mas de una parte. 02_vision_arquitectura.md
seccion 6: si estas definiciones vivieran dentro de una sola parte, las demas
dependerian de ella por una razon que no es arquitectonica. Regla dura de la
carpeta (misma seccion): solo definiciones, nada de logica ni comportamiento.

Granularity es parte de DataRequest (14_contratos_formato.md seccion 3).
FactType, Condition y sus piezas las necesitan tanto la salida del modelo
(model_port) como el plan durable (canonical_language/plan.py) y, mas
adelante, el Ejecutor -- ninguna de las tres puede depender de las otras dos.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel


class Granularity(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    TOTAL = "total"


class FactType(StrEnum):
    """Tipos de hecho declarados por las diez fichas de 10_parte_operaciones.md
    seccion 8. Cada operacion es duena de los suyos; este enum solo los reune
    para poder tiparlos en Condition y Binding.
    """

    PERIOD_VALUE = "period_value"
    ABSOLUTE_VARIANCE = "absolute_variance"
    RELATIVE_VARIANCE = "relative_variance"
    MAIN_CONTRIBUTOR = "main_contributor"
    EXPLAINED_COVERAGE = "explained_coverage"
    DIMENSION_CARDINALITY = "dimension_cardinality"
    RANKING_ELEMENT = "ranking_element"
    UNIVERSE_TOTAL = "universe_total"
    UNIVERSE_SCOPE = "universe_scope"
    METRIC_VALUE = "metric_value"
    VALUE_PER_ELEMENT = "value_per_element"
    SERIES_POINT = "series_point"
    COUNT = "count"
    AVAILABLE_COLUMNS = "available_columns"
    ANOMALOUS_POINT = "anomalous_point"
    APPLIED_CRITERION = "applied_criterion"
    SHARE = "share"


class ConditionOperator(StrEnum):
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    EQ = "eq"
    NEQ = "neq"


class ThresholdName(StrEnum):
    """Umbrales configurados que una Condition puede citar en vez de un valor
    literal. Acotado a los dos umbrales de connection.yaml que se comparan
    contra hechos (09_parte_ejecutor.md seccion 5): el resto de los campos de
    Thresholds son limites operativos (filas, segundos, MB), no criterios de
    suficiencia.
    """

    MIN_EXPLANATION_COVERAGE = "min_explanation_coverage"
    DECOMPOSE_VARIANCE_MAX_DIMENSION_CARDINALITY = "decompose_variance_max_dimension_cardinality"


class Condition(BaseModel):
    fact_type: FactType
    operator: ConditionOperator
    value: Decimal | ThresholdName


class FilterOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    IN = "in"
    NOT_IN = "not_in"


class Filter(BaseModel):
    dimension: str
    operator: FilterOperator
    values: tuple[str, ...]


class SortDirection(StrEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class Binding(BaseModel):
    source_fact_type: FactType
    target_dimension: str
    operator: FilterOperator


DomainValue = str | int | Granularity | SortDirection
