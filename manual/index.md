# QueryPilot

!!! info "Estado del proyecto"
    **QueryPilot — MVP 1 · Estado: experimental.**
    Este manual describe lo que existe hoy en el repositorio, no un plan a futuro.
    Las capacidades que todavía no están construidas se listan explícitamente en
    [Limitaciones del MVP 1](limitaciones.md).

## Qué es QueryPilot

QueryPilot convierte preguntas de negocio escritas en lenguaje natural —"¿cuánto
facturamos en julio?"— en un plan de análisis estructurado y verificable sobre una
base de datos existente.

Un modelo de lenguaje **interpreta** la pregunta y propone qué se quiere calcular. Un
núcleo determinista (código convencional, sin IA) **valida** esa propuesta contra un
vocabulario de negocio cerrado antes de que se convierta en un plan. El modelo nunca
escribe consultas ni decide por sí solo qué es correcto: propone, y el sistema
determinista decide si esa propuesta tiene sentido.

## Qué problema resuelve

Quien dirige un negocio tiene los datos y no tiene las respuestas. Las herramientas
existentes resuelven la mitad del problema:

- los tableros responden solo las preguntas que alguien anticipó;
- las consultas directas exigen conocimiento técnico;
- los asistentes que generan SQL de forma libre producen cifras **plausibles pero no
  verificables** — el peor resultado posible cuando alguien va a tomar una decisión
  con ese número.

QueryPilot no apuesta a que el modelo "entienda" la base de datos. Le da un
vocabulario de negocio explícito (qué es `net_revenue`, qué significa cada dimensión)
y un catálogo cerrado de operaciones que puede invocar. El modelo elige **qué**
calcular; nunca **cómo** se calcula.

## Estado actual

El proyecto se construye en bloques incrementales, cada uno cerrado con contratos,
tests y verificación estática antes de avanzar. Hoy están cerrados los bloques que
cubren:

- el vocabulario canónico y los identificadores base del sistema;
- la carga y validación del artefacto semántico (el vocabulario de negocio de una
  conexión concreta);
- los catálogos cerrados de objetivos y operaciones analíticas;
- el puerto del modelo de lenguaje, con un doble determinista para pruebas y un
  adaptador real sobre OpenAI;
- Interpretación: de pregunta en lenguaje natural a plan de análisis validado;
- un banco congelado de 60 casos de evaluación y el instrumento para correrlo.

181 tests automáticos verifican todo esto sin necesidad de un modelo de lenguaje real
(ver [Calidad y reproducibilidad](calidad.md)). Lo único que falta para cerrar esta
primera etapa es una cosa muy concreta: **correr el banco de evaluación contra un
modelo real de OpenAI y registrar el resultado** — ver [Evaluación](evaluacion.md).

El detalle completo del avance —qué está cerrado, qué falta, qué supuestos siguen
activos— se mantiene en `MAPA_AVANCE.md`, en la raíz del repositorio.

## Alcance del MVP 1

El MVP 1 prueba el supuesto más riesgoso del proyecto: que un modelo de lenguaje,
apoyado en un vocabulario de negocio bien definido, puede convertir preguntas reales
en propuestas estructuradas válidas.

El camino que **hoy existe** llega hasta acá:

```
pregunta en lenguaje natural
        │
        ▼
interpretación estructurada (propuesta del modelo)
        │
        ▼
validación determinista (sin modelo, sin excepciones para "casos especiales")
        │
        ▼
AnalysisPlan (plan de análisis validado)
        │
        ▼
evaluación contra un banco de 60 casos congelado
```

**El MVP 1 todavía no ejecuta ese plan contra una base de datos real.** No hay
resultados de negocio, no hay cifras reales, no hay respuestas en lenguaje natural
todavía. Eso es exactamente lo que mide el experimento: si el sistema entiende bien
la pregunta *antes* de gastar el esfuerzo de ejecutarla. Los detalles de qué queda
fuera de este alcance están en [Limitaciones del MVP 1](limitaciones.md).

## Por dónde empezar

- [Guía rápida](guia_rapida.md) si querés instalarlo y verificarlo en tu máquina.
- [Cómo interpreta preguntas](interpretacion.md) si querés ver ejemplos concretos.
- [Evaluación](evaluacion.md) si te interesa cómo se mide la calidad del sistema.
