<design_checklist>

<check name="calls-real-function">
**Does the test call the REAL function under test?**

PASS: `report = score_extraction(extracted, ground_truth)` — real function, real inputs
FAIL: `mock_score.return_value = report; run_benchmark(...)` — tests the mock, not score_extraction

If the function under test is mocked, the test is tautological. You're verifying your own mock setup.

Exception: mocking DEPENDENCIES is fine (e.g., mock the VLM HTTP call, test the pipeline logic). But never mock the function you're actually trying to test.
</check>

<check name="hand-computed-values">
**Are expected values computed by hand with shown math?**

PASS:
```
# 3 results, 1 wrong value: name_correct=3, value_correct=2, unit_correct=3
# total_for_accuracy = matched(3) + extras(0) = 3
# value_acc = 2/3 ≈ 0.6667
assert acc["value"] == pytest.approx(2/3)
```

FAIL:
```
assert acc["value"] > 0  # what should it actually be?
assert acc["value"] < 1  # anything between 0 and 1 passes
```

The comment WITH the math is part of the design. If the math is wrong, the test is wrong.
</check>

<check name="not-redundant">
**Does an existing test already cover this exact scenario?**

Before designing a test, grep existing tests for:
- Same function being called
- Same input pattern (N extracted vs M ground truth)
- Same assertion values

If found: mark REDUNDANT, document which existing test covers it, skip.

Similar is OK. Exact duplicate is not:
- SIMILAR: existing tests 0.8 accuracy, new tests 2/3 accuracy — different ratio, different input → OK
- DUPLICATE: existing and new both test 3 correct / 0 wrong → REDUNDANT
</check>

<check name="tests-behavior">
**Does the assertion check OUTPUT behavior, not internal state?**

PASS: `assert report.total_matched == 0` — observable output
PASS: `assert acc["name"] == 0.0` — computed accuracy value
FAIL: `assert len(alignment._used_indices) == 2` — internal implementation detail
FAIL: `assert hasattr(report, 'per_field')` — structure, always true for Pydantic
</check>

<check name="edge-case-value">
**Does the test hit a meaningful edge or boundary?**

Good edge cases:
- 0 matched (no alignment at all)
- All wrong (wrong names, wrong values, wrong units)
- Comma vs dot decimal (normalization boundary)
- Values swapped between rows (alignment correctness)
- 1 result only (minimum meaningful input)
- Exact threshold boundary (90.0 fuzzy match)

Bad "edge cases" (not actually edges):
- 1000 results (just slow, not different logic)
- Unicode emoji in test name (never happens in medical data)
- Negative numbers (not possible for lab values)
</check>

<check name="tests-through-the-interface">
**Does the test call the PUBLIC interface (the seam), not internals or raw persistence? (DDD)**

PASS: `svc.decide(...)` / `(await repo.get(id)).state` — through the public verb / repository
FAIL: `obj._used_indices` / `db.execute(select(RawRow)...)` to assert domain behavior — reaches past the seam

A test that asserts private state or raw ORM breaks when the *implementation* changes, not the *behavior*. If the only way to prove something is via a private method, the module may have the wrong shape (or it's a legitimate internal seam — prefer the public verb where the behavior is reachable). Bonus: is the test NAMED in the domain's ubiquitous language?
</check>

<check name="tier-tagged">
**Is the test tagged with its source tier — and is it the RIGHT tier?**

Every test carries exactly one: T1 `# AC-N` (behavioral AC) · T2 `# INV-XX`/`# NFR-XX` (invariant/NFR) · T3 `# QUALITY` (edge/adversarial). NONE untagged.
FAIL: an untagged adversarial test · a structural/infra test wearing an `# AC-N` tag (it's T2/T3) · an invariant with no T2 test.
</check>

<check name="seam-and-real-infra">
**For a port: do the fake AND real adapter share one conformance test? For DB/infra-guaranteed behavior: is it proven on the REAL infra?**

PASS: a conformance test runs `FakeGateway` and the real adapter through the same scenario, asserting the same outcome.
PASS: idempotency (partial-unique index), a CAS lost-update, a FK reject, or a `FOR UPDATE` interleave is proven on the real per-worker DB via a 2-connection barrier harness.
FAIL: a DB-constraint/concurrency claim "proven" against an in-memory fake · `asyncio.gather` on ONE session pretending to be a race (one connection can't race itself → tautological green).
</check>

</design_checklist>
