---
description: "Post-implementation test quality gate. Scores uncommitted tests against 22 criteria (C1-C22) — incl. 3-tier source tagging (T1 AC / T2 INV·NFR / T3 QUALITY), DDD test-through-the-interface, and seam/real-infra conformance — grounding the 'would a wrong impl pass?' checks in mutation testing when available. Uses Explore to verify ACs + invariants against produced tests and implementation. Companion to the `design-tests` skill. Run after /tdd-feature-team or any implementation that produces tests."
argument-hint: "[path or scope — if empty, scans all uncommitted test changes]"
---

MANDATORY FIRST ACTION — load these skills BEFORE any other action:
```
Skill(skill: "fullstack-dev-skills:test-master")
Skill(skill: "fullstack-dev-skills:security-reviewer")
```

You are a strict test quality evaluator. Score the implementation output against ALL 22 criteria below.

## STEP 0: GATHER CONTEXT

1. Run `git diff --name-only` and `git status --short` to find changed/new files
2. Identify: test files, implementation files, fixture files, stub files
3. If $ARGUMENTS is provided, scope to that path. Otherwise scan all uncommitted changes.
4. Find the ACs for this work — check recent conversation, plan files, CLAUDE.md, or story files. List them.

## STEP 1: EXPLORE — verify ACs against tests and implementation

Spawn an Explore agent to do deep verification:

```
Agent(
  subagent_type="Explore",
  prompt="Verify test and implementation coverage for these ACs:\n\n{ac_list}\n\nSearch for:\n1. Every AC tag (`# AC-N`, `<!-- AC-N -->`) in test files — map AC → test function\n2. Every AC's implementation — trace AC → source code that fulfills it\n3. Stub files — check they return wrong values (False, -1, None, []), NEVER raise NotImplementedError\n4. Fixture/golden files — any test comparing against reference data?\n5. Adversarial/chaos tests — tests beyond ACs (invalid input, boundary, timeout, duplicate, concurrent)\n6. Transitive deps — imports-of-imports, configs, migrations, CI configs, type defs\n\nReturn:\n- AC coverage matrix: AC-N → [test functions] → [impl files]\n- Uncovered ACs (zero tests)\n- Stub audit (wrong values vs NotImplementedError)\n- Fixture/snapshot test count\n- Adversarial test count + categories covered\n- Transitive file categories found"
)
```

## STEP 1.5: MUTATION TEST — objective backbone for C5 + C17

C5 ("could a WRONG implementation still pass?") and C17 ("no tautological tests") are hand-rolled mutation testing applied by LLM reasoning. When tooling is available, GROUND them in execution instead of judgment — a **surviving mutant on changed lines is the objective C5/C17 FAIL signal**: it proves a wrong implementation passes the suite. This mirrors Meta's TestGen-LLM/ACH gate, where only tests that kill non-equivalent mutants are trusted.

1. **Detect tooling.** Python → `mutmut` 3.x (preferred) or `cosmic-ray`; TypeScript → Stryker; Go → `gremlins` / `go-mutesting`.
2. **If present, scope to CHANGED code only** (whole-tree runs are slow). mutmut 3.x is config-driven — `[tool.mutmut] paths_to_mutate=[...]` in `pyproject.toml` sets the universe; scope a run with a glob on the changed module. **Mutant names are DOTTED module paths, not file paths** — `"app.domains.reviews.service*"`, NOT `"app/domains/.../service.py"` (slash form silently matches nothing). There is no `--paths-to-mutate` flag (that was 2.x):
   - `uv run mutmut run "app.domains.<area>.<module>*" --max-children N` to parallelize
   - then `uv run mutmut results` (lists only survivors + "no tests" — killed mutants are omitted as fine); `uv run mutmut show <full.mutant.name>` for the diff; `uv run mutmut export-cicd-stats` for machine-readable totals
   - keep runs sane: set `mutate_only_covered_lines=true`, and narrow the stats run via `pytest_add_cli_args_test_selection=["tests/<dir>"]` so it doesn't execute the whole suite per invocation
   - status legend: 🎉 killed (good) · 🙁 survived (= C5/C17 FAIL) · 🫥 no tests cover this line · ⏰ timeout
3. **Record survivors — but RE-RUN before trusting.** A surviving mutant *usually* = a fault the tests miss → attach it to a C5/C17 failure with `file:line` and the mutation (e.g. `< → <=`, `cond → False`, return-value swap). BUT mutation results carry flake noise on infra-heavy suites (shared DB across parallel mutant processes, timing-sensitive teardown). Before reporting a survivor as a finding, **re-run it ≥2-3× — serial (`--max-children 1`) if the suite shares a DB.** If it dies on re-run, it was a flake, not a gap; don't report it. (Observed: a 1-in-9 fsm survivor that never reproduced in 8 serial+parallel re-runs.)
4. **If NO mutation tooling is configured:** emit a MISSING ARTIFACT note recommending it be added (`mutmut` 3.x for pytest projects — needs a one-time `[tool.mutmut]` block), then fall back to manual C5/C17 reasoning — and label those scores **"manual, not execution-verified."**

> ⚠️ mutmut runs in a SANDBOX COPY (`mutants/` dir, one level deeper than the real tree). Two things break infra-heavy / monorepo suites there, both fixable in `conftest.py`:
> 1. **`uv run <x>` subprocesses fail** — the copied tree isn't a uv-workspace member, so deps don't resolve. Fix: call the tool's Python API in-process (e.g. `alembic.command.upgrade(Config(ini), "head")` instead of `subprocess.run(["uv","run","alembic",...])`).
> 2. **`Path(__file__).parents[N]` indexing shifts** by one (the extra `mutants/` level). Fix: locate the repo root by walking UP for a marker (`.git`, or an `apps/`+`packages/` pair) — the sandbox lives inside the repo, so upward search still finds the real root.
> Bring infra up first and confirm a baseline `mutmut run` on ONE module works before trusting the gate.

**Coverage is NOT evidence for C5/C17.** A suite can hit 100% line coverage with ~4% mutation score; coverage proves lines ran, mutation score proves behavior is checked.

## STEP 2: SCORE against 19 criteria

### C1: Source-tag coverage (every AC + invariant tagged; NO untagged tests)
PASS: 100% of ACs have ≥1 **T1** test (`# AC-N`/`<!-- AC-N -->`); every stated/discovered **invariant** has ≥1 **T2** test (`# INV-XX`/`# NFR-XX`); every remaining test is **T3** (`# QUALITY`). ZERO untagged tests.
FAIL: any AC with zero T1 tests · any domain invariant with zero T2 tests · **any untagged test** (an untagged chaos test is a FAIL — it must be tagged `# QUALITY`; a reviewer can't distinguish a deliberate edge case from an orphan).

### C2: RED tests fail on AssertionError only
PASS: all tests reach assertion line and fail with AssertionError
FAIL: any test fails on ImportError, TypeError, AttributeError, ModuleNotFoundError
Run failing tests to verify error type if in RED phase.

### C3: Stubs return wrong values
PASS: all stub functions return wrong values (False, -1, None, []); zero `raise NotImplementedError`
FAIL: any stub uses `raise NotImplementedError` or `raise NotImplemented`
N/A if no stubs needed (testing existing code).

### C4: Zero banned assertion patterns
Grep ALL test files for these patterns. ANY match = FAIL:
- `is not None`, `is not False`
- `assert result` (bare truthy)
- `len(` combined with `> 0`
- `!= ` as sole assertion
- `isinstance(` as sole assertion (ok if paired with exact value check)
- `hasattr(`
- `mock` combined with `.called` or `.call_count`
- `assertTrue(result)` or `assertTrue(bool(`
- `assert "` combined with `not in` (absence-only)
- `assert result in [...]` with overly broad list
- Broad numeric ranges (`assert 0 < x < 1000`)
PASS: every assertion checks exact values or specific observable properties.
For each violation: file:line, offending pattern, exact-value rewrite.

### C5: Zero false-positive-prone tests
For each test: could a WRONG implementation still pass?
PASS: every test would fail given an incorrect but non-trivial implementation
FAIL: any test could pass with a plausible wrong implementation
**Objective signal (preferred):** use STEP 1.5 mutation results — any surviving mutant on changed lines = FAIL (cite the mutant `file:line`). Manual reasoning is the fallback only when no mutation tooling is configured.
For route/endpoint tests: could a hardcoded response, no-op handler, or template-only render still pass? If test only checks status code + static text without verifying server state (DB, session, side effects) → FAIL.

### C6: Adversarial/chaos tests beyond ACs
Categories: invalid input, malformed data, timeout/network failure, partial failure, concurrent access, boundary values, permission denied, disk full, duplicate requests
PASS: at least 3 adversarial tests covering 2+ categories
FAIL: only happy-path AC tests

### C7: Ground truth / fixture / snapshot tests
Types: golden file comparison, before/after file diffs, expected output fixtures, reference data snapshots
PASS: at least 1 test compares against a fixture/golden file/snapshot
FAIL: all assertions computed inline, no reference data

### C8: Explore found transitive deps
Must find: imports-of-imports, config files, test fixtures, CI configs, type definitions, related packages, migration files
PASS: Explore output contains 4+ categories beyond direct source files
FAIL: only direct source files

### C9: CoVe final verification gate
PASS: evidence that a CoVe/adversarial verification step ran after audit and found zero gaps
FAIL: no CoVe gate ran, or gaps were found but not fixed

### C10: Language-appropriate commands
Python → pytest, ruff/flake8, coverage.py, mutmut/cosmic-ray (mutation)
TypeScript → vitest/jest, eslint, c8/istanbul, Stryker (mutation)
Go → go test, golangci-lint, go tool cover, gremlins/go-mutesting (mutation)
PASS: commands match detected project language
FAIL: any hardcoded command from wrong ecosystem

### C11: ACs are behavioral (Given/When/Then) — not structural
PASS: all ACs describe user-observable behavior in Given/When/Then format
FAIL: any AC describes infrastructure, internal state, or code structure instead of user behavior

### C12: Three-tier separation — T1 (AC) / T2 (INV·NFR) / T3 (QUALITY), correctly classified
T1 test user-observable behavior; T2 pin domain invariants + NFRs; T3 are edge/adversarial. Each test tagged to its CORRECT tier.
PASS: behavioral (T1), invariant (T2), and quality (T3) tests are tier-tagged and correctly classified; infra/structural tests are T2/T3, never wearing an AC (T1) tag
FAIL: an infrastructure/structural test masquerades as an AC (T1) test · a domain invariant has no T2 test · tiers are mixed indiscriminately

### C13: Three-part proof — every test has precondition + action + assertion
Each test must: (1) verify precondition, (2) exercise behavior, (3) assert exact values. Tests without preconditions can pass for wrong reasons.
PASS: tests verify their setup is meaningful before asserting outcomes
FAIL: tests go straight from setup to assertion without proving the setup matters

### C14: Route tests verify server state — not just HTTP status + template strings
Route tests that only check status code + string containment are STRUCTURAL.
PASS: every route test verifies at least one server state change or computed output value
FAIL: any route test only checks status code + static string in response body
For route tests: could a hardcoded response, no-op handler, or template-only render still pass? → FAIL

### C15: Hand-computed math derivations — assertions have reasoning comments
Every assertion should have a comment showing WHY the expected value is correct, not just restating it.
PASS: at least 30% of assertions have derivation comments (e.g., `# charge.succeeded → pending→paid`, `# 2/3 ≈ 0.667`)
FAIL: assertions just state expected values without derivation (e.g., `# expected: paid`)

### C16: Stub signatures match framework API
Stubs must have correct function signatures for the framework.
PASS: FastAPI stubs use `async def` + correct params, Go gRPC stubs use receiver methods, etc.
FAIL: wrong async/sync, wrong param types, wrong return types — would cause TypeError in real execution

### C17: No tautological tests — test must NOT assert what the stub returns
A tautological test calls a stub that returns X, then asserts result is X — proves the stub works, not the code.
PASS: no test assertion matches the stub's configured return value
FAIL: any test asserts the exact value the stub was set to return
Example BAD: stub `return "pending"` → test `assert status == "pending"` (passes against stub!)
Example GOOD: stub `return "pending"` → test `assert status == "paid"` (fails — proves stub is wrong)
**Objective signal:** mutation testing detects the same pathology as "pseudo-tested" code — if STEP 1.5 shows a method's mutants all survive (e.g. body strippable with no test failing), the tests are tautological/pseudo-testing it → FAIL.

### C18: Adversarial tests exercise different code paths
Adversarial tests must test genuinely different scenarios, not just same function with different args on same code path.
PASS: adversarial tests cover at least 2 scenarios NOT implied by any AC (e.g., malformed JSON, DB failure)
FAIL: adversarial tests are just reworded versions of AC tests

### C19: Test code is syntactically valid
Test files must parse without SyntaxError.
PASS: all test files compile/parse cleanly (Python: `compile()`, TS: `tsc --noEmit`, Go: `go vet`)
FAIL: missing colons, unbalanced brackets, wrong indentation, mixed tabs/spaces

### C20: DDD — tests exercise the PUBLIC interface, not internals (the interface is the test surface)
PASS: tests call the repository/service/domain-verb/port and read state back through the interface; named in the domain's ubiquitous language
FAIL: tests assert private internals (`obj._x`, private methods) or use raw ORM (`db.execute(select(RawRow))`) to assert domain behavior — brittle to implementation change, not behavior change
For each violation: file:line, the internal/raw reach, and the public-interface rewrite.

### C21: Seam conformance + real-infra truth
PASS: where a port has a fake + real adapter, a conformance test runs BOTH through the same scenario asserting the same outcome; AND any DB/infra-guaranteed behavior (idempotency partial-unique index, CAS lost-update, FK reject, `FOR UPDATE` interleave) is proven on the REAL per-worker DB — a 2-connection barrier harness for genuine races
FAIL: a DB-constraint/concurrency claim "proven" against an in-memory fake (the fake can't enforce it) · `asyncio.gather` on ONE session pretending to be a race (one connection can't race itself → tautological green)
N/A if the scope has no ports and no DB/concurrency-guaranteed behavior.

### C22: Ubiquitous-language naming + no time-rot
PASS: test names read as domain rules (`test_reject_respawns_get_results`, not `test_case_2`); no hardcoded future-date literal that rots — uses `date.today()+timedelta` / a frozen clock; clock injected where timing matters
FAIL: opaque test names · a future date literal that silently starts failing when the year passes

## STEP 3: DEEP GAP ANALYSIS

After C1-C19 scoring, run test-master with args to find domain-specific gaps:

```
Skill(skill: "fullstack-dev-skills:test-master", args: "find weak or wrong tests, find gaps in the uncommitted test changes")
```

Capture test-master's findings (missing coverage, fixture guards, untested paths, false sense of coverage) and include them in the COVERAGE GAPS section of the final output.

## STEP 4: OUTPUT

```
TEST QUALITY REPORT
===================
SCANNED: [N] test files, [N] test functions, [N] assertions
ACs FOUND: [list]
MUTATION: [killed/total on changed lines, or "tooling not configured — C5/C17 manual"]

CRITERIA SCORECARD:
| #   | Criterion                    | Score    | Evidence |
|-----|------------------------------|----------|----------|
| C1  | AC coverage                  | PASS/FAIL| ...      |
| C2  | AssertionError only          | PASS/FAIL| ...      |
| C3  | Stubs wrong values           | PASS/FAIL/N/A | ... |
| C4  | No banned assertions         | PASS/FAIL| ...      |
| C5  | No false positives           | PASS/FAIL| ...      |
| C6  | Adversarial/chaos tests      | PASS/FAIL| ...      |
| C7  | Ground truth/fixtures        | PASS/FAIL| ...      |
| C8  | Explore transitive deps      | PASS/FAIL| ...      |
| C9  | CoVe final gate              | PASS/FAIL| ...      |
| C10 | Language-appropriate commands | PASS/FAIL| ...      |
| C11 | ACs behavioral (Given/When/Then) | PASS/FAIL| ...   |
| C12 | Two-tier separation (BDD/TDD)  | PASS/FAIL| ...      |
| C13 | Three-part proof pattern       | PASS/FAIL| ...      |
| C14 | Route tests verify server state | PASS/FAIL| ...     |
| C15 | Hand-computed math derivations  | PASS/FAIL| ...     |
| C16 | Stub signatures match framework | PASS/FAIL| ...     |
| C17 | No tautological tests           | PASS/FAIL| ...     |
| C18 | Adversarial = different paths   | PASS/FAIL| ...     |
| C19 | Test code parses (no SyntaxError)| PASS/FAIL| ...    |
| C20 | DDD — tests via public interface | PASS/FAIL| ...      |
| C21 | Seam conformance + real-infra    | PASS/FAIL/N/A | ... |
| C22 | Ubiquitous naming + no time-rot  | PASS/FAIL| ...      |

TOTAL: [N]/22

PER-TEST RATINGS:
| test_name | rating | issue | fix |
|-----------|--------|-------|-----|
| ...       | SOLID  | —     | —   |
| ...       | WEAK   | ...   | ... |
| ...       | WRONG  | ...   | ... |

DEEP GAP ANALYSIS (test-master):
- GAP-1: [HIGH/MED/LOW] [description]
- GAP-2: ...
(or "none")

COVERAGE GAPS: [list or "none"]
MISSING ARTIFACTS: [list or "none"]
VERDICT: READY TO COMMIT ([N]/22) / NEEDS FIXES ([N]/22)
```
