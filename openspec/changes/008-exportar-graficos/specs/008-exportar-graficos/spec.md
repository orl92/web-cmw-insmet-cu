# Spec — 008-exportar-graficos (capability: graphic-export)

Delta requirements for exporting the MetPy Skew-T + hodograph figure as PNG / PDF / SVG.
All requirements are anchored to `apps/home/data/plot_generators.py` and the surrounding
views/urls. RFC2119 keywords (MUST, SHOULD, MAY) are used below.

## Requirement: GRAPHIC-EXPORT-FORMATS

The system SHALL generate the Skew-T and hodograph figure in PNG, PDF, and SVG from the
single figure-build routine at `apps/home/data/plot_generators.py:36-341`.

### Scenario: Valid sounding data, PNG output
- **Given** a `sounding_data` dict with keys `p, T, Td, u, v, z` each carrying `value`/`unit`
  (per `plot_generators.py:21-33`)
- **When** `generate_skewt_file(sounding_data, fmt='png')` is called
- **Then** the returned bytes MUST begin with the PNG magic bytes (`\x89PNG\r\n\x1a\n`).

### Scenario: Valid sounding data, PDF output
- **Given** the same valid `sounding_data`
- **When** `generate_skewt_file(sounding_data, fmt='pdf')` is called
- **Then** the returned bytes MUST begin with `%PDF`.

### Scenario: Valid sounding data, SVG output
- **Given** the same valid `sounding_data`
- **When** `generate_skewt_file(sounding_data, fmt='svg')` is called
- **Then** the returned bytes MUST contain an `<svg` root element.

### Scenario: Invalid input
- **Given** a `sounding_data` missing any required key (`plot_generators.py:21`)
- **When** generation is attempted
- **Then** the function MUST raise `ValueError` (existing contract at `plot_generators.py:25`).

## Requirement: GRAPHIC-EXPORT-DOWNLOAD

The system SHALL expose an HTTP endpoint that streams the figure bytes as a download.

### Scenario: Supported format requested
- **Given** a GET to `models_sounding_export` (registered in `apps/home/urls.py`) with `fmt` in `{png, pdf, svg}`
- **When** `SoundingExportView` executes (pattern: `DescargarGifView` at `apps/home/views/modelos/views.py:499`)
- **Then** the response MUST have `Content-Type` `image/png` | `application/pdf` | `image/svg+xml`
  and a `Content-Disposition: attachment; filename="sounding_<datetime>.<ext>"` header.

### Scenario: Unsupported format requested
- **Given** a GET to `models_sounding_export` with `fmt` outside `{png, pdf, svg}`
- **When** `SoundingExportView` executes
- **Then** the response MUST be HTTP 400.

### Scenario: Upstream sounding API failure
- **Given** the upstream `modelo.cmw.insmet.cu/api/sounding/` call fails (`apps/home/views/modelos/views.py:316`)
- **When** `SoundingExportView` executes
- **Then** the response MUST be a non-2xx error (e.g. 502/500) and MUST NOT return a corrupt/empty file.

## Requirement: GRAPHIC-EXPORT-BACKWARD-COMPAT

The existing in-page Skew-T rendering MUST remain functional and unchanged.

### Scenario: In-page JSON contract preserved
- **Given** `SoundingView.post` (`apps/home/views/modelos/views.py:298`) calls `generate_skewt(sounding_data)` (`:324`)
- **When** the change is deployed
- **Then** the JSON response MUST still include `plot_image` as a base64 PNG string (`:326-334`),
  and `generate_skewt` MUST remain a base64 wrapper over the new byte generator.

## Requirement: GRAPHIC-EXPORT-REPORT-EMBED (SHOULD)

The system SHOULD support embedding the figure into `xhtml2pdf` reports via a base64 data URI.

### Scenario: Embed in PDF report
- **Given** an `xhtml2pdf` report built with `pisa.pisaDocument` (`apps/meteo/views/weather_report.py:395`)
- **When** a template embeds the figure using the existing `<img src="data:image/...;base64,...">` pattern (`weather_report.py:405`)
- **Then** the figure MUST render; PDF embeds SHOULD use the PNG variant to bound SVG file size.
