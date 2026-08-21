# 003 · Pronósticos detallados — Plan

## Enfoque

Modelo único `Forecasts` con todos los campos en una tabla (3 regiones × 3 períodos + extendido + astronomía). Vistas CRUD estándar con formulario agrupado por secciones. Template de listado con DataTables y Litepicker para filtro por fecha.

## Implementación

1. **Modelo**: `Forecasts` con prefijos `n_` (norte), `i_` (interior), `s_` (sur); campos `t` (temp), `w` (tiempo), `wdd` (dirección viento), `wdf` (velocidad viento), `s` (mar). Campos `day1_*` a `day5_*` para extendido. Campos `lp`, `nlp`, `nlpd`, `sunrise`, `sunset`, `uv_index` para astronomía.
2. **Formulario**: `ForecastsForm` con DateInput y TimeInput widgets; validación de `clean_date()`.
3. **Vistas**: `ForecastsListView` con filtro GET `?date=`, `AllForecastCreateView` con pre-cálculo de fechas futuras, `ForecastUpdateView` con `UserPassesTestMixin`, `ForecastDeleteView` (POST-only).
4. **Templates**: `pronosticos.html` (listado con 3 tablas de región + extendido + astronomía), `crear_pronostico.html` y `actualizar_pronostico.html` (formularios agrupados).

## Decisiones

- **Modelo único vs 3 modelos separados** — una tabla evita joins y simplifica el formulario comparativo. La desventaja es una tabla ancha (~60 campos), pero el acceso siempre es por fecha única.
- **Prefijos de campo en vez de JSON** — tipado fuerte a nivel BD, consultable, indexable.
- **Litepicker + DataTables** — ambos ya en Tabler; consistencia con el resto del dashboard.

## Riesgos

- **Formulario muy largo** — ~60 campos; se mitiga con agrupación visual por región y sección en el template.
- **Fecha duplicada** — validado con `unique=True` en el modelo + `clean_date()` en el form.
