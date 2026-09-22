<!-- README.md -->
# QueryPilot

Convierte preguntas de negocio en lenguaje natural en **analisis verificables** sobre una
base de datos existente. El modelo de lenguaje interpreta y redacta; un nucleo
determinista valida, calcula y controla que puede afirmarse.

> **El modelo propone planes y redacciones; el sistema determinista valida, autoriza,
> ejecuta y controla que afirmaciones pueden salir. Ninguna afirmacion sale sin haber
> sido validada contra evidencia producida deterministamente.**

---

## El problema

Quien dirige un negocio tiene los datos y no tiene las respuestas. Los tableros responden
preguntas previstas; las consultas directas exigen conocimiento tecnico; y los asistentes
que generan SQL automaticamente producen cifras **plausibles y no verificables**, que es
el peor resultado posible en un contexto de decision.

El problema no es generar consultas. Es producir respuestas **en las que se pueda confiar
sin tener que comprobarlas a mano**.

## Como lo resuelve

| Decision | Consecuencia |
|---|---|
| El modelo **no escribe SQL**: invoca operaciones de un catalogo cerrado | Elimina el SQL alucinado de raiz |
| Una **capa semantica explicita** declara que significa cada concepto y de donde sale | El agente no adivina que es `est_cod = 9`: el integrador se lo ensena una vez |
| La reduccion ocurre **en la fuente**; el modelo ve resultados agregados, nunca filas crudas | Escala, cuesta poco y no expone datos |
| Cada afirmacion se **vincula a un hecho** producido por una invocacion registrada | Trazabilidad, no confianza |
| El sistema construye siempre una **respuesta minima determinista** | Si el modelo cae, la respuesta sale igual, sin elocuencia |
| **El turno es frontera de consistencia**: contexto, semantica y evidencia son constantes | Cifras que no se contradicen entre si |

---

## Estado

**QueryPilot — MVP 1 · Estado: experimental.**

El proyecto se construye en bloques incrementales, cerrando cada uno con contratos,
tests y verificacion estatica antes de avanzar. El primer MVP prueba el supuesto mas
riesgoso del proyecto:

> ¿Puede un modelo de lenguaje, apoyado en una capa semantica bien definida, convertir
> preguntas reales de negocio en propuestas estructuradas validas, de forma confiable?

**Implementado hasta ahora:**

- lenguaje canonico y contratos tipados;
- artefacto semantico versionado, con validador de integridad y version derivada del
  contenido;
- catalogos cerrados de objetivos y operaciones analiticas;
- puerto del modelo de lenguaje: doble determinista para pruebas y adaptador real
  sobre OpenAI;
- Interpretacion: propuesta estructurada, validacion determinista, construccion de
  `AnalysisPlan`, replanificacion;
- banco congelado de 60 casos de evaluacion, con las metricas A1, A2, A4, B1 y B1+B2;
- CLI de evaluacion, con reportes auditables y un guardarrail de hasta tres
  iteraciones experimentales sobre el artefacto semantico;
- manual navegable con MkDocs (ver mas abajo).

El flujo que existe hoy llega hasta acá:

```
pregunta en lenguaje natural
  -> interpretacion estructurada
  -> validacion determinista
  -> AnalysisPlan
  -> evaluacion contra el banco de 60 casos
```

**QueryPilot todavia no ejecuta ese plan contra una base de datos real.** La
ejecucion de operaciones, el acceso real a datos y las etapas posteriores (sintesis
de respuesta, sesion, API publica) quedan para el MVP 2 en adelante.

La corrida real del banco de 60 casos contra OpenAI **todavia esta pendiente**: el
instrumento esta completo y probado con un doble determinista, pero correrla de
verdad consume la API y tiene costo, asi que es una decision deliberada, no una
tarea sin terminar. Umbral duro de esa corrida cuando ocurra: **error silencioso
<= 5 %** — un sistema que pregunta es usable; uno que se equivoca con confianza no
lo es, por alta que sea su exactitud promedio.

Ver `MAPA_AVANCE.md` para el detalle vivo de que esta cerrado y que falta.

---

## Documentacion navegable (manual)

Ademas de este README, el repositorio tiene un manual navegable construido con
**MkDocs + Material**: presenta el MVP 1 con ejemplos, capturas y explicaciones
pensadas para alguien que no necesita conocer la arquitectura interna.

```bash
uv run mkdocs serve          # http://127.0.0.1:8000, con recarga en vivo
uv run mkdocs build --strict # genera el sitio estatico en site/
```

Tres capas de documentacion, cada una con un proposito distinto:

| Capa | Para que sirve |
|---|---|
| `README.md` (este archivo) | Vision rapida del repositorio: que es, como instalarlo, donde seguir |
| `manual/` (servido con MkDocs) | Guia de uso y presentacion del MVP 1: ejemplos, evaluacion, limitaciones |
| `docs/` | Especificacion tecnica: contratos, decisiones de arquitectura, invariantes |

`manual/` no reemplaza a `docs/`: cuando algo tecnico hace falta para entender el
producto, el manual lo resume en lenguaje llano y enlaza al documento interno
correspondiente, que sigue siendo la fuente de verdad.

---

## Desarrollo asistido por IA

QueryPilot tambien funciona como ejercicio de **AI-assisted software engineering**.

El desarrollo utiliza **Claude Code y agentes de IA** como herramientas de implementacion,
analisis y revision. La arquitectura, los contratos, los invariantes y los criterios de
aceptacion se mantienen explicitamente en `docs/` y guian el trabajo de los agentes.

El flujo de trabajo es incremental:

1. Se define el alcance del bloque y sus contratos.
2. El agente propone la implementacion y señala decisiones no resueltas.
3. Las decisiones arquitectonicas se revisan antes de modificar codigo.
4. Cada bloque se valida con tests, `ruff` y `mypy`.
5. Solo despues de cerrar la unidad se realiza el commit.

La IA es una herramienta de implementacion y revision, no la fuente de verdad del
proyecto: **los contratos, los tests, la documentacion versionada, los invariantes y
las decisiones registradas determinan que comportamiento es valido**, no lo que un
agente haya producido en una sesion.

---

## Arranque rapido

En el estado actual del MVP se puede validar y publicar el artefacto semantico, y
correr el banco de evaluacion, sin levantar infraestructura completa.

Requiere Python 3.13 y [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo>
cd querypilot

uv sync

# artefacto semantico: validar y publicar (ver manual para el detalle)
uv run querypilot-semantic validate demo
uv run querypilot-semantic publish demo

# instrumento de evaluacion (sin clave configurada, corre igual -- ver el manual)
uv run querypilot-eval --help

# verificacion determinista, sin modelo de lenguaje
uv run ruff check src tests
uv run mypy src
uv run pytest
```

Para una guia paso a paso con ejemplos y capturas, correr el manual localmente
(`uv run mkdocs serve`) o ver `manual/` directamente.

Docker, PostgreSQL y la API completa se incorporan progresivamente en los siguientes
bloques del plan de implementacion.

---

## Arquitectura

Diez partes. Ocho son deterministas y se verifican **sin base de datos y sin modelo de
lenguaje**. La incertidumbre esta contenida en dos.

| # | Parte | Responsabilidad |
|---|---|---|
| 1 | Frontera de servicio | Contrato publico: autenticar, recibir, entregar, paginar, exportar |
| 2 | Contexto de acceso | Identidad, alcance de datos y operaciones permitidas |
| 3 | Sesion de analisis | Conversacion, estado analitico, plan durable, auditoria |
| 4 | Conocimiento del negocio | Que significan los conceptos y de donde se obtienen |
| 5 | **Interpretacion y planificacion** | De lenguaje natural a propuesta estructurada |
| 6 | **Sintesis de respuesta** | De hechos y alcance a respuesta legible |
| 7 | Ejecutor de analisis | Coordina validaciones, ejecuta, decide terminacion, controla la salida |
| 8 | Operaciones analiticas | Catalogo cerrado de objetivos y operaciones |
| 9 | Acceso a datos | Traduce peticion canonica al dialecto y ejecuta dentro de limites |
| 10 | Conjuntos de datos | Custodia snapshots y decide su validez |

Las partes 5 y 6 son los dos unicos puntos de contacto con el modelo, **aislados entre
si**: si Sintesis conociera la intencion cruda, podria redactar lo que el usuario queria
oir en vez de lo que los datos dijeron.

Diagrama completo en `docs/01_metodo_solucion.md`.

### Prueba de que la arquitectura se sostiene

| Cambio | Que hay que tocar |
|---|---|
| Otro motor SQL | Una pieza de dialecto |
| Otro proveedor de modelo | El puerto del modelo |
| **Mismo motor, otra empresa o base de negocio** | **Solo el artefacto semantico** |
| Otro cliente, o un cliente de terceros | Nada |

Ninguna extension prevista toca el Ejecutor.

---

## Stack

**En uso actualmente:** Python 3.13 · Pydantic v2 · Typer · uv · ruff · mypy · pytest ·
OpenAI SDK (adaptador real de `ModelPort`) · MkDocs + Material (manual) · GitHub
Actions (CI y evaluacion manual)

**Arquitectura prevista:** FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 17 · Docker

En la arquitectura final, la base de negocio usa una conexion de **solo lectura verificada
al conectar**, que es lo que impide escribir por accidente en la base del cliente.

---

## Verificacion

Dos flujos con fronteras nitidas:

| | CI / verificacion determinista | Evaluacion con modelo |
|---|---|---|
| Prueba | Que el sistema es **correcto** | Que el modelo es **bueno** |
| Determinismo | Total | Ninguno |
| Coste | Cero | Por inferencia |
| Secretos | **Ninguno** | Clave del proveedor |

> **Los tests deterministas no dependen de ninguna clave de modelo.** Si una prueba la
> necesita, esta mal categorizada.

### Verificacion actual

```text
uv sync -> ruff -> mypy -> pytest -> validar artefacto semantico
```

Estado observado: **ruff y `ruff format` limpios**, **mypy sin errores sobre `src`**,
**181 tests de pytest aprobados**, sin ninguna clave de modelo configurada. Esa cifra
corresponde al estado del repositorio en el bloque cerrado mas reciente y va a crecer
con cada bloque nuevo — correr `uv run pytest` muestra el numero vigente.

### Flujo objetivo del sistema completo

```text
uv sync -> ruff -> mypy -> pytest con PostgreSQL real -> validar artefacto semantico
```

La evaluacion con modelo real se ejecuta por separado y de forma manual cuando cambian el
prompt, el modelo o el artefacto semantico.

---

## Documentacion

La documentacion forma parte del artefacto tecnico del proyecto y se versiona junto al
codigo. Las decisiones de arquitectura y los contratos son la referencia que deben cumplir
la implementacion y los agentes de desarrollo.

| Documento | Contenido |
|---|---|
| `manual/` (servido con MkDocs) | Manual de uso y presentacion del MVP 1 — ver "Documentacion navegable" arriba |
| `MAPA_AVANCE.md` | Donde estamos, que falta, supuestos activos |
| `docs/00_INDICE.md` | Indice y reglas de carga |
| `docs/01_metodo_solucion.md` | Dominio, invariantes, decisiones de sistema, trazas, supuesto riesgoso |
| `docs/02_vision_arquitectura.md` | Tecnologias, carpetas, tests, primer MVP |
| `docs/03`–`12_parte_*.md` | Un contrato por parte |
| `docs/13`–`16` | Decisiones tecnicas, formato, git, instrucciones para la IA |

---

## Licencia

MIT.
