# src/querypilot/interpretation/evaluation_runner.py
"""Corre el banco de casos contra Interpretacion y arma el reporte de
metricas. 07_parte_interpretacion.md seccion 10.

Provider-agnostico: recibe cualquier `ModelPort`. Con `DeterministicModelPort`
sirve para probar el mecanismo (carga, reintento, clasificacion, agregacion)
sin modelo real -- lo que corre en CI. La corrida real contra el banco de 60
casos, con un proveedor real, es bloque 1.8
(`02_vision_arquitectura.md` seccion 10).

Reintento (B1+B2): solo se reintenta un primer intento `Rejected` -- pasando
`retry_cause` con el primer rechazo a un segundo llamado a
`run_interpretation`. Una `NeedsClarification` (ambiguedad o fuera de
alcance) no se reintenta: no es lo que `retry_cause` esta pensado para
resolver, y una segunda pregunta al modelo sobre lo mismo no es un reintento
legitimo del punto de vista del turno.

Estado analitico para `continuation`: el banco no corre una conversacion real
de varios turnos, asi que el estado previo se sintetiza a partir de lo que el
propio caso declara como heredable (`expected.objectives[0]`) -- es
exactamente lo que ese objetivo espera encontrar ya vigente. Decision local,
documentada aca porque condiciona como se interpretan los resultados de esa
categoria.
"""

from __future__ import annotations

from querypilot.analytics.objective_catalog import ObjectiveCard
from querypilot.analytics.operation_catalog import OperationCard
from querypilot.business_knowledge.evaluation_cases import (
    CaseCategory,
    EvaluationCase,
    ExpectedPlan,
)
from querypilot.business_knowledge.semantic_artifact import SemanticArtifact
from querypilot.canonical_language.shared_values import AnalyticalState
from querypilot.interpretation.case_comparator import CaseVerdict, classify_case
from querypilot.interpretation.evaluation_metrics import EvaluationReport, build_report
from querypilot.interpretation.service import InterpretationOutcome, Rejected, run_interpretation
from querypilot.model_port.port import ModelPort


def _synthesize_state(case: EvaluationCase, semantic_version: str) -> AnalyticalState | None:
    if case.category is not CaseCategory.CONTINUATION:
        return None
    expected = case.expected
    assert isinstance(expected, ExpectedPlan)
    first = expected.objectives[0]
    period = ", ".join(first.temporal) if first.temporal else "periodo previo"
    return AnalyticalState(
        period=period,
        metric=first.metric,
        dimension=first.dimension,
        semantic_version=semantic_version,
    )


async def _run_case(
    model_port: ModelPort,
    case: EvaluationCase,
    prompt_version: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    semantic_version: str,
) -> tuple[InterpretationOutcome, InterpretationOutcome | None]:
    analytical_state = _synthesize_state(case, semantic_version)
    conversation_history = (case.previous_context,) if case.previous_context else ()

    first = await run_interpretation(
        model_port=model_port,
        prompt_version=prompt_version,
        question=case.question,
        objective_catalog=objective_catalog,
        operation_catalog=operation_catalog,
        artifact=artifact,
        analytical_state=analytical_state,
        conversation_history=conversation_history,
        turn_id=f"eval_{case.id}",
        plan_id=f"eval_{case.id}_plan",
    )
    if not isinstance(first, Rejected):
        return first, None

    retry = await run_interpretation(
        model_port=model_port,
        prompt_version=prompt_version,
        question=case.question,
        objective_catalog=objective_catalog,
        operation_catalog=operation_catalog,
        artifact=artifact,
        analytical_state=analytical_state,
        conversation_history=conversation_history,
        turn_id=f"eval_{case.id}",
        plan_id=f"eval_{case.id}_plan_retry",
        retry_cause=first.rejections[0],
    )
    return first, retry


async def run_bank_evaluation(
    model_port: ModelPort,
    cases: tuple[EvaluationCase, ...],
    prompt_version: str,
    objective_catalog: tuple[ObjectiveCard, ...],
    operation_catalog: tuple[OperationCard, ...],
    artifact: SemanticArtifact,
    semantic_version: str,
) -> EvaluationReport:
    verdicts: list[CaseVerdict] = []
    for case in cases:
        first, retry = await _run_case(
            model_port,
            case,
            prompt_version,
            objective_catalog,
            operation_catalog,
            artifact,
            semantic_version,
        )
        verdicts.append(classify_case(case, first, retry))

    return build_report(
        tuple(verdicts), semantic_version=semantic_version, prompt_version=prompt_version
    )
