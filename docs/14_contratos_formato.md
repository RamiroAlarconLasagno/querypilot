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

Aplicacion de la convencion ya fijada: **ingles donde el identificador nombra una
construccion del programa, espanol donde nombra un concepto del negocio del cliente**.

| Concepto del diseno | Clase | Idioma de sus **valores** |
|---|---|---|
| Peticion de datos | `DataRequest` | Espanol (`facturacion_neta`, `cliente`) |
| Descriptor de cobertura | `CoverageDescriptor` | Espanol |
| Hecho | `Fact` | Espanol |
| Plan de analisis | `AnalysisPlan` | Espanol |
| Contexto de acceso resuelto | `ResolvedAccessContext` | Espanol |
| Respuesta | `Answer` | Espanol |
| Rechazo | `Rejection` | — |
| Sugerencia de investigacion | `ResearchSuggestion` | Espanol |

Los **nombres de campo** son ingles; los **valores del dominio** son espanol. Una metrica
se declara como `metric: "facturacion_neta"`, no como `metrica: "net_revenue"`.

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
  evidence:       EvidenceKind original | reconstruida
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
  state:        StepState          pendiente | omitido | iniciado | completado
                                   | rechazado | no_ejecutado
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

```
InterpretationOutput
  objective_proposals:  list[ObjectiveProposal]   maximo configurable
  continuity:           Continuity                nueva | continuacion + que hereda
  concepts:             list[ConceptMapping]      canonico + expresion original
  time_expressions:     list[str]                 SIN resolver
  premises:             list[str]
  references:           list[ResolvedReference]
  ambiguities:          list[MaterialAmbiguity]
  out_of_scope:         OutOfScope | None
  prompt_version:       str

SynthesisOutput
  sections:             list[AnswerSection]       una por objetivo
  cross_objective:      Assertion | None          solo con dependencia declarada
  suggestions:          list[ResearchSuggestion]
  prompt_version:       str

Assertion
  id, objective_id, turn_id
  kind:      AssertionKind    dato | interpretacion | hipotesis
  text:      str
  evidence:  list[str]        identificadores de Fact
```

> **El esquema garantiza forma, no verdad.**

Una salida estructuralmente valida puede citar cifras inexistentes o evidencia fuera de
alcance. La validacion de salida sigue siendo obligatoria: el esquema elimina una clase
entera de fallos y deja intacta la que importa.

`time_expressions` viaja **sin resolver** a proposito. Es el punto donde el formato hace
cumplir la frontera con Conocimiento del negocio: el modelo no tiene ningun campo donde
escribir una fecha.

---

## 9. Superficie HTTP

| Metodo | Ruta | Proposito |
|---|---|---|
| POST | `/conversaciones` | Abrir conversacion sobre una conexion |
| GET | `/conversaciones/{id}` | Estado analitico vigente e historial |
| POST | `/conversaciones/{id}/analisis` | Preguntar. Devuelve `Answer` completa |
| GET | `/analisis/{id}` | Recuperar resultado |
| GET | `/analisis/{id}/eventos` | Canal SSE de progreso |
| POST | `/analisis/{id}/aclaracion` | Responder una aclaracion pendiente |
| POST | `/analisis/{id}/reanudar` | Reanudar un turno recuperable |
| GET | `/conjuntos/{id}` | Pagina de un conjunto |
| GET | `/conjuntos/{id}/exportacion` | Exportacion completa |
| GET | `/conexiones` | Conexiones permitidas |

**Autenticacion:** clave de API por usuario en cabecera, en toda la superficie. Sin
superficie anonima. **Idempotencia:** clave opcional en preguntar y exportar.

### Forma de la respuesta

```json
{
  "turno_id": "t_58",
  "estado": "respondida",
  "secciones": [
    {
      "objetivo_id": "obj_1",
      "objetivo": "explicar_variacion",
      "estado": "satisfecho",
      "afirmaciones": [
        {
          "id": "a1",
          "tipo": "dato",
          "texto": "La facturacion neta de julio fue 4176900.00 ARS frente a 4812400.00 en junio, una caida de 635500.00 (-13.2 %).",
          "evidencia": ["h1", "h2", "h3", "h4"]
        }
      ]
    }
  ],
  "alcance": {
    "periodo": "2026-06-01/2026-07-31",
    "definiciones": ["facturacion = ventas menos notas de credito"],
    "universo": "todos los clientes",
    "captura": {"desde": "2026-08-15T16:41:00-03:00", "hasta": "2026-08-15T16:48:00-03:00"},
    "evidencia": "original",
    "version_semantica": "sem_v7"
  },
  "origen_redaccion": "sintesis_validada",
  "origen_analisis": "reanudado",
  "sugerencias": [],
  "conjuntos": [
    {"id": "ds_311", "filas": 1240, "columnas": 5,
     "vista_previa_parcial": true, "exportable": true,
     "captura": "2026-08-15T16:48:00-03:00"}
  ]
}
```

`captura` es un rango porque el turno se reanudo. Con una sola captura, ambos extremos
coinciden. Los importes viajan como decimal exacto en cadena, no como numero JSON: un
numero JSON se interpreta como coma flotante y perderia la garantia de la seccion 2.

---

## 10. Canal de eventos

```
event: operacion_completada
data: {"turno_id":"t_58","objetivo_id":"obj_1","intento_id":"att_2",
       "paso":"paso_2","estado":"completado"}
```

| Regla | Consecuencia |
|---|---|
| Los eventos son **estados del dominio** | Un evento que no corresponde a un estado es telemetria disfrazada |
| Llevan `turno_id`, `objetivo_id`, `intento_id` | Un evento de intento superado se descarta como su resultado |
| **No transportan datos de negocio** | El canal no es una segunda superficie de salida y no requiere revalidar contexto |
| **Observa, no gobierna** | Cortar el canal no cancela el analisis |

Eventos: `turno_iniciado`, `plan_validado`, `operacion_iniciada`,
`operacion_completada`, `replanificando`, `sintetizando`, `completado`, `interrumpido`,
`rechazado`.

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
| Interpretacion | Sin cambios. `time_expressions` sin resolver quedo impuesto por el esquema |
| Sintesis | Sin cambios |
| Ejecutor | **Cambio menor**: `derives_from` explicito en `PlanStep` |
| Operaciones analiticas | Sin cambios |
| Acceso a datos | Sin cambios |
| Conjuntos de datos | **Cambio menor**: el descriptor contiene la peticion en vez de repetirla |

Tres ajustes menores, ninguna violacion. Las dos decisiones que mas presion ejercieron
sobre el formato —el lenguaje cerrado de condiciones y los identificadores obligatorios—
resultaron expresables sin concesiones.

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
