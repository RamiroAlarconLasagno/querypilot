# src/querypilot/analytics/operation_catalog.py
"""Catalogo cerrado de operaciones. 10_parte_operaciones.md seccion 3: toda
operacion se define con los mismos trece campos, y la ficha es parte del
contrato -- sin ella la operacion no existe para el sistema. Dato, no
logica: el catalogo se recorre, nunca se calcula.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class OperationName(StrEnum):
    COMPARE_PERIODS = "compare_periods"
    DECOMPOSE_VARIANCE = "decompose_variance"
    RANK = "rank"
    QUERY_METRIC = "query_metric"
    BREAKDOWN = "breakdown"
    TIME_SERIES = "time_series"
    COUNT = "count"
    DESCRIBE_DATASET = "describe_dataset"
    DETECT_ANOMALY = "detect_anomaly"
    CALCULATE_SHARE = "calculate_share"


class UniverseRequirement(StrEnum):
    AUTHORIZED = "authorized"
    COMPLETE = "complete"


class Parameter(BaseModel):
    name: str
    domain_type: str
    required: bool
    default: str | None = None


class OperationCard(BaseModel):
    name: OperationName
    purpose: str
    parameters: tuple[Parameter, ...]
    semantic_preconditions: str
    universe_requirement: UniverseRequirement
    data_requests: str
    calculation: str
    products: str
    published_facts: str
    rejection_conditions: str
    cost: int
    verification: str
    reusable: str


OPERATION_CATALOG: tuple[OperationCard, ...] = (
    OperationCard(
        name=OperationName.COMPARE_PERIODS,
        purpose="Obtener una metrica en dos periodos y su variacion",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="current_period", domain_type="period", required=True),
            Parameter(name="comparison_period", domain_type="period", required=True),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions=(
            "Metrica existente, comparable en el tiempo, ambos periodos resueltos a fechas"
        ),
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con granularidad correspondiente a los periodos",
        calculation="Diferencia absoluta y relativa",
        products="Hechos, resultado analitico",
        published_facts="period_value x2, absolute_variance, relative_variance",
        rejection_conditions=(
            "overlapping_periods; periods_of_different_length es advertencia, no rechazo"
        ),
        cost=1,
        verification="Datos fijos de dos periodos, comprobar variacion esperada",
        reusable="Si, si el conjunto activo cubre ambos periodos y la granularidad es derivable",
    ),
    OperationCard(
        name=OperationName.DECOMPOSE_VARIANCE,
        purpose="Repartir una variacion observada entre los elementos de una dimension",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="current_period", domain_type="period", required=True),
            Parameter(name="comparison_period", domain_type="period", required=True),
            Parameter(name="dimension", domain_type="dimension_reference", required=True),
            Parameter(
                name="coverage_threshold",
                domain_type="threshold_value",
                required=False,
                default="por defecto del objetivo",
            ),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions="Metrica y dimension combinables; dimension con cardinalidad manejable",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con la dimension como agrupacion",
        calculation=(
            "Variacion por elemento, contribucion sobre la variacion total, orden "
            "descendente por magnitud de contribucion, corte por contribucion acumulada"
        ),
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts=(
            "main_contributor (uno por elemento sobre el corte), explained_coverage, "
            "dimension_cardinality"
        ),
        rejection_conditions=(
            "excessive_cardinality (dimension con demasiados elementos distintos), "
            "zero_variance (no hay nada que descomponer)"
        ),
        cost=1,
        verification=(
            "Conjunto fijo con contribuciones conocidas; comprobar suma de contribuciones = 100 %"
        ),
        reusable="Si, si el conjunto activo contiene la dimension como columna",
    ),
    OperationCard(
        name=OperationName.RANK,
        purpose="Ordenar elementos de una dimension por una metrica",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="dimension", domain_type="dimension_reference", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(name="n", domain_type="integer", required=False, default="10"),
            Parameter(
                name="direction",
                domain_type="sort_direction",
                required=False,
                default="descending",
            ),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions="Metrica y dimension combinables",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con orden y limite en la fuente",
        calculation="Ninguno adicional: el orden lo resuelve la fuente",
        products="Hechos, resultado analitico, conjunto de datos (siempre se materializa, seccion 5)",
        published_facts="ranking_element x n, universe_total, universe_scope",
        rejection_conditions="excessive_n",
        cost=1,
        verification="Conjunto fijo con orden conocido; comprobar empates y estabilidad del orden",
        reusable="Si, si el conjunto activo contiene la dimension y la metrica",
    ),
    OperationCard(
        name=OperationName.QUERY_METRIC,
        purpose="Valor de una metrica en un alcance",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions="Metrica existente",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, sin agrupacion",
        calculation="Ninguno adicional: el valor lo resuelve la fuente",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="metric_value",
        rejection_conditions="Ninguna adicional a las genericas",
        cost=1,
        verification="Datos fijos de un periodo, comprobar el valor esperado",
        reusable="Si, si el conjunto activo cubre el periodo y la metrica",
    ),
    OperationCard(
        name=OperationName.BREAKDOWN,
        purpose="Una metrica abierta por los elementos de una dimension, sin ordenar ni comparar",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="dimension", domain_type="dimension_reference", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions="Metrica y dimension combinables",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con la dimension como agrupacion",
        calculation="Ninguno adicional: la apertura la resuelve la fuente",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="value_per_element x n, dimension_cardinality, universe_scope",
        rejection_conditions=(
            "Ninguna propia. No comparte excessive_cardinality con decompose_variance: "
            "queda sujeta a los limites generales de filas y materializacion (seccion 5)"
        ),
        cost=1,
        verification=(
            "Conjunto fijo con valores conocidos por elemento; comprobar que la suma "
            "coincide con el total"
        ),
        reusable="Si, si el conjunto activo contiene la dimension y la metrica",
    ),
    OperationCard(
        name=OperationName.TIME_SERIES,
        purpose="Evolucion de una metrica por granularidad",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(name="granularity", domain_type="granularity", required=True),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions=(
            "Metrica existente, con campo temporal disponible para la granularidad pedida"
        ),
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con la granularidad pedida",
        calculation="Ninguno adicional: la serie la resuelve la fuente",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="series_point x n",
        rejection_conditions="Ninguna adicional a las genericas",
        cost=1,
        verification="Serie fija con puntos conocidos; comprobar granularidad y orden temporal",
        reusable="Si, si el conjunto activo cubre el periodo con igual o mayor granularidad",
    ),
    OperationCard(
        name=OperationName.COUNT,
        purpose="Cardinalidad de un universo bajo filtros",
        parameters=(Parameter(name="filters", domain_type="filter_list", required=False),),
        semantic_preconditions="Filtros expresables en vocabulario canonico, si existen",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, sin metrica ni agrupacion, solo conteo",
        calculation="Ninguno adicional",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="count",
        rejection_conditions="Ninguna adicional a las genericas",
        cost=1,
        verification="Universo fijo con conteo conocido",
        reusable="Si, si el conjunto activo cubre el mismo universo y filtros",
    ),
    OperationCard(
        name=OperationName.DESCRIBE_DATASET,
        purpose="Conteo, columnas y vista previa determinista y acotada de un universo",
        parameters=(Parameter(name="filters", domain_type="filter_list", required=False),),
        semantic_preconditions="Ninguna mas alla del universo autorizado",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, sin agrupacion, con vista previa determinista y acotada",
        calculation="Ninguno adicional",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="count, available_columns",
        rejection_conditions="Ninguna adicional a las genericas",
        cost=1,
        verification=(
            "Universo fijo; comprobar conteo, columnas disponibles, y que la vista previa "
            "es determinista y acotada -- no se exige representatividad estadistica, "
            "ninguna inferencia numerica se apoya en ella"
        ),
        reusable="Si, si el conjunto activo cubre el mismo universo",
    ),
    OperationCard(
        name=OperationName.DETECT_ANOMALY,
        purpose="Puntos fuera del comportamiento esperado de una serie",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(
                name="sensitivity",
                domain_type="threshold_value",
                required=False,
                default="valor configurado del objetivo",
            ),
        ),
        semantic_preconditions="Metrica existente, con serie temporal disponible",
        universe_requirement=UniverseRequirement.AUTHORIZED,
        data_requests="Una, con granularidad de serie",
        calculation=(
            "Aplica a la serie completa del periodo un criterio de anomalia configurado "
            "externamente y declara el criterio aplicado. El metodo concreto que implementa "
            "ese criterio es el punto abierto 3 de la seccion 12 y no se fija en este bloque"
        ),
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="anomalous_point x n, applied_criterion",
        rejection_conditions=(
            "Ninguna propia definida en este bloque. Las causas especificas dependientes "
            "del metodo se incorporaran cuando se resuelva el punto abierto 3"
        ),
        cost=1,
        verification=(
            "Con una implementacion de prueba determinista del criterio (un doble de "
            "prueba, no un metodo estadistico real): comprobar que la operacion aplica el "
            "criterio recibido a toda la serie, marca los puntos que ese criterio senala y "
            "publica applied_criterion con el criterio efectivamente usado"
        ),
        reusable="Si, si el conjunto activo cubre el periodo con la granularidad de la serie",
    ),
    OperationCard(
        name=OperationName.CALCULATE_SHARE,
        purpose="Peso de un elemento sobre un total",
        parameters=(
            Parameter(name="metric", domain_type="metric_reference", required=True),
            Parameter(name="dimension", domain_type="dimension_reference", required=True),
            Parameter(name="element", domain_type="dimension_value", required=True),
            Parameter(name="period", domain_type="period", required=True),
            Parameter(name="filters", domain_type="filter_list", required=False),
        ),
        semantic_preconditions="Metrica y dimension combinables; universo completo autorizado para el denominador",
        universe_requirement=UniverseRequirement.COMPLETE,
        data_requests=(
            "Dos: la del numerador aplica filters mas el filtro puntual dimension = "
            "element; la del denominador aplica solo filters, agregado sobre todo el "
            "universo completo de dimension (sin la restriccion de element). Ambas bajo "
            "captura compatible o comun"
        ),
        calculation="Participacion del elemento sobre el total del universo completo",
        products="Hechos, resultado analitico, conjunto de datos",
        published_facts="share, universe_total",
        rejection_conditions="insufficient_universe (causa generica de la seccion 7; no se define una nueva)",
        cost=2,
        verification=(
            "Con datos fijos, comprobar exactamente share = numerator / universe_total, "
            "que el denominador corresponde al universo completo autorizado, que los "
            "filtros generales se aplican a ambos lados, que dimension = element solo se "
            "aplica al numerador y que numerador y denominador provienen de captura compatible"
        ),
        reusable="Si, si el conjunto activo cubre el universo completo con la dimension y la metrica",
    ),
)
