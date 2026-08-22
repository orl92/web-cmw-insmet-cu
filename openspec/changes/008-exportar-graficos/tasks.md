# Tasks — 008-exportar-graficos

## Phase 1 — Generator refactor (format-agnostic bytes)
- [ ] Add `generate_skewt_file(sounding_data, fmt='png') -> bytes` in `apps/home/data/plot_generators.py` that builds the existing figure (`:36-341`) and calls `plt.savefig(buf, format=fmt, bbox_inches='tight', dpi=300 if fmt=='png' else None)`.
- [ ] Convert `generate_skewt` into a base64 wrapper over `generate_skewt_file` so `apps/home/views/modelos/views.py:324` stays unchanged.
- [ ] Confirm PNG/PDF/SVG all serialize from the same figure without layout changes.

## Phase 2 — Download endpoint
- [ ] Add `SoundingExportView(View)` to `apps/home/views/modelos/views.py` (mirror `DescargarGifView` at `:499`).
- [ ] Reuse the upstream fetch + generation flow from `SoundingView.post` (`:305-324`); validate `fmt` against allowlist `{png, pdf, svg}`; return HTTP 400 on invalid `fmt`.
- [ ] Set `Content-Type` (`image/png` | `application/pdf` | `image/svg+xml`) and `Content-Disposition: attachment; filename="sounding_<datetime>.<ext>"`.

## Phase 3 — URL registration
- [ ] Register `path('modelo/sounding/export/<str:fmt>/', SoundingExportView.as_view(), name='models_sounding_export')` under `app_name='home'` in `apps/home/urls.py` (near `:63`).

## Phase 4 — Report embedding (reuse)
- [ ] Document/enable embedding the figure base64 into `xhtml2pdf` reports via the existing `<img src="data:image/...;base64,...">` pattern (`apps/meteo/views/weather_report.py:405`). Prefer PNG for PDF embeds to bound SVG size.

## Phase 5 — Tests & verification
- [ ] Add `apps/home/tests/` tests asserting: PNG magic bytes (`\x89PNG`), PDF header (`%PDF`), SVG root (`<svg`) for `generate_skewt_file`.
- [ ] Add a view test for `models_sounding_export`: correct `Content-Type`, `Content-Disposition`, and HTTP 400 on unsupported `fmt`.
- [ ] Run `python manage.py check && python manage.py test apps.home` and confirm green.
