#!/usr/bin/env bash
# One-command setup for moszoro/skills — installs EVERYTHING the gauntlet needs, not just the skills.
#
#   curl -fsSL https://raw.githubusercontent.com/moszoro/skills/main/install.sh | bash
#
# `npx skills add moszoro/skills` alone installs the 3 skills but NOT the evals COMMAND, NOT the
# external plugins verification-phase's preflight requires. This script closes that gap:
#   1. the 3 skills (verification-phase, cove, eli5)          — bare, so bare-name calls resolve
#   2. the evals:eval-tests COMMAND                           — a command, not a skill; copied directly
#   3. verification-phase's HARD deps: fullstack-dev-skills, andrej-karpathy-skills  — marketplaces
#   4. the context7 MCP (best-practices lens)                 — needs CONTEXT7_API_KEY
# Idempotent: re-run anytime. Uses --global / --scope user (your ~/.claude), touches nothing else.
set -euo pipefail
REPO="https://github.com/moszoro/skills"
say() { printf '\n\033[1m==> %s\033[0m\n' "$1"; }

command -v claude >/dev/null || { echo "FATAL: 'claude' CLI not found — install Claude Code first."; exit 1; }

say "1/4  skills (verification-phase, cove, eli5) — bare into ~/.claude/skills"
npx -y skills@latest add moszoro/skills --global -y

say "2/4  evals:eval-tests command → ~/.claude/commands"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
git clone --depth 1 "$REPO" "$TMP" >/dev/null 2>&1
mkdir -p "$HOME/.claude/commands"
cp -R "$TMP/commands/." "$HOME/.claude/commands/"

say "3/4  verification-phase's external plugins (fullstack-dev-skills, andrej-karpathy-skills)"
claude plugin marketplace add jeffallan/claude-skills            >/dev/null 2>&1 || true
claude plugin marketplace add forrestchang/andrej-karpathy-skills >/dev/null 2>&1 || true
claude plugin install fullstack-dev-skills@fullstack-dev-skills  --scope user || true
claude plugin install andrej-karpathy-skills@karpathy-skills     --scope user || true

say "4/4  context7 MCP (docs-grounded best-practices lens)"
if [ -n "${CONTEXT7_API_KEY:-}" ]; then
  claude mcp add --scope user plugin_context7_context7 -- \
    npx -y @upstash/context7-mcp --api-key "$CONTEXT7_API_KEY" || true
  echo "  ✓ context7 MCP added"
else
  echo "  · CONTEXT7_API_KEY not set — skipping. Export it and re-run to enable the context7 lens."
fi

say "done — verification-phase and its dependencies are installed."
echo "verify with: /verification-phase  (its Preflight will confirm every dep resolves)"
