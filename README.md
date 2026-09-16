# skills

> Maciej Moszoro's personal Claude Code skills — kept in one place.

Each skill lives here once. Your laptop, your CI images, and your teammates all install from this
repo, so nobody ends up with a stale copy.

New to skills? A **skill** teaches Claude Code a repeatable job. You turn one on by typing its name,
like `/qa-phase`. A **command** is a shorter shortcut that runs a skill for you.

## What's inside

### Ship better code

| Skill | What it does for you |
|-------|----------------------|
| `verification-phase` | Runs your finished code past a stack of reviewers — test quality, code smells, security holes, docs, your own project rules. It keeps only the findings that matter and applies the safe fixes for you. Add `--fast` for a quick pass. |
| `qa-phase` | Hands-off QA before you ship. It hunts for gaps against the spec, writes and runs API + UI + end-to-end tests, tries hard to break the code, fixes what it finds, and opens a draft pull request. Then it stops **once** and asks you: ship, hold, or fix more. |
| `verify-plan` | Checks a build-ready plan **before** anyone writes the code. It compares the plan to the spec or ticket, greps your real repo to catch drift, and flags weak tests — while a fix is still a cheap edit. |
| `verify-spec` | Checks a design or spec **before** it turns into a plan. It finds missing decisions and gaps, and backs every note with a real `file:line` from your code, not a guess. |
| `design-tests` | Helps you write good **failing** tests first (TDD). Real hand-computed expected values, clear Given/When/Then, and a check that each test actually proves something. |

### Everyday helpers

| Skill | What it does for you |
|-------|----------------------|
| `cove` | Cuts made-up answers by splitting "write it" from "check it." Based on Meta AI's [Chain-of-Verification](https://arxiv.org/abs/2309.11495). |
| `eli5` | Explains anything in plain steps — 5-year-old simple up to expert — with analogies. |

### Standalone tools

| Skill | What it does for you |
|-------|----------------------|
| `pixel-perfect-svg` | Turns a PNG or screenshot into a clean SVG. It snaps colours, traces each shape (keeps the holes in letters), removes speckles, and drops the background. Ships with a ready-to-run CLI. |
| `watch-reel` | Lets Claude actually watch an Instagram reel. It downloads the video, grabs a frame per scene, and transcribes the audio — then answers about what is **shown** and **said**. Ships with a CLI. |

### Commands (shortcuts)

| Command | What it does |
|---------|--------------|
| `evals:eval-tests` | Scores your just-written tests against 22 quality checks. |
| `/qa-phase [scope]` | Runs the `qa-phase` skill. Add `spec_gap_mode=grill` for a live question-and-answer gap hunt. |

## Install

Pick one:

**1. Full setup (recommended).** `verification-phase` and `qa-phase` need a few extra tools (see
[What some skills need](#what-some-skills-need)). This one command installs the skills, the `evals`
command, **and** those extra tools:

```bash
curl -fsSL https://raw.githubusercontent.com/moszoro/skills/main/install.sh | bash
```

**2. Skills only (quick).** The skills, bare, via the [`skills`](https://github.com/vercel-labs/skills)
CLI. This does **not** install the `evals` command or the extra tools the big review skills need:

```bash
npx skills add moszoro/skills --global
```

**3. Edit-in-place.** Clone once, then link the skills into `~/.claude`. Now editing a skill here also
edits the live copy — `git commit && git push` and it is live everywhere:

```bash
git clone https://github.com/moszoro/skills ~/Projects/skills
for s in verification-phase qa-phase verify-plan verify-spec design-tests cove eli5 pixel-perfect-svg watch-reel; do
  ln -sfn ~/Projects/skills/skills/$s ~/.claude/skills/$s
done
ln -sfn ~/Projects/skills/commands/evals ~/.claude/commands/evals
ln -sfn ~/Projects/skills/commands/qa-phase.md ~/.claude/commands/qa-phase.md
```

## What some skills need

Most skills work on their own. Two big ones call other skills and tools. They check everything is
present at startup and stop with a clear message if a piece is missing.

**`verification-phase` and `qa-phase`** need these. `install.sh` sets them all up; `npx skills add`
does not:

| Needs | Where it comes from | Installed by |
|-------|---------------------|--------------|
| `cove`, `evals:eval-tests` | this repo | `install.sh` (the command needs its own copy — it is not a skill) |
| `fullstack-dev-skills:code-reviewer` / `security-reviewer` | `jeffallan/claude-skills` marketplace | `install.sh` step 3 |
| `andrej-karpathy-skills:karpathy-guidelines` | `forrestchang/andrej-karpathy-skills` marketplace | `install.sh` step 3 |
| context7 MCP | `@upstash/context7-mcp` | `install.sh` step 4 (needs `CONTEXT7_API_KEY`) |

**`qa-phase`** also calls: `grilling` + `domain-modeling` (gap hunt), `design-tests` +
`codebase-design` (fix loop), several `fullstack-dev-skills` experts (test-master, playwright-expert,
chaos-engineer, and the full `*-expert` set for writing fixes), `superpowers` (finish-a-branch,
verify-before-done), `verification-phase`, `eli5`, plus `gh` and a Playwright runner. If your project
has its own native versions (for example a `bmad-*` set), it uses those first — point it at them with a
`.claude/qa-phase.config.toml` file.

**`watch-reel`** needs three tools on your `PATH` — `gallery-dl`, `mlx-whisper` (Apple silicon), and
`ffmpeg` — plus a Chrome you are logged in to (it reads your cookies to download the reel).

## Credits

`cove` is my wrapper around Meta AI's **Chain-of-Verification** (Dhuliawala et al., 2023). The
technique is theirs; the skill is mine.

MIT © Maciej Moszoro
