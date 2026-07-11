---
name: qa-phase
description: Autonomous acceptance-and-ship QA gauntlet. Use when the user says "run QAPhase", "qa this feature/story/branch", or wants a hands-off run that proves a finished story end-to-end — spec-gap analysis, an API+UI+E2E QA session, chaos/adversarial probing, a design-first auto-fix loop, a fast verification pass, live preview AC tests — then STOPS at a single ship gate. Complements verification-phase (static review); this is dynamic proof. Fans out as a multi-agent Workflow when orchestration is available.
---

# QAPhase

## Overview

**What:** Proves a *finished story* works end-to-end and then ships it — fully autonomously up
to a single decision. It runs three proof lenses (spec-gap, an API+UI+E2E QA session, chaos),
auto-fixes what they find through a **design-first micro-cycle** (design the fix → write a failing
regression test → implement via the right domain expert → verify), re-checks the result with
`verification-phase --fast`, gathers fresh evidence, opens a **draft PR**, and runs the story's
acceptance criteria against the **live preview**. Only then does it STOP — one gate — to decide
whether to ship. Everything up to that gate is hands-off.

**How:** Preflight (deps + project skill-config, fail-loud) → **Phase A** (spec-gap/grill ·
API+UI+E2E QA-session · chaos · prove-beyond-tests eli5 live scenarios, each karpathy-filtered +
cove-gated on critical surfaces) → **Fix loop** (≤2 rounds, bugfix-TDD, expert-dispatched) →
**fast-verify** (`verification-phase --fast`) → **evidence** gate → **Phase B** (draft PR +
preview AC) → **⏸ single gate** (Ship / Hold / Fix-more) → **Phase C** (sprint/story/deferral sync
+ finish branch), post-approval only.

**Why:** Today this is 11 manual commands, several of them interactive. Chaining them naively
either stops for input a dozen times or ships plausible-but-unproven work. QAPhase collapses every
human decision to ONE gate while *raising* rigor: distinct lenses catch more, karpathy cuts noise,
cove guards critical surfaces, and no fix lands as a hack — each is designed at a clean seam and
backed by a failing-then-passing test. The only irreversible acts (merge, GitHub tracking writes)
wait behind the gate; the reversible evidence-gathering (draft PR, live preview AC) runs first, so
you decide with maximum evidence in hand.

## Role

Act as a staff-level QA + release engineer running an autonomous acceptance gauntlet. You are
skeptical of your own green: a lens finding earns a fix only after karpathy (and cove on critical
surfaces); a fix earns "done" only after a regression test goes red→green; the story earns "ship"
only after its ACs pass against the live preview. You never claim a result you have not just run.

## Execution contract

This skill orchestrates other skills and (when available) runs as a multi-agent Workflow.
Completeness and the single-stop discipline are on you:

- **First action:** create a TodoWrite with one item per gate/phase below, in order:
  Preflight · A1 spec-gap · A2 QA-session · A3 chaos · A4 prove-beyond-tests · Fix-loop ·
  fast-verify · evidence ·
  B draft-PR · B preview-AC · **GATE** · C sprint-sync · C ship. Mark each in-progress → complete.
- **One stop only.** Nothing before the GATE may ask the user a question. If a lens is genuinely
  blocked (missing config, no preview mechanism, un-resolvable AC), record it and carry it *to the
  gate* — do not interrupt mid-run. The only exception is a Preflight halt (below).
- **Fail loud, never silently degrade.** A missing required dependency, a config that names a
  skill that isn't installed, or a gate that cannot run → STOP and report. Do not "work around."
- **Fresh invocation is mandatory.** Every resolved skill — each lens's reviewer, karpathy, cove,
  the fix-cycle skills, `verification-phase --fast`, `verification-before-completion` — is invoked
  via the `Skill` tool *within this run*. A pre-loaded copy does not count.
- **Autonomous ≠ reckless.** The auto-fix loop is bounded (≤2 rounds); fixes that need product
  judgment are reported at the gate, not applied. Merge and any GitHub write happen ONLY after the
  gate returns "Ship."
- **Do not declare QAPhase complete** until every Todo is done and the report is written. If the
  gate returned "Hold," the run is complete with the PR left as a draft — that is a valid terminal
  state, not a failure.

## Activation

1. **Resolve scope.** `$ARGUMENTS` names the story/feature/branch. **Default: the current feature
   branch vs its PARENT base branch** — config `base_branch`, else the branch it forked from, else
   the merge-base with the default branch. **For a stacked branch this matters:** diffing vs
   merge-base-with-`main` drags in every ancestor phase (e.g. `phase6-2-1-impl` vs `main` = ~38k
   lines of unrelated 6-2-2/6-3 work; vs its real parent `phase6-2-backend-base` = a clean ~3.4k
   slice). Add **plus the story doc it implements**. Read the real diff and the real story; never
   review from memory.
   Locate the story via project convention (config `story_glob`, or a `docs/stories/`-style path,
   or the PR's linked issue). If no story/spec can be found, that is itself the first gap — record
   it, do not fabricate ACs.

2. **Detect the critical surface (gates cove).** Mark the change critical if it touches auth /
   session / tokens / permissions, user PII / health data, payments / money, or high-blast-radius
   state (migrations, audit trails, core domain logic). Use the repo's own conventions. Record it.

3. **Resolve the skill kit** (`## Skill-kit resolution`). Per phase: project config → auto-detected
   native skill → generic fallback. Halt if config names a missing skill.

4. **Bind the report path.** `docs/qa-phase/{YYYY-MM-DD}-{branch-slug}-qa.md` unless the user gave
   one. Create the dir. Start from `## Report`.

5. Run, in order: **Preflight → Phase A (A1·A2·A3·A4) → Fix loop → fast-verify → evidence →
   Phase B → GATE → Phase C**. Phase A lenses may run concurrently (they are independent read-only
   proofs); the Fix loop, fast-verify, evidence, Phase B, and Phase C are sequential — each reads
   the prior's applied state.

## Preflight — required deps & config

Confirm every dependency is available **this session**; STOP with a clear list if any is missing.

**Generic fallbacks (always required — the floor):**
`andrej-karpathy-skills:karpathy-guidelines`, `cove`, `codebase-design`, `design-tests`,
`grilling` + `domain-modeling` (A1 grill mechanism), `verification-phase` (for `--fast`),
`superpowers:verification-before-completion`, `superpowers:finishing-a-development-branch`, `eli5`;
the `gh` CLI; a Playwright runner.
Generic lens fallbacks: `fullstack-dev-skills:code-reviewer`, `fullstack-dev-skills:test-master`,
`fullstack-dev-skills:playwright-expert`, `fullstack-dev-skills:chaos-engineer`, and the **entire
`fullstack-dev-skills:*` implementer set (all 66 — any pickable by capability) for GREEN**. Preflight
records which experts are present; that verified set IS the GREEN allowlist. Tools: context7 MCP
(via `verification-phase --fast`).

**Configured native skills (if any):** every skill named in the project `qa-phase.config` MUST
resolve in this session's skill list — a configured-but-missing skill is a HALT, never a silent
fallback (the config is an explicit choice; honor it or stop).

Record a Preflight line per dependency `available` / `MISSING`, and the **resolved kit** (which
skill each phase will actually use). Availability ≠ invocation — each phase still invokes its skill
fresh.

## Skill-kit resolution (config-driven, native-preferred)

Generic skills ship as baked-in defaults. A project declares native skills in
`{project}/.claude/qa-phase.config.toml`; the skill reads it at Preflight.

```toml
[skills]
spec_gap        = "bmad-code-review"                     # AUTO-mode gap reviewer; else fullstack-dev-skills:code-reviewer + Explore
spec_gap_mode   = "auto"                                 # "auto" = non-interactive gap analysis (keeps ONE stop). "grill" = run grill-with-docs LIVE at A1 (grilling + domain-modeling), interactive, adds one early stop
qa_session      = "bmad-qa-generate-e2e-tests"           # designs API + E2E — absorbs the standalone Playwright step
chaos           = "fullstack-dev-skills:chaos-engineer"  # DYNAMIC breaking has no bmad equivalent — do NOT swap for a review skill
static_boosters = ["bmad-review-adversarial-general", "bmad-review-edge-case-hunter"]  # STATIC review adds, folded into A1/A2 (not chaos)
green           = "bmad-quick-dev"                       # project-aware targeted implementer; else UNIVERSAL capability-match across the full fullstack-dev-skills:* set (66 experts). NOT bmad-dev-story — that implements a WHOLE story from a spec file, wrong shape for one fix
sprint_sync     = "bmad-sprint-status"                   # READ/verify ONLY — it summarizes, it does not WRITE; the status/deferral writes + GitHub mirroring are a generic edit+gh step (see Phase C)
[project]
base_branch = "phase6-2-backend-base"   # SCOPE = diff vs THIS parent (stacked branch), NOT merge-base with main
story_glob  = "_bmad-output/**/phase*-*.md"
preview     = "local"                   # backend story → ACs run against a local API + per-worker test DB
```

**Resolution per phase:** ① config value (halt if it names a missing skill) → ② auto-detect a
native skill (scan the session skill list for `bmad-*`/project-prefixed matches) → ③ generic
fallback. Log the resolved choice for each phase in the report.

**Map by capability, not name.** Before treating a native skill as a phase's reviewer, confirm it
actually does that phase's *job* — a `*-review-*` skill that only reads a diff cannot stand in for a
**dynamic** lens that must run the system (the chaos lens is the canonical trap: static adversarial/
edge-case review is a booster, not a chaos substitute). Auto-detect (②) only proposes a native skill
whose capability matches the phase; when unsure, keep the generic fallback and record why.

## Phase A — prove & harden (autonomous)

Each of the **four lenses (A1 spec-gap · A2 QA-session · A3 chaos · A4 prove-beyond-tests)** runs
`review → karpathy filter → cove (critical only) → collect KEPT findings`, exactly as
verification-phase's per-step pipeline, except findings are *collected*, not applied here. The
**Fix loop runs once, over the POOLED KEPT findings from all four lenses** — so a single designed
fix can resolve findings that several lenses surfaced at the same seam (e.g. a spec-gap in A1 that
is also the edge case A4's scenario broke), instead of fixing per-lens and re-thrashing.

### A1 — Spec-gap & grill lens *(your `/grill-with-docs`, made runnable)*
`grill-with-docs` is `disable-model-invocation: true`, so the Skill tool can't call the wrapper — but
its whole body is *"Run a `/grilling` session, using `/domain-modeling`,"* and **both `grilling` and
`domain-modeling` ARE invocable**. So A1 runs grill-with-docs by invoking its two parts.

- **`spec_gap_mode = auto`** (default — keeps the single stop): non-interactive gap analysis via the
  `spec_gap` reviewer (`bmad-code-review`'s Acceptance-Auditor / `code-reviewer` + `Explore`), with
  `domain-modeling` recording any ADRs/glossary the gaps imply. Apply `grilling`'s own rule — *a fact
  you can find in the code, look up; don't ask* — and since the code already exists, almost every
  gap-question is a verifiable fact. Residual **decision** gaps are carried to the final gate, not
  asked live.
- **`spec_gap_mode = grill`** (opt-in — adds one early interactive stop): invoke **`grilling`** (the
  relentless one-question-at-a-time interview) **+ `domain-modeling`** (writes ADRs/glossary as gaps
  crystallise) LIVE — the genuine grill-with-docs experience, pointed at story/plan/spec vs the
  implemented code. qa-phase pauses here, you answer the decision questions, then it resumes.
- **Goal (either mode):** every story requirement / AC ↔ implemented code → an **AC coverage matrix**
  + a **gap list** (story/plan/spec items with no code; code with no story backing; silently-dropped
  requirements), each grounded in the story; plus any ADRs/glossary from `domain-modeling`.
- You can also just type `/grill-with-docs` yourself before running qa-phase; its ADR/glossary output
  becomes A1's input.

### A2 — QA-session lens: API + UI + E2E *(replaces the interactive `/qa` and the standalone Playwright step)*
- **Skill:** `qa_session` kit skill (`bmad-qa-generate-e2e-tests` / `test-master` +
  `playwright-expert`).
- **Goal:** design and **run** real-world scenarios that prove the feature beyond unit tests —
  **backend** (API/curl scenarios with real assertions on server state, not just status codes),
  **frontend** (Playwright for any UI), and **E2E** (cross-cutting user journeys). Capture actual
  pass/fail evidence. Surface edge cases and gaps the ACs missed. These same UI/E2E scenarios are
  re-run against the live preview in Phase B — no separate Playwright phase.

### A3 — Chaos lens *(dynamic — keep `fullstack-dev-skills:chaos-engineer`; it has no native equivalent)*
- **Skill:** `chaos` kit skill — default `fullstack-dev-skills:chaos-engineer`. This is a
  **dynamic** lens: design + **run** experiments that actually break the running system — auth/authz
  bypass, injection, broken invariants, concurrency races, connection-pool exhaustion, perf cliffs,
  migration replay. Where the project documents its real failure modes (e.g. Aura's `CLAUDE.md`
  "Real-World Scenario Tests (beyond pytest)"), use that as the experiment set.
- **Do NOT substitute static review for chaos.** `bmad-review-adversarial-general` (cynical static
  review) and `bmad-review-edge-case-hunter` (static path tracer) **execute nothing** — they are
  `static_boosters` folded into A1/A2, never the chaos skill. Kit skills are mapped by **capability,
  not name**.
- Because chaos is inherently security-relevant, **treat any surviving finding as critical** for the
  cove gate even if Activation step 2 was borderline. (This is why fast-mode verification later can
  safely skip the dedicated security lens — chaos already covered it.)

### A4 — Prove-beyond-tests: live scenarios + plain-language proof *(your `/eli5` step — runs BEFORE fixes)*
- **Skill:** `eli5` + real-world scenario execution (the project's manual-scenario practice, e.g.
  Aura's `CLAUDE.md` "Real-World Scenario Tests (beyond pytest)").
- **Goal:** prove the feature works **besides the automated tests** — write and *run* real-world/live
  scenarios (cross-process races, real Postgres index plans, real serialization round-trips, failure
  resilience — what the unit suite can't see) that exercise the story end-to-end, and capture the
  plain-language narrative: **what we delivered, what we proved, why it mattered, how we know beyond
  tests.**
- **Runs before the Fix loop on purpose:** these live scenarios surface gaps/edge cases the tests
  missed → they feed the Fix loop like any other lens finding (karpathy → cove → collect). Running
  eli5 only at the gate would surface those gaps too late to fix in this run.
- The narrative it produces is reused verbatim as the gate dossier's executive summary — eli5 is NOT
  re-run at the gate.

## Fix loop — design-first, bugfix-TDD, expert-dispatched (≤2 rounds)

Operates over the **pooled KEPT findings from all four Phase-A lenses (A1–A4)** — deduped by
file:line/seam so one fix answers overlapping findings. For each KEPT finding (survived karpathy;
cove-confirmed on critical surfaces), run a micro-cycle
so the fix is *designed*, not patched:

1. **Design the fix — `codebase-design`.** Decide the seam/interface: where the fix belongs, what
   stays behind a small interface. Grep the collected findings first so one design answers all
   related findings, not one-off. Kills shallow patches.
2. **RED — `design-tests`.** Write the failing regression test first (hand-computed expected value,
   tagged T1/T2/T3, through the public interface). This IS the mandatory "failing test before fix"
   rule — no fix without proof it was broken.
3. **GREEN — the right expert, chosen universally by capability** (nightshift dispatch *pattern*,
   not the `/nightshift-plan-skills` command). Reason from what the code actually is → the matching
   implementer, picked from **every expert available this session — no hardcoded shortlist**. The
   pool is the *entire* `fullstack-dev-skills:*` implementer set (66 skills spanning every mainstream
   language, framework, data layer, platform and mobile — e.g. `python-pro`, `typescript-pro`,
   `golang-pro`, `rust-engineer`, `swift-expert`, `kotlin-specialist`, `java-architect`,
   `csharp-developer`, `cpp-pro`, `php-pro`, `django-expert`, `rails-expert`, `laravel-specialist`,
   `spring-boot-engineer`, `nestjs-expert`, `fastapi-expert`, `react-expert`, `vue-expert`,
   `angular-architect`, `nextjs-developer`, `flutter-expert`, `react-native-expert`, `game-developer`,
   `embedded-systems`, `postgres-pro`, `sql-pro`, `database-optimizer`, `graphql-architect`,
   `websocket-engineer`, … **and the rest**), **plus** any project-native implementer and the config
   `green` override. A fix can need more than one (e.g. an endpoint + its migration). Implement the
   MINIMUM to pass RED through that expert's lens; record a provenance note (`fix-skills finding=N:
   <skills>`).
   - **Allowlist = the LIVE session, not an image.** nightshift validates the pick against a
     self-contained image registry (`~/Projects/nightshift/skills.tsv`) because it runs in a Docker
     image. qa-phase runs **live**, so the allowlist is simply **whatever Preflight confirmed is
     available this session** — the full `fullstack-dev-skills:*` set + the config `green` + any
     project-native experts — no `skills.tsv`. Match by capability; if the code needs an expert
     Preflight did not confirm, **fail loud** (or fall back to the generic implementer and record
     why) — never silently dispatch an unverified skill.
4. **Verify.** Test goes red→green; re-run the affected lens.

**Guards:** karpathy/cove gate BEFORE the cycle (never spend a design cycle on noise); loop capped
at **2 rounds**; a second round re-touches only reopened lenses; a fix that needs product judgment
is **reported at the gate**, not applied. Commit each finding's fix atomically
(`git commit -am "fix(qa): <lens> — <finding>"`) — durable + resumable.

## Fast static re-check — `verification-phase --fast`

Invoke `verification-phase` with `--fast` over the post-fix state: built-in `code-review` +
context7 best-practices + `evals:eval-tests`, karpathy/cove still gating. Any finding it surfaces
feeds **one** more bounded fix round (same micro-cycle). This is the "did our fixes stay clean and
are the tests still quality" pass — not a fresh full audit.

## Evidence gate — `verification-before-completion`

Invoke `superpowers:verification-before-completion`: run the FULL suite / lint / typecheck fresh,
capture the output, confirm exit codes. No green claim without this evidence. If it fails, that is
a gate finding — fix (one bounded round) or carry to the GATE as a blocker.

## Phase B — live proof (autonomous, reversible)

1. **Draft PR.** Push the branch; `gh pr create --draft` with a body summarizing the story +
   evidence. A draft PR is reversible — it is safe to open before approval; **do not mark ready or
   merge here.**
2. **Preview AC.** Discover the preview URL (config `preview`); re-run A2's UI/E2E scenarios —
   **every story AC** — against the live preview. Record an **AC-on-preview matrix** (AC → pass/
   fail + evidence). If no preview mechanism resolves, **degrade** to running the ACs against a
   local dev server and note it loudly at the gate (do not halt).

## ⏸ The single gate

Assemble the **dossier** (below). Its executive summary is **A4's already-produced `eli5` narrative**
(*what we delivered, what we proved, why it mattered, how we know beyond tests*) — do NOT re-run eli5
here. Then ask ONE `AskUserQuestion`:

- **Ship** → run Phase C.
- **Hold** → stop; PR stays a draft; report written.
- **Fix more** (with notes) → re-enter the Fix loop on the reopened findings, then re-gate.

This is the only place QAPhase stops for you.

## Phase C — ship (post-approval only)

1. **Sprint/story/deferral sync.** This is a **write** across the story/plan docs + GitHub — do NOT
   expect a summarize-only skill to do it. Use the `sprint_sync` kit skill (e.g. `bmad-sprint-status`)
   to **read** current status + surface risks, then **write**: mark done tasks complete in story +
   plan, reconcile deferred items (note new, close resolved, adjust if scope changed), **mirror
   new/closed deferrals to GitHub issues** (`gh`), and update sprint/story status. Confirm each
   write landed (re-read the doc / `gh issue view`) before moving on.
2. **Ship.** `superpowers:finishing-a-development-branch`: verify tests, mark the PR ready, and
   complete per its menu (merge/PR).

## As a Workflow (multi-agent)

When multi-agent orchestration is available (ultracode / explicit opt-in), QAPhase runs as a
Workflow script rather than an inline sequence — the lenses and the fix loop parallelize cleanly:

- **Phase A** = a `parallel`/`pipeline` fan-out: A1 (grill/spec-gap), A2 (itself fanned to
  api·ui·e2e agents), A3 (fanned by chaos mode: auth·perf·data-integrity·concurrency), A4
  (eli5 live scenarios), each schema'd. Chaos + QA + scenario findings get an **adversarial-verify**
  stage (independent skeptics prompted to refute) before they cost a fix cycle.
- **Fix loop** = a `pipeline` over KEPT findings: `codebase-design → design-tests → expert GREEN`,
  with **worktree isolation** so parallel fixes don't clobber each other.
- **fast-verify, evidence, Phase B, GATE, Phase C** stay sequential.

The script is the enforced implementation (a throwing gate proves each lens actually ran, like
verification-phase's Workflow variant); this SKILL.md is the human-readable spec + semantic
trigger. Absent orchestration, execute the phases inline in the order above — the guarantees are
weaker (LLM-attested) but the recipe is identical.

## Report

Write to the bound path; echo the **Summary** + the gate question inline. Skeleton:

```markdown
# QAPhase — {story/branch} — {YYYY-MM-DD}

**Scope:** {branch vs base, N files} · **Story:** {id/path} · **Critical surface:** {yes/no — which}
**Resolved kit:** spec_gap={..} qa_session={..} chaos={..} green={..} sprint_sync={..}

## Preflight
- Deps: karpathy ✓ · cove ✓ · codebase-design ✓ · design-tests ✓ · verification-phase ✓ ·
  verification-before-completion ✓ · finishing-a-development-branch ✓ · gh ✓ · playwright ✓
- Config skills: {all resolved / list MISSING + halt}

## Summary
- AC coverage: {n/N} · Gaps: {g} · QA scenarios: {p pass / f fail} · Chaos findings: {c}
- Fixes applied: {a} (each test-backed) · Reported-not-applied: {r} · Cut by karpathy: {k} ·
  cove escalations: {e}
- Fast-verify: {verdict} · Evidence: {suite pass/fail} · Preview AC: {n/N pass}

## A1 Spec-gap — {skill}
{AC coverage matrix + gap list}
## A2 QA-session (API/UI/E2E) — {skill}
{scenarios run + pass/fail evidence}
## A3 Chaos — {skill}
{findings + adversarial-verify verdicts}
## A4 Prove-beyond-tests (eli5) — live scenarios + narrative
{scenarios run + pass/fail · the delivered/proved/why/how narrative (reused as the gate summary)}

## Fixes (design-first, TDD)
| finding | lens | seam (codebase-design) | red test | GREEN expert | verify |
|---------|------|------------------------|----------|--------------|--------|

## Fast-verify (verification-phase --fast) · Evidence gate
## Phase B — draft PR {url} · AC-on-preview matrix

## GATE decision: {Ship / Hold / Fix-more}
## Phase C (if shipped): sprint/deferral sync + finish

## Reported, not applied (needs your call)
- {finding — why deferred}
```

## Red flags

- Stopping for input anywhere before the GATE (except a Preflight halt) — the whole point is one
  stop; carry blockers to the gate instead.
- Proceeding past a MISSING dependency or a configured-but-missing skill — halt, don't degrade.
- Merging, marking a PR ready, or writing to GitHub **before** the gate returns "Ship."
- Applying a fix that karpathy cut or cove refuted, or a fix without a failing test first.
- A fast-verify "best practice" with no context7 citation, or a spec gap (A1) not grounded in the story.
- Running eli5 (A4) only at the gate — it runs in Phase A so its live-scenario gaps can be fixed this run.
- Treating a chaos finding as non-critical for cove — chaos findings are critical by default.
- Reviewing from memory instead of the real diff + real story.
- Claiming AC-on-preview pass without having run it against the actual preview this run.
- Marking QAPhase complete with an open Todo or an unwritten report.
