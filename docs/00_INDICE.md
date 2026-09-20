<!-- docs/00_INDICE.md -->
<!-- Actualizado: 2026-08-16 -->
# 00 — Indice — QueryPilot

## Reglas de uso para la IA del proyecto

> Al iniciar cualquier sesion: cargar `00_INDICE.md` y `MAPA_AVANCE.md`. **Nada mas.**
> Despues, cargar solo el archivo que corresponde al peldano actual. No cargar mas de uno
> a la vez salvo dependencia explicita entre ellos.
> **Prohibido leer el proyecto completo para "entender donde esta".**

El estado del proyecto se responde verificando la **evidencia** del peldano actual, no
leyendo codigo ni interpretando implementaciones anteriores.

---

## Archivos

| Archivo | Contenido | Cuando cargarlo |
|---|---|---|
| `MAPA_AVANCE.md` | Donde estamos, que esta cerrado, que falta, proxima decision, supuestos activos | **Siempre, al inicio de toda sesion** |
| `docs/00_INDICE.md` | Este archivo | Siempre, al inicio |
| `docs/01_metodo_solucion.md` | Problema, actores, dominio, invariantes, decisiones de sistema, arquitectura, flujos, trazas, supuesto riesgoso, revision adversarial, criterio de correctitud | Al reabrir una decision de sistema, o ante una traba cuyo supuesto se rompio |
| `docs/02_vision_arquitectura.md` | Tecnologias, carpetas, tests, regla de dependencias, **primer MVP**, orden de implementacion | Al planificar cualquier bloque de implementacion |
| `docs/03_parte_frontera_servicio.md` | Contrato de la parte 1 | Al implementar o modificar esa parte |
| `docs/04_parte_contexto_acceso.md` | Contrato de la parte 2 | Idem |
| `docs/05_parte_sesion_analisis.md` | Contrato de la parte 3 | Idem |
| `docs/06_parte_conocimiento_negocio.md` | Contrato de la parte 4 | Idem |
| `docs/07_parte_interpretacion.md` | Contrato de la parte 5 | Idem |
| `docs/08_parte_sintesis.md` | Contrato de la parte 6 | Idem |
| `docs/09_parte_ejecutor.md` | Contrato de la parte 7 | Idem |
| `docs/10_parte_operaciones.md` | Contrato de la parte 8 | Idem |
| `docs/11_parte_acceso_datos.md` | Contrato de la parte 9 | Idem |
| `docs/12_parte_conjuntos_datos.md` | Contrato de la parte 10 | Idem |
| `docs/13_decisiones_tecnicas.md` | Decisiones de **implementacion**: librerias, versiones, configuraciones, convenciones | Antes de agregar una dependencia o cambiar una configuracion |
| `docs/14_contratos_formato.md` | Nivel de formato: modelos canonicos, superficie HTTP, eventos, persistencia | Al implementar cualquier contrato entre partes |
| `docs/15_git_github.md` | Ramas, commits, merges, tags de hito, proteccion | **Antes de crear ramas, commits o tags** |
| `docs/16_instrucciones_ia.md` | Como trabajar en este proyecto; que no asumir; reglas de arranque, traba y coherencia | Al inicio de toda sesion de desarrollo |

---

## Mapa rapido: parte del diagrama → archivo → carpetas

| # | Parte | Documento | `src/querypilot/` | `tests/` |
|---|---|---|---|---|
| 1 | Frontera de servicio | `03_parte_frontera_servicio.md` | `service_boundary/` | `service_boundary/` |
| 2 | Contexto de acceso | `04_parte_contexto_acceso.md` | `access_context/` | `access_context/` |
| 3 | Sesion de analisis | `05_parte_sesion_analisis.md` | `analysis_session/` | `analysis_session/` |
| 4 | Conocimiento del negocio | `06_parte_conocimiento_negocio.md` | `business_knowledge/` | `business_knowledge/` |
| 5 | Interpretacion y planificacion | `07_parte_interpretacion.md` | `interpretation/` | `interpretation/` |
| 6 | Sintesis de respuesta | `08_parte_sintesis.md` | `synthesis/` | `synthesis/` |
| 7 | Ejecutor de analisis | `09_parte_ejecutor.md` | `executor/` | `executor/` |
| 8 | Operaciones analiticas | `10_parte_operaciones.md` | `analytics/` | `analytics/` |
| 9 | Acceso a datos | `11_parte_acceso_datos.md` | `data_access/` | `data_access/` |
| 10 | Conjuntos de datos | `12_parte_conjuntos_datos.md` | `datasets/` | `datasets/` |

Carpetas sin caja, justificadas en `02_vision_arquitectura.md` seccion 6:
`canonical_language/`, `observability/`, `model_port/`.

---

## Las cuatro reglas que no se negocian

Estan desarrolladas en `01_metodo_solucion.md`. Se listan aqui porque atraviesan todo el
proyecto y ninguna sesion deberia empezar sin tenerlas presentes.

1. **El modelo propone; el sistema determinista valida, autoriza, ejecuta y controla que
   afirmaciones pueden salir.**
2. **Cada componente es autoridad sobre sus propias reglas.** El Ejecutor coordina y no
   juzga. Agregar una operacion, una metrica, un permiso o una fuente **no debe tocar el
   Ejecutor**.
3. **El turno es frontera de consistencia.** Contexto de acceso, version semantica y
   espacio de evidencia son constantes dentro de un turno.
4. **La calidad linguistica puede degradarse; la integridad factual no.**
