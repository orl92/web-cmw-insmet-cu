# tabler-core-vendor Specification

Capability: `tabler-core-vendor` (versioned, vendored Tabler assets)

## Purpose

The portal serves Tabler from `static/dist/` only: core 1.5.1, icons webfont
3.46.0, socials plugin, and the project's own patched theme loader. No CDN
reference, no npm/build step (JS stays 100% vanilla vendored).

## Requirements

### Requirement: VENDORED-VERSION-PIN

The system SHALL vendor `@tabler/core@1.5.1` and
`@tabler/icons-webfont@3.46.0` in `static/dist/`:

- **SHALL** ship `tabler.min.css`, `tabler-themes.min.css` and `tabler.min.js`
  at core 1.5.1.
- **SHALL** ship `tabler-icons.min.css` (3.46.0) with
  `fonts/tabler-icons.{ttf,woff,woff2}`.
- **SHALL** ship `tabler-socials.min.css` plus the `img/social/` SVG set
  shipped with 1.5.1.
- **SHALL** ship `tabler-theme.min.js` as the 1.5.1 base with the project
  patch re-applied, its provenance header recording the upstream version and
  the patch note.
- **SHALL NOT** leave 1.4.0/3.45.0 Tabler builds in `static/dist/`.

#### Scenario: Version provenance

- GIVEN a vendored Tabler asset
- WHEN its header provenance comment is inspected
- THEN it records Tabler v1.5.1 (or Icons v3.46.0)
- AND `tabler-theme.min.js` documents the re-applied project patch

#### Scenario: Fonts resolve locally

- GIVEN `tabler-icons.min.css` at 3.46.0
- WHEN the page loads the icon font
- THEN the request hits the vendored `fonts/tabler-icons.*`
- AND no remote font request is issued

### Requirement: NO-CDN-NO-BUILD

Templates and static assets SHALL NOT reference Tabler via CDN, and the
upgrade SHALL NOT introduce an npm package or build step.

#### Scenario: Zero CDN links

- GIVEN the repository after the swap
- WHEN searching templates and `static/dist/` for `cdn.jsdelivr.net` or
  `unpkg.com`
- THEN no Tabler asset reference matches

#### Scenario: No build tooling

- GIVEN the project root
- WHEN inspecting for new `package.json`/`node_modules`/bundler config
- THEN none exists

### Requirement: UMD-EXPOSURE-CONTRACT

`tabler.min.js` 1.5.1 SHALL expose Bootstrap components under `window.tabler`
(e.g. `tabler.bootstrap.Toast`) and SHALL NOT expose `window.bootstrap`.
Project JavaScript SHALL construct Bootstrap components through the fallback
`(window.tabler && window.tabler.bootstrap) || window.bootstrap`.

#### Scenario: Maps toast fires

- GIVEN the maps page with a `showToast` call
- WHEN the toast is triggered
- THEN a toast renders without ReferenceError
- AND it hides and removes itself on `hidden.bs.toast`
- AND its icons use the vendored Tabler webfont (`ti ti-*`), never FontAwesome (`fas fa-*`)

#### Scenario: Modal path unchanged

- GIVEN a dashboard page instantiating `window.tabler.Modal`
- WHEN the modal opens
- THEN the component constructs from the 1.5.1 bundle

### Requirement: SOCIALS-PLUGIN

The portal SHALL serve the socials plugin so `social social-app-*` renders
brand marks and the `social-gray` modifier renders the grayscale variant.

#### Scenario: Social assets resolve

- GIVEN `tabler-socials.min.css` is vendored
- WHEN the landing page renders `social social-gray social-app-facebook`
- THEN the mark renders with no missing-asset request (every referenced
  `img/social/*.svg` exists)

### Requirement: NO-REGRESSION-GATE

The upgrade SHALL pass `python manage.py check`, tests for `apps.core`,
`apps.meteo` and `apps.home`, and `djlint --reformat --check` on touched
templates.

#### Scenario: Green gate

- GIVEN the vendored swap and the in-scope fixes applied
- WHEN the gate commands run
- THEN all pass
- AND `collectstatic --no-input` completes

#### Scenario: Visual smoke

- GIVEN the dev server with the swapped assets
- WHEN dashboard, public home and maps pages render in light and dark
- THEN no console errors and no broken Tabler components (modals, toasts,
  datatables, Tempus pickers)
