---
name: verify-spec
description: A fixed 3-step SPEC/design-review gauntlet — Explore(gaps-vs-decisions) → grep-checkable-constraints(evidence) → codebase-design(deep-module review, grounded in grepped code) — that hardens a design/spec against its source of truth (the decisions that produced it, or the driving issue) BEFORE it is built. The spec-altitude sibling of verify-plan: verify-plan checks a code-complete plan's code blocks; verify-spec checks a design's decisions, constraints, and seams. Use after a spec is grilled and before you build it. Every claim is grounded in grepped file:line evidence — never the spec's own narration.
disable-model-invocation: false
---

# verify-spec

## Overview

**What:** A **spec / design document** (higher-altitude than a code-complete plan: it states decisions,
constraints, module interfaces, and seams — not the actual implementation code) is only as good as the
review that catches its gaps *before* anyone builds it. `verify-spec` runs a **fixed 3-step gauntlet**
over such a spec and its source of truth, in this exact order, with each step's full prompt inline (no
substitution, no reordering):

1. **`Explore`** — verify the spec against the **decisions that produced it**; find gaps,
   contradictions, and scope creep. Decision → spec-section mapping, not the spec's own narration.
2. **grep-checkable constraints** — for every FACTUAL claim the spec makes about the real system,
   grep code / spec / protocol / marker-convention to **CONFIRM or REFUTE** it, file:line.
3. **`codebase-design`** — review the design through the **deep-module lens**; before concluding,
   grep the real code for evidence (where the seam lives, which port to reuse, is the interface right).

**Why spec-altitude, not plan-altitude:** a spec's failure mode is not a buggy code block (that is
verify-plan's target) — it is a **decision that was never captured, a factual claim that is false, or a
seam placed where the code cannot support it**. All three are caught by grounding the spec in the real
repo + the real decisions, never in the spec's own prose. This is the sibling of `verify-plan`: run
**verify-spec before you build the spec into a plan/code**, and `verify-plan` after.

**Dual-use.** One parameter changes behaviour:

- **`source`** — `decisions` (**default**) | `issue`. Rebinds the **review target**: what the spec is
  verified *against* in step 1. `source=decisions` (default) checks the spec against the decisions that
  produced it (a grilling transcript, a design conversation, a decisions log); `source=issue` rebinds
  the target to the driving **issue** (its number + fetched body). Steps 2 and 3 are unaffected — they
  always ground in the real repo.

## Parameters

| Param | Values | Default | Effect |
|-------|--------|---------|--------|
| `source` | `decisions` \| `issue` | `decisions` | Rebinds step 1's review **target**. `decisions` (default) = the decisions/conversation that produced the spec; `issue` = the driving issue. Steps 2–3 always ground in the real repo regardless. |

Resolve the param first: read `source` (default `decisions`) from the invocation. Bind **`$TARGET`** =
the decisions/conversation record when `source=decisions`, or the issue (number + fetched body) when
`source=issue`. Also bind **`$SPEC`** = the spec/design file under review (the argument, or the most
recently written spec in scope). Announce the resolved values before step 1, e.g.
`verify-spec: source=decisions → spec = docs/.../2026-07-22-foo.md · target = this session's grill decisions`.

## The gauntlet — run all three, in order, no skipping

### Step 1 — `Explore` (verify spec against the decisions, find gaps)

Use the `Explore` tool (or `Grep`/`Glob`/`Read` if unavailable). Exact prompt:

> Verify the spec **$SPEC** against **$TARGET** — the decisions/requirements it must satisfy.
> Enumerate every decision, constraint, and requirement in $TARGET; for each, map it to where $SPEC
> honors it, and flag: **GAP** (a decision with no spec home), **CONTRADICTION** ($SPEC says X, $TARGET
> settled not-X), **SCOPE CREEP** ($SPEC adds surface $TARGET never asked for), and **AMBIGUITY** (a
> decision $SPEC restates too vaguely to build). Do NOT trust the spec's own narration — map each
> decision → spec section explicitly. Report each finding with the decision it violates and the concrete
> spec-edit that fixes it.

### Step 2 — grep-checkable constraints (evidence, not assertion)

Ground the spec's FACTUAL claims in the real system. Use `Grep`/`Glob`/`Read` (or dispatch an `Explore`
agent for breadth). Exact prompt:

> Do we have any constraints we can double-check with grep — in the code, the spec, a protocol, a
> marker/naming convention, an ADR, whatever? For every FACTUAL claim **$SPEC** makes about the real
> system (a function/seam exists here, a marker has this shape, a checkbox carries this anchor, a file
> holds this state, a gate behaves this way), grep the real repo to **CONFIRM / REFUTE / NOT-FOUND** it,
> with **file:line** evidence. Then SURFACE constraints the spec ASSUMED but never verified — an
> existing port it should reuse instead of re-inventing, a gate its change might trip, a naming/anchor
> rule it must obey, a host-vs-container (or equivalent execution-context) placement it got wrong.
> Output a compact evidence table: claim → verdict → file:line. Read the code; never trust the spec's
> claim. Correct any wrong evidence from a sub-agent against the primary source.

### Step 3 — `codebase-design` (deep-module review, grounded in grepped code)

Load `codebase-design` via the `Skill` tool, then review the design — but **grep the code for evidence
before concluding**. Exact prompt:

> Load `codebase-design` and review **$SPEC** through the deep-module lens. BEFORE concluding, grep the
> real code for EVIDENCE — do not review from the spec's description. Assess: are the proposed modules
> **deep** (small interface, lots of hidden behavior) or shallow pass-throughs? Is each **seam** placed
> where the real code can support it (grep where the seam actually lives, who the real callers are)?
> Does the design **re-invent an existing seam/port** instead of reusing it (grep for the existing one)?
> Is any "abstraction" a one-adapter hypothetical (no real second implementation)? Is the interface
> right against the real call-sites? Flag shallow modules, wrong-seam placement, one-adapter
> abstractions, and re-invention — each grounded in **file:line**, never assumptions. Give the
> surgical design-edit for each.

## Output

After all three steps, emit a compact report: per-step findings (with file:line evidence), the resolved
`source` value, an **evidence table** (claim → CONFIRMED/REFUTED → file:line), and a final verdict —
**spec ready-to-build** / **needs another round** (with the blocking must-fix list). Hand the verdict to
the human; do NOT start building — verify-spec verifies, it does not implement.

## Guardrails

- **Always all three steps, always in order.** No substitution, no reordering, no skipping.
- **`source` only rebinds step 1's target**; it never adds/removes a step. Steps 2–3 always ground in
  the real repo.
- **Evidence over narration — always.** Every CONFIRMED/REFUTED verdict and every design finding cites
  **file:line** from the real repo, not the spec's prose. A sub-agent's evidence that contradicts the
  primary source is corrected against the source, not trusted.
- **Grep before you conclude** (steps 2 and 3): a "best practice" or "the seam is here" with no
  file:line is not a finding — it is a guess. Discard or ground it.
- This gauntlet **verifies**; it never builds. If the spec passes, hand it off (to `writing-plans` /
  `verify-plan` / the build). If it fails, report the must-fix list and stop.
- If `source=decisions` and no decision record exists, or `source=issue` and no issue is resolvable,
  stop and report rather than inventing a target.
