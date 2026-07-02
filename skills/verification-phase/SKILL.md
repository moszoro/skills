---
name: verification-phase
description: Layered code-verification gauntlet with karpathy + cove gating. Use when the user says "run VerificationPhase", "verify this phase", or wants a multi-lens review (preflight → test-quality → smells → security → docs-best-practices → project-rules) that filters every recommendation through karpathy-guidelines, escalates critical findings to cove, and auto-applies the survivors.
---

# VerificationPhase

## Overview

**What:** Verifies a change end to end. First a **preflight** confirms every skill/tool this
gauntlet needs is available; then four review lenses run, one at a time, each with a fixed
prompt: (1) code smells / bad patterns, (2) security vulnerabilities, (3) docs-grounded
best-practices via context7, (4) project-rules-and-learnings conformance; finally a
**test-quality gate** (`evals:eval-tests`) scores the change's tests once and fixes gaps. Every
lens's recommendations are filtered through `andrej-karpathy-skills:karpathy-guidelines`;
critical-surface findings that survive are double-checked with `cove` before anything is applied.
A closing **skill-invocation gate** proves from the session transcript that every required skill
was actually invoked in-window, and re-invokes any that were skipped.

**How:** Preflight → a shared per-step pipeline (review → karpathy filter → conditional cove →
auto-apply → log) for all four lenses → eval-tests gate → skill-invocation gate → a dated report
+ inline summary.

**Why:** A single review pass over-reports (noise) and under-verifies (plausible-but-wrong
fixes ship). Gating on dependencies first prevents silent half-runs; layering distinct lenses
catches more; karpathy cuts the over-engineered and speculative; cove guards the findings that
touch auth / user data / critical data. The test-quality gate runs **last**, once, so it scores
the *final* test state after the lenses have applied their fixes — rather than being invalidated
and re-run every time a step touches the suite. The outcome is a small set of *verified* fixes
applied, and an auditable record of everything considered and why it was kept or cut.

## Role

Act as a meticulous staff-level reviewer running a layered verification gauntlet. You are
skeptical of your own findings: a recommendation only earns an edit after it survives the
karpathy filter and, when it touches a critical surface, a cove check.

## Execution contract

This skill is a prompt, not a code-enforced workflow — completeness is on you. To run it faithfully:

- **First action:** create a TodoWrite with one item per gate and step below, in order:
  Preflight · Step 1 · Step 2 · Step 3 · Step 4 · Test-quality gate · Skill-invocation gate ·
  Report. Mark each in-progress → complete as you go.
- **Run in the listed order. Do not skip, reorder, or batch steps** — later lenses depend on
  earlier applied fixes, and the gates must precede the lenses.
- **Fail loud, never silently degrade.** If Preflight finds a missing skill/tool, or any gate
  cannot run, STOP and report what's missing — do not "work around" it by skipping.
- **Fresh invocation is mandatory; reuse and substitution do not count.** Every required skill —
  each step's reviewer, the karpathy filter, `cove` when its gate fires, and the `evals:eval-tests`
  gate — MUST be invoked via the `Skill` tool *within this phase run*. A copy loaded earlier in the
  session (by a different command, or before the phase started) does **NOT** satisfy a step; invoke
  it again inside the phase. Do **NOT** substitute a previous `eval-tests` result for the closing
  gate, even if the tests look unchanged — run it here. (Re-using a skill *this phase already loaded*
  for an earlier step is fine: the rule is "engaged within the phase," not "reload identical markdown
  N times.")
- **The Skill-invocation gate enforces the above.** Before the report you verify, against the
  session transcript, that each required skill was actually invoked in-window and **re-invoke any
  that are missing** (`## Skill-invocation gate`). A prompt-skill cannot hard-*guarantee* this (an
  agent can deviate) — the transcript gate is the un-spoofable backstop. For an absolute guarantee,
  port this logic to a code-enforced Workflow script with throwing gates.
- **Do not declare VerificationPhase complete** until every Todo is done, the skill-invocation gate
  is green, and the report is written.

## Activation

1. **Resolve scope.** `$ARGUMENTS` (the user's prompt) describes *what* to review and *which
   phase* "this phase" refers to. If it names a scope (a plan, a path, a subsystem, a branch),
   use it. **Default when nothing is specified: uncommitted working-tree changes** —
   `git diff HEAD` plus untracked files (`git status --porcelain`). Read the actual diff; do
   not review from memory or assumption.

2. **Detect the critical surface (drives cove later).** From the changed paths/diff, mark the
   change critical if it touches any of: authentication / authorization / session / tokens /
   permissions / role checks; user PII / personal or health data; payments / money; or other
   high-blast-radius data or state (audit trails, migrations, core domain logic — anything whose
   corruption is hard to detect or reverse). Use the repo's own conventions to recognize these
   surfaces. Record the verdict — it gates cove per step.

3. **Bind the report path.** `docs/verification-phase/{YYYY-MM-DD}-{scope-slug}-verification.md`
   unless the user gave one. Create the directory if missing. Start the report from the
   template in `## Report` below.

4. Run, in order: **Preflight** → the four steps via `## Per-step pipeline` → **Test-quality
   gate** → **Skill-invocation gate** → **Report**. Do not parallelize the steps — later lenses
   read earlier results, and applied fixes change what the next lens sees.

## Preflight — required skills & tools

Before any review, confirm every dependency this gauntlet invokes is available **this session**,
and STOP with a clear message if any is missing (a half-run gauntlet gives false assurance).

Required skills (must appear in this session's available-skills list):

- `fullstack-dev-skills:code-reviewer` — Steps 1, 3, 4
- `fullstack-dev-skills:security-reviewer` — Step 2
- `andrej-karpathy-skills:karpathy-guidelines` — every step's filter
- `cove` — conditional critical-surface gate
- `evals:eval-tests` — the test-quality gate below

Required tools:

- context7 MCP — `mcp__plugin_context7_context7__resolve-library-id` and
  `mcp__plugin_context7_context7__query-docs` (Step 3). They are deferred tools — confirm they
  resolve via ToolSearch (`select:mcp__plugin_context7_context7__query-docs`).

Record a Preflight line in the report: each dependency `available` / `MISSING`. If anything is
MISSING, halt and tell the user which — do not proceed with a degraded subset. Availability ≠
invocation: Preflight only confirms the skills *exist*; the per-step pipeline must still invoke
each one fresh in-window (enforced by the skill-invocation gate).

## Per-step pipeline

Run this for every step. `{reviewer}`, `{prompt}`, and the step number come from the step.

1. **Review.** Invoke `{reviewer}` with `{prompt}` against the resolved scope — a **fresh `Skill`
   invocation inside this phase**. A copy of `{reviewer}` loaded earlier in the session (e.g. by a
   different command) does NOT count; invoke it again now. Collect concrete findings — each with
   file:line, a one-line problem statement, and a proposed fix. No fix without a located cause.

2. **Karpathy filter.** Invoke `andrej-karpathy-skills:karpathy-guidelines` over the step's
   findings (the *recommendations*, not the code). It must: cut over-engineered / speculative /
   gold-plated fixes, surface hidden assumptions, keep every surviving change surgical, and
   restate each kept fix as a verifiable change. Tag each finding **KEEP** or **CUT (reason)**.
   If it cut everything, the step is clean — record that and move on.

3. **cove gate (conditional).** Run `cove` on this step's KEPT findings **only if both** hold:
   the change is on a critical surface (Activation step 2) **and** ≥1 finding survived karpathy.
   cove verifies each kept finding is real and the fix is correct before it's applied; demote
   any finding cove refutes to **reported-not-applied**. If the change is not critical, or
   karpathy kept nothing, skip cove (record "skipped: {not-critical | nothing-kept}").

4. **Auto-apply.** Apply the surviving fixes (KEEP, and cove-confirmed when cove ran) to the
   working tree. Anything CUT, cove-refuted, or needing human judgment is **reported, not
   applied**. After applying, confirm the change does what the finding claimed (re-read the
   edited region; run the relevant test if one exists).

5. **Commit (atomic, per step).** If this step applied any fixes, commit them IMMEDIATELY as a
   focused, atomic commit — do NOT batch fixes across steps:
   ```bash
   git commit -am "fix(verify): {lens} — <one-line summary of what was applied>"
   ```
   This makes the gauntlet **durable + resumable**: if it is interrupted mid-run, the applied
   fixes survive as commits, and a resumed run re-reviews from a clean committed state instead of
   losing work or re-applying it. If the step applied no fixes, commit nothing. (Skip silently in
   a non-git working tree.)

6. **Log + surface progress.** Append the step's block to the report (reviewer + exact prompt,
   raw findings, karpathy KEEP/CUT verdicts, cove outcome, what was applied vs reported), AND
   print a one-line progress milestone to stdout so a watching operator sees it live, e.g.
   `✓ {step} ({lens}): N applied · M reported · {clean | committed <sha>}`.

## Step 1 — Code smells & bad patterns

- **Reviewer:** `fullstack-dev-skills:code-reviewer`
- **Prompt:** "Find bad code, smell code, duplicates, bad patterns, no single responsibility,
  hardcoded variables, over-engineered code, bad-performant code, etc."

## Step 2 — Security vulnerabilities

- **Reviewer:** `fullstack-dev-skills:security-reviewer`
- **Prompt:** "Review code for vulnerabilities."
- Invoke `security-reviewer` fresh here even if a prior command (e.g. an earlier `eval-tests`)
  already loaded it — a pre-phase load does not satisfy this step.
- This step is inherently security-relevant: if any finding survives karpathy, treat the
  change as critical for the cove gate even if Activation step 2 was borderline.

## Step 3 — Docs-grounded best practices (context7)

- **Reviewer:** `fullstack-dev-skills:code-reviewer`
- **Prompt:** "Use context7 and double-check whether we implemented this phase with the best
  practices possible based on the official documentation — no hacks, best practices, clean
  code."
- The reviewer MUST pull real docs for the libraries/frameworks in scope via
  `mcp__plugin_context7_context7__resolve-library-id` then
  `mcp__plugin_context7_context7__query-docs`, and ground each finding in what the docs say —
  not from memory. A "best practice" with no doc citation is a CUT candidate for karpathy.

## Step 4 — Project rules & learnings

- **Reviewer:** `fullstack-dev-skills:code-reviewer`
- **Prompt:** "Check whether the code follows the project rules and learnings."
- Ground findings in this repo's actual rules: `CLAUDE.md` / `AGENTS.md` if present, any ADRs or
  contributing/style docs, and the project's recalled memories (already in your context this
  session — the `MEMORY.md` index and any `<system-reminder>` memories). Cite the rule (file +
  section, or memory slug) each finding violates; an uncited "rule" is a CUT candidate for karpathy.

## Test-quality gate — eval-tests

Runs **last**, after all four lenses, once. Placed here on purpose: the lenses may add or modify
tests as they apply fixes, so scoring the suite earlier would only force re-runs. This gate scores
the *final* test state a single time.

1. **Invoke `evals:eval-tests` now, inside this phase**, over the resolved scope — it scores the
   change's uncommitted tests against its quality criteria and checks ACs against the tests +
   implementation. **Do not substitute or merely reference a prior `eval-tests` run from earlier in
   the session** — even if you believe the tests are unchanged, the gauntlet's closing gate must
   execute here (it will appear in the transcript for the skill-invocation gate).
2. **No tests in scope?** Record "eval-tests skipped: no tests in change". A code change that
   adds no tests is itself a likely gap — note it (Step 4's project-rules lens should already
   have flagged it against the repo's test-first rules).
3. **Fix the gaps it surfaces** (weak/tautological assertions, missing AC coverage, fake tests)
   by strengthening or adding tests — routed through the same `andrej-karpathy-skills:karpathy-guidelines`
   filter so you don't gold-plate the suite, and `cove` if the gap is on a critical surface. These
   fixes are test-only; no need to re-run the four code lenses. Re-run `evals:eval-tests` until
   it's clean or the only remainder is explicitly deferred. **Commit the applied test fixes
   atomically** (`git commit -am "fix(verify): eval-tests — <summary>"`) — same durability rule as
   the per-step pipeline.
4. **Log** the gate to the report (initial verdict, gaps found, fixes applied, final verdict) and
   print a progress milestone (`✓ eval-tests: N gaps fixed · {clean | deferred}`).

## Skill-invocation gate (un-spoofable — runs after eval-tests, before the Report)

Your TodoWrite and your own narration are spoofable; the session transcript is not. Before writing
the report, **prove from the transcript that every required skill was actually invoked within this
phase run, and re-invoke any that are missing** — re-engage the skill if it wasn't, never wave it
through.

1. **List the in-window invocations** straight from the transcript. The window starts at the *real*
   invocation of this skill (its `Skill` tool-use or its slash-command line) — a structural marker
   prose can't forge; the recipe builds that needle at runtime so this file's own text never matches
   itself. Run:
   ```bash
   python3 - <<'PY'
   import json, glob, os
   # Worktree-aware transcript discovery. Do NOT derive the project dir from cwd: Claude Code's
   # project slug maps BOTH '/' and '.' to '-' (so '/.claude' → '--claude'), and a git worktree's
   # session is stored under a different slug than its main repo — so a cwd.replace('/','-') guess
   # silently misses the transcript in worktrees (GATE-DEGRADED false negative). Instead, scan every
   # project transcript newest-first and pick the one that actually contains THIS run's start marker:
   # slug-independent, worktree-proof. (The active session is being written now → it sorts first, so
   # this is one file-read in the common case.)
   CMD = "<command-name>" + "/verification-phase"   # built at runtime → this file never self-matches
   def load(l):
       try: return json.loads(l)
       except Exception: return None
   def items_of(o):
       c = (o.get("message", {}) or {}).get("content")
       if isinstance(c, list): return [it for it in c if isinstance(it, dict)]
       if isinstance(c, str): return [{"type": "text", "text": c}]
       return []
   def is_start(o):  # the genuine invocation of THIS skill (command or Skill tool-use)
       for it in items_of(o):
           if it.get("type") == "tool_use" and it.get("name") == "Skill" \
              and (it.get("input") or {}).get("skill") == "verification-phase":
               return True
           if CMD in (it.get("text") or ""):
               return True
       return False
   base = os.path.expanduser("~/.claude/projects")
   transcripts = sorted(glob.glob(base + "/*/*.jsonl"), key=os.path.getmtime, reverse=True)
   if not transcripts:
       print("GATE-DEGRADED: no transcript found under", base); raise SystemExit
   tx = lines = start = None
   for f in transcripts:                    # newest-first → the active session is matched first
       ls = open(f, errors="ignore").read().splitlines()
       hits = [i for i, l in enumerate(ls) if (o := load(l)) and is_start(o)]
       if hits:
           tx, lines, start = f, ls, hits[-1]   # last marker in this file → window = [start, now]
           break
   if tx is None:
       print("GATE-DEGRADED: no verification-phase invocation found in",
             len(transcripts), "transcripts"); raise SystemExit
   seen = set()
   for l in lines[start:]:
       o = load(l)
       if not o: continue
       for it in items_of(o):
           if it.get("type") == "tool_use" and it.get("name") == "Skill":
               seen.add("skill:" + str((it.get("input") or {}).get("skill")))
           if it.get("type") == "tool_use" and "context7" in (it.get("name") or ""):
               seen.add("tool:context7")
           if it.get("type") == "text" and "/evals:eval-tests" in (it.get("text") or ""):
               seen.add("cmd:evals:eval-tests")
   print("transcript:", os.path.basename(tx), "| window-start-line:", start)
   print("in-window:", sorted(seen))
   PY
   ```
2. **Required in-window** — re-invoke any that are absent, then re-run step 1 to confirm:
   - `fullstack-dev-skills:code-reviewer` (Steps 1/3/4 — ≥1 in-window invocation)
   - `fullstack-dev-skills:security-reviewer` (Step 2)
   - `andrej-karpathy-skills:karpathy-guidelines` (the filter)
   - `evals:eval-tests` (the closing gate — `skill:` or `cmd:` form)
   - context7 (`tool:context7`, Step 3)
   - `cove` — **conditional**: required in-window ONLY if the report records ≥1 KEEP finding on a
     critical surface. Otherwise its absence is correct (the gate never fired) — record
     "cove: correctly not fired".
3. **If any required (non-conditionally-skipped) skill is absent:** invoke it now against the
   relevant step's findings/scope, apply + log per the pipeline, and re-run step 1. **Do not write
   the report until the gate is green** (every required skill present, cove present-or-correctly-skipped).
4. **If the gate prints `GATE-DEGRADED`** (no transcript / no invocation found / unexpected layout):
   say so, fall back to re-invoking every required skill fresh now (manual attestation), and mark the
   gate **"degraded (manual)"** in the report — never silently pass.
5. **Log** the gate's audit line to the report (which skills were transcript-verified in-window,
   and which were re-invoked to close a gap).

## Report

Write to the bound path and echo the **Summary** inline at the end. Skeleton:

```markdown
# VerificationPhase — {scope} — {YYYY-MM-DD}

**Scope reviewed:** {what / how resolved — e.g. "uncommitted working-tree changes, 7 files"}
**Critical surface:** {yes/no — which: auth / user-data / critical-data}

## Preflight
- Skills: code-reviewer ✓ · security-reviewer ✓ · karpathy ✓ · cove ✓ · eval-tests ✓
- Tools: context7 ✓   (or list MISSING + halt)

## Skill-invocation gate (transcript-verified)
- In-window: code-reviewer ✓ · security-reviewer ✓ · karpathy ✓ · eval-tests ✓ · context7 ✓ ·
  cove {ran / correctly not fired}
- Re-invoked to close a gap: {none / list}   ·   Mode: {transcript / degraded-manual}

## Summary
- Applied: {n fixes} · Reported-not-applied: {m} · Cut by karpathy: {k} · cove escalations: {c}
- One line per step: clean / N applied / M reported.
- eval-tests: {final verdict / skipped: no tests}

## Step 1 — Code smells & bad patterns ({reviewer})
**Prompt:** "{exact prompt}"
| # | file:line | finding | proposed fix | karpathy | cove | outcome |
|---|-----------|---------|--------------|----------|------|---------|
...
## Step 2 — Security vulnerabilities (...)
## Step 3 — Best practices via context7 (...)
## Step 4 — Project rules & learnings (...)

## Test-quality gate (eval-tests) — runs last
- Initial: {verdict} · Gaps: {n} · Fixes applied: {n} · Final: {verdict / skipped: no tests}

## Applied changes
- {file:line — what changed — which finding}

## Reported, not applied (needs your call)
- {file:line — finding — why deferred: cut by karpathy / cove-refuted / judgment}
```

## Red flags

- Starting the review before Preflight passes, or proceeding with a MISSING dependency — that's
  a silent half-run; halt instead.
- Skipping the final eval-tests gate, or running it mid-gauntlet (it runs once, last).
- **Satisfying a step with a skill loaded BEFORE the phase** (by another command or an earlier
  run) — that's reuse, not invocation; re-invoke it in-window so the transcript shows it.
- **Substituting a prior `eval-tests` run for the closing gate** because "the tests look
  unchanged" — run it inside the phase regardless.
- **Writing the report before the skill-invocation gate is green** (or marking the gate passed
  from memory instead of the transcript).
- Reviewing from memory instead of the actual diff — always read it first.
- Applying a fix that karpathy cut or cove refuted — those are reported, never applied.
- Running cove as a blanket final pass — it's per-step and conditional (critical + kept).
- A Step-3 "best practice" with no context7 citation, or a Step-4 "rule" with no file/ADR
  reference — unverified claims; let karpathy cut them.
- Parallelizing the steps — order matters; applied fixes change later lenses' input.
- Marking VerificationPhase complete with an open Todo or an unwritten report.
