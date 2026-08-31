# Proposal: Export Skew-T and Hodograph Graphics (PNG / PDF / SVG)

## Intent

Enable users to export the atmospheric sounding graphic — a MetPy Skew-T log-pressure
diagram combined with a hodograph and a thermodynamic/kinematic parameter box — to the
**PNG, PDF, and SVG** formats for inclusion in reports and as downloadable files.

The implemented graphic pipeline today is **matplotlib + MetPy** (see
`apps/home/data/plot_generators.py:17` `generate_skewt`), rendered server-side and
returned as a base64 PNG to the page. This change makes those same figures available as
first-class downloadable artifacts and embeddable assets for PDF reports.

> Note: the original proposal for this change described exporting ApexCharts dashboard
> charts. That framing does not match the actual codebase (there is no ApexCharts export
> path; the only sounding graphic is the matplotlib/MetPy figure above). This proposal
> **supersedes** that legacy framing and is anchored to the real, shipping implementation.

## Scope

### In Scope
- Produce the Skew-T + hodograph figure in **PNG, PDF, and SVG** from the existing
  single figure-build routine (`apps/home/data/plot_generators.py:36-341`).
- Expose an HTTP download endpoint that streams the figure bytes with the correct
  `Content-Type` and `Content-Disposition: attachment`.
- Keep existing in-page rendering fully working (the `SoundingView.post` JSON contract at
  `apps/home/views/modelos/views.py:298-334` must remain unchanged).
- Allow the figure to be embedded into `xhtml2pdf` reports via a base64 data URI, reusing
  the established pattern in `apps/meteo/views/weather_report.py:405` `get_image_base64`.
- Add tests under `apps.home` proving format validity and endpoint behavior.

### Out of Scope
- ApexCharts / dashboard chart export (legacy framing — not implemented in this repo).
- Changing the sounding data source or the upstream API call
  (`apps/home/views/modelos/views.py:316-321`).
- Adding new MetPy parameters or altering the figure layout/calculations
  (`apps/home/data/plot_generators.py:36-341`).
- Client-side / lazy export, batch ZIP of multiple charts, or authentication/permission
  changes beyond what the existing view already enforces.

## Approach

All claims below are anchored to the current code.

1. **Refactor the generator to return raw bytes per format (grounded).**
   - `generate_skewt(sounding_data)` at `apps/home/data/plot_generators.py:17` currently
     builds the full figure (lines `36-341`) and writes a **PNG only**:
     `plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)` (`plot_generators.py:345`)
     then returns `base64.b64encode(buf.getvalue()).decode('utf-8')` (`plot_generators.py:349`).
   - matplotlib's `savefig` natively supports `format='png'`, `'pdf'`, and `'svg'` using the
     same in-memory `BytesIO` buffer — no figure changes required (`matplotlib` is a declared
     dependency at `requirements.txt:30`; `MetPy` at `requirements.txt:31`).
   - Add `generate_skewt_file(sounding_data, fmt='png') -> bytes` that builds the identical
     figure (reuse the body at `plot_generators.py:36-341`) and calls
     `plt.savefig(buf, format=fmt, bbox_inches='tight', dpi=300 if fmt == 'png' else None)`.
     Keep `generate_skewt` as a thin base64 wrapper delegating to it, so
     `apps/home/views/modelos/views.py:324` `img_base64 = generate_skewt(sounding_data)`
     keeps returning base64 PNG unchanged.

2. **Add a download view (grounded in existing pattern).**
   - Follow the precedent `DescargarGifView` (`apps/home/views/modelos/views.py:499`),
     registered as `models_download_gif` (`apps/home/urls.py:93`).
   - Add `SoundingExportView(View)` in `apps/home/views/modelos/views.py` that:
     - fetches the sounding data exactly as `SoundingView.post` does
       (`views.py:305-324`) from `https://modelo.cmw.insmet.cu/api/sounding/`;
     - validates `fmt` against an allowlist `{png, pdf, svg}`;
     - returns `HttpResponse(bytes, content_type=...)` with
       `Content-Disposition: attachment; filename="sounding_<datetime>.<ext>"`,
       where content type maps `png -> image/png`, `pdf -> application/pdf`,
       `svg -> image/svg+xml`. Unsupported `fmt` returns HTTP 400.

3. **Register the route (grounded).**
   - Under `app_name = 'home'` (`apps/home/urls.py:25`), add
     `path('modelo/sounding/export/<str:fmt>/', SoundingExportView.as_view(), name='models_sounding_export')`
     adjacent to the existing `models_sounding` route (`apps/home/urls.py:63`).

4. **Report embedding (reuse, not reinvent).**
   - For PDF reports, `xhtml2pdf.pisa.pisaDocument` is already used
     (`apps/meteo/views/weather_report.py:5`, `:395`). Images are embedded as base64 data
     URIs via `get_image_base64` (`weather_report.py:405`). The base64 output of
     `generate_skewt` (PNG) and an analogous SVG base64 can be dropped into report templates
     using that same `<img src="data:image/...;base64,...">` mechanism — no new PDF
     machinery required.

5. **Tests (grounded).**
   - In `apps/home/tests/` add a test module asserting: PNG magic bytes (`\x89PNG`),
     PDF header (`%PDF`), and SVG XML root (`<svg`) for `generate_skewt_file`;
     plus a view test for `models_sounding_export` (correct `Content-Type`,
     `Content-Disposition`, and HTTP 400 on invalid `fmt`).
   - Verify with `python manage.py check && python manage.py test apps.home`.

## Acceptance Criteria

- [ ] `generate_skewt_file(sounding_data, fmt)` produces valid **PNG, PDF, and SVG** bytes from the figure built at `apps/home/data/plot_generators.py:36-341`.
- [ ] PNG output begins with the PNG magic bytes, PDF with `%PDF`, and SVG with an `<svg` root element.
- [ ] The `models_sounding_export` endpoint returns the bytes with the correct `Content-Type` (`image/png` | `application/pdf` | `image/svg+xml`) and `Content-Disposition: attachment; filename=...<ext>`.
- [ ] The endpoint rejects formats outside `{png, pdf, svg}` with HTTP 400.
- [ ] `SoundingView.post` (`apps/home/views/modelos/views.py:298`) still returns the base64 PNG `plot_image` in its JSON response, unchanged.
- [ ] The figure can be embedded in `xhtml2pdf` reports via a base64 data URI, consistent with `apps/meteo/views/weather_report.py:405`.
- [ ] `python manage.py test apps.home` passes, including the new format and endpoint tests.

## Rollback

- The change is **code-only**: no Django models, no migrations, no `record_active`/soft-delete
  or schema impact. Reverting is a single `git revert` of the change commit.
- `generate_skewt` is untouched in behavior, so `SoundingView` (`models_sounding`) keeps
  working with zero follow-up. No data migration or environment change is required to roll back.
