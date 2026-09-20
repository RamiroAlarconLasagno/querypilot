<!-- docs/16_instrucciones_ia.md -->
<!-- Actualizado: 2026-08-16 -->
# 16 — Instrucciones para la IA

Como trabajar en QueryPilot. Leer al inicio de toda sesion de desarrollo.

---

## 1. Regla de arranque de sesion

1. Cargar `00_INDICE.md` y `MAPA_AVANCE.md`. **Nada mas.**
2. Ubicar el peldano actual y **verificar solo su evidencia**.
3. Cargar unicamente el documento del peldano actual.

> **Prohibido leer el proyecto completo para "entender donde esta".** El estado se
> responde verificando evidencia, no interpretando codigo.

Si la evidencia de un peldano marcado como cerrado no se verifica, el peldano **no esta
cerrado**: se lista que falta y se informa antes de avanzar.

---

## 2. Regla de arranque del proyecto

> La primera sesion de desarrollo construye el **primer MVP** definido en
> `02_vision_arquitectura.md` seccion 9, y lo valida con el usuario **antes** de generar
> infraestructura o arquitectura completa.

Ese MVP prueba el supuesto mas riesgoso. No requiere ejecutar ninguna consulta ni
construir la maquinaria determinista. Construir infraestructura primero invierte el orden
y retrasa la unica pregunta que puede invalidar el proyecto.

---

## 3. Regla de traba

> Ante un problema: identificar **que supuesto se rompio** —no que linea fallo— y volver
> al peldano dueno de ese supuesto.

1. Nombrar el supuesto roto.
2. Localizar el peldano que lo posee.
3. Marcar como **Invalidado** lo decidido debajo. No se arrastra: se revisa, aunque
   muchas decisiones se reconfirmen.
4. Registrar el retroceso en `MAPA_AVANCE.md`.
5. Recien entonces, rehacer el descenso.

Parchear donde aparecio el sintoma, sin subir al dueno del supuesto, es la causa habitual
de sistemas que degeneran. Cada parche es localmente razonable y el conjunto rompe el
diseno.

---

## 4. Regla de coherencia

> Todo archivo nuevo debe caer en una carpeta que corresponda a una caja del diagrama.

Si un elemento no encuentra carpeta, **el problema es la descomposicion**, no la falta de
un cajon generico. Consultar antes de crear `utils/`, `helpers/`, `common/` o `models/`.

Las tres carpetas que no son cajas —`canonical_language/`, `observability/`,
`model_port/`— estan justificadas en `02_vision_arquitectura.md` seccion 6 y **no admiten
una cuarta sin discusion explicita**.

---

## 5. Las cuatro reglas del sistema

Antes de escribir codigo que las toque, releer `01_metodo_solucion.md`.

1. **El modelo propone; el sistema determinista valida, autoriza, ejecuta y controla que
   afirmaciones pueden salir.**
2. **Cada componente es autoridad sobre sus propias reglas.** El Ejecutor coordina y no
   juzga.
3. **El turno es frontera de consistencia.** Contexto de acceso, version semantica y
   espacio de evidencia son constantes dentro de un turno.
4. **La calidad linguistica puede degradarse; la integridad factual no.**

### Verificacion permanente del Ejecutor

`executor/` es la caja bajo vigilancia declarada. **Antes de agregarle cualquier cosa:**
si la tarea requiere que el Ejecutor conozca semantica, permisos, catalogos o dialectos,
la tarea esta mal planteada.

Prueba: agregar una operacion, una metrica, una regla de permisos o una fuente nueva **no
debe tocar `executor/`**.

---

## 6. Que no hacer sin consultar

| Accion | Por que requiere aprobacion |
|---|---|
| Modificar un contrato entre partes | Es una decision de sistema |
| Agregar una operacion o un objetivo al catalogo | El catalogo es cerrado por diseno |
| Cambiar un invariante | Reabre el metodo |
| Agregar una dependencia | Debe justificarse; verificar version publicada, nunca de memoria |
| Crear una carpeta que no corresponda a una caja | Ver regla de coherencia |
| Relajar un umbral o un limite | Los valores tienen senal de invalidacion; se revisa la senal, no el numero |
| Introducir llamadas reales al modelo en pruebas de CI | El CI no tiene claves y no debe tenerlas |

---

## 7. Convenciones de codigo

> **Regla de idioma.** Todo identificador, contrato, estructura o valor **interpretado
> por software** va en **ingles**: codigo, campos de modelos Pydantic, claves de
> YAML/JSON, enums, estados, objetivos, operaciones, metricas, dimensiones, API HTTP,
> SSE y tests (nombres de funcion, variables, fixtures y datos canonicos incluidos). El
> **espanol** queda reservado para lo que lee una persona: comentarios, docstrings,
> documentacion, descripciones, mensajes al usuario, y los sinonimos o expresiones en
> lenguaje natural que el sistema debe reconocer como entrada.
>
> Ejemplo: `metric: net_revenue` con `description: "Facturacion neta"` y
> `synonyms: ["facturacion", "ventas netas"]` — nunca `metrica: facturacion_neta`.
>
> Se corrige asi la version anterior de esta regla ("valores del dominio en espanol"),
> que entraba en conflicto con `14_contratos_formato.md`, donde los modelos ya usaban
> nombres de campo en ingles. Decision tomada al inicio del proyecto, sin API publicada
> que mantener compatible: se aplica desde ahora, sin capa de compatibilidad.

| Ambito | Convencion |
|---|---|
| Identificadores de programa (variables, clases, funciones, modulos) | **Ingles** |
| Campos de modelos Pydantic | **Ingles** |
| Claves de artefactos YAML/JSON interpretados por el programa | **Ingles** |
| Identificadores canonicos: metricas, dimensiones, objetivos, operaciones, estados | **Ingles** |
| Enumeraciones (enums) | **Ingles** |
| Fixtures y datos canonicos de los tests | **Ingles** |
| Docstrings y comentarios | **Espanol** |
| Documentacion | **Espanol** |
| Descripciones legibles y mensajes al usuario | **Espanol** |
| Sinonimos y expresiones en lenguaje natural que el sistema debe reconocer | **Espanol** |
| Primera linea de cada archivo | Comentario con su ruta relativa |
| Importes y magnitudes derivadas | `Decimal` de punta a punta. **Nunca coma flotante** |
| Rechazos | Valores de retorno con causa y accion, **no excepciones** |
| Excepciones | Solo para fallas operativas |
| `turn_id`, `objective_id`, `attempt_id` | **Obligatorios**, sin valor por defecto |

Un `float` que se cuela es silencioso hasta que rompe la prueba de propiedades, y ahi el
diagnostico apunta al lugar equivocado.

---

## 8. Como trabajar

- **Cambios pequenos y verificables.** Una unidad de trabajo, una rama, un squash merge.
- **Leer el contrato de la parte antes de tocar su codigo.** No inferir el diseno leyendo
  la implementacion.
- **Tests obligatorios para todo comportamiento nuevo.**
- **Nunca adaptar un test para que pase una implementacion incorrecta.** Si un test
  molesta, o el test esta mal —y se corrige explicando por que— o la implementacion lo
  esta.
- **Validar cada modulo antes de integrarlo.** Parte probada e integrada son evidencias
  distintas.
- **Al cerrar un peldano:** re-recorrer las tres trazas, anotar el resultado en
  `MAPA_AVANCE.md`, actualizar el mapa como ultimo commit, y crear el tag de hito con la
  regresion en su mensaje.

### Al terminar cada tarea, informar

1. Archivos tocados.
2. Decisiones tomadas y su razon.
3. Tests ejecutados y su resultado.
4. Pendientes y bloqueos.

---

## 9. Herramientas

```bash
uv sync                                  # entorno y dependencias
uv run pytest                            # tests
uv run pytest tests/analytics -q         # tests de una parte
uv run ruff check src tests              # lint
uv run ruff format src tests             # formato
uv run mypy src                          # tipos
uv run querypilot-semantic validate demo # validar artefacto semantico
uv run querypilot-semantic publish demo  # publicar version
uv run querypilot-eval run demo          # banco de evaluacion (consume el modelo)
docker compose up -d                     # levantar el sistema
```

Obsoletos que **no se usan**: `setup.py`, `setup.cfg`, `requirements.txt` como fuente
principal, `black`, `flake8`, `isort`, `pylint`, `tox`, `requests`, `argparse`.

Antes de crear ramas, commits o tags: cargar `15_git_github.md`.

---

## 10. Checklist antes de cerrar cualquier unidad de trabajo

```
□ El codigo cae en una carpeta que corresponde a una caja del diagrama
□ El contrato de la parte se leyo antes de modificar su codigo
□ Ningun contrato entre partes cambio sin aprobacion explicita
□ executor/ no absorbio reglas ajenas
□ Los identificadores de aislamiento son obligatorios donde corresponde
□ Los importes son Decimal de punta a punta
□ Los rechazos son valores de retorno con causa y accion
□ Hay tests para todo comportamiento nuevo
□ Ningun test se adapto para que pase una implementacion incorrecta
□ ruff check y ruff format sin observaciones
□ mypy sin errores
□ pytest en verde
□ Ninguna prueba del CI requiere clave del proveedor de modelo
□ Si cerro un peldano: trazas re-recorridas, mapa actualizado, tag creado
```
