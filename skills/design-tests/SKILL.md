---
name: design-tests
description: Design and write failing tests (TDD/BDD/DDD) with hand-computed expected values, behavioral Given/When/Then format, domain-boundary/interface discipline, 3-tier source tagging (T1 AC / T2 INV·NFR / T3 QUALITY), and feasibility rating (SOLID/TAUTOLOGICAL/REDUNDANT). Executes directly — no agent spawning. Use when you need well-designed tests for any feature, bugfix, invariant, or refactor where correctness matters. Triggers on "design tests", "write tests first", "TDD", "BDD", "red phase", "failing tests", "test this".
---

<objective>
Design and write failing tests directly. Read source code, design each test with hand-computed expected values, rate feasibility (SOLID/TAUTOLOGICAL/REDUNDANT), then implement only SOLID designs as failing RED tests with stubs. Test through the module's PUBLIC INTERFACE (the seam), assert exact values, tag every test with its tier.

Direct execution — no agent spawning. You ARE the test designer and writer. Do NOT spawn Agent() or use subagent_type. Follow the workflow steps yourself.
</objective>

<essential_principles>

<principle name="ac-and-invariant-driven" priority="CRITICAL">
Acceptance Criteria AND domain invariants drive everything. **Every test is source-tagged with its tier — there are NO untagged tests:**

- **T1 `# AC-N` / `<!-- AC-N -->`** — Acceptance-criteria tests. BEHAVIORAL (Given/When/Then), test what the user SEES. On failure: the AC is not met.
- **T2 `# INV-XX` / `# NFR-XX`** — Domain-invariant / non-functional tests (a rule that must always hold — a single-writer seam, a No-Orphan guarantee, a concurrency/CAS property, an authz boundary, a latency budget). On failure: a safety/compliance violation, not just an AC miss.
- **T3 `# QUALITY-<slug>`** — Edge cases, adversarial/chaos, robustness, perf baselines. NOT an AC — but STILL TAGGED, **and with its own identifier**, e.g. `# QUALITY-withdraw-ownership`. On failure: a review finding, not an AC miss.

The older "adversarial tests are left untagged" rule is REJECTED — untagged tests read as "someone forgot," and a reviewer can't tell a deliberate edge case from an orphan. Tag it `# QUALITY-<slug>` (or `# INV-XX` if it pins an invariant).

**A tier does NOT decide whether a failing test blocks — every failing test blocks, T3 included. The tier decides whether anyone is obliged to notice the test's ABSENCE.** A planned-but-unwritten T1 is caught ("every AC has ≥1 T1 test") and a planned-but-unwritten T2 is caught ("every invariant has ≥1 T2 test") — so a planned T3 needs an identifier of its own, or its absence is checkable by nothing and a test that was named, described and justified can simply never get written. Key on the identifier, never on the test NAME: renaming a test while implementing it is normal and the shipped name is usually better.

**Never put an access-control, ownership, data-destruction, or PHI-handling test in T3.** Those are T2 invariants even when nobody remembered to list them among the invariants — "everything left over is T3" is the default that buries them. If a test genuinely enforces no rule (a positive-control baseline such as "a valid reason is accepted"), T3 is right: say so in the tag rather than deleting the security wording from the description. Source incident: 2026-08-05, Aura #773 — an ownership check on a PHI-destroying path shipped as `<!-- QUALITY / bezpieczeństwo -->`; the tag named the risk out loud, no gate looked, and the test was never written.

GOOD T1 (behavioral — user would notice):
  "Given a customer with items in cart, when they apply coupon SAVE20, then total decreases by 20%"
GOOD T2 (invariant — safety):
  "# INV-single-writer: after any decide(), exactly ONE state-transition audit row exists"
BAD T1 (structural — user wouldn't notice → make it T2/T3 or drop):
  "Given config files removed from disk, when prices calculated, then values from DB cache"
</principle>

<principle name="ddd-test-through-the-interface" priority="CRITICAL">
Test through the module's PUBLIC INTERFACE (the seam), NOT its internals. "The interface is the test surface" — a test that reaches past the public surface into private state or the raw persistence layer breaks when the *implementation* changes, not when the *behavior* does.

- Call the **repository / service / domain verb / port** — NOT raw ORM (`db.query(...)`), NOT private methods/attributes (`svc._internal`, `obj._used_indices`), NOT the DB directly to assert.
- Name tests in the **ubiquitous language** of the domain (`test_reject_respawns_get_results`, not `test_update_row_2`). The test name is living documentation of a domain rule.
- Test **at the aggregate/consistency boundary**: assert the invariant the aggregate owns (e.g. "an obligation always has accepted evidence OR an open acquire task"), not incidental field mechanics.
- **Internal seams are allowed** for genuinely finicky machinery (a CAS 0-row disambiguation) — but prefer the public verb wherever the behavior is reachable there. If you can only prove something by testing a private method, ask whether the module has the wrong shape.

PASS: `report = svc.score_extraction(extracted, truth)` — real public function
PASS: `assert (await repo.get(id)).state == State.COMPLETED` — through the repository
FAIL: `assert alignment._used_indices == [0, 2]` — private internal
FAIL: `rows = (await db.execute(select(Raw)...)).all()` used to assert domain behavior — reaches past the seam
</principle>

<principle name="design-before-code" priority="CRITICAL">
Never write a test without designing it first. For each test:
1. What inputs will you create? (real FK ids via the public/admin API — never fabricated ids that a constraint would reject)
2. What PUBLIC function/verb will you call? (real function, not a mock; the seam, not internals)
3. What is the EXACT expected output? (hand-compute it, show the math)
4. Which tier is it — T1 / T2 / T3 — and what tag?
5. Is it already covered by existing tests?
6. Rate: SOLID / TAUTOLOGICAL / REDUNDANT

A test without a design is a guess. A design with wrong math is worse than no test.
</principle>

<principle name="hand-compute-expected-values" priority="CRITICAL">
Every assertion must have a hand-computed justification shown in a comment.

BAD: `assert acc > 0` — what should it actually be?
BAD: `assert len(results) >= 1` — how many exactly?

GOOD:
```python
# 3 results, 1 wrong value: value_correct=2/3
assert acc["value"] == pytest.approx(2/3)  # AC-3
```
</principle>

<principle name="three-part-proof" priority="HIGH">
Every test proves a specific claim with evidence:
1. **Precondition** — verify setup is what you think (and, for state-change tests, capture the BEFORE)
2. **Action** — exercise behavior through the public interface
3. **Assertion** — exact values (not ranges, not absence, not truthiness), AND for mutations re-read the state through the interface to prove it changed (or, on the reject arm, did NOT change)
</principle>

<principle name="banned-assertions" priority="HIGH">
NEVER use these — they let wrong implementations pass:
- `is not None` / `toBeDefined()` — almost anything passes
- `assert result` (bare truthy) / `toBeTruthy()`
- `len() > 0` — any non-empty result passes
- `!= old_value` — anything different passes
- `isinstance()` / `hasattr()` alone — always passes on Pydantic/dataclass
- `mock_fn.called` — tests wiring not output
- `assertTrue(result)` — any truthy value passes
- Broad numeric ranges (`0 < x < 1000`)

INSTEAD: exact values — `== expected`, `.field == "specific"`, `== pytest.approx(2/3)`
</principle>

<principle name="no-tautological-tests" priority="HIGH">
A tautological test proves nothing (asserting what the mock/stub was set to return). Test the REAL function; mock only DEPENDENCIES, never the function under test.

BAD — tests mock returns what you set:
```python
mock_score.return_value = ScoreReport(value_acc=0.85)
assert run_benchmark(...).value_acc == 0.85  # proves the mock works, not the code
```
GOOD — tests real function:
```python
assert score_extraction(extracted, truth)["value"] == pytest.approx(2/3)  # proves the math
```
</principle>

<principle name="seam-and-adapter-conformance" priority="HIGH">
When a module has a PORT (an injected interface with a real adapter + a fake — e.g. a gateway, a blob store, a clock), the fake and the real adapter MUST both satisfy the SAME contract. Write a conformance test that runs both through the identical scenario and asserts the same observable outcome. A fake that silently diverges from the real adapter is a false-green generator.

Corollary — **prove DB/infra-guaranteed behavior on the REAL infra, never a fake:** idempotency backed by a partial-unique index, a CAS lost-update, a FK/constraint rejection, a `FOR UPDATE` interleave — a fake can't prove these; they need the real per-worker DB. For a genuine two-writer race use a **2-connection barrier harness** (open a second session/connection, commit an out-of-band change, then assert the primary flow raises the stale/conflict error). `asyncio.gather` on one session is tautological (one connection can't race itself).
</principle>

<principle name="assertion-not-implementation" priority="HIGH">
RED tests MUST fail on AssertionError, NOT ImportError/TypeError/AttributeError.

For NEW modules: create STUB files with WRONG return values (False, -1, None, []) so tests fail on AssertionError (wrong value), never ImportError. NEVER `raise NotImplementedError`. Stub signatures must match the framework API (async for FastAPI, receiver methods for Go gRPC). Framework gotchas: a new native-enum value needs its `ALTER TYPE` migration written in the RED phase (else `DataError`, not `AssertionError`); a crashing/missing endpoint needs a lenient client (`ASGITransport(..., raise_app_exceptions=False)`) so the failure is an `AssertionError`, not an unhandled 500.
</principle>

<principle name="objective-strength-mutation-and-property" priority="MEDIUM">
SOLID/TAUTOLOGICAL is a SUBJECTIVE rating. Where tooling exists, GROUND test strength objectively:
- **Mutation testing** (`mutmut` 3.x / Stryker / gremlins) is the ground truth for "would a wrong impl pass?" — a surviving mutant on changed lines = a real gap. Coverage is NOT evidence (100% line coverage can sit at ~4% mutation score). This is the same signal `evals:eval-tests` C5/C17 use — design toward killing mutants.
- **Property-based testing** (Hypothesis / fast-check) for invariants and normalization boundaries — instead of (or alongside) a few hand-picked cases, state the property ("for any two rows, alignment is order-independent") and let the engine hunt counter-examples. Especially strong for T2 invariant tests.
</principle>

<principle name="route-tests-behavioral" priority="MEDIUM">
Route tests that ONLY check HTTP status + response text are structural.

BAD: `assert resp.status_code == 303` + `assert "Select" in resp.text`
GOOD: `assert resp.status_code == 200` + re-read through the interface: `assert (await repo.get(id)).status == "paid"`

Route tests MUST verify server state changed (DB via the repository, session, side effect, computed value) — and on an error arm (422/409), assert the state did NOT change (`pre == post`).
</principle>

<principle name="no-time-rot" priority="MEDIUM">
Never hardcode a future date literal that silently rots (a test that starts failing when the year passes). Use `date.today() + timedelta(...)` for "future", and `freezegun`/a frozen clock when an assertion needs an exact instant. Inject the clock; don't read wall-time inside the function under test.
</principle>

</essential_principles>

<quick_start>
Pipeline: describe feature/area → read code + design tests with math, tier, and the public seam to call → rate feasibility → implement SOLID designs as failing RED tests with stubs → run and verify all fail on AssertionError → (if tooling) sanity-check strength with mutation/property-based.

Provide: feature description with ACs (and any INV/NFR the work must uphold), or an area to test with specific concerns.
</quick_start>

<intake>
Provide one of:

**Option A — Feature with ACs + invariants (preferred):**
```
Feature: payment webhook handler
ACs (T1):   AC-1 Given valid signature, when handler receives event, then payload is parsed
            AC-2 Given charge.succeeded, when processed, then order status → 'paid'
Invariants (T2): INV-idempotent — a duplicate event_id processes exactly once
Files: src/webhook/handler.py   Interface: WebhookService.process(event)
```

**Option B — Area to test:**
```
Area: scoring engine (score_extraction)   Interface: score_extraction(extracted, truth)
Concern: wrong values → partial accuracy, not 0% or 100%
Existing: tests/test_engine.py
```

If ACs are missing, I'll derive them from the code and confirm with you. I'll also surface the invariants the code must uphold (T2) even if you didn't list them.
</intake>

<reference_guides>
- references/design-checklist.md — feasibility + DDD/seam/real-DB checks for SOLID/TAUTOLOGICAL/REDUNDANT rating
- references/agent-prompts.md — tdd-red prompt template (replace {placeholders})
- Companion gate: `evals:eval-tests` scores the produced tests against C1–C22 (mutation-grounded). Design toward passing it.
</reference_guides>

<routing>
After receiving input, follow workflows/design-and-write.md
</routing>

<success_criteria>
- Every AC has ≥1 T1 test; every stated/discovered invariant has ≥1 T2 test; **every test is tier-tagged (T1/T2/T3) — none untagged**
- **Every planned test carries a unique identifier at its own tier — `AC-N <qualifier>`, `INV-<slug>`, `QUALITY-<slug>` — so "planned but never written" is detectable at all three tiers, not just the first two**
- **No access-control / ownership / data-destruction / PHI test sits in T3**
- Tests call the PUBLIC interface (repository/service/verb/port), not raw ORM or private internals
- Every test design has hand-computed expected values with math shown
- All designs rated SOLID/TAUTOLOGICAL/REDUNDANT — only SOLID implemented
- BDD: T1 tests are behavioral (user-observable), Given/When/Then; named in ubiquitous language
- Adversarial/quality tests present (3+, 2+ categories), tagged `# QUALITY` (or `# INV-XX`)
- Port/adapter conformance test where a fake+real adapter exist; DB/infra-guaranteed behavior proven on the REAL infra (2-connection harness for races)
- Stubs return wrong values (never `NotImplementedError`); all tests fail on AssertionError (not ImportError/TypeError)
- Zero banned assertion patterns; ≥1 fixture/golden test; no mocks on the function under test; no redundancy with the existing suite
- No time-rotting date literals; clock injected where timing matters
- (If tooling) mutation survivors on changed lines triaged; property-based test used for at least the trickiest invariant
</success_criteria>
