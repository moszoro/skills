#!/usr/bin/env bash
# Frontmatter-validity test for every skill in this repo.
#
# Why this exists: a SKILL.md whose `description:` is an UNQUOTED YAML scalar containing ": "
# (colon-space) is not valid YAML — the parser reads it as a nested mapping and errors with
# "mapping values are not allowed here". The file still LOOKS fine, still has a name and a
# description, and still installs by `cp` — but every frontmatter-parsing consumer drops it:
#
#   $ npx skills add moszoro/skills/verify-plan
#   No valid skills found. Skills require a SKILL.md with name and description.
#
# That is how verify-plan and verify-spec silently went missing from `npx skills add
# moszoro/skills` (7 of 9 installed) while nightshift's skills.tsv declared verify-plan as an
# image dependency. Fixed by quoting; this test stops it coming back.
#
# Pure-grep harness, bash-3.2 safe — mirrors test-verify-plan-skill.sh.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
pass=0; fail=0
ok()  { pass=$((pass+1)); }
bad() { echo "FAIL: $1"; fail=$((fail+1)); }

found=0
for skill in "$HERE"/skills/*/SKILL.md; do
  [ -f "$skill" ] || continue
  found=$((found+1))
  name="$(basename "$(dirname "$skill")")"

  # Frontmatter is the block between the first two `---` lines.
  fm="$(awk 'NR==1 && $0=="---" {inside=1; next} inside && $0=="---" {exit} inside {print}' "$skill")"

  # ── test_skill_declares_name_and_description (T1) ────────────────────────────────────────────
  printf '%s\n' "$fm" | grep -Eq '^name:[[:space:]]*[^[:space:]]' \
    && ok || bad "$name: frontmatter must declare a non-empty name"
  printf '%s\n' "$fm" | grep -Eq '^description:[[:space:]]*[^[:space:]]' \
    && ok || bad "$name: frontmatter must declare a non-empty description"

  # ── test_description_is_valid_yaml_scalar (T1) ───────────────────────────────────────────────
  # A plain (unquoted) YAML scalar may not contain ": ". Quoted scalars may contain anything.
  desc="$(printf '%s\n' "$fm" | grep -E '^description:' | head -1 | sed -E 's/^description:[[:space:]]*//')"
  case "$desc" in
    \'*|\"*) ok ;;                                  # quoted — any content is safe
    *": "*)  bad "$name: unquoted description contains \": \" — invalid YAML, the skill will be silently skipped by every frontmatter parser. Quote the value." ;;
    *)       ok ;;
  esac
done

[ "$found" -gt 0 ] && ok || bad "no skills/*/SKILL.md found — is this the repo root?"

echo "frontmatter: $found skill(s), $pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
