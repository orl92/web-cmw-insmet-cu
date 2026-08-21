# Spec — 023-model-validation

## Criterios de aceptación

- [ ] Forecasts: clean() valida min_temp < max_temp
- [ ] ServiceSubscription: clean() valida start_date < end_date
- [ ] Invoice: clean() valida amount > 0
- [ ] InvoiceItem: clean() valida cantidad > 0, precio > 0
- [ ] Customer: validación de formato REEUP/NIT
- [ ] Forms llaman full_clean() o model clean()
- [ ] `python manage.py test` — todos pasan
