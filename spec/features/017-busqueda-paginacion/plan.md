# 017 · Búsqueda y paginación — Plan

## Enfoque

Mixin en common/utils.py que sobreescribe `get_queryset()` para filtrar por `q`. Include de template para search bar. Agregar paginate_by uno por uno.

## Implementación

1. `SearchMixin` con `search_fields` + `get_queryset()` que filtra por `?q=`
2. Aplicar a cada ListView definiendo `search_fields`
3. Agregar `paginate_by = 20`
4. Template `includes/dashboard/search_bar.html`
5. Incluir search bar en layouts/list.html
