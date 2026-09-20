<!-- docs/13_decisiones_tecnicas.md -->
<!-- Actualizado: 2026-08-16 -->
# 13 — Decisiones tecnicas

Solo decisiones de **implementacion**: reversibles sin reabrir el metodo. Las decisiones
de **sistema** viven en `01_metodo_solucion.md` seccion 10.

---

## 1. Versiones

Verificadas en agosto de 2026. **Los pines exactos viven en `uv.lock`**; en
`pyproject.toml` se declaran cotas, no versiones exactas.

| Paquete | Version verificada | Cota declarada | Nota |
|---|---|---|---|
| Python | 3.13 | `>=3.13,<3.14` | Declarada en `.python-version` |
| uv | 0.12.3 | — | Gestor de entorno |
| FastAPI | 0.141.1 | `>=0.141` | — |
| Pydantic | 2.12+ | `>=2.12` | v2 obligatorio |
| SQLAlchemy | 2.0.52 | `>=2.0.52,<2.1` | **La serie 2.1 sigue en beta**: no se adopta |
| Alembic | 1.19.0 | `>=1.19` | — |
| ruff | 0.16.3 | `>=0.16` | Ver seccion 3 |
| mypy | 1.20.1 | `>=1.20` | Modo estricto |
| PostgreSQL | 17 | — | Misma version en Compose y CI |

**Regla:** ninguna version se cita de memoria. Antes de agregar o subir una dependencia,
verificar la version publicada.

---

## 2. Gestion del proyecto

| Decision | Razon |
|---|---|
| `uv` + `pyproject.toml` + `uv.lock` | Una sola herramienta para entorno, dependencias y ejecucion |
| Dependencias de desarrollo en `[dependency-groups]` | No son extras opcionales del paquete |
| Sin `requirements.txt` | Obsoleto como fuente principal |
| `uv sync` / `uv run` como forma canonica | Evita divergencia entre entornos |

Obsoletos que **no se usan**: `setup.py`, `setup.cfg`, `black`, `flake8`, `isort`,
`pylint`, `tox`, `requests`, `argparse` en proyectos nuevos.

---

## 3. Calidad de codigo

**ruff 0.16 amplio el conjunto de reglas por defecto de 59 a 413.** Consecuencia
practica: no hace falta activar familias de reglas a mano, y conviene partir del conjunto
por defecto y **desactivar lo que estorbe**, en vez de acumular una lista larga de
`select`. Una configuracion heredada de versiones anteriores probablemente sobra.

| Decision | Razon |
|---|---|
| ruff para lint y formato | Reemplaza cuatro herramientas por una |
| Configuracion en `pyproject.toml` | Un solo archivo de configuracion |
| mypy en modo estricto | El proyecto es fuertemente tipado por diseno |
| Docstrings y comentarios en espanol | Convencion del proyecto |
| Identificadores de programa en ingles | Convencion del proyecto |
| Valores del dominio en espanol | Pertenecen al negocio del cliente |

---

## 4. Persistencia

| Decision | Razon |
|---|---|
| PostgreSQL unico, para sistema y conjuntos | Transaccion unica para plan, hechos y conjuntos: es lo que sostiene la reanudacion |
| Almacen de conjuntos **detras de un puerto** | Permite otra implementacion sin tocar Ejecutor ni Operaciones |
| `dataset_rows` con una fila por registro | Paginar y exportar salen nativos; no obliga a traer el conjunto a memoria |
| Importes en `NUMERIC` | Coherente con `Decimal` de punta a punta |
| Dos conexiones independientes | El usuario de solo lectura es la barrera real, no un chequeo cosmetico |
| Alembic para migraciones | El esquema evoluciona con el proyecto |

Descartados: memoria del proceso —no funciona con varios trabajadores, y paginar o
exportar son peticiones separadas que pueden caer en otro—; Redis —duplicaria la fuente
de verdad de la vigencia, que tiene cuatro ejes y solo uno se parece a un vencimiento
automatico—.

---

## 5. API y cliente

| Decision | Razon |
|---|---|
| REST/JSON como contrato canonico | Un tercero lo consume sin conocer la implementacion |
| SSE como modo de entrega, no segundo contrato | El objeto final es identico haya o no eventos |
| Sin WebSocket | Bidireccional no aporta hasta que exista cancelacion |
| Sin cancelacion | Introduce dominio nuevo para una funcion secundaria; el presupuesto de turno es la cota |
| Clave de API en cabecera | Funciona igual desde navegador y desde linea de comandos |
| `fetch` en modo streaming, no `EventSource` | `EventSource` no admite cabeceras arbitrarias; las alternativas romperian otra cosa |
| Cliente minimo servido por FastAPI | Un solo despliegue, sin origen cruzado |
| El cliente propio consume la API publica | Si necesitara un atajo interno, la frontera estaria incompleta |
| Importes serializados como cadena decimal | Un numero JSON se interpreta como coma flotante del otro lado |

---

## 6. Modelo de lenguaje

| Decision | Razon |
|---|---|
| Proveedor inicial OpenAI, **detras de un puerto de dos operaciones** | El dominio no conoce proveedor, modelo ni prompts |
| Salida estructurada por esquema derivado de Pydantic | El esquema que restringe y el contrato que valida son **el mismo objeto** |
| Sin llamada a funciones | No hay herramientas que elegir en tiempo real: el modelo devuelve estructura, el sistema ejecuta |
| Sin LangChain ni LangGraph como arquitectura | Planes, estados, criterios y reanudacion pertenecen a este sistema |
| Prompts como artefactos versionados | Permite regresion entre versiones de prompt |
| `prompt_version` en el registro durable | Sin ella se reconstruye que datos produjeron una respuesta, pero no que instruccion la redacto |

> **El esquema garantiza forma, no verdad.** La validacion de salida sigue siendo
> obligatoria.

**Corolario de evaluacion:** prompt y artefacto semantico se versionan por separado pero
se evaluan juntos. Una corrida mide la combinacion; un resultado solo es comparable
contra otro que varie uno de los dos, nunca los dos a la vez.

---

## 7. Artefacto semantico

| Decision | Razon |
|---|---|
| YAML como fuente de verdad | Legible, admite comentarios, revisable y comparable en control de versiones |
| Cargado y validado con Pydantic | Una definicion sirve para validar y para documentar |
| Metricas y dimensiones en archivos separados | Son lo que mas crece; el resto casi no cambia |
| Definicion de negocio y receta fisica **en el mismo bloque** | Separarlas invitaria a que divergieran |
| Version derivada del contenido | Escribirla a mano garantiza que alguien la olvide |
| Version publicada guardada en PostgreSQL | Descriptores y analisis guardados la referencian y deben resolverla |
| Sin interfaz grafica de configuracion | Un artefacto versionado con regresion es mas defendible que una consola de administracion |

---

## 8. Infraestructura y CI

| Decision | Razon |
|---|---|
| Docker + Compose con `app` y `postgres` | Reproducible y desplegable con un comando |
| Dos bases y **dos usuarios** en Compose | Sin dos usuarios, la prueba de solo lectura no prueba nada |
| Misma version de PostgreSQL en Compose y CI | Probar contra otro motor invalidaria las pruebas de dialecto |
| Sin Redis, sin Kubernetes, sin despliegue continuo | Alcance de MVP demostrativo |
| CI como puerta de merge | Codigo, contratos y artefacto deben ser validos antes de integrar |
| **CI sin ninguna clave de proveedor de modelo** | Cero red externa, cero coste por inferencia, cero secretos |
| Prueba estructural con variables del proveedor ausentes | Convierte la regla en propiedad ejercitada |
| Artefacto semantico de ejemplo en el repositorio | Sirve a CI, documentacion y experimento a la vez |
| Base sintetica reproducible, no datos reales | Esquema deliberadamente incomodo; un esquema de manual no prueba nada |

Cadena del CI: `uv sync` → `ruff` → `mypy` → `pytest` con PostgreSQL real →
validacion del artefacto de ejemplo.

La **evaluacion con modelo real** queda fuera de esa cadena y se dispara manualmente
cuando cambian prompts, modelo o artefacto semantico.

---

## 9. Convenciones

| Ambito | Convencion |
|---|---|
| Identificadores de programa | Ingles |
| Valores del dominio | Espanol, sin acentos ni `n` con virgulilla |
| Documentacion y comentarios | Espanol |
| Importes y magnitudes derivadas | `Decimal` de punta a punta; redondeo solo de presentacion |
| Rechazos | Valores de retorno, no excepciones |
| Excepciones | Reservadas para fallas operativas |
| Tests | Por parte de la solucion, despues por tipo de prueba |
| Primera linea de cada archivo | Comentario con su ruta relativa |
