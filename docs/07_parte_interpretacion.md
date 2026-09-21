<!-- docs/07_parte_interpretacion.md -->
<!-- Bloque 2 - Contrato semantico. Nivel de formato pendiente (Bloque 3). -->

# Parte 5 — Interpretacion y planificacion

> **Responsabilidad**
> Convertir una pregunta en lenguaje natural en una propuesta estructurada y
> verificable: objetivo, conceptos canonicos, plan de pasos y condiciones.

> **Invariante propio**
> Nunca ejecuta operaciones ni produce conclusiones de negocio. Unicamente transforma
> intencion en estructuras que otros componentes pueden validar.

> **Aislamiento**
> No se comunica con Sintesis de respuesta. El Ejecutor es el unico intermediario.
> Sintesis jamas puede ver una intencion que no haya sobrevivido a las validaciones
> deterministas.

> **Consumidor mas exigente**
> El Ejecutor, en su validacion estatica del plan: necesita condiciones que referencien
> hechos que los pasos previos declaran publicar. Un plan que no soporta esa
> comprobacion es inutil aunque la interpretacion sea correcta.

---

## 1. Posicion en el sistema

```mermaid
flowchart LR
    EJE1[7 Ejecutor] -->|pregunta + catalogos + estado| INT[5 Interpretacion]
    INT -->|propuesta estructurada| EJE2[7 Ejecutor]
    EJE2 -->|validaciones| OPE[8 Operaciones]
    OPE -->|hechos| EJE3[7 Ejecutor]
    EJE3 -->|hechos + alcance| SIN[6 Sintesis]
    INT -.-x SIN
```

La flecha tachada es una prohibicion del diseno, no una omision.

---

## 2. Entradas

| Entrada | De quien | Nota |
|---|---|---|
| Pregunta en lenguaje natural | Ejecutor | Texto crudo |
| Catalogo de objetivos | Ejecutor (via Operaciones) | Cerrado, con su criterio de suficiencia |
| Catalogo semantico filtrado | Ejecutor (via Conocimiento) | Solo conceptos visibles en este contexto |
| Catalogo de operaciones filtrado | Ejecutor (via Operaciones) | Fichas con parametros **y hechos que publican** |
| Estado analitico vigente | Ejecutor (via Sesion) | Periodo, filtros y definiciones en curso |
| Historial conversacional acotado | Ejecutor (via Sesion) | Para resolver referencias |
| Aclaracion previa, si existe | Ejecutor | Complementa la pregunta original |
| Causa de rechazo, si es reintento | Ejecutor | Motivo concreto de la propuesta anterior |
| Plan ejecutado, hechos y causa de insuficiencia | Ejecutor | Solo en replanificacion |

### Consecuencia de contrato

El catalogo de operaciones que recibe **debe incluir los tipos de hecho que cada
operacion publica**. Sin eso, Interpretacion no puede escribir condiciones validas y
todo plan condicional fallaria la validacion estatica. Es una dependencia real entre
la ficha de operacion y esta parte, y es la razon por la que "hechos publicados" es un
campo obligatorio de la ficha.

### Catalogo de objetivos recibido: solo los verificables

El catalogo de objetivos que Interpretacion recibe **excluye cualquier objetivo sin
criterio de suficiencia verificable** -- hoy, solo `explore`
(`10_parte_operaciones.md` seccion 2). Sin un criterio, el Ejecutor nunca sabria
cuando darlo por satisfecho. Si una propuesta llegara igual con un objetivo excluido
-- algo que en operacion normal no deberia ocurrir, dado que nunca aparecio en el
catalogo que el modelo recibio -- se rechaza con la causa `objective_not_available`
(`14_contratos_formato.md` seccion 7), como defensa, no como camino esperado.

### Lo que no recibe

- Datos de negocio. Ni filas, ni cifras, ni muestras.
- Conjuntos de datos activos. La reutilizacion no es decision suya.
- Reglas de permisos. Los catalogos ya llegan filtrados; no debe conocer que se le
  oculto ni por que.

---

## 3. Salida — propuesta estructurada

| Campo | Contenido |
|---|---|
| Objetivo | Uno del catalogo cerrado |
| Continuidad | `new` o `continuation`, con lo que hereda del estado analitico |
| Conceptos | Metricas y dimensiones canonicas, cada una con la expresion original que la origino |
| Expresiones temporales | Sin resolver: "julio", "el ultimo trimestre" |
| Filtros | Dimension canonica, operador y valores literales |
| Referencias resueltas | Que significa "esos tres", "eso", "y en junio" |
| Premisas | Lo que la pregunta da por supuesto |
| Plan | Pasos ordenados con operacion, argumentos y condicion de activacion |
| Ambiguedades | Las materiales no resueltas, con opciones concretas |
| Fuera de alcance | Si corresponde, con que si puede hacerse |

### Frontera con Conocimiento del negocio

| Interpretacion resuelve | Conocimiento resuelve |
|---|---|
| Que expresion del usuario corresponde a que concepto del catalogo | Que significa el concepto y de donde se obtiene |
| Que expresion temporal se menciono | A que fechas corresponde, segun el calendario del negocio |

**Las fechas nunca las resuelve el modelo.** "Julio" sin ano, cierres fiscales,
"el ultimo trimestre" y "este mes" son fuente clasica de error silencioso: el modelo
produce una fecha plausible y nadie lo nota. Interpretacion informa la expresion;
Conocimiento la traduce.

Los conceptos si se eligen del catalogo recibido, porque el catalogo esta ahi
precisamente para eso. La expresion original se conserva para poder explicar la
eleccion y para formular la aclaracion cuando haga falta.

### Continuidad explicita

`continuation` declara **que** hereda: periodo, filtros, metrica, dimension. Nunca se
hereda por omision. Un estado analitico que se arrastra en silencio produce respuestas
correctas sobre el alcance equivocado, que es el error mas dificil de detectar para el
usuario.

### Premisas

Una pregunta como *"¿por que cayo la facturacion?"* **presupone** la caida. La premisa
se declara para que el plan pueda condicionarse a ella y para que la respuesta pueda
corregirla. Sin esta declaracion, el sistema explicaria una caida que no ocurrio.

---

## 4. Forma del plan

Pasos ordenados. Cada paso declara operacion, argumentos y, opcionalmente, una
condicion de activacion que referencia un hecho de un paso anterior.

Ejemplo de la traza nominal — *"Compara la facturacion de julio contra junio y decime
que clientes explican la caida"*:

```
objective:     explain_variance
continuity:    new
concepts:      net_revenue  (de "facturacion")
               customer     (de "clientes")
temporal:      "julio", "junio"
premises:      existe una caida entre ambos periodos
plan:
  step 1  compare_periods
          metric = net_revenue
          current_period = "julio"
          comparison_period = "junio"
          condition: (ninguna)

  step 2  decompose_variance
          metric = net_revenue
          current_period = "julio"
          comparison_period = "junio"
          dimension = customer
          condition: fact(relative_variance) < 0
ambiguities:   (ninguna)
```

El paso 2 es condicional porque la premisa puede ser falsa. Si julio subio, el paso no
se ejecuta y la respuesta corrige la premisa en vez de explicar una caida inexistente.

---

## 5. Ambiguedad material

Preguntar demasiado arruina la experiencia; preguntar de menos produce respuestas
correctas a la pregunta equivocada. La regla que separa ambos casos:

> Una ambiguedad es **material** cuando distintas resoluciones producen respuestas
> distintas **y** no existe un valor por defecto declarado en la capa semantica.

| Caso | Material | Comportamiento |
|---|---|---|
| "ventas", con `net_revenue` declarada como acepcion por defecto | No | Se resuelve y se declara en el alcance |
| "los mejores clientes", sin criterio declarado | Si | Aclaracion con opciones concretas |
| "el ultimo trimestre" con calendario fiscal ambiguo | Si | La detecta Conocimiento, no Interpretacion |
| "este mes" | No | Resuelve Conocimiento con la fecha de referencia |
| "esos tres" sin referente localizable en el historial | Si | Aclaracion |

Una ambiguedad material **detiene la propuesta**: no se propone un plan tentativo
junto con la pregunta. Proponer y preguntar a la vez invita a ejecutar la propuesta
por defecto, que es exactamente lo que la aclaracion venia a evitar.

Las opciones ofrecidas se construyen **con conceptos del catalogo recibido**, por lo
que nunca ofrecen algo que el usuario no puede ver.

### Verificacion determinista de la materialidad declarada

La regla tiene dos mitades con dueños distintos. *"Distintas resoluciones producen
respuestas distintas"* no es verificable sin ejecutar la pregunta, y Interpretacion no
ejecuta nada (seccion 8): esa mitad queda confiada al modelo, sin contraverificacion
posible. *"No existe un valor por defecto declarado"* **si** es mecanico: cuando
`MaterialAmbiguity.expression` esta presente (14_contratos_formato.md seccion 8), el
sistema puede consultar `default_sense_of` de las metricas del artefacto semantico.

El sistema **nunca decide materialidad de forma positiva** -- no tiene con que. Solo
puede **refutar** una ambiguedad que el modelo declaro material cuando existe una
acepcion por defecto inequivoca para `expression`. En ese caso no modifica la
propuesta ni construye un plan en su nombre: devuelve un rechazo corregible ("`ventas`
ya tiene sentido por defecto declarado: `net_revenue`"), que consume el unico
reintento de planificacion ya existente (`09_parte_ejecutor.md` seccion 4). El modelo
vuelve a proponer, ahora informado.

### Verificacion determinista de las referencias resueltas

`reference_resolver` tiene la misma limitacion de fondo: no puede confirmar que la
`resolution` de una `ResolvedReference` sea correcta -- comparar ese texto contra el
estado analitico o el historial es la misma heuristica de texto que se evito arriba.
Lo unico verificable sin heuristicas es que **exista algun contexto** del cual la
referencia pudiera haberse resuelto (`last_reference` del estado analitico, o
historial conversacional no vacio). Si una propuesta trae referencias resueltas sin
ningun contexto disponible, la referencia es imposible por construccion -- no una
cuestion de acierto del modelo -- y se rechaza con `reference_without_context`,
acción `clarify`: coherente con la fila de la seccion 5, *"esos tres" sin referente
localizable en el historial -> Aclaracion*.

---

## 6. Ejemplos concretos

### 6.1 Aclaracion por ambiguedad material

Pregunta: *"Mostrame los mejores clientes de este trimestre."*

```
objective:     rank
concepts:      customer
temporal:      "este trimestre"
ambiguities:   criterio de "mejores"
               opciones: facturacion neta, unidades vendidas, cantidad de operaciones
plan:          (no se propone)
```

Tras la respuesta *"por facturacion"*, la aclaracion **complementa** la pregunta
original; no la reemplaza. El registro conserva ambas.

### 6.2 Referencia conversacional

Estado analitico vigente: periodo julio-junio, dimension cliente, conjunto `ds_301`.
Pregunta: *"Saca esos tres y compara de nuevo."*

```
objective:           compare
continuity:          continuation (hereda metrica, ambos periodos y dimension)
references:          "esos tres" = los tres contribuyentes principales del turno anterior,
                     identificados nominalmente
filters:             cliente distinto de [los tres identificados]
plan:
  step 1  compare_periods con el filtro aplicado
```

Los tres clientes se nombran explicitamente en la propuesta. Si el referente no fuera
localizable, corresponde aclaracion, no suposicion.

### 6.3 Fuera de alcance

Pregunta: *"¿Nos conviene abrir una sucursal en Cordoba?"*

```
objective:      (ninguno aplicable)
out_of_scope:   la pregunta requiere proyeccion y criterio de negocio, no analisis
                de datos existentes
alternatives:   facturacion por region, evolucion mensual de la region Centro,
                ranking de clientes por region
```

Declarar el limite y ofrecer lo adyacente es una salida legitima y frecuente. No es un
fallo del sistema.

### 6.4 Premisa falsa

Pregunta: *"¿Por que cayeron las ventas en julio?"*, con julio en alza.

El plan es el mismo del ejemplo de la seccion 4. La condicion del paso 2 no se cumple,
el paso no se ejecuta, y la respuesta corrige la premisa con el hecho obtenido. La
correccion es posible **porque la premisa se declaro**; si no se hubiera declarado, el
sistema habria descompuesto una variacion positiva como si fuera una caida.

---

## 6bis. Turno con multiples objetivos

Una pregunta puede contener mas de una intencion legitima y compatible. No se obliga
al usuario a separarlas.

Pregunta: *"Compara julio contra junio y decime tambien el ranking anual."*

```
turn:
  objective_1: compare
    plan: compare_periods(net_revenue, "julio", "junio")
    continuity: new

  objective_2: rank
    plan: rank(net_revenue, customer, "ano actual", n = 10)
    continuity: new
    dependency: (ninguna)
```

### Reglas

- Cantidad de objetivos por turno **pequena y configurable**.
- Cada objetivo mantiene su propio plan y su propio criterio de suficiencia. El
  Ejecutor los evalua por separado.
- **No se fusionan en un objetivo compuesto.** Un megaobjetivo sin criterio de
  suficiencia propio rompe el control de terminacion.
- **Un objetivo no hereda periodo, filtros ni alcance de otro**, salvo dependencia
  declarada explicitamente. En el ejemplo, "julio" pertenece al primero; el segundo
  usa el ano. Suponer lo contrario es la misma herencia silenciosa que la continuidad
  explicita viene a impedir.
- Si las intenciones son contradictorias, mutuamente ambiguas, o exceden el limite del
  turno, corresponde aclaracion pidiendo separacion.

### Dependencia explicita entre objetivos

Pregunta: *"Compara julio contra junio y para esos mismos clientes dame el ranking
anual."*

```
  objective_2: rank
    dependency: filtro cliente proveniente de los elementos del objective_1
```

Una dependencia declarada obliga a ordenar los objetivos y hace que el segundo no
pueda ejecutarse si el primero fallo o fue rechazado. Sin declaracion, los objetivos
son independientes y el fallo de uno no impide responder el otro.

---

## 7. Replanificacion

Entrada acotada: objetivo original, plan ejecutado, hechos obtenidos, causa de
insuficiencia, catalogos.

| Puede | No puede |
|---|---|
| Proponer otra dimension de descomposicion | Cambiar el objetivo |
| Proponer operaciones adicionales del catalogo | Proponer una tercera ronda |
| Declarar que no hay via para satisfacer el criterio | Reinterpretar la pregunta original |

Si el objetivo estaba mal elegido, el camino valido es `awaiting_clarification`, no
replanificar hacia otra cosa. Reinterpretar en la segunda ronda equivale a responder
una pregunta distinta de la que el usuario hizo.

Declarar que no hay via es una salida util: evita gastar una ronda para llegar a la
misma insuficiencia.

---

## 8. Lo que esta parte no hace

- No resuelve fechas.
- No ejecuta ni calcula nada.
- No decide si los datos alcanzan: eso es cobertura, y la verifica codigo.
- No decide si el objetivo esta satisfecho: eso es el criterio de suficiencia.
- No elige entre conjuntos activos.
- No aplica ni conoce reglas de permisos.
- No redacta texto para el usuario, salvo las opciones de una aclaracion.
- No se comunica con Sintesis.

---

## 9. Riesgos propios

| Riesgo | Manifestacion | Contencion |
|---|---|---|
| Intencion mal entendida | Responde correctamente otra pregunta | Aclaracion ante ambiguedad material; alcance declarado en la respuesta |
| Concepto inventado | Propone una metrica que no existe | Catalogo cerrado + validacion semantica |
| Operacion inventada | Propone un calculo inexistente | Catalogo cerrado + validacion de firma |
| Condicion mal formada | Referencia un hecho que nadie publica | Validacion estatica del plan |
| Herencia silenciosa de estado | Responde sobre el periodo anterior | Continuidad explicita obligatoria |
| Premisa no declarada | Explica algo que no ocurrio | Campo de premisas obligatorio |
| Exceso de aclaraciones | Fricción; el usuario abandona | Criterio de materialidad + valores por defecto en la capa semantica |
| Valor de filtro inexistente | "region Centro" cuando no existe esa region | Rechazo al ejecutar, con las regiones disponibles como opciones |

El ultimo caso merece nota: los **valores** de filtro son datos, no esquema.
Interpretacion no puede validarlos contra ningun catalogo, y su inexistencia solo se
descubre al consultar. La causa `nonexistent_filter_value` deriva en aclaracion con
los valores reales disponibles, no en un resultado vacio presentado como respuesta.

---

## 10. Verificacion y evaluacion

Dos cosas distintas que conviene no confundir.

### Verificacion de contrato — determinista, sin modelo

Con un doble del modelo que devuelve propuestas fijas:

| Que verifica |
|---|
| Una propuesta con objetivo fuera de catalogo se rechaza |
| Una propuesta con concepto fuera del catalogo filtrado se rechaza |
| Una condicion sobre un hecho no publicado se rechaza en validacion estatica |
| Una `continuation` declara explicitamente que hereda |
| Una ambiguedad material no viene acompanada de plan |
| La replanificacion que cambia el objetivo se rechaza |

### Evaluacion de interpretacion — con modelo, contra el banco de casos

Bloque 1.7. Cada caso (`business_knowledge/evaluation_cases.py`, `EvaluationCase`)
declara pregunta e interpretacion esperada. `expected` es una union discriminada
por `kind`, simetrica a `InterpretationOutcome`:

```
question:
  "Mostrame los mejores clientes de este trimestre"

expected:
  kind: ambiguity
  description: 'criterio de "mejores"'
  options: [net_revenue, units_sold, operations]
```

```
question:
  "¿Cuanto facturamos en julio?"

expected:
  kind: plan
  objectives:
    - objective: query_metric
      metric: net_revenue
      temporal: [julio]
```

El tercer `kind` es `out_of_scope` (`reason`, `offered_alternatives`, y opcionalmente
`rejection_cause` cuando lo que declina es un validador deterministico -- p. ej. un
concepto inexistente -- en vez del modelo). Un caso **no declara cifras**: la
interpretacion esperada depende solo de la capa semantica.

Categorias y composicion fija del banco (60 casos, `CaseCategory` en el mismo modulo):

| Categoria | % | Casos |
|---|---|---|
| `direct` | 40 % | 24 |
| `material_ambiguity` | 15 % | 9 |
| `continuation` | 15 % | 9 |
| `premise` | 10 % | 6 |
| `multiple_objectives` | 10 % | 6 |
| `out_of_scope` | 10 % | 6 |

`direct`, `premise`, `continuation` y `multiple_objectives` son "plan_expected": el
turno debe terminar en un `AnalysisPlan`. Es el subconjunto sobre el que se miden
A1/A2/B1/B2 (`01_metodo_solucion.md` seccion 12).

### Formulas de A1/A2/A4/B1/B2

No estaban especificadas con precision en ningun documento anterior a este bloque --
se registran aca, junto al codigo que las implementa
(`interpretation/case_comparator.py`, `interpretation/evaluation_metrics.py`):

| Metrica | Formula |
|---|---|
| A1 | `AnalysisPlan` semanticamente correcto al primer intento / total plan_expected |
| A2 | `AnalysisPlan` semanticamente incorrecto al primer intento / total plan_expected |
| A4 | casos con `expected.kind != out_of_scope` declinados por alcance / total de esos casos |
| B1 | plan valido (pasa la validacion estatica) al primer intento / total plan_expected |
| B1+B2 | plan valido al primer intento o tras un unico reintento / total plan_expected |

El denominador de A4 **incluye** `material_ambiguity`: una pregunta ambigua sigue
siendo respondible, y declinarla como fuera de alcance es el mismo error que declinar
una pregunta directa. Una aclaracion innecesaria resta A1 (no cumple "sin aclaracion")
pero no es A2: A2 mide exclusivamente el desenlace silencioso -- un plan que se
construyo y esta mal. Un rechazo con causa (`Rejected`) tampoco es A2, por la misma
razon: lleva causa y accion, no es silencioso.

"Declinado por alcance" (para A4) cubre dos caminos: el modelo declara `out_of_scope`
por su cuenta, o un validador deterministico rechaza por una causa de
existencia/alcance del concepto (`nonexistent_concept`, `unauthorized_concept`,
`objective_not_available`). `invalid_parameters` y las demas causas estructurales no
cuentan: son un plan mal formado, no una declinacion de alcance.

El comparador semantico solo verifica lo que cada `ExpectedObjective` declara
(objetivo, metrica, dimension, expresiones temporales, presencia de premisas,
dependencia con el objetivo anterior, operacion del plan cuando se declara) --
nunca `proposal_id`, `step_id` ni ningun identificador durable.

Todas las formulas de arriba se calculan sobre casos **evaluados**, no sobre el total
del banco (bloque 1.8): un caso cuyo `ModelPort` levanto una excepcion en el primer
intento (timeout, limite de tasa, respuesta que no parseo --
`model_port/openai_adapter.py`) no llega a clasificarse, y se cuenta aparte como falla
operativa. `passes_thresholds()` exige `operational_failures == 0`: una corrida con
fallas operativas no midio el supuesto completo, y ningun umbral compensa eso.

Metricas diagnosticas (no son criterio de aceptacion, solo lectura fina):

| Metrica | Que mide |
|---|---|
| Acierto de objetivo | Casos plan_expected donde el objetivo propuesto coincide |
| Acierto de conceptos | Casos plan_expected donde metrica y dimension coinciden |
| Tasa de aclaracion | Proporcion del banco entero que el sistema decide aclarar |
| Acierto fuera de alcance | Casos `out_of_scope` correctamente declinados |
| Herencia correcta | Casos `continuation` donde `inherits` coincide con lo declarado |
| Validez de plan | Alias de B1 |

El banco se re-corre **cada vez que cambia la capa semantica**, porque un cambio de
vocabulario puede romper interpretaciones que antes funcionaban. Esa regresion es el
motivo principal por el que existe el banco. Congelamiento: el banco se fija por commit
antes de la primera corrida real (bloque 1.8) y no se modifica en funcion de los
resultados (`01_metodo_solucion.md` seccion 12); el reporte de cada corrida
(`interpretation/evaluation_metrics.py`, `EvaluationReport`) registra `semantic_version`
y `prompt_version` juntos, porque se versionan por separado pero se evaluan juntos
(`14_contratos_formato.md` seccion 11).

`querypilot-eval run <conexion>` (`interpretation/evaluation_cli.py`) carga el
artefacto, lo valida, carga el banco, corre la evaluacion contra el `ModelPort` que
resuelva `model_port/factory.py` (`QP_MODEL_PROVIDER`/`QP_MODEL_NAME`/
`OPENAI_API_KEY`, bloque 1.8) y escribe el reporte con `--report <ruta>`. Con
`--history-dir <ruta>` ademas guarda una copia nombrada
`<semantic_version>__<prompt_version>__<timestamp>.md` y avisa cuantas versiones
semanticas distintas se evaluaron hasta ahora -- el limite de tres iteraciones de
`01_metodo_solucion.md` seccion 12 es una decision que registra una persona, no algo
que el comando bloquee. El banco de casos nunca se escribe desde codigo: `run` solo
lo lee.

Todo el mecanismo -- carga, comparador, metricas, reintento, fallas operativas,
registro -- esta probado entero con `DeterministicModelPort` y con un adaptador de
OpenAI mockeado (`tests/interpretation/evaluation/`, `tests/model_port/unit/`), sin
red ni clave. La primera corrida real contra el modelo es la decision que se toma y se
registra al cerrar el bloque 1.8.

---

## 11. Decisiones registradas

| Decision | Supuesto | Senal de invalidacion | Tipo |
|---|---|---|---|
| Interpretacion y Sintesis separadas y sin comunicacion | Ambos usos del modelo tienen riesgos distintos y se evaluan mejor por separado | Un caso legitimo requiere que Sintesis conozca la intencion cruda | Sistema |
| Conceptos se eligen del catalogo; fechas las resuelve Conocimiento | El calendario del negocio no es deducible del texto | Aparece un caso temporal que el catalogo no puede resolver | Sistema |
| Continuidad explicita, sin herencia por omision | El costo de declararla es menor que el de un alcance equivocado | La declaracion explicita produce continuaciones incorrectas frecuentes | Sistema |
| Premisas declaradas como campo obligatorio | Las preguntas de negocio presuponen con frecuencia | Las premisas resultan siempre vacias en el banco | Sistema |
| Ambiguedad material detiene la propuesta | Proponer y preguntar a la vez induce a ejecutar por defecto | La tasa de aclaracion resulta inaceptable para el usuario | Sistema |
| Una propuesta por turno, no varias alternativas rankeadas | Elegir entre planes alternativos es trabajo del modelo, no del usuario | Los casos ambiguos se resolverian mejor mostrando dos planes | Implementacion |

---

## 12. Relacion con el supuesto mas riesgoso del proyecto

Esta parte es donde vive el supuesto que sostiene el producto entero:

> **Un modelo de lenguaje puede convertir preguntas reales de negocio en propuestas
> estructuradas validas, con confiabilidad suficiente, si dispone de una capa semantica
> bien definida y un catalogo cerrado de objetivos y operaciones.**

Si es falso, ninguna otra decision de arquitectura salva el producto: seria un sistema
correcto que responde la pregunta equivocada. El experimento minimo y su criterio de
aceptacion se definen en `01_metodo_solucion.md`, y el banco de casos de esta parte es
el instrumento con el que se mide.

---

## 13. Puntos abiertos

1. **Profundidad del historial conversacional** que se entrega para resolver
   referencias. Demasiado poco rompe las continuaciones; demasiado encarece cada turno.
2. ~~Como se declara una acepcion por defecto en la capa semantica~~ **Resuelto**:
   `Metric.default_sense_of` (bloque 1.2, `06_parte_conocimiento_negocio.md` seccion
   6) ya lo implementa y lo valida `check_default_sense_points_to_existing_concept`.
   Consumido deterministamente por `ambiguity_detector` en la seccion 5 de esta parte.
3. **Tamano minimo del banco de casos** para que la regresion sea significativa.
4. **Umbral de materialidad** de una ambiguedad: hasta que punto una diferencia de
   resolucion justifica molestar al usuario.


---

## Ubicacion en el proyecto

| Aspecto | Valor |
|---|---|
| Caja del diagrama | **5 Interpretacion y planificacion** |
| Codigo | `src/querypilot/interpretation/` |
| Tests | `tests/interpretation/` — subcarpetas: contract/ evaluation/ |
| Sub-peldano de implementacion | 5.1 de `MAPA_AVANCE.md` |
| Estado actual | Pendiente |

### Modulos que la componen

| Modulo | Proposito |
|---|---|
| `proposal_builder` | Objetivo, conceptos, premisas y continuidad |
| `plan_builder` | Pasos, argumentos, condiciones y `derives_from` |
| `reference_resolver` | Resolucion de referencias conversacionales |
| `ambiguity_detector` | Materialidad y opciones concretas |
| `replanner` | Entrada acotada; no puede cambiar el objetivo |

Las firmas concretas se definen al implementar. Este documento fija **el contrato**, no
la implementacion: cualquier firma que lo respete es valida.

### Pasos de implementacion

1. Modelos de salida estructurada.
2. Puerto del modelo con doble determinista.
3. Construccion del material: catalogos filtrados, estado, historial acotado.
4. Propuesta: objetivo, conceptos, premisas, continuidad.
5. Plan con condiciones y `derives_from`.
6. Deteccion de ambiguedad material y resolucion de referencias.
7. Replanificador acotado.
8. Banco de casos y reporte de metricas.

### Nivel de formato

Los modelos canonicos que esta parte recibe y entrega estan definidos en
`14_contratos_formato.md`. La **regla de herencia estricta** sigue vigente: si un formato
no puede transportar algo de este contrato, se revisa este contrato, no el formato.
