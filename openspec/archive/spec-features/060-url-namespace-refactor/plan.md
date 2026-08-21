# Plan: 060 — URL namespace refactor

## Estrategia

Refactorizar app por app en orden de menor a mayor complejidad para minimizar
riesgo de regresiones.

## Orden

1. `login/` — 2 URLs, 2 templates, 0 vistas internas con reverse_lazy → 5 min
2. `accounts/` — ~15 URLs, 8 templates, varias vistas con reverse_lazy → 30 min
3. `home/` — ~20 URLs, 15+ templates, 0 reverse_lazy en vistas → 30 min
4. `dashboard/` — ~70+ URLs, 40+ templates, muchas reverse_lazy → 2-3 h

## Por cada app

1. Agregar `app_name = 'X'` en urls.py
2. Renombrar cada URL name del plano al namespaced (`listado_clientes` → `clientes:list`)
3. Buscar y reemplazar referencias:
   - `{% url 'nombre_plano' %}` → `{% url 'app:nombre' %}` en templates
   - `reverse('nombre_plano')` → `reverse('app:nombre')` en vistas
   - `reverse_lazy('nombre_plano')` → `reverse_lazy('app:nombre')` en vistas/forms
   - `redirect('nombre_plano')` → `redirect('app:nombre')` en vistas
4. Verificar includes modales que pasan `delete_url_name`
5. `python manage.py test` por cada app

## Riesgos

- Las URLs planas se usan en muchos templates como strings literales.
  Un `grep` completo después de cada app es obligatorio.
- `dashboard/` tiene ~70+ URL names usados en includes modales con JS
  (modal_delete_js.html). Prestar atención a `delete_url_name`.
- Algunas vistas de dashboard usan `redirect('nombre_plano')` en lugar de
  `reverse_lazy`. Buscar con grep exhaustivo.
