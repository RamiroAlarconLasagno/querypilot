# Limitaciones del MVP 1

Esta página existe para que nadie —incluido el propio equipo— confunda lo que el
MVP 1 demuestra con lo que el producto terminado va a hacer. Ninguna de las
limitaciones que siguen es un defecto: son, literalmente, el corte de alcance que se
decidió para este primer experimento.

## No ejecuta operaciones sobre una base de datos real

Interpretación produce un `AnalysisPlan` **validado**, pero hoy nada lo ejecuta.
Todavía no existe código funcional en las partes que harían eso:

- **Operaciones analíticas** (el cálculo real detrás de cada operación del catálogo);
- **Acceso a datos** (traducir una petición canónica al dialecto de la base y
  ejecutarla dentro de límites);
- **Ejecutor de análisis** (coordinar validaciones, ejecutar, decidir si el resultado
  alcanza);
- **Conjuntos de datos**, **Sesión de análisis**, **Contexto de acceso**, **Síntesis
  de respuesta** y **Frontera de servicio** (la API pública).

Esas carpetas existen en el repositorio como cajas reservadas del diseño, pero están
vacías de implementación. No hay atajo ni versión simplificada funcionando por
detrás.

## No inventa respuestas

En ningún punto del camino actual el modelo redacta una respuesta de negocio ni cita
una cifra. Lo único que produce es una propuesta estructurada, que se valida
deterministamente antes de convertirse en plan. Cuando exista ejecución real, el
mismo principio se sostiene: ninguna afirmación puede salir sin una invocación
determinista que la respalde (`01_metodo_solucion.md`, sección 9).

## La corrida real contra el modelo todavía está pendiente

El instrumento para evaluar contra OpenAI está completo y probado —ver
[Evaluación](evaluacion.md)— pero la corrida real, la que consume la API y tiene
costo, todavía no se ejecutó. Hasta que eso ocurra y se registre el resultado, el
supuesto más riesgoso del proyecto sigue sin veredicto.

Además, por una limitación concreta del modo de generación estructurada estricta de
OpenAI (no admite un campo con claves libres que el contrato de Interpretación sí
necesita), el adaptador real usa un modo de generación más simple y valida la
respuesta con las mismas reglas deterministas de siempre. El detalle técnico completo
de esa decisión está en `docs/13_decisiones_tecnicas.md`, sección 6bis.

## Qué queda reservado para etapas siguientes

- ejecutar de verdad las operaciones analíticas y traer resultados desde una base de
  datos;
- redactar respuestas en lenguaje natural a partir de esos resultados;
- sesiones de conversación con estado, continuidad entre preguntas y un historial
  real;
- contexto de acceso y permisos por usuario;
- una API pública y un cliente.

El orden aproximado en el que esto se va incorporando está en
[Próximos pasos](proximos_pasos.md).
