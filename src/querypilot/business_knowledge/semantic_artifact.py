# src/querypilot/business_knowledge/semantic_artifact.py
"""Modelos Pydantic del artefacto semantico y su carga desde YAML.

06_parte_conocimiento_negocio.md seccion 2: el artefacto tiene dos caras que
se versionan juntas -- el modelo semantico (que significa un concepto) y el
mapeo fisico (de donde se obtiene). Este modulo solo carga y tipa; la
integridad se comprueba en artifact_validator.py.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CalendarType(StrEnum):
    CALENDAR = "calendar"
    FISCAL = "fiscal"


class Aggregation(StrEnum):
    SUM = "sum"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    AVERAGE = "average"


class Granularity(StrEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"
    TOTAL = "total"


class Calendar(BaseModel):
    type: CalendarType
    closing_month: int
    week_start: str


class Thresholds(BaseModel):
    context_rows: int
    preview_rows: int
    preview_columns: int
    materialization_rows: int
    active_datasets_per_session: int
    active_datasets_mb: int
    decompose_variance_max_dimension_cardinality: int
    min_explanation_coverage: Decimal
    closed_period_freshness_hours: int
    open_period_freshness_minutes: int
    query_time_limit_seconds: int
    turn_budget_seconds: int
    model_calls_budget: int
    rows_examined_to_confirm: int


class SensitivityRule(BaseModel):
    concept: str
    condition: str


class Connection(BaseModel):
    id: str
    description: str
    engine: str
    calendar: Calendar
    thresholds: Thresholds
    sensitivity: list[SensitivityRule]


class DimensionPhysical(BaseModel):
    source: str
    attribute: str
    key: str
    relation: str
    permanent_filter: str | None = None


class Dimension(BaseModel):
    id: str
    business_name: str
    synonyms: list[str]
    expected_cardinality: int
    hierarchy: list[str] | None = None
    physical: DimensionPhysical


class MetricRelation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: str = Field(alias="from")
    to: str
    condition: str


class MetricPhysical(BaseModel):
    source: str
    measure: str
    relations: list[MetricRelation] | None = None
    temporal_field: str
    exclusions: list[str] | None = None


class Metric(BaseModel):
    id: str
    business_name: str
    definition: str
    synonyms: list[str]
    default_sense_of: list[str] | None = None
    unit: str
    aggregations: list[Aggregation]
    combinable_dimensions: list[str]
    min_granularity: Granularity
    sensitive: bool = False
    physical: MetricPhysical


class DimensionsFile(BaseModel):
    dimensions: list[Dimension]


class MetricsFile(BaseModel):
    metrics: list[Metric]


class SemanticArtifact(BaseModel):
    connection: Connection
    dimensions: list[Dimension]
    metrics: list[Metric]


def load_semantic_artifact(directory: Path) -> SemanticArtifact:
    """Carga connection.yaml, dimensions.yaml y metrics.yaml desde directory.

    evaluation/cases.yaml no se carga aqui: pertenece al bloque 1.7.
    """
    connection = Connection.model_validate(
        yaml.safe_load((directory / "connection.yaml").read_text(encoding="utf-8"))
    )
    dimensions_file = DimensionsFile.model_validate(
        yaml.safe_load((directory / "dimensions.yaml").read_text(encoding="utf-8"))
    )
    metrics_file = MetricsFile.model_validate(
        yaml.safe_load((directory / "metrics.yaml").read_text(encoding="utf-8"))
    )
    return SemanticArtifact(
        connection=connection,
        dimensions=dimensions_file.dimensions,
        metrics=metrics_file.metrics,
    )


def derive_semantic_version(artifact: SemanticArtifact) -> str:
    """Version derivada del contenido, nunca escrita a mano (13 seccion 7).

    Hash del contenido serializado: mismo artefacto, misma version; un
    cambio de una sola sinonimo cambia la version. model_dump_json() usa el
    orden de declaracion de los campos del modelo, que es estable entre
    corridas para un mismo shape de modelo.
    """
    content = artifact.model_dump_json().encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    return f"sem_v{digest[:12]}"
