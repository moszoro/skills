# skills

> Maciej Moszoro's personal Claude Code skills — **one source of truth.**

Edit a skill once, here; every consumer (your local `~/.claude`, the
[nightshift](https://github.com/moszoro/nightshift) loop image, any teammate) pulls the same
version. No scattered copies to drift.

## What's here

| path | kind | what it does |
|------|------|--------------|
| `skills/verification-phase/` | skill | Layered code-verification gauntlet (preflight → test-quality → smells → security → docs-best-practices → project-rules), karpathy-filtered, cove-escalated, auto-applies survivors. |
| `skills/cove/` | skill | Chain-of-Verification — separate generation from verification to cut hallucinations. Implements Meta AI's [CoVe](https://arxiv.org/abs/2309.11495) technique. |
| `skills/eli5/` | skill | Explain any concept in layered simplicity, 5-year-old → adult, with analogies. |
| `commands/evals/` | command | `evals:eval-tests` — post-implementation test-quality gate scoring uncommitted tests against 22 criteria. |

## Install

**Whole collection (bare, so bare-name calls like `Invoke cove` / `evals:eval-tests` resolve):**

```bash
git clone --depth 1 https://github.com/moszoro/skills /tmp/mm-skills
cp -R /tmp/mm-skills/skills/*   ~/.claude/skills/
cp -R /tmp/mm-skills/commands/* ~/.claude/commands/
rm -rf /tmp/mm-skills
```

**Edit-in-place (this repo stays the source of truth):** clone once, then symlink into `~/.claude`:

```bash
git clone https://github.com/moszoro/skills ~/Projects/skills
for s in verification-phase cove eli5; do
  ln -sfn ~/Projects/skills/skills/$s ~/.claude/skills/$s
done
ln -sfn ~/Projects/skills/commands/evals ~/.claude/commands/evals
```

Now editing `~/.claude/skills/cove/SKILL.md` edits the repo working tree — `git commit && git push` and it's live everywhere.

## Credits

`cove` implements Meta AI's **Chain-of-Verification** (Dhuliawala et al., 2023). The skill wrapper is
mine; the technique is theirs.

MIT © Maciej Moszoro
