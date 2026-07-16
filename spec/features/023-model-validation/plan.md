# 023 · Model validation — Plan

## Enfoque

Agregar `clean()` a modelos + asegurar que forms lo invocan. Validaciones simples (comparaciones, rangos, formato).

## Implementación

1. Forecasts.clean() — validar temperaturas consistentes
2. ServiceSubscription.clean() — validar fechas
3. Invoice.clean() — amount > 0
4. InvoiceItem.clean() — cantidad > 0, precio > 0
5. Customer.clean() — REEUP/NIT format
6. Asegurar que forms llaman `full_clean()` o el modelo define `clean()` y el form lo hereda
