# Delta for tema-personalizado (007)

Capability: `tema-personalizado` (custom brand/theme without forking Tabler)

## ADDED Requirements

### Requirement: LIGHT-DEFAULT-EXPLICIT

The portal SHALL render light mode by default regardless of OS
`prefers-color-scheme`. When the resolved theme is not dark, `head.html`
SHALL set `data-bs-theme="light"` on `<html>` server-side (the 1.5.1 default
is `auto`, which would follow the OS and render the portal dark on dark
systems).

#### Scenario: OS-dark visitor sees light

- GIVEN an OS in dark mode and no stored `tabler-theme` choice
- WHEN the portal loads (landing, home or dashboard)
- THEN `<html>` carries `data-bs-theme="light"`
- AND the page renders the light palette

#### Scenario: Dark choice still wins

- GIVEN a stored `tabler-theme=dark` or a `?theme=dark` URL
- WHEN the portal renders
- THEN `<html>` carries `data-bs-theme="dark"`
- AND the navbar `?theme=light` link switches back to explicit light

### Requirement: THEME-LOADER-151

The patched `tabler-theme.min.js`, re-derived on the 1.5.1 base and
documented in its provenance header, SHALL manage ONLY the light/dark toggle
and SHALL NOT read or write `data-bs-theme-base`, `data-bs-theme-font`,
`data-bs-theme-primary` or `data-bs-theme-radius`, nor their `tabler-*`
localStorage keys (1.5.1 mechanism: `tabler-<key>` localStorage to
`data-bs-*` attribute).

#### Scenario: Model theme attrs survive

- GIVEN `site_branding` seeds `data-bs-theme-base` (plus font/primary/radius)
  on `<html>`
- WHEN the patched loader runs and the visitor toggles light/dark
- THEN the four admin-seeded attributes remain unchanged

#### Scenario: Toggle persists across reloads

- GIVEN the visitor follows a navbar `?theme=dark` link
- WHEN the page reloads
- THEN the choice is read from `localStorage["tabler-theme"]` and applied
  before first paint, with no flash of the wrong mode

### Requirement: THEME-BASE-020-VERIFIED

The `data-bs-theme-base` contract (change 020) SHALL survive the 1.5.1
upgrade: the five model choices (slate, gray, zinc, neutral, stone) SHALL
resolve in the vendored `tabler-themes.min.css`, with `gray` as the default.

#### Scenario: All presets resolve

- GIVEN the page rendered with each of the five model `theme_base` values
- WHEN the page is inspected
- THEN the expected gray-scale palette applies (no unstyled fallback)
- AND `gray` renders identically to Tabler's built-in default

#### Scenario: No theme regression

- GIVEN the portal before and after the upgrade
- WHEN both render with the same `site_branding` values
- THEN the applied palette looks identical (no brand-breaking visual drift)
