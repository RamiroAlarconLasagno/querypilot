<!-- docs/10_parte_operaciones.md -->
<!-- Bloque 2 - Contrato semantico. Nivel de formato pendiente (Bloque 3). -->

# Parte 8 — Operaciones analiticas

> **Responsabilidad**
> Definir y custodiar el **catalogo cerrado de objetivos y operaciones**, y ejecutar
> los calculos analiticos que el sistema sabe hacer. Es el techo de lo que el producto puede responder: nada que no este en este
> catalogo puede ser preguntado con exito.

> **Invariante propio**
> Ningun objetivo ni operacion existe fuera del catalogo, y ninguna operacion manipula
> tablas, columnas ni joins.

> **Consumidor mas exigente**
> El Ejecutor, cuando evalua condiciones de plan y criterios de suficiencia sobre los
> productos de una operacion.

> **Convencion de nomenclatura**
> El lenguaje canonico del dominio se escribe en espanol (`facturacion_neta`,
> `comparar_periodos`, `descomponer_variacion`), porque pertenece al negocio del
> cliente y aparece en la capa semantica, en la interfaz del integrador y en las
> explicaciones al usuario. El codigo y la infraestructura se escriben en ingles.
> La frontera es explicita: donde un identificador nombra un concepto del negocio, va
> en espanol; donde nombra una construccion del programa, va en ingles.

---

## 1. Que constituye una operacion

Una operacion es una **unidad de calculo analitico nombrada, cerrada y verificable en
aislamiento**. No es una funcion cualquiera: es un elemento del vocabulario del
producto.

Para que algo sea una operacion debe cumplir las cinco condiciones:

1. **Es invocable por el modelo pero no definible por el.** El modelo elige cual usar
   y con que argumentos; no puede crear una nueva ni alterar su comportamiento.
2. **Declara sus parametros en conceptos del dominio**, nunca en estructura fisica.
   Recibe `metrica = facturacion_neta`, jamas `tabla = ventas, campo = importe_neto`.
3. **Expresa su necesidad de datos como una o mas Peticiones de datos.** No accede a
   la fuente: la describe.
4. **Su calculo es determinista y reproducible.** Con las mismas entradas produce
   siempre la misma salida. No consulta al modelo de lenguaje en ningun momento.
5. **Declara que produce**: hechos, resultado analitico, conjunto de datos, o una
   combinacion.

### Que NO es una operacion

| No es operacion | Por que | A quien pertenece |
|---|---|---|
| Ejecutar SQL arbitrario | Rompe la cerradura del catalogo | A nadie: prohibido |
| Resolver que significa "facturacion" | Es conocimiento semantico | Conocimiento del negocio |
| Resolver que tabla contiene las ventas | Es mapeo fisico | Conocimiento del negocio |
| Traducir una peticion al dialecto del motor | Es ejecucion | Acceso a datos |
| Decidir si hace falta una segunda ronda | Es orquestacion | Ejecutor |
| Redactar la explicacion del resultado | Es sintesis | Sintesis de respuesta |

### Regla de extension

Agregar una capacidad al producto significa **agregar una ficha de operacion, su
calculo, sus tests y sus casos de evaluacion**. Nunca significa tocar el Ejecutor, el
Conocimiento ni el Acceso a datos. Si agregar una operacion obliga a modificar otra
caja, la operacion esta mal definida o la caja esta mal cortada.

Esta es la via principal de escalabilidad del sistema y conviene protegerla: es lo
que permite que el producto crezca sin que crezca su riesgo.

---

## 2. Objetivo, operacion y criterio de suficiencia

Tres conceptos que se confunden con facilidad y que aqui se separan de forma estricta.

| Concepto | Que es | Quien lo elige | Quien lo evalua |
|---|---|---|---|
| **Objetivo** | Que se quiere lograr con el turno | El modelo, de un catalogo cerrado | El Ejecutor |
| **Operacion** | Un paso de calculo concreto | El modelo, de un catalogo cerrado | Operaciones (validez) |
| **Criterio de suficiencia** | Cuando el objetivo esta satisfecho | Nadie: lo declara el objetivo | El Ejecutor, deterministamente |

El punto central: **el criterio de suficiencia pertenece al objetivo, no a la
operacion ni al modelo**. Es lo que impide que el sistema entre en bucle o se rinda
temprano, y lo que convierte "ya se lo suficiente" en una comparacion numerica en vez
de un juicio.

### Duenez del catalogo de objetivos

El catalogo de objetivos **pertenece a esta parte**, junto con el de operaciones. No es
un artefacto suelto ni vive en el Ejecutor.

Razon: el criterio de suficiencia de un objetivo se expresa **sobre hechos**, y los
hechos los publican las operaciones. Objetivos y operaciones se versionan juntos por el
mismo motivo por el que el modelo semantico y el mapeo fisico viven en una sola caja:
cambiar uno sin el otro produce un sistema incoherente.

No pertenece a Conocimiento del negocio: los objetivos no son vocabulario del negocio
del cliente, son **capacidades del producto**. Son los mismos para todas las conexiones.

### Catalogo de objetivos (version inicial)

| Objetivo | Pregunta tipica | Criterio de suficiencia | Umbral configurable |
|---|---|---|---|
| `consultar_metrica` | "¿Cuanto vendimos en julio?" | La metrica se obtuvo para el alcance completo pedido | — |
| `comparar` | "¿Julio contra junio?" | Ambos terminos obtenidos, comparables y con igual definicion | — |
| `rankear` | "¿Los diez mejores clientes?" | Se obtuvieron N elementos ordenados sobre el universo autorizado completo | N por defecto = 10 |
| `explicar_variacion` | "¿Por que cayo la facturacion?" | La contribucion acumulada de los factores identificados alcanza el umbral | 70 % por defecto |
| `detectar_anomalia` | "¿Hay algo raro esta semana?" | Se evaluo la serie completa del periodo con el criterio declarado | Sensibilidad |
| `describir_conjunto` | "¿Quienes fueron los invitados?" | Se obtuvo el conteo total y una vista previa representativa | — |
| `explorar` | "¿Como viene el negocio?" | Se cubrieron todas las dimensiones declaradas del panorama | Dimensiones del panorama |

Un objetivo que no esta en el catalogo no puede ser propuesto. Si el modelo interpreta
una intencion que no mapea a ningun objetivo, la salida correcta es
`fuera_de_alcance`, con explicacion de que si puede hacerse.

### Relacion entre los tres

```mermaid
flowchart LR
    OBJ[Objetivo declarado] --> CRIT[Criterio de suficiencia]
    OBJ --> PLAN[Plan de analisis]
    PLAN --> OP1[Operacion 1]
    PLAN --> OP2[Operacion 2 condicional]
    OP1 --> HEC[Hechos producidos]
    OP2 --> HEC
    HEC --> CRIT
    CRIT -->|satisfecho| FIN[Sintesis]
    CRIT -->|insuficiente| REP[Replanificacion acotada]
```

---

## 3. Que declara una operacion — ficha de operacion

Toda operacion se define mediante una ficha con los mismos catorce campos. La ficha es
parte del contrato: sin ella la operacion no existe para el sistema.

| Campo | Contenido |
|---|---|
| Nombre canonico | Identificador estable de la operacion |
| Proposito | Una frase, en lenguaje de negocio |
| Parametros | Nombre, tipo de dominio, obligatorio u opcional, valor por defecto |
| Precondiciones semanticas | Que debe confirmar Conocimiento antes de ejecutar |
| Requisito de universo | Autorizado, o completo (ver seccion 4) |
| Peticiones de datos | Cuantas emite y con que forma |
| Calculo | Que hace deterministamente sobre los datos recibidos |
| Productos | Hechos, resultado analitico, conjunto de datos |
| Hechos publicados | Tipos de hecho que emite, con su forma |
| Condiciones de rechazo | Causas propias, ademas de las genericas |
| Coste | Numero de accesos a la fuente en el peor caso |
| Verificacion | Como se prueba en aislamiento |
| Reutilizable | Si puede resolverse desde un conjunto activo valido |
| Version | Version de la ficha, para trazabilidad de resultados historicos |

### Nota sobre "hechos publicados" — cambio respecto de la traza nominal

En la traza, los hechos los armaba el Ejecutor a partir de los resultados. Se corrige:
**cada operacion declara y publica sus propios hechos**. Motivos:

- El Ejecutor deja de necesitar conocimiento sobre que significa cada resultado, lo
  que era su principal riesgo estructural.
- La respuesta minima determinista se vuelve construible por plantilla a partir del
  tipo de hecho, sin logica especial por operacion.
- La validacion de salida puede comprobar tipos de hecho, no solo cifras sueltas.
- Agregar una operacion no obliga a tocar el Ejecutor. Coherente con la regla de
  extension.

Un hecho declara:

| Campo | Contenido |
|---|---|
| Identificador | Estable dentro del turno |
| `turno_id` | Turno que lo produjo. **Frontera de consistencia** |
| `objetivo_id` | Objetivo al que pertenece |
| Tipo | Tipo de hecho declarado en la ficha |
| Valor | Magnitud, texto o elemento, segun el tipo |
| Unidad | Cuando aplica |
| Alcance | Universo al que corresponde, incluido el alcance autorizado |
| Momento de captura | De los datos que lo produjeron, no de su publicacion |
| Naturaleza de la evidencia | Original o reconstruida |
| Invocacion | Referencia a la invocacion que lo produjo |

`turno_id` y `objetivo_id` son los dos ejes de aislamiento de la evidencia, y ambos se
comprueban mecanicamente en la validacion de salida. El **momento de captura por hecho**
es necesario porque una misma respuesta puede apoyarse en hechos capturados en momentos
distintos: reanudaciones y reutilizacion de conjuntos activos lo producen de forma
rutinaria.

---

## 4. Requisito de universo

El punto donde permisos y analisis se cruzan, y el mas facil de resolver mal.

Una operacion declara si su calculo es correcto sobre el **universo autorizado** del
usuario, o si exige el **universo completo** de la conexion.

### Regla dura

> Una operacion que necesita un denominador, un total o un universo mayor que el
> autorizado **se rechaza**. Jamas se calcula sobre el subconjunto autorizado y se
> presenta como si fuera el total.

Esta regla existe porque el modo de fuga tipico no es mostrar filas prohibidas: es
mostrar un **porcentaje sobre un total prohibido**, que permite deducirlo.

### Clasificacion

| Operacion | Universo | Motivo |
|---|---|---|
| `consultar_metrica` | Autorizado | El resultado es correcto dentro del alcance y se declara como tal |
| `comparar_periodos` | Autorizado | Ambos terminos comparten alcance |
| `serie_temporal` | Autorizado | Idem |
| `desglosar` | Autorizado | El desglose es del alcance autorizado y se declara como tal |
| `rankear` | Autorizado | Un ranking dentro del alcance es valido si se declara el alcance |
| `descomponer_variacion` | Autorizado | La descomposicion es de la variacion observada dentro del alcance |
| `contar` | Autorizado | — |
| `describir_conjunto` | Autorizado | — |
| `detectar_anomalia` | Autorizado | La serie autorizada es una serie legitima |
| `calcular_participacion` | **Completo** | El denominador es el total; si no esta autorizado, se rechaza |
| `comparar_contra_pares` | **Completo** | Requiere el universo de pares, que puede no estar autorizado |

### Regla de declaracion de alcance

Toda operacion sobre universo autorizado **publica el alcance como parte de sus
hechos**, y Sintesis esta obligada a reflejarlo. "Los diez mejores clientes" bajo un
contexto restringido se responde como "los diez mejores **entre tus clientes**". Un
resultado correcto presentado sin su alcance es un resultado enganoso.

---

## 5. Productos de una operacion

Tres productos posibles, no excluyentes.

| Producto | Que es | Destino |
|---|---|---|
| **Hechos** | Afirmaciones atomicas con valor, unidad y alcance | Sintesis, validacion de salida, respuesta minima |
| **Resultado analitico** | Cifras y metadatos del calculo | Respuesta, evaluacion de condiciones y suficiencia |
| **Conjunto de datos** | Filas materializadas con su descriptor | Vista previa, paginado, exportacion, reutilizacion |

### Regla de materializacion

> **Toda ejecucion de una Peticion de datos produce un conjunto materializado con su
> descriptor, sin importar el numero de filas.** El umbral de vista previa determina
> cuanto viaja dentro de la respuesta, no si el conjunto existe. El umbral de
> materializacion maxima es un limite superior: por encima, la operacion se rechaza.

Motivo de la correccion: si un resultado de doce filas no se materializa, exportarlo
obliga a re-ejecutar y el archivo puede no coincidir con lo que el usuario vio. La
consistencia del snapshot y la reutilizacion por cobertura exigen que el conjunto
exista siempre, no solo cuando es grande.

Consecuencia: **la existencia de un conjunto no es informacion**. Lo que informa al
usuario es la relacion entre filas totales y filas mostradas, que se declara siempre
de forma explicita.

### Descriptor en dos capas

Un conjunto materializado guarda datos obtenidos de la fuente y, con frecuencia,
columnas calculadas encima. Su descriptor refleja ambas cosas por separado:

| Capa | Contenido | Para que sirve |
|---|---|---|
| **Obtenido** | Vocabulario de Peticion de datos: metricas, dimensiones, periodo, granularidad, filtros, universo | Verificar cobertura de una peticion nueva |
| **Derivado** | Columnas calculadas en zona determinista y el calculo que las produjo | Verificar si una pregunta de seguimiento se resuelve reordenando, filtrando o recortando lo ya presentado |

La distincion importa: de una columna de contribucion ya calculada se puede derivar
"los diez de mayor caida", pero **no** se puede derivar una metrica nueva. Mezclar
ambas capas en un solo descriptor haria pasar por cubierta una peticion que no lo esta.

### Coherencia de captura en calculos derivados

> **Si varios hechos participan de un mismo calculo derivado, deben provenir de una
> captura compatible.** Si no la comparten, se re-ejecutan los pasos necesarios bajo una
> **captura comun** antes de calcular.

Es la unica regla del diseno que protege la **coherencia numerica entre hechos**. Todas
las demas protegen la correccion de cada hecho por separado, lo cual no alcanza: hechos
individualmente correctos obtenidos sobre estados distintos de la fuente producen
respuestas que se contradicen a si mismas.

Aparece de forma rutinaria en dos situaciones: cuando un paso reutiliza un conjunto
activo y otro consulta de nuevo, y cuando un analisis se reanuda y sus pasos se
ejecutaron en momentos distintos.

**Cuando aplica:** un calculo es derivado cuando uno de sus insumos es un hecho de otro
paso. La ficha de la operacion declara esa dependencia; el Ejecutor la comprueba antes
de invocar. Operaciones sin insumos de otros pasos no estan sujetas a esta regla, y sus
hechos pueden convivir con capturas distintas siempre que el alcance declare el rango.

### Conjuntos activos de la sesion

La sesion mantiene un numero acotado de conjuntos activos, no uno solo. La
verificacion de validez se evalua contra todos ellos y gana el mas reciente que la
satisfaga. El desalojo ocurre por vencimiento de frescura, por invalidacion semantica
o por capacidad, en ese orden de prioridad.

### Tabla de productos por operacion

Todas las operaciones materializan conjunto: la columna indica que contiene.

| Operacion | Hechos | Resultado analitico | Contenido del conjunto |
|---|---|---|---|
| `consultar_metrica` | Si | Si | La cifra y su alcance |
| `comparar_periodos` | Si | Si | Los dos valores por periodo |
| `serie_temporal` | Si | Si | Los puntos de la serie |
| `desglosar` | Si | Si | La metrica por cada elemento de la dimension |
| `rankear` | Si | Si | Los elementos ordenados |
| `descomponer_variacion` | Si | Si | Elementos con variacion y contribucion |
| `contar` | Si | Si | El conteo y sus filtros |
| `describir_conjunto` | Si | Si | Las filas del universo descrito |
| `detectar_anomalia` | Si | Si | La serie completa, con marca de anomalia |
| `calcular_participacion` | Si | Si | Elemento, total y participacion |

---

## 6. Peticion de datos — como una operacion expresa su necesidad

La Peticion de datos es el lenguaje interno canonico. Lo construye Operaciones, lo
traduce Acceso a datos, y **el Descriptor de cobertura usa exactamente el mismo
vocabulario**, que es lo que hace verificable la reutilizacion.

### Campos

| Campo | Contenido |
|---|---|
| Metricas | Conceptos canonicos ya resueltos por Conocimiento |
| Dimensiones | Conceptos canonicos de agrupacion |
| Periodo | Rango de fechas resuelto, con el campo temporal aplicable |
| Granularidad | Dia, semana, mes, trimestre, anio, o total |
| Filtros | Dimension canonica, operador, valores |
| Orden | Campo y sentido |
| Limite | Maximo de filas solicitadas |
| Universo requerido | Autorizado o completo |
| Restricciones de acceso | Inyectadas por Contexto de acceso, no negociables |

### Ejemplo concreto — de la traza nominal

Operacion `comparar_periodos`, primera peticion:

```
metricas:      facturacion_neta
dimensiones:   (ninguna)
periodo:       2026-06-01 .. 2026-07-31, campo temporal: fecha de emision
granularidad:  mes
filtros:       (ninguno)
orden:         periodo ascendente
limite:        (no aplica)
universo:      autorizado
restricciones: (ninguna, contexto ctx_884 sin restriccion de filas)
```

Operacion `descomponer_variacion`, segunda peticion:

```
metricas:      facturacion_neta
dimensiones:   cliente
periodo:       2026-06-01 .. 2026-07-31, campo temporal: fecha de emision
granularidad:  mes
filtros:       (ninguno)
orden:         (se ordena en el calculo, no en la fuente)
limite:        (no aplica)
universo:      autorizado
restricciones: (ninguna)
```

Devuelve 1.240 filas por dos periodos. El calculo de variacion absoluta, contribucion
y contribucion acumulada ocurre en zona determinista, **no en la fuente**: eso lo hace
identico en cualquier motor y testeable sin base de datos.

### Ejemplo de descriptor de cobertura resultante

```
metricas:        facturacion_neta
dimensiones:     cliente
periodo:         2026-06-01 .. 2026-07-31
granularidad:    mes
filtros:         (ninguno)
universo:        todos los clientes con actividad en el rango
columnas:        cliente, facturacion junio, facturacion julio, variacion, contribucion
contexto:        ctx_884
version semantica: sem_v7
captura:         2026-08-15 14:32
```

Mismo vocabulario que la peticion, mas cuatro campos de validez. La comparacion entre
una peticion nueva y este descriptor es una operacion mecanica, sin juicio.

---

## 7. Condiciones de rechazo

Toda operacion puede rechazar. **El rechazo siempre lleva causa y accion sugerida**,
nunca es un booleano: la causa determina si el sistema informa, pide aclaracion,
acota, o consulta de nuevo.

### Causas genericas

| Causa | Origen | Accion sugerida |
|---|---|---|
| `concepto_inexistente` | Conocimiento | Ofrecer conceptos disponibles |
| `concepto_no_autorizado` | Contexto de acceso | Informar limitacion, sin revelar el concepto |
| `dimension_incompatible` | Conocimiento | Ofrecer dimensiones combinables |
| `granularidad_no_disponible` | Conocimiento | Ofrecer la granularidad minima real |
| `parametros_invalidos` | Operaciones | Corregir la invocacion (reintento del plan) |
| `universo_insuficiente` | Operaciones + Contexto | Informar que el calculo no es posible con el alcance |
| `limite_filas_excedido` | Acceso a datos | Pedir acotar o agregar |
| `limite_tiempo_excedido` | Acceso a datos | Pedir acotar el periodo |
| `periodo_sin_datos` | Acceso a datos | Ofrecer periodos cercanos con datos |
| `fuente_no_disponible` | Acceso a datos | Interrupcion recuperable |

### Regla de silencio selectivo

`concepto_no_autorizado` se informa como limitacion de alcance **sin nombrar el
concepto**. Decir "no podes ver el margen" confirma que el margen existe y esta
calculado. Coherente con el filtrado del catalogo entregado al modelo: si no aparece
en el catalogo, tampoco aparece en el rechazo.

---

## 8. Catalogo inicial — fichas

### 8.1 `comparar_periodos`

| Campo | Contenido |
|---|---|
| Proposito | Obtener una metrica en dos periodos y su variacion |
| Parametros | `metrica` (obligatorio), `periodo_actual` (obligatorio), `periodo_comparacion` (obligatorio), `filtros` (opcional) |
| Precondiciones | Metrica existente, comparable en el tiempo, ambos periodos resueltos a fechas |
| Universo | Autorizado |
| Peticiones | Una, con granularidad correspondiente a los periodos |
| Calculo | Diferencia absoluta y relativa |
| Productos | Hechos, resultado analitico |
| Hechos | `valor_periodo` x2, `variacion_absoluta`, `variacion_relativa` |
| Rechazo propio | `periodos_solapados`, `periodos_de_distinta_longitud` (advertencia, no rechazo) |
| Coste | 1 acceso |
| Verificacion | Datos fijos de dos periodos, comprobar variacion esperada |
| Reutilizable | Si, si el conjunto activo cubre ambos periodos y la granularidad es derivable |

**Ejemplo de salida (traza nominal):**
`valor_periodo(2026-06) = 4.812.400 ARS` · `valor_periodo(2026-07) = 4.176.900 ARS` ·
`variacion_absoluta = -635.500 ARS` · `variacion_relativa = -13,2 %` ·
alcance: todos los clientes.

---

### 8.2 `descomponer_variacion`

| Campo | Contenido |
|---|---|
| Proposito | Repartir una variacion observada entre los elementos de una dimension |
| Parametros | `metrica`, `periodo_actual`, `periodo_comparacion`, `dimension`, `umbral_cobertura` (por defecto del objetivo), `filtros` (opcional) |
| Precondiciones | Metrica y dimension combinables; dimension con cardinalidad manejable |
| Universo | Autorizado |
| Peticiones | Una, con la dimension como agrupacion |
| Calculo | Variacion por elemento, contribucion sobre la variacion total, orden descendente por magnitud de contribucion, corte por contribucion acumulada |
| Productos | Hechos, resultado analitico, conjunto de datos |
| Hechos | `contribuyente_principal` (uno por elemento sobre el corte), `cobertura_explicada`, `cardinalidad_dimension` |
| Rechazo propio | `cardinalidad_excesiva` (dimension con demasiados elementos distintos), `variacion_nula` (no hay nada que descomponer) |
| Coste | 1 acceso |
| Verificacion | Conjunto fijo con contribuciones conocidas; comprobar suma de contribuciones = 100 % |
| Reutilizable | Si, si el conjunto activo contiene la dimension como columna |

**Coherencia de captura (obligatoria):** la contribucion reparte **la variacion total**,
que proviene de otro paso. Si ese paso y este provienen de capturas distintas de la
fuente, la suma de contribuciones deja de dar el 100 % de la variacion informada: dos
cifras individualmente correctas que **no cierran entre si**. Ver la regla general en la
seccion 5bis.

**Nota de diseno:** la contribucion se calcula **sobre la variacion**, no sobre el
total. Un cliente que representa el 2 % de la facturacion puede explicar el 40 % de la
caida. Confundir ambas cosas es el error mas comun en este tipo de analisis.

**Ejemplo de salida (traza nominal):**
tres `contribuyente_principal` · `cobertura_explicada = 72 %` ·
`cardinalidad_dimension = 1.240` · conjunto `ds_301`.

---

### 8.3 `rankear`

| Campo | Contenido |
|---|---|
| Proposito | Ordenar elementos de una dimension por una metrica |
| Parametros | `metrica`, `dimension`, `periodo`, `n` (por defecto 10), `sentido` (por defecto descendente), `filtros` (opcional) |
| Precondiciones | Metrica y dimension combinables |
| Universo | Autorizado, con declaracion obligatoria de alcance |
| Peticiones | Una, con orden y limite en la fuente |
| Calculo | Ninguno adicional: el orden lo resuelve la fuente |
| Productos | Hechos, resultado analitico, conjunto si supera umbral |
| Hechos | `elemento_ranking` x n, `total_universo`, `alcance_universo` |
| Rechazo propio | `n_excesivo` |
| Coste | 1 acceso |
| Verificacion | Conjunto fijo con orden conocido; comprobar empates y estabilidad del orden |
| Reutilizable | Si, si el conjunto activo contiene la dimension y la metrica |

---

### 8.4 Resto del catalogo inicial

| Operacion | Proposito | Productos distintivos |
|---|---|---|
| `consultar_metrica` | Valor de una metrica en un alcance | `valor_metrica` |
| `desglosar` | Una metrica abierta por los elementos de una dimension, sin ordenar ni comparar | `valor_por_elemento` x n, `cardinalidad_dimension`, `alcance_universo` |
| `serie_temporal` | Evolucion de una metrica por granularidad | `punto_serie` x n, `tendencia` |
| `contar` | Cardinalidad de un universo bajo filtros | `conteo` |
| `describir_conjunto` | Conteo, columnas y vista previa representativa de un universo | `conteo`, `columnas_disponibles`, vista previa |
| `detectar_anomalia` | Puntos fuera del comportamiento esperado de una serie | `punto_anomalo` x n, `criterio_aplicado` |
| `calcular_participacion` | Peso de un elemento sobre un total | `participacion`, `total_universo` (requiere universo completo) |

Diez operaciones y siete objetivos. Deliberadamente pocas: coherente con el principio
de que un conjunto acotado de capacidades coherentes vale mas que un catalogo extenso
a medias. **El catalogo no crece hasta haber corrido el banco de preguntas reales**:
la evidencia de que falta una operacion es que preguntas legitimas caigan en
`fuera_de_alcance`, no la intuicion de que podria hacer falta.

`desglosar` y `rankear` se parecen y conviene no confundirlas: `desglosar` responde
"cuanto vendio cada region", `rankear` responde "las cinco mejores regiones". La
primera devuelve el universo, la segunda un recorte ordenado. Una pregunta que pide
las dos cosas usa `desglosar` y ordena sobre el conjunto derivado.

---

## 9. Estructura interna de la parte

```mermaid
flowchart TB
    subgraph OPE[8 Operaciones analiticas]
        CAT[Catalogo de fichas]
        VAL[Validador de invocacion]
        PET[Constructor de peticion de datos]
        NUC[Nucleo de calculo determinista]
        PUB[Publicador de hechos y productos]
    end

    EJE[7 Ejecutor] -->|invocacion propuesta| VAL
    VAL --> CAT
    CON[4 Conocimiento] -.->|especificacion semantico-fisica| PET
    ACC[2 Contexto de acceso] -.->|restricciones| PET
    VAL --> PET
    PET -->|peticion de datos| DAT[9 Acceso a datos]
    DAT -->|filas| NUC
    NUC --> PUB
    PUB -->|hechos, resultado analitico| EJE
    PUB -->|conjunto + descriptor| CJD[10 Conjuntos de datos]
```

Ningun sub-bloque introduce entradas o salidas que la caja padre no tenga.

| Sub-bloque | Responsabilidad |
|---|---|
| Catalogo de fichas | Define que operaciones existen y que declaran. Es dato, no logica |
| Validador de invocacion | Comprueba nombre, parametros, tipos y precondiciones |
| Constructor de peticion | Combina calculo pedido + especificacion de Conocimiento + restricciones de acceso |
| Nucleo de calculo | Matematica del dominio sobre filas ya reducidas. Sin acceso a fuente ni a modelo |
| Publicador | Emite hechos, resultado analitico y, si corresponde, conjunto con descriptor |

El nucleo de calculo es la unica parte con logica de negocio real y es
**completamente testeable con datos fijos**, sin base de datos y sin modelo de
lenguaje. Esa propiedad es intencional y conviene defenderla en la implementacion.

---

## 10. Verificacion de la parte

| Nivel | Que verifica | Como |
|---|---|---|
| Ficha | Toda operacion del catalogo declara los catorce campos | Prueba estructural sobre el catalogo |
| Validacion | Invocaciones invalidas se rechazan con la causa correcta | Casos de invocacion malformada |
| Construccion de peticion | La peticion generada corresponde al calculo y lleva las restricciones de acceso | Comparacion contra peticion esperada |
| Calculo | Resultados correctos sobre datos fijos | Datos de prueba con resultado conocido |
| Propiedades | Invariantes matematicos independientes de los datos | Suma de contribuciones = 100 %; ranking estable ante empates; variacion consistente con los valores |
| Universo | Operaciones de universo completo se rechazan bajo contexto restringido | Casos con contexto restringido |
| Productos | Materializacion ocurre exactamente al superar el umbral | Casos en el limite del umbral |

Las pruebas de propiedades son especialmente valiosas aqui: capturan errores que los
datos de ejemplo no revelan, y son el tipo de verificacion que distingue un calculo
analitico correcto de uno que funciona con el caso probado.

---

## 11. Decisiones registradas en esta parte

| Decision | Supuesto | Senal de invalidacion | Tipo |
|---|---|---|---|
| Catalogo cerrado de operaciones | Las preguntas reales de negocio se cubren con un catalogo acotado | Mas del 30 % de las preguntas de prueba caen en `fuera_de_alcance` | Sistema |
| Catalogo cerrado de objetivos con criterio de suficiencia | La terminacion puede decidirse deterministamente | Aparecen objetivos legitimos sin criterio expresable numericamente | Sistema |
| Cada operacion publica sus propios hechos | El Ejecutor no necesita conocer la semantica de los resultados | Un tipo de hecho requiere logica de composicion en el Ejecutor | Sistema |
| Calculo derivado en zona determinista, no en la fuente | El resultado reducido cabe comodamente en memoria | Un calculo necesita operar sobre volumenes que no se pueden traer | Sistema |
| Rechazo de operaciones que exigen universo no autorizado | Es preferible no responder a responder con un total enganoso | Aparece un caso donde el rechazo bloquea un uso legitimo y frecuente | Sistema |
| Materializacion siempre, con descriptor en dos capas | El coste de conservar conjuntos pequenos es despreciable frente a la consistencia que garantiza | La sesion acumula conjuntos hasta volverse costosa en almacenamiento | Sistema |
| Identificadores canonicos del dominio en espanol | El vocabulario de negocio es del cliente, no del codigo | Un consumidor externo de la API necesita identificadores en ingles | Sistema |
| El catalogo de objetivos pertenece a esta parte | El criterio de suficiencia se expresa sobre hechos, que publican las operaciones | Aparecen objetivos sin relacion con ninguna operacion | Sistema |
| Coherencia de captura obligatoria en calculos derivados | Hechos correctos sobre estados distintos producen respuestas incoherentes | Re-ejecutar por coherencia resulta prohibitivamente caro | Sistema |

---

## 12. Puntos abiertos

1. **Capacidad maxima de conjuntos activos por sesion.** Numero y tamano total
   pendientes de la revision adversarial, junto con la politica de desalojo.
2. **Cardinalidad maxima de una dimension** para `descomponer_variacion`: valor
   concreto pendiente de la revision adversarial.
3. **Criterio de `detectar_anomalia`**: el metodo estadistico concreto es decision de
   implementacion, pero el criterio aplicado debe publicarse como hecho.
4. **Comparacion de periodos de distinta longitud**: definido como advertencia; falta
   decidir si ademas se normaliza.


---

## Ubicacion en el proyecto

| Aspecto | Valor |
|---|---|
| Caja del diagrama | **8 Operaciones analiticas** |
| Codigo | `src/querypilot/analytics/` |
| Tests | `tests/analytics/` — subcarpetas: unit/ properties/ request/ universe/ |
| Sub-peldano de implementacion | 5.2 de `MAPA_AVANCE.md` |
| Estado actual | Pendiente |

### Modulos que la componen

| Modulo | Proposito |
|---|---|
| `objective_catalog` | Objetivos y criterios de suficiencia |
| `operation_catalog` | Fichas: parametros, universo, hechos publicados |
| `invocation_validator` | Firma, tipos y precondiciones |
| `request_builder` | Construye la peticion de datos canonica |
| `fact_publisher` | Emite hechos, resultado analitico y conjunto |
| `computations/` | Nucleo determinista: un archivo por operacion |

Las firmas concretas se definen al implementar. Este documento fija **el contrato**, no
la implementacion: cualquier firma que lo respete es valida.

### Pasos de implementacion

1. Modelo de ficha de operacion y de objetivo.
2. Catalogos cargados como dato, no como logica.
3. Validador de invocacion.
4. Constructor de peticion de datos.
5. Nucleo de calculo, una operacion por vez, con sus propiedades.
6. Publicador de hechos y productos.
7. Requisito de universo y declaracion de alcance.

### Nivel de formato

Los modelos canonicos que esta parte recibe y entrega estan definidos en
`14_contratos_formato.md`. La **regla de herencia estricta** sigue vigente: si un formato
no puede transportar algo de este contrato, se revisa este contrato, no el formato.
