<!-- docs/14_contratos_formato.md -->
<!-- Bloque 3 - Nivel de formato. Deriva de los contratos semanticos del Bloque 2. -->

# 14 — Contratos, nivel de formato

El Bloque 2 cerro **que informacion viaja**. Este documento cierra **como se codifica**.

> **Regla de herencia estricta.** Si un formato no puede transportar algo del contrato
> semantico, o necesita transportar algo que el contrato no preve, se detecto una
> violacion: se sube al contrato semantico y se revisa, **no se ajusta el formato en
> silencio**.

La seccion 11 registra el resultado de aplicar esa regla a los diez contratos.

---

## 1. Nomenclatura

Aplicacion de la convencion fijada en `16_instrucciones_ia.md` seccion 7: **ingles para
todo lo que el programa interpreta** -- nombres de campo, identificadores canonicos,
claves de YAML/JSON, valores de enumeracion, rutas de la API HTTP, nombres de evento --
y **espanol reservado para lo que lee una persona**.

| Concepto del diseno | Clase | Campos que siguen en espanol |
|---|---|---|
| Peticion de datos | `DataRequest` | Ninguno: `metrics` y `dimensions` llevan identificadores canonicos en ingles |
| Descriptor de cobertura | `CoverageDescriptor` | Ninguno |
| Hecho | `Fact` | Ninguno |
| Plan de analisis | `AnalysisPlan` | Ninguno |
| Contexto de acceso resuelto | `ResolvedAccessContext` | Ninguno |
| Respuesta | `Answer` | `Assertion.text`: prosa redactada para el usuario |
| Rechazo | `Rejection` | `detail`, cuando existe: mensaje para el usuario |
| Sugerencia de investigacion | `ResearchSuggestion` | La pregunta sugerida: se le presenta al usuario |

Una metrica se declara como `metric: "net_revenue"`, no como `metric: "facturacion_neta"`.
Sus sinonimos reconocidos si van en espanol, porque son lenguaje natural de entrada:
`synonyms: ["facturacion", "ventas netas"]`.

---

## 2. Tipos base

### Importes y magnitudes derivadas

| Ambito | Tipo |
|---|---|
| Modelo | `Decimal`. **Nunca `float`** para dinero ni para magnitudes derivadas |
| PostgreSQL | `NUMERIC` |
| Calculos derivados | Se mantienen en `Decimal` de punta a punta |
| Serializacion | Valor decimal exacto; el redondeo es **solo de presentacion** |
| Tests | Comparacion exacta, o contra una regla explicita de redondeo. Nunca tolerancias arbitrarias |

> **Porcentajes y contribuciones tambien son `Decimal`.** La propiedad "la suma de
> contribuciones da el 100 % de la variacion" se verifica **antes** del redondeo de
> presentacion. Que la interfaz muestre 99,9 % o 100,1 % segun la precision elegida no
> significa incoherencia.

Sin esta decision, la prueba de propiedades —que es tambien la prueba de coherencia de
captura— fallaria por redondeo de coma flotante en vez de por el problema real, y el
diagnostico seria imposible.

### Identificadores

Cadenas opacas con prefijo legible: `t_58`, `obj_1`, `att_2`, `ds_301`, `ctx_884`,
`conv_12`, `sem_v7`, `prompt_v3`. El prefijo es para el humano que lee un registro de
auditoria; el sistema no lo interpreta.

### Enumeraciones cerradas

Todo conjunto acotado del diseno es una enumeracion, no una cadena libre: tipos de
afirmacion, estados de turno, estados de paso, causas de rechazo, operadores de
condicion, objetivos, operaciones, granularidades, tipos de evento.

Una cadena libre donde el diseno declaro un catalogo cerrado es una puerta por la que el
catalogo deja de ser cerrado.

### Marcas temporales

Instantes absolutos con zona horaria explicita. Se distinguen siempre dos: **momento de
captura de los datos** y **momento de la respuesta**.

---

## 3. `DataRequest` — el lenguaje canonico

```
DataRequest
  metrics:          list[str]            conceptos canonicos ya resueltos
  dimensions:       list[str]
  period:           DateRange            desde, hasta, campo temporal aplicable
  granularity:      Granularity          dia | semana | mes | trimestre | anio | total
  filters:          list[Filter]         dimension, operador, valores
  order:            Order | None
  limit:            int | None
  universe:         Universe             autorizado | completo
  access_filters:   list[Filter]         inyectados por ResolvedAccessContext
```

`access_filters` se separa de `filters` deliberadamente: los primeros no son negociables
y no provienen de la pregunta. Mezclarlos haria imposible verificar que la restriccion
viajo, que es una de las pruebas obligatorias.

---

## 4. `CoverageDescriptor` — contiene la peticion

```
CoverageDescriptor
  request:           DataRequest          la peticion que lo origino
  columns:           list[str]            columnas efectivamente presentes
  derived:           list[DerivedColumn]  columna + calculo que la produjo
  row_count:         int
  context_id:        str
  semantic_version:  str
  captured_at:       datetime
  plan_id:           str
  valid_until:       datetime
```

> El descriptor **contiene** la peticion en vez de repetir sus campos.

Motivo: si fueran dos modelos distintos que casualmente comparten nombres, divergirian en
el primer cambio. Conteniendola, la comparacion de cobertura es entre objetos del mismo
tipo y no hay forma de que se separen.

Las dos capas del contrato semantico se materializan asi: **obtenido** es `request` mas
`columns`; **derivado** es `derived`. Solo la primera responde por la cobertura de una
peticion nueva; la segunda habilita reordenar, filtrar y recortar sobre lo ya presentado.

---

## 5. `Fact`

```
Fact
  id:             str
  turn_id:        str          obligatorio
  objective_id:   str          obligatorio
  attempt_id:     str          obligatorio
  type:           FactType     enumeracion declarada en la ficha de la operacion
  value:          Decimal | str | list
  unit:           str | None
  scope:          FactScope    universo, filtros y alcance autorizado
  captured_at:    datetime
  evidence:       EvidenceKind original | reconstructed
  invocation_id:  str
```

> Los tres identificadores de aislamiento son **obligatorios**, sin valor por defecto.

Si fueran opcionales, aparecería el primer sitio donde se omiten y la validacion de
aislamiento pasaria a ser una sugerencia. `captured_at` por hecho es lo que permite
declarar un **rango** de captura cuando una respuesta mezcla momentos, y lo que hace
verificable la coherencia de captura.

---

## 6. `AnalysisPlan` y el lenguaje cerrado de condiciones

```
AnalysisPlan
  id, turn_id
  objectives:  list[PlannedObjective]
  budget:      TurnBudget          tiempo total, llamadas al modelo

PlannedObjective
  objective_id, objective: ObjectiveName
  sufficiency:  Condition
  depends_on:   str | None         dependencia declarada entre objetivos
  steps:        list[PlanStep]

PlanStep
  step_id, operation: OperationName
  arguments:    dict[str, DomainValue]
  condition:    Condition | None
  derives_from: list[str]          pasos cuyos hechos consume  -> coherencia de captura
  state:        StepState          pending | skipped | started | completed
                                   | rejected | not_executed
  attempt_id:   str | None

Condition
  fact_type:  FactType
  operator:   ConditionOperator    lt | lte | gt | gte | eq | neq
  value:      Decimal | ThresholdName
```

> `Condition` tiene **tres campos y seis operadores**. No admite composicion, negacion ni
> anidamiento.

Esa pobreza es intencional y ahora la hace cumplir el formato, no la revision de codigo.
Un tipo que admitiera expresiones compuestas terminaria siendo un interprete, y el
conocimiento del dominio volveria al Ejecutor por la puerta de atras.

`derives_from` es la novedad del nivel de formato: hace **explicita en el dato** la
dependencia entre pasos que la coherencia de captura necesita comprobar. En el contrato
semantico estaba descrita en prosa; aqui es un campo.

---

## 7. `Rejection` — valor, no excepcion

```
Rejection
  cause:        RejectionCause     enumeracion cerrada
  action:       SuggestedAction    informar | aclarar | acotar | reintentar | reejecutar
  options:      list[str]          alternativas concretas, cuando aplica
  detail:       str | None         sin revelar conceptos ocultos
```

> Las autoridades **devuelven** `Rejection`; no lanzan excepciones.

Como valor de retorno, la disciplina de "todo rechazo lleva causa y accion" la impone el
tipo. Como excepcion, cada punto del codigo decidiria que hacer y la disciplina se
perderia. Ademas, un rechazo es un **resultado normal del dominio**, no un error: tratarlo
como excepcion contradice la clasificacion de estados del diseno.

Las excepciones quedan reservadas para fallas operativas: fuente caida, modelo no
disponible, defectos del sistema.

---

## 8. Salida estructurada del modelo

Los esquemas que restringen al modelo se **derivan de estos mismos modelos**. Una sola
definicion valida la salida y restringe la generacion; no pueden divergir.

Esta seccion cierra una revision de herencia estricta propia: la version anterior
nombraba `ObjectiveProposal`, `Continuity`, `ConceptMapping`, `ResolvedReference`,
`MaterialAmbiguity`, `OutOfScope`, `AnswerSection` y `ResearchSuggestion` sin declarar
sus campos, y ubicaba `continuity`/`concepts`/`premises`/`ambiguities` a nivel de todo
el turno -- una forma que no puede representar el turno multi-objetivo que
`07_parte_interpretacion.md` seccion 6bis y `09_parte_ejecutor.md` seccion 7 exigen
(cada objetivo con su propia continuidad, sus propios conceptos, sus propias premisas).
Ver seccion 11 para el detalle de los cambios.

### `InterpretationOutput`

```
InterpretationOutput
  objective_proposals:  list[ObjectiveProposal]   maximo configurable por turno
  out_of_scope:         list[OutOfScope]           intenciones que no formaron propuesta
  prompt_version:       str

ObjectiveProposal
  proposal_id:       str                      local, efimero (p1, p2...). El sistema
                                               le asigna `objective_id` durable recien
                                               al construir AnalysisPlan (seccion 6)
  objective:         ObjectiveName
  continuity:         Continuity
  concepts:           list[ConceptMapping]
  time_expressions:   list[str]                SIN resolver
  filters:            list[Filter]
  premises:           list[str]
  references:         list[ResolvedReference]
  ambiguities:        list[MaterialAmbiguity]
  plan:               list[ProposedPlanStep]
  dependency:         ObjectiveDependency | None

Continuity
  mode:      new | continuation
  inherits:  list[InheritedField]     InheritedField = period | filters | metric | dimension
                                       Nunca se hereda por omision: si no esta en la
                                       lista, no se hereda

ConceptMapping
  canonical:            str            concepto canonico del catalogo filtrado
  original_expression:  str

ResolvedReference
  expression:  str        "esos tres", "eso", "y en junio"
  resolution:  str

MaterialAmbiguity
  description:  str
  options:      list[str]

OutOfScope
  reason:        str
  alternatives:  list[str]

ObjectiveDependency
  source_proposal_id:  str        el proposal_id del que depende esta propuesta
  binding:              Binding

Binding
  source_fact_type:  FactType     tipo de hecho del objetivo origen que se consume
  target_dimension:  str          dimension del objetivo dependiente que recibe el valor
  operator:          FilterOperator

FilterOperator = eq | neq | in | not_in

ProposedPlanStep
  step_id:       str                      local, efimero (s1, s2...). El sistema le
                                           asigna `step_id` durable al construir PlanStep
  operation:     OperationName
  arguments:     dict[str, DomainValue]
  condition:     Condition | None
  derives_from:  list[str]                step_id locales de este mismo plan propuesto

DomainValue = str | int | Granularity | SortDirection

SortDirection = ascending | descending
```

> **`Binding` declara la dependencia, no la ejecuta.** En este bloque `Binding` es una
> declaracion semantica: que tipo de hecho se consume y a que dimension se aplica. Como
> extraer el valor concreto de un `Fact` compuesto (por ejemplo, cual campo de un
> `ranking_element` es el identificador que debe convertirse en valor de filtro) **no
> esta resuelto**: `Fact.value` (seccion 5) no declara la forma interna de sus hechos
> compuestos. Es un hueco contractual pendiente, registrado para resolverse antes de
> que el bloque que construye `AnalysisPlan` a partir de `InterpretationOutput` consuma
> un `Binding` real.

`DomainValue` es la union cerrada de los tipos concretos que hoy necesitan los
argumentos de las diez operaciones de `10_parte_operaciones.md` seccion 8 (excluyendo
`filters`, que vive en `ObjectiveProposal.filters`, no en `arguments`). No incluye
`Decimal`: ningun parametro lo necesita mientras el modelo no tenga autoridad
confirmada para proponer un valor propio de `sensitivity` o `coverage_threshold` --
ver el punto abierto 5 de `10_parte_operaciones.md` seccion 12. Si ese punto se
resuelve a favor de permitir un valor propuesto, `DomainValue` se amplia entonces, no
antes.

### `SynthesisOutput`

```
SynthesisOutput
  sections:         list[AnswerSection]
  cross_objective:  CrossObjectiveAssertion | None
  suggestions:       list[ResearchSuggestion]
  prompt_version:    str

AnswerSection
  objective_id:  str
  assertions:    list[Assertion]

Assertion
  id, objective_id, turn_id
  kind:      AssertionKind    dato | interpretacion | hipotesis
  text:      str
  evidence:  list[str]        identificadores de Fact

CrossObjectiveAssertion
  turn_id:        str
  objective_ids:  list[str]    los objetivos citados; solo con dependencia declarada
  kind:            AssertionKind
  text:            str
  evidence:        list[str]

ResearchSuggestion
  question:  str
```

> **`Assertion` y `CrossObjectiveAssertion` son tipos distintos, no una variante con
> excepcion.** La regla de aislamiento -- ninguna afirmacion mezcla hechos de objetivos
> distintos -- es absoluta para `Assertion`, sin excepcion alguna. `CrossObjectiveAssertion`
> no la excepciona: es un tipo separado que nunca aparece dentro de una `AnswerSection`,
> solo en el campo `cross_objective` de `SynthesisOutput`, y solo cuando existe
> dependencia declarada entre los objetivos que cita (`08_parte_sintesis.md` seccion 5).

> **`status` y `scope` no son campos de `SynthesisOutput`.** El estado de cada objetivo
> (satisfecho, insuficiente, rechazado, no ejecutado) ya lo determina el Ejecutor
> deterministicamente (`09_parte_ejecutor.md` seccion 3); el alcance lo compone el
> compositor de alcance, tambien deterministico (`08_parte_sintesis.md` seccion 12).
> Que el modelo los reprodujera abriria una fuente de contradiccion entre lo que el
> sistema ya sabe y lo que el modelo redacta. Ambos se agregan a la respuesta final
> (`Answer`) fuera de `SynthesisOutput`.

`ResearchSuggestion` no lleva identificador: el modelo no genera identificadores
persistentes sin necesidad. Si una interfaz necesita referenciar una sugerencia
individual, el sistema le asigna un id **despues** de recibir `SynthesisOutput`, no antes.

> **El esquema garantiza forma, no verdad.**

Una salida estructuralmente valida puede citar cifras inexistentes o evidencia fuera de
alcance. La validacion de salida sigue siendo obligatoria: el esquema elimina una clase
entera de fallos y deja intacta la que importa.

`time_expressions` viaja **sin resolver** a proposito, y ahora vive dentro de cada
`ObjectiveProposal` porque objetivos distintos del mismo turno pueden mencionar
expresiones temporales distintas (`07_parte_interpretacion.md` seccion 6bis: "julio"
pertenece a un objetivo, "el ano actual" a otro). Es el punto donde el formato hace
cumplir la frontera con Conocimiento del negocio: el modelo no tiene ningun campo donde
escribir una fecha.

---

## 9. Superficie HTTP

| Metodo | Ruta | Proposito |
|---|---|---|
| POST | `/conversations` | Abrir conversacion sobre una conexion |
| GET | `/conversations/{id}` | Estado analitico vigente e historial |
| POST | `/conversations/{id}/analyses` | Preguntar. Devuelve `Answer` completa |
| GET | `/analyses/{id}` | Recuperar resultado |
| GET | `/analyses/{id}/events` | Canal SSE de progreso |
| POST | `/analyses/{id}/clarification` | Responder una aclaracion pendiente |
| POST | `/analyses/{id}/resume` | Reanudar un turno recuperable |
| GET | `/datasets/{id}` | Pagina de un conjunto |
| GET | `/datasets/{id}/export` | Exportacion completa |
| GET | `/connections` | Conexiones permitidas |

**Autenticacion:** clave de API por usuario en cabecera, en toda la superficie. Sin
superficie anonima. **Idempotencia:** clave opcional en preguntar y exportar.

### Forma de la respuesta

```json
{
  "turn_id": "t_58",
  "state": "answered",
  "sections": [
    {
      "objective_id": "obj_1",
      "objective": "explain_variance",
      "state": "satisfied",
      "assertions": [
        {
          "id": "a1",
          "type": "data",
          "text": "La facturacion neta de julio fue 4176900.00 ARS frente a 4812400.00 en junio, una caida de 635500.00 (-13.2 %).",
          "evidence": ["h1", "h2", "h3", "h4"]
        }
      ]
    }
  ],
  "scope": {
    "period": "2026-06-01/2026-07-31",
    "definitions": ["facturacion neta = ventas menos notas de credito"],
    "universe": "todos los clientes dentro de tu alcance autorizado",
    "capture": {"from": "2026-08-15T16:41:00-03:00", "to": "2026-08-15T16:48:00-03:00"},
    "evidence": "original",
    "semantic_version": "sem_v7"
  },
  "drafting_origin": "validated_synthesis",
  "analysis_origin": "resumed",
  "suggestions": [],
  "datasets": [
    {"id": "ds_311", "rows": 1240, "columns": 5,
     "partial_preview": true, "exportable": true,
     "captured_at": "2026-08-15T16:48:00-03:00"}
  ]
}
```

`capture` es un rango porque el turno se reanudo. Con una sola captura, ambos extremos
coinciden. Los importes viajan como decimal exacto en cadena, no como numero JSON: un
numero JSON se interpreta como coma flotante y perderia la garantia de la seccion 2.

Dos campos distintos, dos idiomas distintos:

```
DataRequest.universe   -> lenguaje interno   -> authorized | complete
scope.universe          -> lenguaje humano    -> "todos los clientes dentro de tu
                                                   alcance autorizado"
```

`DataRequest.universe` (seccion 3) es el enum cerrado que usa Operaciones
internamente para decidir si un calculo necesita cruzar la restriccion de filas del
usuario. `scope.universe`, en cambio, es la descripcion del alcance efectivo que lee
quien recibe la respuesta, y admite texto libre -- `08_parte_sintesis.md` lo ejemplifica
tambien como `"region Centro (tu alcance actual)"` bajo contexto restringido. En esta
traza las operaciones `comparar` y `explicar_variacion` trabajan sobre universo
autorizado (`10_parte_operaciones.md` seccion 4), y `scope.universe` lo declara en
lenguaje humano en vez de repetir el literal interno.

---

## 10. Canal de eventos

```
event: operation_completed
data: {"turn_id":"t_58","objective_id":"obj_1","attempt_id":"att_2",
       "step":"step_2","state":"completed"}
```

| Regla | Consecuencia |
|---|---|
| Los eventos son **estados del dominio** | Un evento que no corresponde a un estado es telemetria disfrazada |
| Llevan `turn_id`, `objective_id`, `attempt_id` | Un evento de intento superado se descarta como su resultado |
| **No transportan datos de negocio** | El canal no es una segunda superficie de salida y no requiere revalidar contexto |
| **Observa, no gobierna** | Cortar el canal no cancela el analisis |

Eventos: `turn_started`, `plan_validated`, `operation_started`,
`operation_completed`, `replanning`, `synthesizing`, `completed`, `interrupted`,
`rejected`.

El evento final transporta el mismo `Answer` que devuelve el endpoint sincrono. **SSE es
un modo de entrega, no un segundo contrato.**

---

## 11. Verificacion de herencia estricta

Resultado de bajar los diez contratos semanticos al nivel de formato:

| Contrato | Resultado |
|---|---|
| Frontera de servicio | Sin cambios |
| Contexto de acceso | Sin cambios |
| Sesion de analisis | **Cambio menor**: el registro durable incorpora `prompt_version` |
| Conocimiento del negocio | Sin cambios |
| Interpretacion | **Cambio**: la version anterior de `InterpretationOutput` no podia representar un turno con mas de un objetivo, cada uno con su propia continuidad, conceptos y premisas (`07` seccion 6bis). Se movieron esos campos a `ObjectiveProposal` y se agrego `proposal_id`, `dependency` y `ObjectiveDependency` para expresar dependencias entre objetivos sin ids persistentes prematuros. `time_expressions` sin resolver quedo impuesto por el esquema, ahora por objetivo |
| Sintesis | **Cambio**: se introdujo `CrossObjectiveAssertion` como tipo separado de `Assertion`, para que la regla de aislamiento de `Assertion` (`09` seccion 10) siga siendo absoluta sin una excepcion implicita. Se retiraron `status` y `scope` de `SynthesisOutput`: ambos los compone el sistema deterministicamente, nunca el modelo |
| Ejecutor | **Cambio menor**: `derives_from` explicito en `PlanStep` |
| Operaciones analiticas | Sin cambios |
| Acceso a datos | Sin cambios |
| Conjuntos de datos | **Cambio menor**: el descriptor contiene la peticion en vez de repetirla |

Cinco ajustes, ninguna violacion sin resolver: los dos de Interpretacion y Sintesis se
detectaron y cerraron en la misma revision que motiva esta nota. Las dos decisiones que
mas presion ejercieron sobre el formato —el lenguaje cerrado de condiciones y los
identificadores obligatorios— resultaron expresables sin concesiones.

### `prompt_version` en el registro durable

Si el codigo referencia una version de prompt, esa version **debe quedar auditada junto a
la version semantica**. Sin ella se podria reconstruir que datos produjeron una respuesta
pero no que instruccion la redacto.

Corolario para la evaluacion: **prompt y artefacto semantico se versionan por separado
pero se evaluan juntos**. Una corrida del banco mide la combinacion; un resultado solo es
comparable contra otro que varie uno de los dos, nunca los dos a la vez.

---

## 12. Persistencia

Un solo motor, dos conexiones independientes y con permisos distintos:

| Conexion | Uso | Permisos |
|---|---|---|
| Sistema | Sesion, planes, hechos, conjuntos, versiones publicadas | Lectura y escritura |
| Negocio | Consultas del cliente | **Solo lectura, verificada al conectar** |

Con dos conexiones separadas, el usuario de solo lectura deja de ser buena practica y
pasa a ser **lo que impide escribir por accidente en la base del cliente**.

Tablas principales: `conversations`, `turns`, `analytical_states`, `plans`, `plan_steps`,
`invocations`, `facts`, `answers`, `saved_analyses`, `semantic_versions`,
`prompt_versions`, `datasets`, `dataset_rows`.

| Decision | Motivo |
|---|---|
| `dataset_rows` con **una fila por registro** | Paginar y exportar salen nativos; no obliga a traer el conjunto entero a memoria |
| Importes en `NUMERIC` | Coherente con la seccion 2 |
| Migraciones versionadas | El esquema evoluciona con el proyecto |
| Registro previo y posterior **en la misma transaccion** que el estado del paso | Es lo que sostiene la reanudacion |

> Con conjuntos durables, **la reanudacion tras reinicio del proceso se promete sin
> condicion**. La capacidad condicionada registrada como P9 queda resuelta.

---

## 13. Puntos abiertos del nivel de formato

1. **Formato de exportacion**: separado por comas y planilla. Limite ligado al maximo de
   materializacion.
2. **Paginacion**: por desplazamiento o por cursor. Sobre un snapshot inmutable el
   desplazamiento es seguro, pero el cursor escala mejor.
3. **Versionado del contrato publico** y politica de compatibilidad hacia atras.
4. **Reconexion del canal de eventos**: si se reanuda el flujo desde el ultimo evento o
   el cliente consulta el estado por HTTP y vuelve a suscribirse.
