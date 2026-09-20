<!-- .github/pull_request_template.md -->
## Que cambia

<!-- Una o dos lineas. -->

## Parte del sistema

<!-- Carpeta de src/querypilot/ afectada, o "infraestructura" / "documentacion". -->

## Contratos

- [ ] No modifica ningun contrato entre partes
- [ ] Modifica un contrato, y el documento correspondiente se actualizo en este mismo PR

## Verificacion

- [ ] `uv run ruff check src tests` sin observaciones
- [ ] `uv run mypy src` sin errores
- [ ] `uv run pytest` en verde
- [ ] Hay tests para todo comportamiento nuevo
- [ ] Ningun test se adapto para que pase una implementacion incorrecta
- [ ] Ninguna prueba nueva requiere clave del proveedor de modelo

## Reglas del sistema

- [ ] El codigo cae en una carpeta que corresponde a una caja del diagrama
- [ ] `executor/` no absorbio reglas ajenas
- [ ] Los importes son `Decimal`; los rechazos son valores de retorno

## Si cierra un peldano

- [ ] Trazas re-recorridas y anotadas en `MAPA_AVANCE.md`
- [ ] Mapa actualizado como ultimo commit
- [ ] Tag de hito creado con la regresion en su mensaje
