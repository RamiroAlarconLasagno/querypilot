# tests/interpretation/evaluation/test_evaluation_runner.py
"""run_bank_evaluation extremo a extremo, con un doble del modelo enrutado
por pregunta (no `DeterministicModelPort`, que solo puede devolver una salida
fija -- el banco real necesita una respuesta distinta por pregunta, y eso es
justamente lo que un proveedor real hace en el bloque 1.8). Este doble sigue
siendo 100% determinista: no hay modelo real ni clave de por medio.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.analytics.objective_catalog import OBJECTIVE_CATALOG
from querypilot.analytics.operation_catalog import OPERATION_CATALOG
from querypilot.business_knowledge.evaluation_cases import (
    CaseCategory,
    EvaluationCase,
    ExpectedAmbiguity,
    ExpectedObjective,
    ExpectedOutOfScope,
    ExpectedPlan,
)
from querypilot.business_knowledge.semantic_artifact import (
    Calendar,
    CalendarType,
    Connection,
    Metric,
    MetricPhysical,
    SemanticArtifact,
    Thresholds,
)
from querypilot.canonical_language.shared_values import (
    Binding,
    FilterOperator,
    Granularity,
    ObjectiveName,
)
from querypilot.interpretation.evaluation_metrics import MetricValue
from querypilot.interpretation.evaluation_runner import run_bank_evaluation
from querypilot.model_port.structured_output import (
    ConceptMapping,
    Continuity,
    ContinuityMode,
    InheritedField,
    InterpretationOutput,
    MaterialAmbiguity,
    ObjectiveDependency,
    ObjectiveProposal,
    OutOfScope,
    ProposedPlanStep,
    SynthesisOutput,
)


class _RoutedModelPort:
    """Enruta por pregunta (buscada dentro del user_prompt) y consume las
    respuestas configuradas en orden -- la segunda es la del reintento.
    """

    def __init__(self, responses: dict[str, list[InterpretationOutput]]) -> None:
        self._responses = {question: list(outputs) for question, outputs in responses.items()}

    async def interpret(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> InterpretationOutput:
        for question, queue in self._responses.items():
            if question in user_prompt:
                output = queue.pop(0)
                return output.model_copy(update={"prompt_version": prompt_version})
        raise AssertionError(f"sin respuesta configurada para: {user_prompt[:200]!r}")

    async def synthesize(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> SynthesisOutput:
        raise NotImplementedError


def _artifact() -> SemanticArtifact:
    thresholds = Thresholds(
        context_rows=20,
        preview_rows=100,
        preview_columns=20,
        materialization_rows=50000,
        active_datasets_per_session=5,
        active_datasets_mb=50,
        decompose_variance_max_dimension_cardinality=5000,
        min_explanation_coverage=Decimal("0.70"),
        closed_period_freshness_hours=24,
        open_period_freshness_minutes=15,
        query_time_limit_seconds=30,
        turn_budget_seconds=90,
        model_calls_budget=5,
        rows_examined_to_confirm=1_000_000,
    )
    connection = Connection(
        id="demo",
        description="Conexion de prueba.",
        engine="postgresql",
        calendar=Calendar(type=CalendarType.CALENDAR, closing_month=12, week_start="monday"),
        thresholds=thresholds,
        sensitivity=[],
    )
    metric = Metric(
        id="net_revenue",
        business_name="Facturacion",
        definition="Definicion de prueba.",
        synonyms=["ventas"],
        unit="ARS",
        aggregations=[],
        combinable_dimensions=[],
        min_granularity=Granularity.DAY,
        physical=MetricPhysical(source="cmp_cab", measure="sum(x)", temporal_field="cmp_cab.f"),
    )
    return SemanticArtifact(connection=connection, dimensions=[], metrics=[metric])


def _proposal(
    proposal_id: str,
    objective: ObjectiveName,
    temporal: tuple[str, ...] = (),
    premises: tuple[str, ...] = (),
    continuity: Continuity | None = None,
    dependency: ObjectiveDependency | None = None,
    plan: tuple[ProposedPlanStep, ...] = (),
) -> ObjectiveProposal:
    return ObjectiveProposal(
        proposal_id=proposal_id,
        objective=objective,
        continuity=continuity or Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(ConceptMapping(canonical="net_revenue", original_expression="facturacion"),),
        time_expressions=temporal,
        filters=(),
        premises=premises,
        references=(),
        ambiguities=(),
        plan=plan,
        dependency=dependency,
    )


def _step(bogus: bool = False) -> ProposedPlanStep:
    arguments: dict[str, object] = {"metric": "net_revenue", "period": "julio"}
    if bogus:
        arguments["bogus"] = "x"
    return ProposedPlanStep(
        step_id="s1", operation="query_metric", arguments=arguments, derives_from=()
    )


async def test_run_bank_evaluation_end_to_end_with_a_routed_double() -> None:
    direct = EvaluationCase(
        id="direct",
        category=CaseCategory.DIRECT,
        question="Q_DIRECT",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",)
                ),
            )
        ),
    )
    retry = EvaluationCase(
        id="retry",
        category=CaseCategory.DIRECT,
        question="Q_RETRY",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",)
                ),
            )
        ),
    )
    premise = EvaluationCase(
        id="premise",
        category=CaseCategory.PREMISE,
        question="Q_PREMISE",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.QUERY_METRIC,
                    metric="net_revenue",
                    temporal=("julio",),
                    premises=("existe una caida",),
                ),
            )
        ),
    )
    continuation = EvaluationCase(
        id="continuation",
        category=CaseCategory.CONTINUATION,
        question="Q_CONTINUATION",
        previous_context="Facturacion de julio.",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(objective=ObjectiveName.QUERY_METRIC, metric="net_revenue"),
            ),
            inherits=(InheritedField.METRIC,),
        ),
    )
    multi = EvaluationCase(
        id="multi",
        category=CaseCategory.MULTIPLE_OBJECTIVES,
        question="Q_MULTI",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.COMPARE,
                    metric="net_revenue",
                    temporal=("julio", "junio"),
                ),
                ExpectedObjective(
                    objective=ObjectiveName.COMPARE,
                    metric="net_revenue",
                    temporal=("julio", "junio"),
                    depends_on_previous=True,
                ),
            )
        ),
    )
    ambiguity = EvaluationCase(
        id="ambiguity",
        category=CaseCategory.MATERIAL_AMBIGUITY,
        question="Q_AMBIG",
        expected=ExpectedAmbiguity(description='criterio de "mejores"'),
    )
    out_of_scope = EvaluationCase(
        id="out_of_scope",
        category=CaseCategory.OUT_OF_SCOPE,
        question="Q_OOS",
        expected=ExpectedOutOfScope(reason="requiere proyeccion"),
    )

    compare_step = ProposedPlanStep(
        step_id="s1",
        operation="compare_periods",
        arguments={
            "metric": "net_revenue",
            "current_period": "julio",
            "comparison_period": "junio",
        },
        derives_from=(),
    )
    binding = Binding(
        source_fact_type="main_contributor",
        target_dimension="customer",
        operator=FilterOperator.NOT_IN,
    )

    responses: dict[str, list[InterpretationOutput]] = {
        "Q_DIRECT": [
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1", ObjectiveName.QUERY_METRIC, temporal=("julio",), plan=(_step(),)
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            )
        ],
        "Q_RETRY": [
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1",
                        ObjectiveName.QUERY_METRIC,
                        temporal=("julio",),
                        plan=(_step(bogus=True),),
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            ),
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1", ObjectiveName.QUERY_METRIC, temporal=("julio",), plan=(_step(),)
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            ),
        ],
        "Q_PREMISE": [
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1",
                        ObjectiveName.QUERY_METRIC,
                        temporal=("julio",),
                        premises=("existe una caida",),
                        plan=(_step(),),
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            )
        ],
        "Q_CONTINUATION": [
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1",
                        ObjectiveName.QUERY_METRIC,
                        temporal=("junio",),
                        continuity=Continuity(
                            mode=ContinuityMode.CONTINUATION, inherits=(InheritedField.METRIC,)
                        ),
                        plan=(_step(),),
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            )
        ],
        "Q_MULTI": [
            InterpretationOutput(
                objective_proposals=(
                    _proposal(
                        "p1",
                        ObjectiveName.COMPARE,
                        temporal=("julio", "junio"),
                        plan=(compare_step,),
                    ),
                    _proposal(
                        "p2",
                        ObjectiveName.COMPARE,
                        temporal=("julio", "junio"),
                        plan=(compare_step,),
                        dependency=ObjectiveDependency(source_proposal_id="p1", binding=binding),
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            )
        ],
        "Q_AMBIG": [
            InterpretationOutput(
                objective_proposals=(
                    ObjectiveProposal(
                        proposal_id="p1",
                        objective=ObjectiveName.RANK,
                        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
                        concepts=(),
                        time_expressions=(),
                        filters=(),
                        premises=(),
                        references=(),
                        ambiguities=(
                            MaterialAmbiguity(description='criterio de "mejores"', options=()),
                        ),
                        plan=(),
                    ),
                ),
                out_of_scope=(),
                prompt_version="fixture",
            )
        ],
        "Q_OOS": [
            InterpretationOutput(
                objective_proposals=(),
                out_of_scope=(OutOfScope(reason="requiere proyeccion", alternatives=()),),
                prompt_version="fixture",
            )
        ],
    }

    model_port = _RoutedModelPort(responses)
    cases = (direct, retry, premise, continuation, multi, ambiguity, out_of_scope)

    report = await run_bank_evaluation(
        model_port=model_port,
        cases=cases,
        prompt_version="v1",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        semantic_version="test_version",
        provider="doble",
        model="fixture",
    )

    assert report.total_cases == 7
    assert report.evaluated_cases == 7
    assert report.operational_failures == 0
    assert report.semantic_version == "test_version"
    assert report.provider == "doble"
    assert report.model == "fixture"
    assert report.a1_correct_without_clarification.numerator == 4
    assert report.a1_correct_without_clarification.denominator == 5
    assert report.a2_silent_error.numerator == 0
    assert report.b1_valid_first_attempt.numerator == 4
    assert report.b1_valid_first_attempt.denominator == 5
    assert report.b1_plus_b2_valid_within_retry.numerator == 5
    assert report.b1_plus_b2_valid_within_retry.denominator == 5
    assert report.a4_false_out_of_scope.numerator == 0
    assert report.a4_false_out_of_scope.denominator == 6
    assert report.out_of_scope_accuracy.numerator == 1
    assert report.out_of_scope_accuracy.denominator == 1
    assert report.clarification_rate.numerator == 1
    assert report.clarification_rate.denominator == 7
    assert report.inheritance_accuracy.numerator == 1
    assert report.inheritance_accuracy.denominator == 1


class _FlakyModelPort:
    """Levanta una excepcion generica (falla operativa: timeout, limite de
    tasa, parseo) para una pregunta puntual; responde normal para el resto.
    """

    def __init__(self, failing_question: str, output: InterpretationOutput) -> None:
        self._failing_question = failing_question
        self._output = output

    async def interpret(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> InterpretationOutput:
        if self._failing_question in user_prompt:
            raise RuntimeError("timeout simulado")
        return self._output.model_copy(update={"prompt_version": prompt_version})

    async def synthesize(
        self, prompt_version: str, system_prompt: str, user_prompt: str
    ) -> SynthesisOutput:
        raise NotImplementedError


async def test_an_operational_failure_on_one_case_does_not_abort_the_rest_of_the_bank() -> None:
    ok_case = EvaluationCase(
        id="ok",
        category=CaseCategory.DIRECT,
        question="Q_OK",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(
                    objective=ObjectiveName.QUERY_METRIC, metric="net_revenue", temporal=("julio",)
                ),
            )
        ),
    )
    failing_case = EvaluationCase(
        id="fails",
        category=CaseCategory.DIRECT,
        question="Q_TIMEOUT",
        expected=ExpectedPlan(
            objectives=(
                ExpectedObjective(objective=ObjectiveName.QUERY_METRIC, metric="net_revenue"),
            )
        ),
    )
    output = InterpretationOutput(
        objective_proposals=(
            _proposal("p1", ObjectiveName.QUERY_METRIC, temporal=("julio",), plan=(_step(),)),
        ),
        out_of_scope=(),
        prompt_version="fixture",
    )
    model_port = _FlakyModelPort(failing_question="Q_TIMEOUT", output=output)

    report = await run_bank_evaluation(
        model_port=model_port,
        cases=(ok_case, failing_case),
        prompt_version="v1",
        objective_catalog=OBJECTIVE_CATALOG,
        operation_catalog=OPERATION_CATALOG,
        artifact=_artifact(),
        semantic_version="test_version",
        provider="openai",
        model="gpt-test",
    )

    assert report.total_cases == 2
    assert report.evaluated_cases == 1
    assert report.operational_failures == 1
    assert report.operational_failure_case_ids == ("fails",)
    assert report.a1_correct_without_clarification == MetricValue(numerator=1, denominator=1)
