# 019 · Exportación CSV/Excel

**Estado:** planificado

## Qué hace

Agrega botón de exportación CSV en los list views del dashboard. Actualmente no existe ninguna funcionalidad de exportación (solo importación Excel vía ExcelJSONView).

## Criterios de aceptación

- [ ] Botón "Exportar CSV" visible en list views
- [ ] CSV exporta datos correctamente (columnas relevantes)
- [ ] Aplica a: Clientes, Servicios, Suscripciones, Facturas, Pronósticos, Reportes, Avisos
- [ ] `python manage.py test` — todos pasan
