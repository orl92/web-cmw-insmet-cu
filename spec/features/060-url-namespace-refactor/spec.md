# 060 — URL namespace refactor

## Motivation

Cada app existente define URL names planos (ej: `listado_publicaciones`,
`crear_cliente`) sin `app_name`. Esto causa:
- Colisiones entre apps con names iguales (ej: dos `detail` en distintas apps)
- Dificultad para identificar el origen de una URL en templates/views
- Inconsistencia con `publications/` que ya usa `app_name` y namespaced names

## Alcance

Aplicar el patrón estandarizado a las 4 apps con URLs que no lo tienen:

- `login/`
- `accounts/`
- `home/`
- `dashboard/`

`api/` y `publications/` quedan excluidas: api usa patrones REST sin names, publications
ya implementa el patrón correcto.

## Patrón estándar

```python
# apps/mi_app/urls.py
app_name = 'mi_app'

urlpatterns = [
    path('', MiListView.as_view(), name='list'),
    path('crear/', MiCreateView.as_view(), name='create'),
    path('<uuid:uuid>/editar/', MiUpdateView.as_view(), name='update'),
    path('<uuid:uuid>/eliminar/', MiDeleteView.as_view(), name='delete'),
    path('<uuid:uuid>/', MiDetailView.as_view(), name='detail'),
    path('<uuid:uuid>/pdf/', MiPDFView.as_view(), name='pdf'),
]
```

Templates usan `{% url 'mi_app:list' %}`, vistas usan `reverse_lazy('mi_app:list')`.

## No incluido

- `api/` — DRF genera names automáticos. No tocar.
- `publications/` — Ya implementado. Verificar consistencia.

## Criterios de aceptación

1. `python manage.py check` sin errores
2. `python manage.py test` 100% OK
3. No hay URLs planas sin `app_name` en apps de dominio
