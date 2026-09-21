<!-- MAPA_AVANCE.md -->
<!-- Actualizado: 2026-08-16 -->
# Mapa de avance — QueryPilot

## Estado actual

Fase actual: **Implementacion — sub-peldano 5.1 (primer MVP)**

Objetivo de la fase:
Probar el supuesto mas riesgoso del proyecto: que Interpretacion puede convertir
preguntas reales de negocio en propuestas estructuradas validas. La primera sesion de
desarrollo construye ese experimento, **no infraestructura ni arquitectura completa**.

## Escalera del proyecto

| # | Peldano | Estado | Evidencia de cierre | Tag |
|---|---------|--------|---------------------|-----|
| 1 | Problema y contexto | Cerrado | `01_metodo_solucion.md` secciones 1-3 | `hito/problema` |
| 2 | Metodo de solucion | Cerrado | Seis evidencias del criterio de cierre del Bloque 2 | `hito/metodo` |
| 3 | Tecnologias | Cerrado | `02_vision_arquitectura.md` + `13_decisiones_tecnicas.md` | `hito/tecnologias` |
| 4 | Contratos de formato | Cerrado | `14_contratos_formato.md`; herencia estricta verificada | `hito/contratos-formato` |
| 5 | Implementacion | Pendiente | Cierra cuando cierran todos sus sub-peldanos | — |
| 5.1 | └ primer MVP: interpretacion | **En progreso** | Banco corrido; metricas A1/A2/A4/B1 dentro de umbral | `hito/mvp-interpretacion` |
| 5.2 | └ operaciones y acceso a datos | Pendiente | `tests/analytics` y `tests/data_access` en verde; propiedades incluidas | `hito/parte-operaciones` |
| 5.3 | └ ejecutor | Pendiente | `tests/executor` en verde; `tests/system/limits` incluido | `hito/parte-ejecutor` |
| 5.4 | └ conjuntos de datos | Pendiente | `tests/datasets` en verde; `tests/system/recovery` incluido | `hito/parte-conjuntos` |
| 5.5 | └ sintesis y validacion de salida | Pendiente | `tests/synthesis` y `tests/executor/degradation` en verde | `hito/parte-sintesis` |
| 5.6 | └ sesion, frontera y cliente | Pendiente | `tests/analysis_session`, `tests/service_boundary` en verde | `hito/parte-frontera` |
| 6 | Verificacion de sistema | Pendiente | `tests/system` y `tests/structural` en verde; CI completo | `hito/verificacion` |
| 7 | Entrega | Pendiente | Compose levanta el sistema; `README.md` reproducible de cero | `hito/entrega` |

El numero es orden visual y puede cambiar al adaptar la escalera. El tag usa el nombre y
no cambia nunca.

### Faltantes del peldano en progreso (5.1)

- Base sintetica de demostracion generada, con esquema deliberadamente incomodo.
- Artefacto semantico de la conexion de demostracion, validado.
- Fichas de 10 operaciones y 7 objetivos, con hechos publicados declarados.
- Puerto del modelo con salida estructurada y su doble determinista.
- Interpretacion y validador estatico de plan.
- ~~Banco de 60 casos con interpretacion esperada, congelado antes de la primera
  corrida.~~ **Hecho** (bloque 1.7): `semantic/demo/evaluation/cases.yaml`, 60 casos,
  distribucion 40/15/15/10/10/10 verificada por test.
- ~~Comando de evaluacion y reporte de metricas.~~ **Hecho** (bloque 1.7):
  `querypilot-eval run <conexion>`, formulas de A1/A2/A4/B1/B2 y diagnosticos
  probadas con `DeterministicModelPort`.
- ~~Adaptador real de `ModelPort`.~~ **Hecho** (bloque 1.8): `OpenAIModelPort`
  (`model_port/openai_adapter.py`, Structured Outputs degradado -- ver
  `13_decisiones_tecnicas.md` seccion 6bis), `model_port/factory.py`
  (`QP_MODEL_PROVIDER`/`QP_MODEL_NAME`), fallas operativas separadas de las
  metricas de dominio, registro de cada corrida (`--report`, `--history-dir`)
  y guardarraíl de tres iteraciones. Probado entero sin `OPENAI_API_KEY`.
- **Corrida real del experimento y decision registrada sobre el supuesto —
  pendiente.** Necesita `OPENAI_API_KEY` y autorizacion explicita: consume el
  modelo real y tiene costo. Es la unica pieza de 5.1 que no se puede cerrar
  sin esa autorizacion.

## Proxima decision

Ninguna decision de diseno pendiente. La proxima decision del proyecto es **el veredicto
sobre el supuesto mas riesgoso**, que se toma con las metricas del sub-peldano 5.1.

Si A2 supera el 5 %, se aplica el pivote registrado en `01_metodo_solucion.md` seccion 12:
confirmacion explicita de la interpretacion antes de ejecutar.

## Bloqueos

- Ninguno.

## Supuestos activos

| Supuesto | Riesgo | Senal de invalidacion | Estado |
|---|---|---|---|
| El modelo convierte preguntas reales en propuestas validas con capa semantica | **Critico** | A2 > 5 % tras 3 iteraciones sobre el artefacto | Activo — en prueba |
| El catalogo acotado cubre las preguntas reales | Alto | Mas del 30 % del banco cae en fuera de alcance | Activo |
| El conteo previo es barato en el volumen objetivo | Medio | Conteos que superan el limite de tiempo con datos realistas | Activo |
| Dos rondas alcanzan | Medio | Mas del 20 % de los turnos termina con insuficiencia | Activo |
| Sintesis no contradice su propia evidencia | Medio | Interpretaciones contradictorias con los hechos citados en el banco | Activo |
| La capa semantica es sostenible para el integrador | Alto | Configurar una conexion cuesta mas de lo que ahorra | Activo — se mide con la segunda conexion real |
| La fuente no admite cargas retroactivas sobre periodos cerrados | Medio | Aparecen modificaciones sobre periodos cerrados | Activo |
| El catalogo cerrado de condiciones alcanza | Bajo | Un objetivo legitimo necesita una condicion compuesta | Activo |
| Reutilizar conjuntos ahorra consultas | Bajo | Casi ninguna pregunta se resuelve desde conjunto activo | Activo |
| La durabilidad de los conjuntos permite prometer reanudacion | — | — | **Resuelto**: conjuntos durables |

## Adaptacion de la escalera

- Se resolvio **seguridad** junto con arquitectura y no despues: el contexto de acceso
  condiciona el corte de las partes.
- Se agrego **coherencia de captura** como peldano propio; aparecio en la revision
  adversarial y afecta la correctitud, no la implementacion.
- Se agrego **evaluacion** como peldano junto a tests: el comportamiento de la zona no
  determinista se mide, no se prueba.
- Se agrego **contratos de formato** como peldano 4 separado de tecnologias, para poder
  verificar la herencia estricta de forma explicita.

## Regresion de trazas

| Fecha | Peldano cerrado | Nominal | Falla | Recuperacion | Observacion |
|-------|-----------------|---------|-------|--------------|-------------|
| 2026-08-16 | Metodo | OK | OK | OK | Diez hallazgos aplicados a los contratos |
| 2026-08-16 | Contratos de formato | OK | OK | OK | Tres ajustes menores; ninguna violacion de herencia |

## Retrocesos registrados

| Fecha | Supuesto roto | Peldano reabierto | Decisiones invalidadas |
|-------|---------------|-------------------|------------------------|
| — | — | — | — |
