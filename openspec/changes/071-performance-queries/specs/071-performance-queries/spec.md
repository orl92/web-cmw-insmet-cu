# Spec — 071-performance-queries

## Criterios de Aceptación

1. Ninguna list view produce más de 10 queries (medido con `assertNumQueries`)
2. Migraciones añaden índices sin romper existente
3. `python manage.py test` pasa
