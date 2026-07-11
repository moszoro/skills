---
description: Run QAPhase — the autonomous acceptance-and-ship QA gauntlet. Proves a finished story end-to-end (spec-gap/grill · API+UI+E2E QA-session · chaos · prove-beyond-tests) then ships it, stopping at ONE gate. Dynamic-proof sibling to verification-phase.
argument-hint: "[scope — story/feature/branch; empty = current branch vs parent base]  [spec_gap_mode=auto|grill]"
---

Run the **qa-phase** skill against `$ARGUMENTS` (empty ⇒ default scope = the current feature branch
vs its **parent base branch** + the story it implements).

**First action — invoke the skill:**

```
Skill(skill: "qa-phase")
```

Then execute it faithfully per its `SKILL.md`, in order, **stopping only at the single ship gate**:

Preflight (deps + project `qa-phase.config` kit, fail-loud) → **Phase A** (A1 spec-gap/grill · A2
QA-session API+UI+E2E · A3 chaos · A4 prove-beyond-tests eli5 live scenarios; each karpathy→cove →
collect) → **pooled design-first fix loop** (codebase-design → design-tests RED → universal expert
GREEN → verify, ≤2 rounds, bugfix-TDD) → **fast-verify** (`verification-phase --fast`) → **evidence**
(`verification-before-completion`) → **Phase B** (draft PR + preview AC) → **⏸ ONE gate**
(Ship / Hold / Fix-more) → **Phase C** ship (sprint/deferral sync + finish branch), post-approval only.

`$ARGUMENTS` carries the scope and any flags — e.g. `spec_gap_mode=grill` runs the **live
grill-with-docs interview** (`grilling` + `domain-modeling`) at A1 instead of the hands-off gap
analysis.

> **Enforced/parallel variant (optional):** if a `qa-phase.js` Workflow is present, this command may
> instead invoke it — multi-agent fan-out (parallel lenses + worktree-isolated fixes) plus a
> throwing "every-lens-provably-ran" gate, mirroring `verification-phase`'s Workflow. **Not required**
> to run qa-phase; the skill executes fine sequentially without it.
