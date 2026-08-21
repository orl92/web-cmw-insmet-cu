# 023 · Model validation

**Estado:** planificado

## Qué hace

Agrega métodos `clean()` y validadores a modelos clave. Actualmente hay 0 métodos `clean()` en 27 modelos y solo 1 custom validator.

## Criterios de aceptación

- [ ] Forecasts: clean() valida min_temp < max_temp
- [ ] ServiceSubscription: clean() valida start_date < end_date
- [ ] Invoice: clean() valida amount > 0
- [ ] InvoiceItem: clean() valida cantidad > 0, precio > 0
- [ ] Customer: validación de formato REEUP/NIT
- [ ] Forms llaman full_clean() o model clean()
- [ ] `python manage.py test` — todos pasan
