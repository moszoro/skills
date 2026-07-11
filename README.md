# skills

> Maciej Moszoro's personal Claude Code skills — **one source of truth.**

Edit a skill once, here; every consumer (your local `~/.claude`, CI images, teammates) pulls the
same version. No scattered copies to drift.

## What's here

| path | kind | what it does |
|------|------|--------------|
| `skills/verification-phase/` | skill | Layered code-verification gauntlet (preflight → test-quality → smells → security → docs-best-practices → project-rules), karpathy-filtered, cove-escalated, auto-applies survivors. Supports `--fast` (code-review + context7 + eval-tests). |
| `skills/qa-phase/` | skill | Autonomous **acceptance-and-ship** QA gauntlet — spec-gap/grill → API+UI+E2E QA-session → chaos → prove-beyond-tests → design-first fix loop → fast-verify → evidence → draft PR + preview AC → **one ship gate** → ship. Dynamic-proof sibling to verification-phase. |
| `skills/cove/` | skill | Chain-of-Verification — separate generation from verification to cut hallucinations. Implements Meta AI's [CoVe](https://arxiv.org/abs/2309.11495) technique. |
| `skills/eli5/` | skill | Explain any concept in layered simplicity, 5-year-old → adult, with analogies. |
| `commands/evals/` | command | `evals:eval-tests` — post-implementation test-quality gate scoring uncommitted tests against 22 criteria. |
| `commands/qa-phase.md` | command | `/qa-phase [scope]` — entrypoint that runs the `qa-phase` skill (add `spec_gap_mode=grill` for the live grill-with-docs interview). |

## Install

**Full setup (recommended) — `verification-phase` needs more than the skills** (see [Dependencies](#dependencies)). One command installs the skills, the `evals` command, *and* every external dependency:

```bash
curl -fsSL https://raw.githubusercontent.com/moszoro/skills/main/install.sh | bash
```

**Skills only (quick)** — the three skills, bare, via the [`skills`](https://github.com/vercel-labs/skills) CLI (does **not** install the `evals` command or `verification-phase`'s external deps):

```bash
npx skills add moszoro/skills --global
```

**Edit-in-place (this repo stays the source of truth)** — clone once, then symlink into `~/.claude`:

```bash
git clone https://github.com/moszoro/skills ~/Projects/skills
for s in verification-phase qa-phase cove eli5; do
  ln -sfn ~/Projects/skills/skills/$s ~/.claude/skills/$s
done
ln -sfn ~/Projects/skills/commands/evals ~/.claude/commands/evals
ln -sfn ~/Projects/skills/commands/qa-phase.md ~/.claude/commands/qa-phase.md
```

Now editing `~/.claude/skills/cove/SKILL.md` edits the repo working tree — `git commit && git push` and it's live everywhere.

## Dependencies

`verification-phase` and `qa-phase` are gauntlets that orchestrate other skills — their Preflight fails
loud unless all deps resolve. `install.sh` installs the verification-phase set; `npx skills add` does **not**:

| dependency | source | provided by |
|---|---|---|
| `cove`, `evals:eval-tests` | this repo | `install.sh` (command needs a copy — it's not a skill) |
| `fullstack-dev-skills:code-reviewer` / `security-reviewer` | `jeffallan/claude-skills` marketplace | `install.sh` step 3 |
| `andrej-karpathy-skills:karpathy-guidelines` | `forrestchang/andrej-karpathy-skills` marketplace | `install.sh` step 3 |
| context7 MCP | `@upstash/context7-mcp` | `install.sh` step 4 (needs `CONTEXT7_API_KEY`) |

**`qa-phase`** additionally orchestrates (its Preflight lists them, fail-loud): `grilling` +
`domain-modeling` (A1 grill), `design-tests` + `codebase-design` (fix loop), `fullstack-dev-skills:`
`{test-master, playwright-expert, chaos-engineer, + the full *-expert set for GREEN}`,
`superpowers:{verification-before-completion, finishing-a-development-branch}`, `verification-phase`
(for `--fast`), `eli5`, plus `gh` + a Playwright runner. It **prefers project-native skills** (e.g.
Aura's `bmad-*`) via a per-project `.claude/qa-phase.config.toml`, falling back to the generic ones.

`cove` and `eli5` are standalone — `npx skills add` is enough for those.

## Credits

`cove` implements Meta AI's **Chain-of-Verification** (Dhuliawala et al., 2023). The skill wrapper is
mine; the technique is theirs.

MIT © Maciej Moszoro
