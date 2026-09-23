# Delta for tabler-core-vendor

## MODIFIED Requirements

### Requirement: SOCIALS-PLUGIN

The portal SHALL serve the socials plugin so `social social-app-*` renders
brand marks and the `social-gray` modifier renders the grayscale variant. The
base `head.html` SHALL link the vendored `tabler-socials.min.css?v=151`, and
the public home footer and the dashboard footer SHALL each render four anchors
`social social-app-{facebook,instagram,x,telegram} social-gray`, each with an
`aria-label`.
(Previously: socials CSS vendored but not linked in `head.html`; footers used
`btn btn-icon btn-facebook/...` with webfont icons)

#### Scenario: Social assets resolve

- GIVEN `tabler-socials.min.css` is vendored
- WHEN the landing page renders `social social-gray social-app-facebook`
- THEN the mark renders with no missing-asset request (every referenced
  `img/social/*.svg` exists)

#### Scenario: Socials stylesheet linked site-wide

- GIVEN `head.html` renders as part of `base.html`
- WHEN the `<head>` is inspected
- THEN it links `tabler-socials.min.css?v=151`
- AND no CDN reference to the socials stylesheet exists

#### Scenario: Footers expose social-gray anchors

- GIVEN the public home footer and the dashboard footer
- WHEN both render
- THEN each exposes exactly four anchors
  `social social-app-{facebook,instagram,x,telegram} social-gray`
- AND each anchor carries an `aria-label` naming its brand

#### Scenario: Grayscale contrast in dark mode

- GIVEN the footer renders with `data-bs-theme="dark"`
- WHEN the social anchors are inspected
- THEN the grayscale marks remain visible with AA-compliant contrast