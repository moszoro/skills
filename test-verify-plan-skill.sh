#!/usr/bin/env bash
# Artifact-contract test for the dual-use `verify-plan` skill (ticket moszoro/nightshift#37).
# The skill BODY is prose, so we assert its DECLARED contract (params + the fixed 5-step gauntlet +
# how the two flags rebind behaviour), NOT runtime prose. Pure grep-contract harness — mirrors
# nightshift/test-skills-install.sh. bash-3.2 safe. The lockstep half (skills.tsv row <-> Dockerfile
# install line) lives in nightshift/test-verify-plan-lockstep.sh — this file owns tests 3-6.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$HERE/skills/verify-plan/SKILL.md"
pass=0; fail=0
ok()  { pass=$((pass+1)); }
bad() { echo "FAIL: $1"; fail=$((fail+1)); }

[ -f "$SKILL" ] || { echo "FAIL: skills/verify-plan/SKILL.md missing"; exit 1; }

# ── test_skill_declares_source_and_interactive_params (T1) ──────────────────────────────────────
# The skill declares `source` (spec|issue, default spec) and `interactive` (true|false, default true).
# Canonical declaration form: "<param> — <default-value> (default) | <alt-value>" (one line), which
# also pins WHICH value is the default.
grep -Eiq 'source[^\n]*spec[^\n]*default[^\n]*issue' "$SKILL" \
  && ok || bad "P1 skill must declare the source param: spec (DEFAULT) | issue"
grep -Eiq 'interactive[^\n]*true[^\n]*default[^\n]*false' "$SKILL" \
  && ok || bad "P2 skill must declare the interactive param: true (DEFAULT) | false"

# ── test_skill_five_steps_in_order (T1) ─────────────────────────────────────────────────────────
# The 5 steps appear in FIXED order:
#   code-reviewer -> Explore -> grill-with-docs -> nightshift-plan-skills -> evals:eval-tests
# Anchor on the numbered "### Step N" HEADINGS (not the frontmatter, which lists all five on one line).
ln_cr="$(grep -nE '^#+ *Step[^\n]*code-reviewer'          "$SKILL" | head -1 | cut -d: -f1)"
ln_ex="$(grep -nE '^#+ *Step[^\n]*Explore'                "$SKILL" | head -1 | cut -d: -f1)"
ln_gr="$(grep -nE '^#+ *Step[^\n]*grill-with-docs'        "$SKILL" | head -1 | cut -d: -f1)"
ln_ps="$(grep -nE '^#+ *Step[^\n]*nightshift-plan-skills' "$SKILL" | head -1 | cut -d: -f1)"
ln_ev="$(grep -nE '^#+ *Step[^\n]*evals:eval-tests'       "$SKILL" | head -1 | cut -d: -f1)"
for pair in "cr:$ln_cr" "ex:$ln_ex" "gr:$ln_gr" "ps:$ln_ps" "ev:$ln_ev"; do
  n="${pair##*:}"; k="${pair%%:*}"
  [ -n "$n" ] || bad "S-token $k step reference missing from the skill"
done
{ [ -n "$ln_cr" ] && [ -n "$ln_ex" ] && [ -n "$ln_gr" ] && [ -n "$ln_ps" ] && [ -n "$ln_ev" ] \
  && [ "$ln_cr" -lt "$ln_ex" ] && [ "$ln_ex" -lt "$ln_gr" ] \
  && [ "$ln_gr" -lt "$ln_ps" ] && [ "$ln_ps" -lt "$ln_ev" ]; } \
  && ok || bad "S-order steps must be code-reviewer($ln_cr) < Explore($ln_ex) < grill-with-docs($ln_gr) < nightshift-plan-skills($ln_ps) < evals:eval-tests($ln_ev)"

# ── test_interactive_false_governs_step3_only (T2) ──────────────────────────────────────────────
# interactive=false -> step 3 becomes an AFK self-grill; steps 1,2,4,5 unaffected by the flag.
# Assert the step-3 (grill) region names BOTH branches, and no OTHER step branches on `interactive`.
grep -Eiq 'interactive[^\n]*false[^\n]*self-grill|self-grill[^\n]*interactive[^\n]*false|AFK[^\n]*self-grill' "$SKILL" \
  && ok || bad "I1 step 3 must define interactive=false => AFK self-grill"
grep -Eiq 'interactive[^\n]*true[^\n]*(live|human)|(live|human)[^\n]*grill' "$SKILL" \
  && ok || bad "I2 step 3 must define interactive=true => live human grill"
# The flag must be scoped to step 3 only: an explicit "step 3 only" / "governs step 3" statement.
grep -Eiq 'interactive[^\n]*(governs|affects|scoped|only)[^\n]*step[^\n]*3|step[^\n]*3[^\n]*only|only[^\n]*step[^\n]*3' "$SKILL" \
  && ok || bad "I3 skill must state interactive governs STEP 3 ONLY (steps 1,2,4,5 unaffected)"

# ── test_source_issue_rebinds_target (T1) ───────────────────────────────────────────────────────
# source=issue rebinds the review target to the issue (vs the default spec).
grep -Eiq 'source[^\n]*issue[^\n]*(target|review|rebind|the issue)|issue[^\n]*(review target|target)' "$SKILL" \
  && ok || bad "R1 skill must state source=issue rebinds the review target to the issue"
grep -Eiq 'source[^\n]*spec[^\n]*(target|default|review)|default[^\n]*spec[^\n]*target|spec[^\n]*(the default|default)' "$SKILL" \
  && ok || bad "R2 skill must state source=spec (default) is the default review target"

echo "verify-plan-skill: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
