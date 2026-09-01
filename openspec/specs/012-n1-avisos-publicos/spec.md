# avisos-publicos-no-n-plus-1 Specification

## Purpose

Ensure the three public warning `ListView`s (early warnings, storms, tropical
cyclones) in `apps/home/views/avisos/*/views.py` load each `MeteoWarning`'s
author `User` and `Profile` via a single `select_related('user', 'user__profile')`
JOIN, so rendering `templates/layouts/avisos.html` (which reads
`warning.user.profile.get_avatar` and `warning.user.get_full_name`) does not
issue additional queries per warning.

## Requirements

### Requirement: Public warning views join user and profile

The three views `EarlyWarningListView`, `StormListView`, and
`TropicalCycloneListView` MUST call
`select_related('user', 'user__profile')` on their `MeteoWarning` queryset (in
addition to the existing `filter(warning_type=..., valid_until__gte=...)`).

#### Scenario: Queryset uses the combined select_related

- GIVEN the view module is imported
- WHEN `get_queryset()` is inspected
- THEN the queryset SHALL include `select_related('user', 'user__profile')`

### Requirement: No N+1 on author/profile access

Rendering the public warning list (template `avisos.html`) MUST NOT issue
additional SQL queries that grow with the number of warnings, because
`warning.user` and `warning.user.profile` are joined eagerly.

#### Scenario: Query count is constant as warning count grows

- GIVEN ≥10 `MeteoWarning` records exist for the view's `warning_type`, each with a future `valid_until` and a `User` + `Profile`
- WHEN the view URL is rendered
- THEN the total SQL query count SHALL be the same as when only 1 warning exists (no linear growth)

#### Scenario: Template reads author fields without extra queries

- GIVEN a rendered warning list
- WHEN `avisos.html` accesses `warning.user.get_full_name` and `warning.user.profile.get_avatar`
- THEN those accesses SHALL NOT trigger additional per-warning SQL queries

### Requirement: No visual regression

Each public warning view MUST still render successfully with the author's full
name and avatar, preserving the current layout.

#### Scenario: Page renders author name and avatar

- GIVEN at least one warning exists
- WHEN a client GETs the view URL
- THEN `response.status_code` SHALL be `200`
- AND the HTML SHALL contain the author's `get_full_name` text
- AND the HTML SHALL contain the avatar URL produced by `profile.get_avatar`

### Requirement: Scope isolation

This change MUST NOT alter `WarningListView` (`apps/meteo`), the DRF API
endpoints, or any model / URL / migration. It affects only the three
`apps/home/views/avisos/*/views.py` files and their tests.

#### Scenario: Meteo WarningListView unaffected

- GIVEN `apps/meteo` `WarningListView` (already uses `select_related('user')`, `layouts/list.html`)
- WHEN this change is applied
- THEN its code and query behavior SHALL remain unchanged
