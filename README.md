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

En desarrollo. El diseno esta cerrado; la implementacion arranca por el primer MVP.

**Peldano actual:** 5.1 — probar el supuesto mas riesgoso del proyecto.

> ¿Puede un modelo convertir preguntas reales de negocio en propuestas estructuradas
> validas, con una capa semantica bien definida?

Se mide con un banco de 60 preguntas congelado. Umbral duro: **error silencioso <= 5 %**.
Un sistema que pregunta es usable; uno que se equivoca con confianza no lo es, por alta
que sea su exactitud promedio.

Ver `MAPA_AVANCE.md`.

---

## Arranque rapido

Requiere Docker y [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo> && cd querypilot
cp .env.example .env          # completar credenciales
docker compose up -d --build  # levanta app + postgres
```

Desarrollo local:

```bash
uv sync
uv run querypilot-seed schema-only     # esquema de la base de demostracion
uv run querypilot-semantic validate demo
uv run pytest
uv run uvicorn querypilot.service_boundary.app:app --reload
```

Atajos en el `Makefile`: `make install`, `make check`, `make test`, `make up`.

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
| **Otra empresa, otra base de negocio** | **Nada. Solo el artefacto semantico** |
| Otro cliente, o un cliente de terceros | Nada |

Ninguna extension prevista toca el Ejecutor.

---

## Stack

Python 3.13 · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · PostgreSQL 17 ·
uv · ruff · mypy · pytest · Docker · GitHub Actions

Un solo motor, dos conexiones con permisos distintos: la de negocio usa un usuario de
**solo lectura verificada al conectar**, que es lo que impide escribir por accidente en
la base del cliente.

---

## Verificacion

Dos flujos con fronteras nitidas:

| | CI, en cada PR | Evaluacion, manual |
|---|---|---|
| Prueba | Que el sistema es **correcto** | Que el modelo es **bueno** |
| Determinismo | Total | Ninguno |
| Coste | Cero | Por inferencia |
| Secretos | **Ninguno** | Clave del proveedor |

> **El CI no tiene acceso a ninguna clave de modelo.** Si un test la necesita, esta mal
> categorizado. Hay una prueba estructural que lo verifica.

```
uv sync -> ruff -> mypy -> pytest con PostgreSQL real -> validar artefacto semantico
```

---

## Documentacion

| Documento | Contenido |
|---|---|
| `MAPA_AVANCE.md` | Donde estamos, que falta, supuestos activos |
| `docs/00_INDICE.md` | Indice y reglas de carga |
| `docs/01_metodo_solucion.md` | Dominio, invariantes, decisiones de sistema, trazas, supuesto riesgoso |
| `docs/02_vision_arquitectura.md` | Tecnologias, carpetas, tests, primer MVP |
| `docs/03`–`12_parte_*.md` | Un contrato por parte |
| `docs/13`–`16` | Decisiones tecnicas, formato, git, instrucciones para la IA |

---

## Licencia

MIT.
