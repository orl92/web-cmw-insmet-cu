# Design: Export Skew-T and Hodograph Graphics (PNG / PDF / SVG)

## Context

The sounding graphic is produced entirely server-side by
`apps/home/data/plot_generators.py:17` `generate_skewt(sounding_data)`. It:

- validates input — a dict with keys `p, T, Td, u, v, z`, each carrying `value`/`unit`
  (`plot_generators.py:21-33`);
- builds a matplotlib `Agg` figure (`matplotlib.use('Agg')`, `plot_generators.py:4`) with a
  Skew-T (`metpy.plots.SkewT`, `:39`), a hodograph inset (`metpy.plots.Hodograph`, `:86`),
  a parameter box and title (`:152-341`);
- serializes **only to PNG** via `plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)`
  (`:345`) and returns `base64.b64encode(buf.getvalue()).decode('utf-8')` (`:349`).

The single consumer is `SoundingView.post` (`apps/home/views/modelos/views.py:298`), which
calls `generate_skewt` (`:324`) and returns `{ 'plot_image': img_base64, ... }` as JSON
(`:326-334`) for in-page display. There is **no download path and no PDF/SVG output** today.

Dependencies already present: `matplotlib` (`requirements.txt:30`), `MetPy` (`:31`),
`xhtml2pdf` (`:73`).

## Goal

Make the identical figure available as PNG / PDF / SVG bytes, downloadable via HTTP and
embeddable in PDF reports — without changing the figure or the in-page JSON contract.

## Technical Approach

### 1. Split generation from serialization
Keep the figure-building logic (`:36-341`) intact. Introduce:

```python
def generate_skewt_file(sounding_data, fmt='png') -> bytes:
    # body identical to generate_skewt (plot_generators.py:36-341)
    buf = BytesIO()
    plt.savefig(buf, format=fmt, bbox_inches='tight',
                dpi=300 if fmt == 'png' else None)
    plt.close()
    return buf.getvalue()
```

- `savefig` natively emits `png`, `pdf`, `svg` to the same `BytesIO`; vector formats ignore
  `dpi`, so the `dpi` branch only affects raster PNG quality.
- Make `generate_skewt` a backward-compatible wrapper:
  `return base64.b64encode(generate_skewt_file(sounding_data, 'png')).decode('utf-8')`.
  This guarantees `SoundingView.post` (`:324`) is unchanged.

### 2. Download view
Add `SoundingExportView(View)` to `apps/home/views/modelos/views.py`, mirroring the
existing `DescargarGifView` (`:499`):

- Reuse the upstream fetch + `generate_skewt_file` call already proven in
  `SoundingView.post` (`:305-324`).
- Allowlist: `ALLOWED_FMT = {'png', 'pdf', 'svg'}`. Unknown `fmt` -> `HttpResponse(status=400)`.
- Content-type map: `png -> image/png`, `pdf -> application/pdf`, `svg -> image/svg+xml`.
- Response headers:
  `Content-Disposition: attachment; filename="sounding_{datetime}.{ext}"`.

### 3. URL registration
Under `app_name = 'home'` (`apps/home/urls.py:25`):

```python
path('modelo/sounding/export/<str:fmt>/',
     SoundingExportView.as_view(), name='models_sounding_export'),
```

placed next to `models_sounding` (`apps/home/urls.py:63`).

### 4. Report embedding (no new PDF engine)
`apps/meteo/views/weather_report.py:395` already builds PDFs with
`xhtml2pdf.pisa.pisaDocument`, embedding images as base64 data URIs through
`get_image_base64` (`:405`). A report template can embed the figure with:

```html
<img src="data:image/png;base64,{{ skewt_base64 }}" />
```

(or `image/svg+xml` for the SVG variant). This reuses the established pattern and avoids
introducing a second PDF library.

> **Note (apply):** the actual report templates under
> `apps/meteo/templates/pages/meteo/weather_report/<type>/pdf.html` embed images via
> `<img src="data:image/png;base64,{{ logo_base64 }}" ...>`, but no Python code populates
> `logo_base64` today and **no `pisaDocument` / `xhtml2pdf` / `get_image_base64` code exists
> in the repo** (xhtml2pdf is a declared dependency in `requirements.txt` but never imported;
> the `weather_report.py:395/405` references in the proposal are against an earlier revision
> of the file, which is now only 339 lines). Because `generate_skewt` already returns a base64
> PNG string and the report engine (when implemented) consumes `data:image/...;base64,`
> URIs, embedding the figure is a pure template concern:
>
> ```html
> <img src="data:image/png;base64,{{ skewt_base64 }}" alt="Sondeo" />
> ```
>
> with `skewt_base64` sourced from `generate_skewt_file(sounding_data, 'png')` (base64-wrapped)
> in whichever view supplies context to the PDF template. PNG is preferred for PDF embeds to
> bound file size (SVG of the colormapped hodograph can be large). No production wiring was
> added in this change because no report pipeline exists to wire into; the pattern is documented
> for the future report-implementation task.

## Data Flow

```
HTTP GET /home/modelo/sounding/export/<fmt>/
        -> SoundingExportView.get
             -> fetch sounding_data from modelo.cmw.insmet.cu/api/sounding/   (views.py:316)
             -> generate_skewt_file(sounding_data, fmt)                        (plot_generators.py)
             -> HttpResponse(bytes, content_type, Content-Disposition: attach)
```

In-page path is untouched: `SoundingView.post -> generate_skewt -> base64 PNG JSON`.

## Constraints & Risks

- **Upstream dependency**: the figure still depends on the external
  `modelo.cmw.insmet.cu` API (`views.py:316`, `verify=False`); export inherits its failure
  modes. The view MUST return HTTP 502/500 (not a corrupt file) when the upstream call fails.
- **SVG size**: colormapped hodograph (`plot_generators.py:125`) can produce large SVG;
  acceptable for reports/downloads, but PDF embed SHOULD prefer PNG to bound size.
- **No DB change**: no models/migrations involved; rollback is a plain revert.
- **Format allowlist** is the only security boundary — never forward an arbitrary `fmt`
  string to `savefig` beyond the validated set.

## Verification

- `python manage.py check`
- `python manage.py test apps.home` (new tests assert PNG/PDF/SVG validity + endpoint
  behavior and 400 on bad format).
