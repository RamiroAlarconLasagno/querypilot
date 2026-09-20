<!-- prompts/README.md -->
# Prompts versionados

Los prompts son **artefactos versionados**, no cadenas embebidas en el codigo. El codigo
referencia una version; la version queda auditada en el registro durable junto a la
version semantica.

## Estructura

```
prompts/
├── interpretation/
│   ├── v1.md
│   └── v1.meta.yaml
└── synthesis/
    ├── v1.md
    └── v1.meta.yaml
```

Cada `*.meta.yaml` declara:

```yaml
version: v1
fecha: 2026-08-16
proposito: Version inicial de interpretacion
cambios_respecto_anterior: null
resultados_banco:
  conexion: demo
  version_semantica: null
  A1: null
  A2: null
  A4: null
  B1: null
```

## Regla de comparacion

> Prompt y artefacto semantico se versionan por separado pero **se evaluan juntos**.

Una corrida del banco mide la combinacion de ambos. Un resultado solo es comparable
contra otro que varie **uno** de los dos, nunca los dos a la vez. Sin esa disciplina, la
regresion no significa nada.
