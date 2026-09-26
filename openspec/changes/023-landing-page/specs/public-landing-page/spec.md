# public-landing-page Specification

Capability: `public-landing-page` (light public landing at `/`; home at `/home/`)

## Purpose

`/` serves a light visitor-facing landing replacing the heavy admin home. The
home moves to `/home/` keeping `reverse('home:index')` stable; the landing
renders forecast, warnings, featured services, models/satellites/publications
links and institution logos without amCharts or dashboard tooling.

## Requirements

### Requirement: ROOT-ROUTING

The system SHALL serve the landing at `/` with URL name `landing`, so
`reverse('home:landing') == '/'`, and SHALL serve the `IndexView` home at
`/home/` keeping URL name `index`, so `reverse('home:index') == '/home/'`.
No other `home` URL SHALL change.

#### Scenario: Landing resolves at root

- GIVEN `app_name='home'` in the home URL configuration
- WHEN `reverse('home:landing')` is resolved
- THEN it returns `/`
- AND `GET /` returns HTTP 200 rendering `landing.html` (`assertTemplateUsed`)

#### Scenario: Home keeps its canonical name

- GIVEN the home view moved from `/`
- WHEN `reverse('home:index')` is resolved
- THEN it returns `/home/`
- AND `GET /home/` returns HTTP 200 rendering the original home template

#### Scenario: Other home paths unchanged

- GIVEN existing `home` URLs beyond index
- WHEN they are reversed
- THEN their paths remain unchanged

### Requirement: LANDING-RENDER

The landing SHALL render a `landing.html` template with a hero (latest forecast
+ call to action), an active-warnings strip, three region cards, featured
services, links to models/satellites/publications, and an institution block
(CITMA/AMA/INSMET logos). The page SHALL render HTTP 200 when no data exists.

#### Scenario: Sections render with data

- GIVEN forecast data, active warnings and published services exist
- WHEN `GET /` renders
- THEN hero, warnings strip, three region cards, featured services,
  models/satellites/publications links and institution block are present

#### Scenario: None-safe empty state

- GIVEN no forecast, warning or service data exists
- WHEN `GET /` renders
- THEN HTTP 200 is returned
- AND no section raises an error or renders unescaped content

### Requirement: NAVBAR-CONDITIONAL

The shared public navbar SHALL point its logo and "Inicio" link to `/` when
`url_name == 'landing'`, and to `/home/` on every other page.

#### Scenario: Landing links home

- GIVEN the navbar renders on the landing (`url_name == 'landing'`)
- WHEN its logo and "Inicio" hrefs are inspected
- THEN both equal `/`

#### Scenario: Off-landing links unchanged

- GIVEN any non-landing page renders the navbar
- WHEN its logo and "Inicio" hrefs are inspected
- THEN both equal `/home/`
- AND the remaining menu renders without error

### Requirement: SEO-OG-MINIMUM

The landing SHALL include a meta description and the OG tags `og:title`,
`og:description`, `og:type`, `og:url` and `og:locale` in its `<head>`, without
altering the site-wide CSP response headers.

#### Scenario: Social meta present on landing

- GIVEN `GET /` renders
- WHEN the landing `<head>` is inspected
- THEN meta description and the five OG tags are present

#### Scenario: CSP intact

- GIVEN the landing rendered
- WHEN response headers are inspected
- THEN the CSP headers match the site-wide policy

### Requirement: LANDING-REGRESSION-GATE

The change SHALL keep `apps.home` and `apps.core` test suites green and the
CDN-reference scan passing for the new templates, and SHALL render the public
footer `social-gray` anchors without breaking the light theme default.

#### Scenario: Green suites

- GIVEN the landing implemented
- WHEN `python manage.py test apps.home apps.core` runs
- THEN all tests pass

#### Scenario: No CDN references

- GIVEN the landing template and layout
- WHEN templates are scanned for CDN references
- THEN none match

#### Scenario: Social footer integration

- GIVEN `GET /` renders the landing with the public footer
- WHEN the footer anchors are inspected
- THEN they use `social social-app-* social-gray` and each carries an `aria-label`

#### Scenario: Light theme default unchanged

- GIVEN the landing layout extends `base.html`
- WHEN the page renders
- THEN `data-bs-theme="light"` is the server-side default
