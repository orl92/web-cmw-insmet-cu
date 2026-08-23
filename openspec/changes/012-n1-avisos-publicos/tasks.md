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

- [ ] 1.1 In `apps/home/views/avisos/alertas_tempranas/views.py` change line 14 `select_related('user')` → `select_related('user', 'user__profile')`.
- [ ] 1.2 In `apps/home/views/avisos/tormentas/views.py` change line 14 likewise.
- [ ] 1.3 In `apps/home/views/avisos/ciclones_tropicales/views.py` change line 14 likewise.

## Phase 2: Tests (strict_tdd, apps/home/tests/)

- [ ] 2.1 N+1 test — early warnings view: seed 1 and N (≥10) `MeteoWarning` (`warning_type='early'`, future `valid_until`, with `User` + `Profile`); render the URL inside `assertNumQueries` and assert the count is identical for 1 vs N (constant, no linear growth).
- [ ] 2.2 Repeat 2.1 for storm (`warning_type='storm'`) and tropical_cyclone (`warning_type='tropical_cyclone'`).
- [ ] 2.3 Render test: GET each view URL; `assertContains(response, user.get_full_name)` and that the avatar URL from `profile.get_avatar` is present; `response.status_code == 200`.

## Phase 3: Verification

- [ ] 3.1 Run `python manage.py test apps.home` — all new tests pass.
- [ ] 3.2 Run `python manage.py check` — no system check errors.

## Phase 4: Documentation

- [ ] 4.1 Note in the change summary that `select_related('user')` already existed; this change adds `user__profile` to remove the remaining profile N+1.

## Phase 5: Commit

- [ ] 5.1 Commit the three view files and added tests with a conventional message referencing `012-n1-avisos-publicos`.
