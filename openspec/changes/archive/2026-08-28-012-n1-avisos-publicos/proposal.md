# Proposal: Eliminate N+1 on Public Warning Views (select_related user__profile)

## Intent

The public warning views under `apps/home/views/avisos/*/views.py` render each
`MeteoWarning` with author metadata (`warning.user.profile.get_avatar` and
`warning.user.get_full_name`) through `templates/layouts/avisos.html`. The
current querysets do `filter(...).select_related('user')`. Because
`user.profile` is a separate `OneToOne` relation that is NOT joined, each
rendered warning triggers an extra query to load its `Profile` → linear N+1
growth with the number of warnings.

**Correction to the investigated context (verified in code):** the three views
*already contain* `select_related('user')` (line 14 of each file), so
`warning.user` is eager and `user.get_full_name` (template line 50) does NOT
cause N+1. The remaining, real N+1 is exclusively
`warning.user.profile.get_avatar` (template line 48), caused by the missing
`user__profile` join. This change completes the fix by adding
`select_related('user', 'user__profile')`.

## Scope

### In Scope
- Add `user__profile` to the `select_related(...)` call in the three public
  warning `ListView`s (`alertas_tempranas`, `tormentas`, `ciclones_tropicales`).
- Add `strict_tdd` tests that assert the query count is constant as the warning
  count grows, plus a render regression test.

### Out of Scope
- `WarningListView` in `apps/meteo` (already fixed in change 001 with
  `select_related('user')`, uses `layouts/list.html` + DataTables).
- DRF API pagination (change 010).
- Model / migration / URL changes.
- The redundant second `get_queryset()` call inside `get_context_data` (lines
  23–29 of each view) which DOUBLES the base query. It is constant (not linear)
  but wasteful; flagged as a follow-up, not fixed here, to keep the diff minimal.

## Capabilities

### New Capabilities
- `avisos-publicos-no-n-plus-1`: public warning views load author + profile in a
  single `JOIN`, so rendered query count is independent of the number of
  warnings.

### Modified Capabilities
- None at the OpenSpec capability level (this tightens an existing view query).

## Approach

1. In each of the three views, change
   `.select_related('user')` → `.select_related('user', 'user__profile')` so the
   `Profile` (and its `get_avatar`) is joined in the same query.
2. Add Django `TestCase`s in `apps/home/tests/` using `assertNumQueries` that
   render each view's URL with 1 vs N warnings and assert the query count does
   NOT grow. Also assert the page renders `user.get_full_name` and
   `profile.get_avatar`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/home/views/avisos/alertas_tempranas/views.py` | Modified | `select_related('user')` → `('user', 'user__profile')` |
| `apps/home/views/avisos/tormentas/views.py` | Modified | same |
| `apps/home/views/avisos/ciclones_tropicales/views.py` | Modified | same |
| `templates/layouts/avisos.html` | Unchanged | already reads `user.profile.get_avatar` (line 48) and `user.get_full_name` (line 50) |
| `apps/home/tests/test_views.py` (extend) | New | `assertNumQueries` + render tests |
| `openspec/changes/012-n1-avisos-publicos/specs/012-n1-avisos-publicos/spec.md` | New | Delta spec |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `user__profile` join changes nothing visible | Low | Template already uses both fields; test asserts render |
| A warning whose `user` has no `Profile` | Low | `Profile` is created via `post_save` signal; `OneToOne` guarantees 1 row |
| Query-count baseline flaky due to double `get_queryset()` | Low | Test asserts CONSTANT growth (1 vs N), not an absolute number |

## Rollback Plan

`git checkout --` the three view files (no migrations). Tests are removed with
the change. The `select_related` tuple reverts to `('user',)`.

## Dependencies

- `Profile` (`apps/user_auth`): `user = models.OneToOneField(User, ..., related_name='profile')`;
  `get_avatar` defined on `Profile` (line 41). Both verified.

## Success Criteria

- [ ] All three views use `select_related('user', 'user__profile')`.
- [ ] `assertNumQueries` proves query count is constant as warning count grows.
- [ ] Each view renders `user.get_full_name` and `profile.get_avatar`.
- [ ] `python manage.py test apps.home` passes.
