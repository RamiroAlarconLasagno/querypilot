# tests/model_port/unit/test_structured_output.py
"""InterpretationOutput y SynthesisOutput: 14_contratos_formato.md seccion 8.
Fixtures completas que ejercitan todos los subtipos, mas guardas de regresion
sobre las tres decisiones de esta ronda: AnswerSection sin status, sin id en
ResearchSuggestion, cross_objective como tipo separado de Assertion.
"""

from __future__ import annotations

from decimal import Decimal

from querypilot.analytics.objective_catalog import ObjectiveName
from querypilot.analytics.operation_catalog import OperationName
from querypilot.canonical_language.shared_values import (
    Binding,
    Condition,
    ConditionOperator,
    FilterOperator,
    Granularity,
    SortDirection,
    ThresholdName,
)
from querypilot.model_port.structured_output import (
    AnswerSection,
    Assertion,
    AssertionKind,
    ConceptMapping,
    Continuity,
    ContinuityMode,
    CrossObjectiveAssertion,
    InheritedField,
    InterpretationOutput,
    MaterialAmbiguity,
    ObjectiveDependency,
    ObjectiveProposal,
    OutOfScope,
    ProposedPlanStep,
    ResearchSuggestion,
    ResolvedReference,
    SynthesisOutput,
)


def _interpretation_output() -> InterpretationOutput:
    p1 = ObjectiveProposal(
        proposal_id="p1",
        objective=ObjectiveName.EXPLAIN_VARIANCE,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=()),
        concepts=(ConceptMapping(canonical="net_revenue", original_expression="facturacion"),),
        time_expressions=("julio", "junio"),
        filters=(),
        premises=("existe una caida entre ambos periodos",),
        references=(),
        ambiguities=(),
        plan=(
            ProposedPlanStep(
                step_id="s1",
                operation=OperationName.COMPARE_PERIODS,
                arguments={
                    "metric": "net_revenue",
                    "current_period": "julio",
                    "comparison_period": "junio",
                },
                condition=None,
                derives_from=(),
            ),
            ProposedPlanStep(
                step_id="s2",
                operation=OperationName.DECOMPOSE_VARIANCE,
                arguments={
                    "metric": "net_revenue",
                    "current_period": "julio",
                    "comparison_period": "junio",
                    "dimension": "customer",
                },
                condition=Condition(
                    fact_type="relative_variance",
                    operator=ConditionOperator.LT,
                    value=Decimal(0),
                ),
                derives_from=("s1",),
            ),
        ),
        dependency=None,
    )
    p2 = ObjectiveProposal(
        proposal_id="p2",
        objective=ObjectiveName.RANK,
        continuity=Continuity(mode=ContinuityMode.NEW, inherits=(InheritedField.METRIC,)),
        concepts=(ConceptMapping(canonical="customer", original_expression="clientes"),),
        time_expressions=("el ano actual",),
        filters=(),
        premises=(),
        references=(
            ResolvedReference(
                expression="esos tres",
                resolution="los tres contribuyentes principales del turno anterior",
            ),
        ),
        ambiguities=(
            MaterialAmbiguity(
                description='criterio de "mejores"',
                options=("facturacion neta", "unidades vendidas"),
            ),
        ),
        plan=(
            ProposedPlanStep(
                step_id="s1",
                operation=OperationName.RANK,
                arguments={
                    "metric": "net_revenue",
                    "dimension": "customer",
                    "period": "el ano actual",
                    "n": 10,
                    "direction": SortDirection.DESCENDING,
                    "granularity": Granularity.MONTH,
                },
                condition=None,
                derives_from=(),
            ),
        ),
        dependency=ObjectiveDependency(
            source_proposal_id="p1",
            binding=Binding(
                source_fact_type="main_contributor",
                target_dimension="customer",
                operator=FilterOperator.NOT_IN,
            ),
        ),
    )
    return InterpretationOutput(
        objective_proposals=(p1, p2),
        out_of_scope=(
            OutOfScope(
                reason="requiere proyeccion y criterio de negocio, no analisis de datos existentes",
                alternatives=("facturacion por region", "ranking de clientes por region"),
            ),
        ),
        prompt_version="interpretation_v1",
    )


def _synthesis_output() -> SynthesisOutput:
    return SynthesisOutput(
        sections=(
            AnswerSection(
                objective_id="obj_1",
                assertions=(
                    Assertion(
                        id="a1",
                        objective_id="obj_1",
                        turn_id="t_1",
                        kind=AssertionKind.DATA,
                        text="La facturacion cayo 13,2 % respecto de junio.",
                        evidence=("h1", "h2"),
                    ),
                    Assertion(
                        id="a2",
                        objective_id="obj_1",
                        turn_id="t_1",
                        kind=AssertionKind.HYPOTHESIS,
                        text="Podria responder a un cambio puntual en pocas cuentas.",
                        evidence=(),
                    ),
                ),
            ),
        ),
        cross_objective=CrossObjectiveAssertion(
            turn_id="t_1",
            objective_ids=("obj_1", "obj_2"),
            kind=AssertionKind.INTERPRETATION,
            text="Los mismos clientes explican la caida y encabezan el ranking anual.",
            evidence=("h1", "h9"),
        ),
        suggestions=(
            ResearchSuggestion(question="¿Esos mismos clientes explican caidas en otros periodos?"),
        ),
        prompt_version="synthesis_v1",
    )


def test_interpretation_output_round_trips_through_json() -> None:
    output = _interpretation_output()
    restored = InterpretationOutput.model_validate_json(output.model_dump_json())
    assert restored == output


def test_synthesis_output_round_trips_through_json() -> None:
    output = _synthesis_output()
    restored = SynthesisOutput.model_validate_json(output.model_dump_json())
    assert restored == output


def test_objective_dependency_references_another_proposal_by_local_id() -> None:
    output = _interpretation_output()
    dependent = output.objective_proposals[1]
    assert dependent.dependency is not None
    assert dependent.dependency.source_proposal_id == "p1"


def test_domain_value_accepts_the_closed_set_of_concrete_types() -> None:
    step = ProposedPlanStep(
        step_id="s1",
        operation=OperationName.RANK,
        arguments={
            "dimension": "customer",
            "n": 10,
            "granularity": Granularity.MONTH,
            "direction": SortDirection.DESCENDING,
        },
        derives_from=(),
    )
    assert step.arguments["dimension"] == "customer"
    assert step.arguments["n"] == 10
    assert step.arguments["granularity"] == Granularity.MONTH
    assert step.arguments["direction"] == SortDirection.DESCENDING


def test_condition_value_accepts_decimal_or_threshold_name() -> None:
    literal = Condition(
        fact_type="relative_variance", operator=ConditionOperator.LT, value=Decimal(0)
    )
    threshold = Condition(
        fact_type="explained_coverage",
        operator=ConditionOperator.GTE,
        value=ThresholdName.MIN_EXPLANATION_COVERAGE,
    )
    assert literal.value == Decimal(0)
    assert threshold.value == ThresholdName.MIN_EXPLANATION_COVERAGE


def test_cross_objective_assertion_is_not_an_assertion() -> None:
    """CrossObjectiveAssertion y Assertion son tipos separados (14_contratos_formato.md
    seccion 8): no hay herencia ni union entre ellos. mypy ya lo demuestra en tiempo
    de tipado -- ninguna subclase podria satisfacer ambos a la vez -- esto lo
    confirma en tiempo de ejecucion sobre una instancia real.
    """
    output = _synthesis_output()
    assert output.cross_objective is not None
    assert type(output.cross_objective) is CrossObjectiveAssertion
    assert len(output.cross_objective.objective_ids) == 2


def test_research_suggestion_has_no_identifier_field() -> None:
    assert set(ResearchSuggestion.model_fields) == {"question"}


def test_answer_section_has_no_status_field() -> None:
    assert set(AnswerSection.model_fields) == {"objective_id", "assertions"}


def test_synthesis_output_has_no_scope_field() -> None:
    assert "scope" not in SynthesisOutput.model_fields
    assert "status" not in SynthesisOutput.model_fields
