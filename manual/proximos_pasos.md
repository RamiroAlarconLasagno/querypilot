# Próximos pasos

El plan de implementación avanza en experimentos incrementales, cada uno construido
sobre el anterior. Esta página describe el orden previsto **en términos generales**,
sin fechas ni promesas de funcionalidad — el detalle vivo y actualizado siempre está
en `MAPA_AVANCE.md`, en la raíz del repositorio.

## Qué habilita la próxima etapa

Con Interpretación ya produciendo planes validados, el paso natural siguiente es
hacer que esos planes se puedan **ejecutar de verdad**:

- que las operaciones analíticas calculen resultados reales, no solo se validen
  como propuestas;
- que exista una capa de acceso a datos que traduzca una petición canónica al
  dialecto de una base concreta y la ejecute dentro de límites de tiempo y volumen.

Esa es la parte más voluminosa del proyecto, pero también la de menor incertidumbre:
es matemática y traducción de consultas, verificable sin necesidad de un modelo de
lenguaje.

## Después de eso

En términos generales, el resto del plan incorpora, en orden:

- un **Ejecutor** que coordine las validaciones existentes, ejecute los planes y
  decida cuándo un resultado alcanza o hace falta una segunda ronda;
- **conjuntos de datos**: snapshots reutilizables de lo que ya se consultó, con
  reglas claras sobre cuándo un conjunto sigue siendo válido;
- **Síntesis de respuesta**: redactar, a partir de los resultados y su alcance, una
  respuesta legible en lenguaje natural — separada de Interpretación, para que el
  modelo nunca redacte lo que el usuario "quería escuchar" en vez de lo que los
  datos dijeron;
- **sesión, frontera de servicio y cliente**: conversaciones con estado, una API
  pública y una interfaz mínima para usarla.

## Qué no cambia en el camino

Los principios que ya gobiernan el MVP 1 —el modelo propone, el sistema determinista
valida; ninguna afirmación sale sin evidencia verificable; los rechazos son
resultados normales, no errores— se sostienen para todo lo que sigue. Cada etapa
nueva se mide con el mismo criterio: contratos explícitos, tests antes de avanzar, y
evidencia reproducible de que funciona.
