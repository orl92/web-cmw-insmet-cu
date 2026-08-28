```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:1f9559b924c1bc53a9a65b98afca5fc068dab3f685ae8063c1abae0080613231
verdict: fail
blockers: 3
critical_findings: 3
requirements: 5/5
scenarios: 5/8
test_command: python manage.py test
test_exit_code: 0
test_output_hash: sha256:1f9559b924c1bc53a9a65b98afca5fc068dab3f685ae8063c1abae0080613231
build_command: python manage.py check
build_exit_code: 0
build_output_hash: sha256:1e3e63f221bde88816c4a4ef7367691607b20cc1d194028a02ec9ae0586cf9b1
```

## Verification Report

**Change**: 004-monitoreo-tareas
**Version**: N/A (delta spec `task-monitoring`)
**Mode**: Strict TDD

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 15 |
| Tasks complete | 15 |
| Tasks incomplete | 0 |

### Build & Tests Execution

**Build**: ✅ Passed
```text
python manage.py check
System check identified no issues (0 silenced).
exit 0
```

**Tests**: ✅ 448 passed / ❌ 0 failed / ⚠️ 0 skipped
```text
python manage.py test
Ran 448 tests in 133.538s
OK (exit 0)
```
Baseline pre-004 was 444 passing; this change added 4 tests (success log, failure log+traceback, retry config, no-swallow) → 448 matches the expected ~448.

**Coverage**: ➖ Not available (no coverage tool configured/run).

### Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| TASK-LOG-1 | task enqueued | `test_task_monitoring.py > test_enqueue_creates_success_log` | ✅ COMPLIANT |
| TASK-LOG-1 | task succeeds | `test_task_monitoring.py > test_enqueue_creates_success_log` | ✅ COMPLIANT |
| TASK-LOG-2 | task fails | `test_task_monitoring.py > test_failure_records_error` | ✅ COMPLIANT |
| TASK-LOG-2 | task retries | `test_task_monitoring.py > test_send_email_no_swallow` (exercises SIGNAL_RETRYING → status RETRYING, attempts incremented in same handler update) | ✅ COMPLIANT |
| TASK-RETRY-1 | email send failure is visible | `test_send_email_no_swallow` + `test_failure_records_error` | ✅ COMPLIANT |
| TASK-VIEW-1 | stale queue alert | (none — static only) | ❌ UNTESTED |
| TASK-VIEW-1 | non-superuser blocked | (none — static only) | ❌ UNTESTED |
| TASK-ADMIN-1 | admin inspects failures | (none — static only) | ❌ UNTESTED |

**Compliance summary**: 5/8 scenarios COMPLIANT (runtime), 3/8 UNTESTED (no automated test — verified by source inspection only).

### Correctness (Static Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| TASK-LOG-1 model | ✅ Implemented | `TaskExecutionLog` in `apps/core/models.py:248` — all required fields, `STATUS_CHOICES` (6 values), `db_index` on `task_id`, `Meta.indexes` on `(status, enqueued_at)`, `default_permissions=()` + 4 Spanish custom perms, **no** soft delete (plain `models.Model`). |
| TASK-LOG-2 signals | ✅ Implemented | `apps/core/apps.py` `ready()` registers SIGNAL_ENQUEUED/EXECUTING/COMPLETE/RETRYING/ERROR; every handler body wrapped in `try/except` that only logs → cannot raise into the worker. `_safe_args`/`_tb` sanitize (truncate + omit sensitive args). |
| TASK-RETRY-1 retry + no-swallow | ✅ Implemented | `tasks.py:11` and `:34` both `@huey.task(retries=3, retry_delay=30, retry_backoff=True)`; the bare `try/except` swallow at old `:59-62` is removed — `email.send()` propagates. |
| TASK-VIEW-1 view | ✅ Implemented (static) | `TaskMonitoringView` (`dashboard.py:400`) = `LoginRequiredMixin` + `UserPassesTestMixin` with `test_func` → `is_superuser`; `stale_count`/`error_count` queries; template renders red stale banner, warning error banner, DataTables, expandable traceback. URL `tasks/` in `urls.py:11` (`app_name='dashboard'`). NO runtime test. |
| TASK-ADMIN-1 admin | ✅ Implemented (static) | `TaskExecutionLogAdmin` (`admin.py:34`) read-only (`readonly_fields` all, `has_add/change_permission=False`), `list_display`, `list_filter=('status',)`. NO runtime test. |

### Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Keep raw `SqliteHuey` broker (no djhuey) | ✅ Yes | `config/huey.py` untouched; signals layered on top. |
| Primary-DB store (not huey.db) | ✅ Yes | `TaskExecutionLog` in main DB; admin/ORM queryable. |
| Signal handlers resilient (never raise) | ✅ Yes | `try/except` logging only in every handler. |
| Retry config on both tasks | ✅ Yes | `retries=3, retry_delay=30, retry_backoff=True`. |
| `SIGNAL_RETRYING` preserves prior error/traceback | ✅ Yes | `on_retrying` keeps `error_message`/`traceback` when `exc is None` (verified huey 3.3.4 emits RETRYING without exc). |
| Dashboard superuser + DataTables + banners | ✅ Yes | Matches design §7. |
| Admin read-only + status filter | ✅ Yes | Matches design §6. |

### TDD Compliance (Strict TDD)

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ Partial | Apply-progress (Engram `sdd/004-monitoreo-tareas/apply-progress`) is a prose summary; it does not contain the formal "TDD Cycle Evidence" table required by the Strict TDD module. TDD was nonetheless confirmed via runtime evidence below. |
| All tasks have tests | ⚠️ Partial | 4 tests cover the 3 behavioral tasks (model signals, retry, no-swallow); the view/admin tasks (4.1–4.3, 1.3) have no dedicated test → CRITICAL per gate. |
| RED confirmed (tests exist) | ✅ | `apps/core/tests/test_task_monitoring.py` exists with 4 test methods. |
| GREEN confirmed (tests pass) | ✅ | All 4 pass within the full 448-test run. |
| Triangulation adequate | ✅ | success/error/retry-config/no-swallow cover distinct behaviors. |
| Safety Net for modified files | ➖ | Test file is new; no pre-existing file was modified by 004, so no safety-net re-run applies. |

**TDD Compliance**: 4/6 checks passed (view/admin tasks untested; evidence-table format partial).

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 0 | 0 | unittest/TestCase |
| Integration | 4 | 1 (`test_task_monitoring.py`) | Django TestCase + huey immediate mode |
| E2E | 0 | 0 | not installed |
| **Total** | **4** | **1** | |

### Changed File Coverage

Coverage analysis skipped — no coverage tool detected (NOT a failure).

### Assertion Quality

| File | Line | Assertion | Issue | Severity |
|------|------|-----------|-------|----------|
| `test_task_monitoring.py` | 49-51 | `log is not None` + `status == SUCCESS` | Real behavior (lifecycle persistence) | — |
| `test_task_monitoring.py` | 59-63 | `status == ERROR`, `attempts >= 1`, `traceback` truthy | Real behavior (failure capture) | — |
| `test_task_monitoring.py` | 65-69 | `retry_count >= 1` for both tasks | Real config assertion (`task.settings['default_retries']`) | — |
| `test_task_monitoring.py` | 85-93 | `status in [ERROR, RETRYING]`, `traceback` truthy | Real behavioral assertion (no-swallow) | — |

**Assertion quality**: ✅ All assertions verify real behavior (no tautologies, ghost loops, or smoke tests).

### Quality Metrics

**Linter (ruff)**: ✅ No errors (`ruff check` on all 8 changed `.py` files passed).
**Type Checker**: ➖ Not available (no mypy/pyright in project).
**djlint (new template)**: ✅ `tasks.html` clean (`--reformat --check` 0 changes, `--lint` 0 errors).

> Note: a project-wide `djlint . --reformat --check` flags 4 known pre-existing baseline templates (e.g. `apps/meteo/templates/pages/meteo/warning/early_warning/list.html` and 3 others) that pre-date this change and are out of scope. The new `tasks.html` is NOT among them.

### Issues Found

**CRITICAL**:
1. `TASK-VIEW-1 / stale queue alert` — no automated test exercises the red stale-queue banner (`stale_count` context). Verified by source inspection only. (Per decision gate: untested scenario → CRITICAL/UNTESTED.)
2. `TASK-VIEW-1 / non-superuser blocked` — no automated test asserts a non-superuser is denied `dashboard:tasks`. Verified by source inspection only (`UserPassesTestMixin.test_func` → `is_superuser`).
3. `TASK-ADMIN-1 / admin inspects failures` — no automated test exercises `TaskExecutionLogAdmin` read-only registration + `status` filter. Verified by source inspection only.

**WARNING**:
1. Apply-progress lacked the formal "TDD Cycle Evidence" table required by Strict TDD mode; TDD adherence was confirmed via runtime execution instead.

**SUGGESTION**:
1. Add `TaskMonitoringView` tests (banner context when `stale_count/error_count > 0`, and 403/redirect for non-superuser) and a `TaskExecutionLogAdmin` (`status=ERROR` filter) test to close the runtime-coverage gap.
2. Optionally assert `attempts >= 1` in `test_send_email_no_swallow` to make the RETRYING increment explicit (currently inferred from the same handler update that sets `status=RETRYING`).

### Verdict

**FAIL** — not archive-ready. All 15 tasks complete, full 448-test suite green, `manage.py check` clean, ruff/djlint clean on changed files; every spec requirement is implemented and design-coherent. However 3 of 8 spec scenarios (TASK-VIEW-1 ×2, TASK-ADMIN-1 ×1) have no automated runtime test, which the verification gate treats as CRITICAL/UNTESTED. Add the missing view/admin tests and re-run `sdd-verify` to reach PASS and unlock archive.

## Key Learnings

1. Huey 3.3.4 emits SIGNAL_RETRYING without the exception argument, so the retrying handler must preserve error_message/traceback stored by on_error.
2. In huey immediate mode a failing task with retries>0 emits SIGNAL_ERROR then SIGNAL_RETRYING synchronously, ending in RETRYING (not ERROR), so no-swallow assertions must accept both states.
3. `@huey.task(retries=N)` stores the value as `task.settings['default_retries']`; the wrapper `.retries` stays None, so tests read `task.settings`.
4. `call_local()` does not emit signals; verification must use `huey.immediate = True` to exercise signal handlers.
5. gentle-ai sdd-verify-validate denies a passing verdict when scenario coverage is incomplete, enforcing "untested scenario → CRITICAL/FAIL" from the decision gate.
