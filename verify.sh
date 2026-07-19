#!/bin/bash
# ==============================================================================
# Ultimate Memory Stack v4.0.0 — post-install verification
# Apache-2.0 © 2026 esoteric1entity. A PDuk Brainworks project.
# ==============================================================================
#
# Validates a UMS *install* — scaffold, registration, profile, logs — using its
# own [T1]–[T7] structural checks. These are a DIFFERENT namespace from the
# protocol's T1–T9 entry-level self-test (common-specs/MEMORY_PROTOCOL.md §1.3),
# which the agent runs each session over your memory entries; the shared "T#"
# prefix does NOT map 1:1. Run verify.sh after install.
#
# Usage:
#   ./verify.sh                 # verify install in current directory
#   ./verify.sh /path/to/dir    # verify install at explicit path
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKING_DIR="${1:-$(pwd)}"
EXIT_CODE=0

if [ ! -d "$WORKING_DIR" ]; then
    echo "❌ Working directory not found: $WORKING_DIR" >&2
    exit 1
fi

# Version: read from the VERSION file (#14 re-audit follow-on — was hardcoded,
# would lie after a bump). Prefer the installed scaffold's copy, then the
# package next to this script; fall back only if neither is present.
STACK_VERSION="4.0.0"
for _vf in "$WORKING_DIR/ultimate-memory-stack/VERSION" "$SCRIPT_DIR/VERSION"; do
    if [ -f "$_vf" ]; then STACK_VERSION="$(tr -d ' \r\n' < "$_vf")"; break; fi
done

echo "▶ Verifying Ultimate Memory Stack install at: $WORKING_DIR"
echo

# T1 — Required root files
check_file() {
    if [ -f "$WORKING_DIR/$1" ]; then
        echo "  ✓ $1"
    else
        echo "  ✗ MISSING: $1"
        EXIT_CODE=1
    fi
}

check_dir() {
    if [ -d "$WORKING_DIR/$1" ]; then
        echo "  ✓ $1/"
    else
        echo "  ✗ MISSING: $1/"
        EXIT_CODE=1
    fi
}

echo "[T1] Root files:"
check_file ".claude/rules/memory_protocol.md"

# Protocol CORE size guard — must stay under Claude Code's ~40,000-byte
# auto-load recommendation (the whole point of the CORE/EXTENDED split).
if [ -f "$WORKING_DIR/.claude/rules/memory_protocol.md" ]; then
    PROTOCOL_SIZE=$(wc -c < "$WORKING_DIR/.claude/rules/memory_protocol.md" 2>/dev/null || echo 0)
    if [ "$PROTOCOL_SIZE" -lt 40000 ]; then
        echo "  ✓ .claude/rules/memory_protocol.md is ${PROTOCOL_SIZE} bytes (< 40,000-byte auto-load recommendation)"
    else
        echo "  ✗ .claude/rules/memory_protocol.md is ${PROTOCOL_SIZE} bytes — exceeds the 40,000-byte auto-load recommendation"
        EXIT_CODE=1
    fi
fi

# Regression guard: the on-demand EXTENDED reference must NEVER land under
# .claude/rules/ — that would auto-load it every session and recreate the
# eager-load bug the CORE/EXTENDED split exists to fix.
if [ -d "$WORKING_DIR/.claude/rules" ]; then
    EXTENDED_IN_RULES=$(find "$WORKING_DIR/.claude/rules" -maxdepth 1 -iname "*EXTENDED*" 2>/dev/null | wc -l | tr -d ' ')
    if [ "${EXTENDED_IN_RULES:-0}" -eq 0 ]; then
        echo "  ✓ no EXTENDED protocol file under .claude/rules/ (correct — stays on-demand only)"
    else
        echo "  ✗ EXTENDED protocol file found under .claude/rules/ — recreates the eager-load bug; it belongs in memory/"
        EXIT_CODE=1
    fi
fi

echo
echo "[T2] Memory directory structure:"
check_dir "memory"
check_dir "memory/decisions"
check_dir "memory/feedback"
check_dir "memory/projects"
check_dir "memory/sessions"
check_dir "memory/user"
check_dir "memory/security"
check_dir "memory/references"
check_dir "memory/archive"
check_dir "memory/quarantine"
check_file "memory/MEMORY_PROTOCOL_EXTENDED.md"

# Hot/cold tiering (v4.0.0): existence-only — behavioral/aging checks are
# lint_runner.py's job (SCHEMA_lint.md §13 ownership split), not verify.sh's.
check_file "memory/archive/sessions/ARCHIVE_INDEX.md"
check_file "memory/archive/decisions/ARCHIVE_INDEX.md"
check_file "memory/archive/feedback/ARCHIVE_INDEX.md"

echo
echo "[T3] Edition profile:"
PROFILE_PATH=""
for candidate in \
    "$WORKING_DIR/ultimate-memory-stack/general-edition/PROFILE.md" \
    "$WORKING_DIR/memory/PROFILE.md"; do
    if [ -f "$candidate" ]; then
        PROFILE_PATH="$candidate"
        break
    fi
done
PRESET="unknown"
if [ -n "$PROFILE_PATH" ]; then
    EDITION=$(grep -E "^edition:" "$PROFILE_PATH" 2>/dev/null | head -1 | sed 's/edition: *//; s/#.*$//; s/ *$//' || echo "unknown")
    PRESET=$(grep -E "^compliance:" "$PROFILE_PATH" 2>/dev/null | head -1 | sed 's/compliance: *//; s/#.*$//; s/ *$//' || echo "unknown")
    echo "  ✓ PROFILE.md at ${PROFILE_PATH#$WORKING_DIR/}"
    echo "    edition:    ${EDITION:-(unset)}"
    echo "    compliance: ${PRESET:-(unset)} (shipped default)"
    if grep -q "REGENERABLE" "$PROFILE_PATH" 2>/dev/null; then
        echo "  ✓ PROFILE.md header marks itself regenerable (v4.0.0 overrides pattern)"
    else
        echo "  ℹ️  PROFILE.md header does not mark itself regenerable — pre-v4.0.0 package or a stale copy"
    fi

    # USER_OVERRIDES.md (v4.0.0): absence is normal for Door-4 manual installs,
    # so this is informational only — it never sets EXIT_CODE.
    OVERRIDES_PATH="$WORKING_DIR/memory/user/USER_OVERRIDES.md"
    if [ -f "$OVERRIDES_PATH" ]; then
        OV_PRESET=$(grep -E "^compliance:" "$OVERRIDES_PATH" 2>/dev/null | head -1 | sed 's/compliance: *//; s/#.*$//; s/ *$//')
        echo "  ✓ USER_OVERRIDES.md present at memory/user/USER_OVERRIDES.md"
        if [ -n "$OV_PRESET" ]; then
            echo "    compliance override: ${OV_PRESET} (active value — wins over PROFILE.md's ${PRESET:-unknown})"
            # Adversarial-round finding (2026-07-14): downstream checks (e.g. [T4])
            # branch on $PRESET — leaving it at PROFILE.md's shipped default made
            # [T4] permanently report "opt-in, skipped" for any non-default-preset
            # install, even one with a real, populated audit_log.jsonl. The
            # override, when present, IS the active value.
            PRESET="$OV_PRESET"
        fi
    else
        echo "  ℹ️  USER_OVERRIDES.md absent — PROFILE.md defaults apply directly (normal for Door-4 manual installs)"
    fi
else
    echo "  ✗ MISSING: PROFILE.md (looked in ultimate-memory-stack/<edition>-edition/ and memory/)"
    EXIT_CODE=1
fi

echo
echo "[T4] Audit + quarantine logs (preset-dependent):"
if [ "$PRESET" = "none" ]; then
    echo "  ✓ skipped — audit + quarantine logs are OPT-IN for compliance=none"
else
    check_file "memory/security/audit_log.jsonl"
    check_file "memory/quarantine/quarantine_log.jsonl"
fi

echo
echo "[T5] Common-specs reachable:"
COMMON_SPECS=""
for candidate in \
    "$WORKING_DIR/ultimate-memory-stack/common-specs" \
    "$WORKING_DIR/memory/common-specs" \
    "$SCRIPT_DIR/common-specs"; do
    if [ -d "$candidate" ]; then
        COMMON_SPECS="$candidate"
        break
    fi
done
if [ -d "$COMMON_SPECS" ]; then
    echo "  ✓ common-specs/ at $COMMON_SPECS"
    for f in MEMORY_PROTOCOL.md MEMORY_PROTOCOL_EXTENDED.md ARCHITECTURE.md SCHEMA_A18_per_entry_metadata.md; do
        if [ -f "$COMMON_SPECS/$f" ]; then
            echo "  ✓ common-specs/$f"
        else
            echo "  ✗ MISSING: common-specs/$f"
            EXIT_CODE=1
        fi
    done
else
    echo "  ✗ common-specs/ not found"
    EXIT_CODE=1
fi

echo
echo "[T6] Registered Skills (Claude Code discoverability):"
# A skill is DISCOVERABLE only as .claude/skills/<name>/SKILL.md with the
# directory name matching the frontmatter `name:` (#12 fix, 2026-06-11 —
# this check previously counted flat install-*.md files, which Claude Code
# never discovers, so T6 passed on a broken registration).
if [ -d "$WORKING_DIR/.claude/skills" ]; then
    T6_OK=0
    T6_BAD=0
    while IFS= read -r skill_file; do
        dir_name="$(basename "$(dirname "$skill_file")")"
        fm_name="$(sed -n 's/^name:[[:space:]]*//p' "$skill_file" | head -1 | tr -d '\r')"
        if [ "$dir_name" = "$fm_name" ] && [ -n "$fm_name" ]; then
            T6_OK=$((T6_OK+1))
        else
            echo "  ✗ $skill_file: dir '$dir_name' != frontmatter name '$fm_name' (not discoverable)"
            T6_BAD=$((T6_BAD+1))
        fi
    done < <(find "$WORKING_DIR/.claude/skills" -mindepth 2 -maxdepth 2 -name "SKILL.md" -type f 2>/dev/null)
    FLAT_COUNT=$(find "$WORKING_DIR/.claude/skills" -maxdepth 1 -name "*.md" -type f 2>/dev/null | wc -l)
    if [ "$FLAT_COUNT" -gt 0 ]; then
        echo "  ✗ $FLAT_COUNT flat .md file(s) directly under .claude/skills/ — Claude Code does not discover these"
        T6_BAD=$((T6_BAD+1))
    fi
    if [ "$T6_BAD" -gt 0 ]; then
        EXIT_CODE=1
    elif [ "$T6_OK" -gt 0 ]; then
        echo "  ✓ $T6_OK skill(s) discoverable as .claude/skills/<name>/SKILL.md"
    else
        echo "  ⚠ no skills registered (minimal install, or addons skipped)"
    fi
else
    echo "  ⚠ .claude/skills/ not present (Claude Code may not be initialized in this directory)"
fi

echo
echo "[T7] Bootstrap-prompt sanity:"
if [ -f "$COMMON_SPECS/BOOTSTRAP_PROMPT.md" ]; then
    BOOT_SIZE=$(wc -c < "$COMMON_SPECS/BOOTSTRAP_PROMPT.md" 2>/dev/null || echo 0)
    echo "  ✓ BOOTSTRAP_PROMPT.md ($BOOT_SIZE bytes)"
else
    echo "  ✗ MISSING: common-specs/BOOTSTRAP_PROMPT.md"
    EXIT_CODE=1
fi

# T8 — Manifest ↔ registered-skills cross-check (informational, WARN-only —
# never touches EXIT_CODE). .ums-manifest.json is written only by the
# setup-memory-stack.sh wrapper (Door 2/4 installs don't write one — its
# absence is not itself a finding). Deliberately small by design: no manifest
# file-list is invented, and the manifest is never
# made load-bearing — this only checks its addons array against what [T6]
# would consider a registered skill. lint_runner.py's job (SCHEMA_lint.md §13
# ownership split) owns behavioral/aging checks; this stays existence-adjacent.
MANIFEST_FILE="$WORKING_DIR/.ums-manifest.json"
if [ -f "$MANIFEST_FILE" ]; then
    echo
    echo "[T8] Manifest addons ↔ registered skills (informational):"
    # The addons array is written on ONE line by the wrapper's heredoc
    # (verified in setup-memory-stack.sh) — grep/sed extraction, no jq
    # dependency. Every extraction below is `set -e`-guarded: an empty or
    # malformed manifest must never abort the whole verifier.
    ADDONS_LINE="$(grep -o '"addons"[[:space:]]*:[[:space:]]*\[[^]]*\]' "$MANIFEST_FILE" 2>/dev/null || true)"
    MANIFEST_ADDONS=()
    if [ -n "$ADDONS_LINE" ]; then
        while IFS= read -r addon; do
            [ -n "$addon" ] && MANIFEST_ADDONS+=("$addon")
        done < <(echo "$ADDONS_LINE" | grep -o '"[^"]*"' 2>/dev/null | sed '1d' | tr -d '"' || true)
    fi
    if [ "${#MANIFEST_ADDONS[@]}" -eq 0 ]; then
        echo "  ✓ 0 addon(s) listed in manifest"
    else
        for addon in "${MANIFEST_ADDONS[@]}"; do
            SHORT="${addon#memory-}"
            MATCHED=0
            if [ -d "$WORKING_DIR/.claude/skills" ]; then
                while IFS= read -r skill_dir; do
                    case "$(basename "$skill_dir")" in
                        *"$SHORT"*) MATCHED=1 ;;
                    esac
                done < <(find "$WORKING_DIR/.claude/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null || true)
            fi
            if [ "$MATCHED" -eq 1 ]; then
                echo "  ✓ $addon → matching skill found"
            else
                echo "  ⚠ $addon: listed in manifest but no matching registered skill found (informational — does not fail verify)"
            fi
        done
    fi
fi

echo
echo "──────────────────────────────────────────────────"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✅ All checks passed — Ultimate Memory Stack v${STACK_VERSION} install is valid."
else
    echo "⚠ Some checks failed. See ✗ markers above."
    echo "  Re-run ./setup-memory-stack.sh or invoke /install-ultimate-memory-stack to repair."
fi
echo "──────────────────────────────────────────────────"
exit $EXIT_CODE
