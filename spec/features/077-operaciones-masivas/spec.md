# 077 — operaciones-masivas

## Motivación

Actualmente cada factura, certificado o contrato se procesa individualmente. Para clientes con múltiples suscripciones, sería útil poder facturar en lote o exportar certificados por período.

## Alcance

- Selección múltiple en list views (checkboxes)
- Acción "Facturar seleccionados" → redirige a create con preselección
- "Exportar certificados seleccionados como ZIP"
- Botón de impresión masiva de facturas

## Criterios de Aceptación

1. Checkboxes en list views de Subscription, Invoice, Certificate
2. "Facturar seleccionados" crea factura batch
3. "Exportar ZIP" descarga certificados agrupados
4. `python manage.py test` pasa
