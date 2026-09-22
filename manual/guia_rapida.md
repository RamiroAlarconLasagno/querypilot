# Guía rápida

## Requisitos

- **Python 3.13** (el proyecto fija `>=3.13,<3.14`).
- **[uv](https://docs.astral.sh/uv/)** como gestor de entorno y dependencias. Todo el
  proyecto se maneja con `uv`; no hace falta crear un virtualenv a mano.

No hace falta PostgreSQL ni Docker para lo que cubre el MVP 1: la validación del
artefacto semántico, la interpretación y la evaluación corren sobre archivos locales.

## Instalación

```bash
git clone <repositorio>
cd querypilot

uv sync
```

`uv sync` crea el entorno virtual e instala exactamente las versiones fijadas en
`uv.lock`.

## Cómo verificar que el proyecto funciona

Tres comandos, en este orden, verifican que el código es correcto sin necesidad de
ningún modelo de lenguaje ni base de datos:

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest
```

El detalle de qué verifica cada uno, con capturas, está en
[Calidad y reproducibilidad](calidad.md).

## Primeros comandos

### Validar el artefacto semántico de la conexión de demostración

```bash
uv run querypilot-semantic validate demo
```

Carga el vocabulario de negocio de la conexión `demo` (`semantic/demo/`) y corre las
comprobaciones de integridad. Ver [Artefacto semántico](artefacto_semantico.md) para
el detalle completo.

### Correr el banco de evaluación

```bash
uv run querypilot-eval run demo --report reporte.md
```

Este comando carga el banco de 60 casos de evaluación y corre Interpretación contra
el proveedor de modelo configurado. **Sin una clave de OpenAI configurada, esto es
normal y esperado**: el comando va a terminar con un veredicto `NO ACEPTADO` y todos
los casos marcados como falla operativa, no como un error del programa. La razón
completa está en [Evaluación](evaluacion.md).

## Qué no hace falta todavía

No hace falta configurar PostgreSQL, Docker, ni ninguna clave de API para explorar el
MVP 1 tal como está hoy. Esas piezas se incorporan progresivamente en los bloques
siguientes del plan de implementación (ver [Próximos pasos](proximos_pasos.md)).
