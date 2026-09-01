# Design: Eliminate N+1 on Public Warning Views

## Technical Approach

Change the `select_related(...)` tuple on the three `MeteoWarning` querysets
from `('user',)` to `('user', 'user__profile')`. `select_related` follows the
`ForeignKey` / `OneToOne` chain: `user` (FK on `Warning` → `User`) and
`user__profile` (`OneToOne` `User` → `Profile`). Both are joined in the single
SQL `SELECT`, so accessing `warning.user`, `warning.user.get_full_name`, and
`warning.user.profile.get_avatar` in the template requires no additional
queries.

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| Join depth | `select_related('user', 'user__profile')` vs `prefetch_related('user__profile')` | `profile` is a `OneToOne` (1:1) → `select_related` is a single `JOIN`, cheaper than a prefetch (extra query + in-Python join). `prefetch` only wins for reverse/FKs with multiple rows. | `select_related('user', 'user__profile')` |
| Scope | patch 3 views vs centralize queryset | Only these 3 public views read `avisos.html` with author + avatar; minimal diff, no behavior change elsewhere. | patch 3 views |
| Double `get_queryset()` | fix now vs leave | `get_context_data` re-calls `self.get_queryset()` (lines 23–29) doubling the base query; constant but wasteful. Out of scope to keep change tight; flagged as follow-up. | leave (note only) |

## Data Flow

```
Request GET /avisos/early/  (and /storm/, /tropical/)
        │
        ▼
EarlyWarningListView.get_queryset()
        │  MeteoWarning.objects.filter(warning_type=..., valid_until__gte=now)
        │    .select_related('user', 'user__profile')
        ▼
Single SQL SELECT joining Warning + User + Profile
        │
        ▼
Template avisos.html per warning:
   warning.user.get_full_name        → already in row
   warning.user.profile.get_avatar  → already in row  (NO extra query)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `apps/home/views/avisos/alertas_tempranas/views.py` | Modify | line 14: `select_related('user')` → `select_related('user', 'user__profile')` |
| `apps/home/views/avisos/tormentas/views.py` | Modify | line 14: same |
| `apps/home/views/avisos/ciclones_tropicales/views.py` | Modify | line 14: same |
| `apps/home/tests/test_views.py` | Modify/Add | new `TestCase`s for the 3 warning views |
| `templates/layouts/avisos.html` | Unchanged | reads `user.profile.get_avatar` (line 48) and `user.get_full_name` (line 50) |

## Interfaces / Contracts

No new HTTP/JSON contract. The views still return the same `ListView` response
and `avisos.html` renders unchanged. The only observable change is a constant
number of SQL queries regardless of warning count.

## Testing Strategy

Repo uses `strict_tdd`; tests live in `apps/home/tests/`. Use Django
`TestCase` + `Client` and seed via model creation (User + Profile + MeteoWarning
with future `valid_until`).

| Layer | What to Test | Approach |
|-------|--------------|----------|
| Query count (N+1) | Query count is constant as warning count grows | For each of the 3 views: seed 1 warning, render URL inside `assertNumQueries(n)`; seed N (e.g. ≥10) warnings, render inside `assertNumQueries(n)` again — same `n`. Capture `n` as the baseline (includes the double `get_queryset()` cost). |
| Render | Page renders author fields | GET each URL; `assertContains` the author's `get_full_name` and that the `get_avatar` output (avatar URL) appears in the HTML. |
| Regression | No 500 / correct template | `response.status_code == 200`; expected template `pages/home/warnings/...`. |

## Threat Matrix

`N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary is changed.` This is a query
optimization on read-only public views; no untrusted-input execution path is
added. (Note: the views' `valid_until__gte=timezone.now()` filter is unchanged.)

## Migration / Rollout

No migrations, no model/URL changes. Safe to merge as a 3-line diff + tests.

## Rollback

`git checkout -- apps/home/views/avisos/alertas_tempranas/views.py apps/home/views/avisos/tormentas/views.py apps/home/views/avisos/ciclones_tropicales/views.py`. No migrations.

## Open Questions

- Should the redundant second `get_queryset()` call in `get_context_data` be
  removed later? (Follow-up, out of scope here.)
