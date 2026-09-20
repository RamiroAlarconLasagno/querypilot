# src/querypilot/business_knowledge/artifact_validator.py
"""Las 8 comprobaciones de integridad de 06_parte_conocimiento_negocio.md
seccion 6. "Un artefacto que no valida no se publica": por eso cada
comprobacion devuelve sus hallazgos como valor de retorno (nunca una
excepcion), siguiendo 16_instrucciones_ia.md seccion 7.
"""

from __future__ import annotations

from dataclasses import dataclass

from querypilot.business_knowledge.semantic_artifact import (
    Dimension,
    Metric,
    SemanticArtifact,
)


@dataclass(frozen=True)
class ArtifactValidationIssue:
    check: str
    detail: str


def _source_tables_from_relation(relation: str) -> tuple[str, str] | None:
    """Extrae las dos tablas de una expresion 'tabla.col = tabla.col'.

    Devuelve None si la expresion no tiene la forma esperada: eso no es una
    ambiguedad de camino, es un dato mal formado que otra comprobacion (o
    Pydantic) ya deberia haber atrapado antes de llegar aqui.
    """
    sides = relation.split("=")
    if len(sides) != 2:
        return None
    tables: list[str] = []
    for side in sides:
        column_ref = side.strip()
        if "." not in column_ref:
            return None
        table, _, _ = column_ref.rpartition(".")
        tables.append(table)
    return tables[0], tables[1]


def check_metrics_have_complete_physical_mapping(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    issues: list[ArtifactValidationIssue] = []
    for metric in artifact.metrics:
        missing = [
            field
            for field, value in (
                ("source", metric.physical.source),
                ("measure", metric.physical.measure),
                ("temporal_field", metric.physical.temporal_field),
            )
            if not value.strip()
        ]
        if missing:
            issues.append(
                ArtifactValidationIssue(
                    check="metrics_have_complete_physical_mapping",
                    detail=f"{metric.id}: falta {', '.join(missing)}",
                )
            )
    return issues


def check_combinable_dimensions_exist(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    known_dimension_ids = {dimension.id for dimension in artifact.dimensions}
    issues: list[ArtifactValidationIssue] = []
    for metric in artifact.metrics:
        for dimension_id in metric.combinable_dimensions:
            if dimension_id not in known_dimension_ids:
                issues.append(
                    ArtifactValidationIssue(
                        check="combinable_dimensions_exist",
                        detail=f"{metric.id}: dimension '{dimension_id}' no existe",
                    )
                )
    return issues


def check_min_granularity_has_temporal_field(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    issues: list[ArtifactValidationIssue] = []
    for metric in artifact.metrics:
        if not metric.physical.temporal_field.strip():
            issues.append(
                ArtifactValidationIssue(
                    check="min_granularity_has_temporal_field",
                    detail=(
                        f"{metric.id}: declara min_granularity={metric.min_granularity} "
                        "sin temporal_field"
                    ),
                )
            )
    return issues


def check_aggregations_are_from_closed_catalog(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    """Siempre vacia: Aggregation es un StrEnum, Pydantic ya rechazo cualquier
    valor fuera del catalogo cerrado al cargar el YAML. Existe como funcion
    para que las 8 comprobaciones de 06 seccion 6 tengan una contraparte
    explicita aca, documentando donde se hizo cumplir cada una.
    """
    del artifact
    return []


def check_synonyms_do_not_collide(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    owners_by_synonym: dict[str, set[str]] = {}
    concepts: list[Metric | Dimension] = [*artifact.metrics, *artifact.dimensions]
    for concept in concepts:
        for synonym in concept.synonyms:
            owners_by_synonym.setdefault(synonym, set()).add(concept.id)

    issues: list[ArtifactValidationIssue] = []
    for synonym, owners in owners_by_synonym.items():
        if len(owners) > 1:
            issues.append(
                ArtifactValidationIssue(
                    check="synonyms_do_not_collide",
                    detail=f"'{synonym}' pertenece a {sorted(owners)}",
                )
            )
    return issues


def check_default_sense_points_to_existing_concept(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    issues: list[ArtifactValidationIssue] = []
    for metric in artifact.metrics:
        for word in metric.default_sense_of or []:
            if word not in metric.synonyms:
                issues.append(
                    ArtifactValidationIssue(
                        check="default_sense_points_to_existing_concept",
                        detail=(
                            f"{metric.id}: default_sense_of '{word}' no esta en "
                            "sus propios synonyms"
                        ),
                    )
                )
    return issues


def check_source_relations_have_no_path_ambiguity(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    relations_by_source_pair: dict[frozenset[str], set[str]] = {}

    for metric in artifact.metrics:
        for relation in metric.physical.relations or []:
            pair = frozenset({relation.from_, relation.to})
            relations_by_source_pair.setdefault(pair, set()).add(relation.condition)

    for dimension in artifact.dimensions:
        tables = _source_tables_from_relation(dimension.physical.relation)
        if tables is None:
            continue
        pair = frozenset(tables)
        relations_by_source_pair.setdefault(pair, set()).add(dimension.physical.relation)

    issues: list[ArtifactValidationIssue] = []
    for pair, declared_relations in relations_by_source_pair.items():
        if len(declared_relations) > 1:
            issues.append(
                ArtifactValidationIssue(
                    check="source_relations_have_no_path_ambiguity",
                    detail=f"{sorted(pair)}: {sorted(declared_relations)}",
                )
            )
    return issues


def check_thresholds_are_coherent(
    artifact: SemanticArtifact,
) -> list[ArtifactValidationIssue]:
    thresholds = artifact.connection.thresholds
    if not (thresholds.context_rows < thresholds.preview_rows < thresholds.materialization_rows):
        return [
            ArtifactValidationIssue(
                check="thresholds_are_coherent",
                detail=(
                    f"context_rows={thresholds.context_rows}, "
                    f"preview_rows={thresholds.preview_rows}, "
                    f"materialization_rows={thresholds.materialization_rows}"
                ),
            )
        ]
    return []


def validate_artifact(artifact: SemanticArtifact) -> list[ArtifactValidationIssue]:
    checks = (
        check_metrics_have_complete_physical_mapping,
        check_combinable_dimensions_exist,
        check_min_granularity_has_temporal_field,
        check_aggregations_are_from_closed_catalog,
        check_synonyms_do_not_collide,
        check_default_sense_points_to_existing_concept,
        check_source_relations_have_no_path_ambiguity,
        check_thresholds_are_coherent,
    )
    return [issue for check in checks for issue in check(artifact)]
