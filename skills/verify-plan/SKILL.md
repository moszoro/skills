---
name: verify-plan
description: A dual-use, fixed 5-step plan-review gauntlet — code-reviewer → Explore → grill-with-docs → nightshift-plan-skills → evals:eval-tests — that hardens a code-complete plan against a source of truth (a spec by default, or the driving issue) before it is applied. Use when a human wants to stress-test a plan standalone, or when nightshift wants an AFK plan-review pass. Runs the same five steps in the same order either way; only two knobs change: `source` rebinds WHAT the plan is checked against, and `interactive` decides whether step 3's grill is a live human interview or an AFK self-grill.
disable-model-invocation: false
---

# verify-plan

## Overview

**What:** A **code-complete plan** (each task carries the actual test + implementation + config
code with exact file paths; a build agent later *applies* it, it does not author) is only as good as
its review. `verify-plan` runs a **fixed 5-step gauntlet** over such a plan and its target, in this
exact order, with each step's full prompt inline (no substitution, no reordering):

1. **`code-reviewer`** — broad correctness / security / smell pass over the plan's code blocks.
2. **`Explore`** — ground the plan in the real repo (paths, imports, signatures actually exist).
3. **`grill-with-docs`** — relentlessly interrogate the plan against its source of truth.
4. **`nightshift-plan-skills`** — per-task expert-skill review, fixes landed IN the plan + the stamp.
5. **`evals:eval-tests`** — score the plan's tests; a wrong implementation must not pass them.

**Dual-use.** The same five steps run for both callers; only two parameters change behaviour:

- **`source`** — `spec` (**default**) | `issue`. Rebinds the **review target**: what the plan is
  verified *against*. `source=spec` (the default) checks the plan against its originating **spec**;
  `source=issue` rebinds the target to the driving **issue** instead. Nothing else changes.
- **`interactive`** — `true` (**default**) | `false`. Governs **step 3 only**. `interactive=true`
  runs step 3 as a **live human grill** (a real interview at the terminal); `interactive=false`
  makes step 3 an **AFK self-grill** (the agent grills itself and answers from the source, no human).
  **Steps 1, 2, 4, and 5 are unaffected by this flag.**

**Two canonical invocations:**

- **Human, standalone:** bare `verify-plan` ⇒ `source=spec interactive=true` — grills you live
  against the spec.
- **Nightshift, AFK:** `verify-plan source=issue interactive=false` — grills the plan against the
  issue with no human, so it runs unattended in the loop.

## Parameters

| Param | Values | Default | Effect |
|-------|--------|---------|--------|
| `source` | `spec` \| `issue` | `spec` | Rebinds the review **target**. `source=spec` (default) verifies the plan against its **spec**; `source=issue` rebinds the target to the **issue**. Applies to every step that reads the source of truth (steps 1–5). |
| `interactive` | `true` \| `false` | `true` | Governs **step 3 only**. `true` ⇒ **live human grill**; `false` ⇒ **AFK self-grill**. Steps 1, 2, 4, 5 are identical regardless. |

Resolve the params first: read `source` (default `spec`) and `interactive` (default `true`) from the
invocation. Then bind **`$TARGET`** = the spec file when `source=spec`, or the issue (its number +
fetched body) when `source=issue`. Announce the resolved values before step 1, e.g.
`verify-plan: source=issue interactive=false → target = issue #37`.

## The gauntlet — run all five, in order, no skipping

### Step 1 — `code-reviewer` (unaffected by `interactive`)

Load `fullstack-dev-skills:code-reviewer` via the `Skill` tool, then run this exact prompt:

> Review every code block in the plan (tests, stubs, implementations, config) for correctness bugs,
> security vulnerabilities (injection, XSS, unsafe deserialization, secret handling), N+1 queries,
> race conditions, error-path gaps, and code smells. For each finding give file:line (as the plan
> names it), severity, and the concrete fix. Cross-check each code block against **$TARGET** — flag
> anything the plan does that $TARGET does not ask for, and anything $TARGET requires that the plan
> omits. Produce a prioritized, actionable list.

### Step 2 — `Explore` (unaffected by `interactive`)

Use the `Explore` tool (or `Grep`/`Glob`/`Read` if `Explore` is unavailable) to ground the plan in
the real repository:

> For every path, import, symbol, and function signature the plan references, confirm it exists in
> the real repo and matches (an LLM-authored plan drifts from reality). List each referenced
> artifact, whether it exists, and any mismatch (wrong path, renamed symbol, changed signature,
> removed API). Do not trust the plan's own claims — read the code. Report drift as concrete
> plan-edit corrections.

### Step 3 — `grill-with-docs` (THE ONLY step `interactive` governs)

Load `grill-with-docs` via the `Skill` tool. Its behaviour forks on `interactive`, **and only here**:

- **`interactive=true` (default) — live human grill.** Run the full live interview: relentlessly
  question the human operator about the plan's assumptions, gaps, and risks against **$TARGET**,
  recording answers as ADR/glossary entries as you go. Wait for real answers at the terminal.

  > Run a live `/grilling` interview (with `/domain-modeling`) against **$TARGET**. Interrogate every
  > assumption, ambiguity, missing edge case, and unstated risk in the plan; drive each to a decision
  > and capture it. Do not answer for the human — ask, then wait for the reply.

- **`interactive=false` — AFK self-grill.** No human is present, so the agent grills **itself** and
  answers **from $TARGET**, never blocking on a prompt:

  > AFK self-grill: with NO human available, generate the same relentless grilling questions about
  > the plan against **$TARGET**, then answer each one yourself using only $TARGET and the real repo
  > as authority. Where $TARGET cannot settle a question, record it as an OPEN risk in the plan
  > rather than blocking. Never wait for human input.

**Steps 1, 2, 4, 5 do not read `interactive` at all** — they run identically in both modes.

### Step 4 — `nightshift-plan-skills` (unaffected by `interactive`)

Load `nightshift-plan-skills` via the `Skill` tool (or run the `/nightshift-plan-skills` command),
then run its per-task expert review over the plan:

> Review the plan task by task through the right `fullstack-dev-skills:*` expert for each task's
> actual code, grounding fixes in the real repo, and land the fixes IN the plan. Record a
> `<!-- task-skills task=N: … -->` marker per reviewed task and the single
> `<!-- skills-annotated: nightshift-plan-skills -->` stamp near the top. Verify each fix against
> **$TARGET**.

### Step 5 — `evals:eval-tests` (unaffected by `interactive`)

Run the `evals:eval-tests` command over the plan's test code:

> Score the plan's tests against the eval-tests criteria: 3-tier source tagging (T1 AC / T2 INV·NFR /
> T3 QUALITY), test-through-the-interface, seam/real-infra conformance, and the decisive check —
> would a WRONG implementation pass these tests? Trace each test back to an AC or invariant in
> **$TARGET**. Report gaps and add the missing tests.

## Output

After all five steps, emit a compact report: per-step findings + fixes applied, the resolved
`source`/`interactive` values, and a final verdict (plan ready-to-apply / needs another round).
Standalone (`interactive=true`) ends by handing the verdict to the human; nightshift
(`interactive=false`) ends by leaving the annotated plan + verdict for the loop to gate on.

## Guardrails

- **Always all five steps, always in order.** No substitution, no reordering, no skipping — even in
  AFK mode.
- **`source` only rebinds the target**; it never adds/removes a step. **`interactive` only forks
  step 3**; it never touches steps 1, 2, 4, 5.
- Ground every fix in the real repo (Explore/grep), not assumptions.
- If `source=spec` and no spec exists, or `source=issue` and no issue is resolvable, stop and report
  rather than inventing a target.
