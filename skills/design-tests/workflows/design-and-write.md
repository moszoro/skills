<required_reading>
- references/design-checklist.md
- references/agent-prompts.md
</required_reading>

<process>

<step name="1-load-skills" goal="Load domain expertise before any work">
Load all 3 skills FIRST — before reading files or writing code:

1. Detect language from project files and load matching skill:
   .py → Skill(skill: "fullstack-dev-skills:python-pro") or fastapi-expert if FastAPI
   .ts/.tsx → Skill(skill: "fullstack-dev-skills:typescript-pro")
   .go → Skill(skill: "fullstack-dev-skills:golang-pro")
2. Skill(skill: "fullstack-dev-skills:test-master")
3. Skill(skill: "fullstack-dev-skills:security-reviewer")

Do NOT read files or write code until all 3 are loaded.
</step>

<step name="2-gather-acs" goal="Ensure ACs exist before writing tests">
If user provided ACs → confirm they're behavioral (Given/When/Then, user-observable).
If user provided area/concern → derive ACs from reading the source code, then confirm with user.
Also surface the **domain invariants** the code must uphold (single-writer, No-Orphan, idempotency, authz boundary, a concurrency/CAS property) even if the user didn't list them — these become T2 tests.

Tier every test with its SOURCE (no untagged tests):
- **T1 `# AC-N`** — behavioral ACs the user would notice if broken (Given/When/Then)
- **T2 `# INV-XX` / `# NFR-XX`** — domain invariants / non-functional constraints (safety/compliance, concurrency, latency)
- **T3 `# QUALITY`** — edge/adversarial/robustness (still TAGGED, just not an AC)

Also identify the **public interface (seam)** each test will call — the repository/service/verb/port, NOT raw ORM or internals.

Do NOT proceed until ACs + invariants + the interface are confirmed.
</step>

<step name="3-read-context" goal="Understand codebase before designing tests">
Read:
- Source files to test (from user input or grep)
- Existing test files (check for redundancy, match patterns)
- Project config (pyproject.toml, package.json, go.mod)
- references/agent-prompts.md for quality rules
</step>

<step name="4-design-tests" goal="Design each test with hand-computed values before writing">
For EACH AC (T1) and each invariant (T2), design a test (do NOT write code yet):

1. **Inputs** — exact objects/data you'll create (real FK ids via the public/admin API, never fabricated ids)
2. **Interface + call** — which PUBLIC verb/repository/port (the seam), REAL (no mocks on the function under test; no raw ORM / private internals to assert)
3. **Tier + tag** — T1 `# AC-N` / T2 `# INV-XX`·`# NFR-XX` / T3 `# QUALITY`
4. **Hand-computed expected value** — show the math in a comment explaining WHY
5. **Assertions** — exact assert statements with computed values (re-read through the interface for state changes)
6. **Rating** — apply references/design-checklist.md:
   - SOLID: calls real function, hand-computed values correct, not redundant, behavioral
   - TAUTOLOGICAL: tests mock returns what you set, not real behavior. REJECT.
   - REDUNDANT: already covered by existing test. SKIP.

Only SOLID designs proceed to implementation.
</step>

<step name="5-implement-tests" goal="Write failing tests + stubs from SOLID designs">
For each SOLID design, write the test following references/agent-prompts.md rules:

- Tier-tag every test: T1 `# AC-N` / T2 `# INV-XX`·`# NFR-XX` / T3 `# QUALITY` — NONE untagged
- Call the PUBLIC interface (repository/service/verb/port), not raw ORM or private internals; name it in the domain's ubiquitous language
- Use Given/When/Then in docstrings (T1)
- Use three-part proof: precondition (+ BEFORE capture) → action → assertion (re-read state through the interface)
- No banned assertion patterns
- Create stub files with WRONG return values (never raise NotImplementedError); match the framework API (async FastAPI, Go gRPC receivers); a new native-enum value needs its ALTER TYPE migration in RED
- **Seam conformance:** if a port has a fake + a real adapter, add a test running BOTH through the same scenario asserting the same outcome
- **Real-infra truth:** prove DB/infra-guaranteed behavior (idempotency index, CAS lost-update, FK reject, FOR-UPDATE interleave) on the REAL per-worker DB — a 2-connection barrier harness for races (never `asyncio.gather` on one session)

Then write adversarial/quality tests (T3):
- At least 3 covering 2+ categories, **tagged `# QUALITY`** (or `# INV-XX` if they pin an invariant) — NOT `# AC-N`, but NOT untagged either
- Categories: invalid input, duplicate requests, timeout/failure, concurrent access, boundary values
- Prefer a **property-based** test (Hypothesis/fast-check) for the trickiest invariant instead of a few hand-picked cases

Then write fixture-based test:
- Create fixtures/ directory with golden reference data
- At least 1 test loads fixture and compares output
</step>

<step name="6-run-and-verify" goal="Verify all tests fail correctly">
1. Run tests using project's test runner (auto-detect: pytest, vitest, go test)
2. Verify EVERY test fails on AssertionError (not ImportError/TypeError)
3. Run existing tests to verify no regressions
4. Review against quality checklist:
   - Every AC (T1) + every invariant (T2) covered?
   - Every test tier-tagged (T1/T2/T3), NONE untagged?
   - Tests call the public interface (no raw ORM / private internals)?
   - Zero banned patterns?
   - Hand-computed math comments present?
   - Stubs use wrong values?
   - Port conformance + real-infra race proven where applicable?
5. If issues found → fix inline, re-run
6. (If tooling) run mutation testing on the changed module — a surviving mutant on a changed line = a real gap; strengthen the test
</step>

</process>

<success_criteria>
- All 3 skills loaded before any file reads
- ACs + invariants + the public interface confirmed with user before writing tests
- Every test designed with hand-computed math before implementation
- All TAUTOLOGICAL/REDUNDANT designs rejected
- Tests call the public interface (repository/service/verb/port), not raw ORM or internals; named in ubiquitous language
- T1 tests behavioral + Given/When/Then; every invariant has a T2 test
- Every test tier-tagged (T1/T2/T3) — NONE untagged; adversarial/quality tagged `# QUALITY`
- Port/adapter conformance test where applicable; DB/infra-guaranteed behavior proven on the real infra (2-connection harness for races)
- All tests fail on AssertionError
- Zero banned patterns
- At least 1 fixture-based golden test; property-based test for the trickiest invariant where tooling exists
- No time-rotting date literals
- No regressions in existing suite; (if tooling) mutation survivors on changed lines triaged
</success_criteria>
