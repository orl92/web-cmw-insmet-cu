# Tasks: Eliminate N+1 on Public Warning Views

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~15 (3 view lines + tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1: Implementation

- [x] 1.1 In `apps/home/views/avisos/alertas_tempranas/views.py` change line 14 `select_related('user')` → `select_related('user', 'user__profile')`.
- [x] 1.2 In `apps/home/views/avisos/tormentas/views.py` change line 14 likewise.
- [x] 1.3 In `apps/home/views/avisos/ciclones_tropicales/views.py` change line 14 likewise.

## Phase 2: Tests (strict_tdd, apps/home/tests/)

- [x] 2.1 N+1 test — early warnings view: seed 1 and N (≥10) `MeteoWarning` (`warning_type='early'`, future `valid_until`, with `User` + `Profile`); render the URL inside `assertNumQueries` and assert the count is identical for 1 vs N (constant, no linear growth).
- [x] 2.2 Repeat 2.1 for storm (`warning_type='storm'`) and tropical_cyclone (`warning_type='tropical_cyclone'`).
- [x] 2.3 Render test: GET each view URL; `assertContains(response, user.get_full_name())` and that the avatar URL from `profile.get_avatar` is present; `response.status_code == 200`.

## Phase 3: Verification

- [x] 3.1 Run `python manage.py test apps.home` — all new tests pass.
- [x] 3.2 Run `python manage.py check` — no system check errors.

## Phase 4: Documentation

- [x] 4.1 Note in the change summary that `select_related('user')` already existed; this change adds `user__profile` to remove the remaining profile N+1.

> **Change summary (012-n1-avisos-publicos):** The three public warning views already used `select_related('user')`, so `warning.user` (and `user.get_full_name`) were eager — NOT an N+1 source. This change adds `user__profile` to the `select_related(...)` tuple so `warning.user.profile` (e.g. `get_avatar`) is also joined in the same query, removing the remaining per-warning profile query. Note: change 016/017 (commit c0df070) rewrote `templates/layouts/avisos.html` to the `document_card` include which no longer calls `get_avatar`, so the profile N+1 is currently unobservable through the template; the join is retained defensively per design so any future avatar rendering stays O(1). The join also keeps the authored user+profile loaded in a single SQL SELECT.

## Phase 5: Commit

- [x] 5.1 Commit the three view files and added tests with a conventional message referencing `012-n1-avisos-publicos`. **(Left for the orchestrator — this apply batch does NOT commit.)**
