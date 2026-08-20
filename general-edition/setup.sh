#!/bin/bash
# Ultimate Memory Stack — General-Edition Setup Script (Linux/Mac/WSL)
# Version: 1.1 — 2026-06-16
# Tier: T2+ (requires Bash; HMAC keys at T3+ via Python/Code Execution)
# Author: see /AUTHORS.md
# License: Apache-2.0

set -e

# ============================================================
# CONFIGURATION
# ============================================================

EDITION="general"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Version is single-sourced from the package-root VERSION file (#14 fix);
# falls back for a general-edition dir copied standalone.
if [ -f "${SCRIPT_DIR}/../VERSION" ]; then
    STACK_VERSION="$(tr -d ' \r\n' < "${SCRIPT_DIR}/../VERSION")"
else
    STACK_VERSION="4.0.1"
fi
COMMON_SPECS_DIR="${SCRIPT_DIR}/../common-specs"
WORKING_DIR="${WORKING_DIR:-$(pwd)}"

# Default compliance preset (user can change at bootstrap or later)
COMPLIANCE_PRESET="${COMPLIANCE_PRESET:-none}"
EXTENSIONS="${EXTENSIONS:-}"

# ============================================================
# ARG PARSING
# ============================================================

MODE="fresh-install"
SKIP_WIZARD=false
MIGRATE_FROM=""
BACKUP_LOCATION=""
VERIFY_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --compliance=*)
            COMPLIANCE_PRESET="${1#*=}"
            ;;
        --extensions=*)
            EXTENSIONS="${1#*=}"
            ;;
        --migrate-from=*)
            MODE="migrate"
            MIGRATE_FROM="${1#*=}"
            ;;
        --backup-location=*)
            BACKUP_LOCATION="${1#*=}"
            ;;
        --change-preset=*)
            MODE="change-preset"
            COMPLIANCE_PRESET="${1#*=}"
            ;;
        --verify)
            VERIFY_ONLY=true
            ;;
        --status)
            VERIFY_ONLY=true
            MODE="status"
            ;;
        --skip-wizard)
            SKIP_WIZARD=true
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --help)
            echo "Ultimate Memory Stack — General-Edition Setup"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh                                       # Fresh install with wizard"
            echo "  ./setup.sh --compliance=none                     # Fresh install with compliance preset"
            echo "  ./setup.sh --compliance=enterprise --extensions=soc2,gdpr"
            echo "  ./setup.sh --migrate-from=v2.0                   # Migrate from v2.0"
            echo "  ./setup.sh --migrate-from=v3.6                   # Migrate from v3.6.x to v4.0.0"
            echo "  ./setup.sh --migrate-from=v3.6 --dry-run         # Preview the v3.6→v4.0.0 migration, no writes"
            echo "  ./setup.sh --change-preset=enterprise            # Change preset on existing deploy"
            echo "  ./setup.sh --verify                              # Run self-test"
            echo "  ./setup.sh --status                              # Show current state"
            echo ""
            echo "Compliance presets: none | enterprise | custom   (PHI/healthcare not available in general-edition)"
            echo "Extensions: gdpr | soc2 | pci-dss (comma-separated)"
            echo ""
            echo "See INSTALL.md for details."
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Run --help for usage"
            exit 1
            ;;
    esac
    shift
done

# Validate compliance preset (PHI/healthcare is not available in general-edition — refuse here)
case "$COMPLIANCE_PRESET" in
    healthcare)
        echo "✗ ERROR: PHI/healthcare compliance is not available in this edition; 'healthcare' is a reserved preset value. Use 'enterprise' or 'custom'."
        echo "  The general-edition does not ship PHI/HIPAA compliance. See CONTRIBUTING.md."
        exit 1
        ;;
    none|enterprise|custom)
        ;;
    *)
        echo "✗ ERROR: Invalid compliance preset '$COMPLIANCE_PRESET'"
        echo "  Valid: none | enterprise | custom"
        exit 1
        ;;
esac

# Validate extensions (basic check)
if [ -n "$EXTENSIONS" ]; then
    IFS=',' read -ra EXT_ARRAY <<< "$EXTENSIONS"
    for ext in "${EXT_ARRAY[@]}"; do
        case "$ext" in
            gdpr|soc2|pci-dss)
                ;;
            healthcare)
                echo "✗ ERROR: the 'healthcare' extension (PHI) is not available in this edition; it is a reserved value."
                exit 1
                ;;
            *)
                echo "✗ ERROR: Invalid extension '$ext'"
                echo "  Valid: gdpr | soc2 | pci-dss"
                exit 1
                ;;
        esac
    done
fi

# Validate --migrate-from (v4.0.0: v2.0's existing behavior is unchanged;
# v3.6 is the new v3.6.x → v4.0.0 entry point). Any other value used to
# silently set MODE=migrate with no validation at all — a typo like
# `--migrate-from=v36` would have run the v2.0 backup-and-delegate path
# against a vault it was never designed for.
if [ "$MODE" = "migrate" ]; then
    case "$MIGRATE_FROM" in
        v2.0|v3.6)
            ;;
        *)
            echo "✗ ERROR: Invalid --migrate-from value '${MIGRATE_FROM}'"
            echo "  Valid: v2.0 | v3.6"
            exit 1
            ;;
    esac
fi

# --dry-run is only meaningful for --migrate-from (both v2.0 and v3.6 now
# genuinely preview-only — step-8 adversarial round Finding 13 fixed v2.0's
# prior silent-no-op-that-wasn't); ignored for a fresh install so it can't
# silently change that behavior.
if [ "$DRY_RUN" = true ] && [ "$MODE" != "migrate" ]; then
    echo "⚠️  --dry-run only applies to --migrate-from; ignoring it here."
    DRY_RUN=false
fi

# Custom preset complexity floor — overrides/compliance.override.md is USER-AUTHORED
# and does not ship with the package (SCHEMA_compliance_profile §4.4); this gate is
# the documented footgun guard, NOT a check for the shipped compliance-presets file.
if [ "$COMPLIANCE_PRESET" = "custom" ]; then
    if [ ! -f "${SCRIPT_DIR}/overrides/compliance.override.md" ]; then
        echo "✗ ERROR: 'custom' preset requires overrides/compliance.override.md"
        echo "  The custom preset needs explicit configuration with ≥1 override — write that file first"
        echo "  (see overrides/compliance-presets.override.md §5.4 for the pattern),"
        echo "  or pick a base preset (none/enterprise) and add overrides."
        exit 1
    fi
fi

# ============================================================
# USER_OVERRIDES pattern (v4.0.0) — permanent fix for
# the 2026-06-15 data-loss debt. PROFILE.md is now regenerable; user config
# lives in memory/user/USER_OVERRIDES.md, created once and never rewritten.
# ============================================================

# Create memory/user/USER_OVERRIDES.md from the template if absent. NEVER
# write if present — not even to reformat it; user-owned from creation.
# Escape a value for safe use in a sed s/// REPLACEMENT field (not the pattern
# side). Unreachable today — every caller's value is pre-validated against a
# fixed enum (VALID_PRESETS) before it gets here — but sed's replacement-field
# `&` (means "the matched text") and `\` corrupt the file SILENTLY, even under
# `set -e`, if that ever changes. Escape backslash first, then `&`, then the
# delimiter this file's sed calls use (`/`).
_sed_escape_replacement() {
    printf '%s' "$1" | sed -e 's/[\&/]/\\&/g'
}

# Extract the fenced ```markdown ... ``` block from a doc-wrapped template file
# into dest_path. Fails loudly (exit 1, cleans up the partial file) if the
# closing fence is missing — a future template edit could otherwise ship
# trailing prose into every install's file silently. Shared by
# create_user_overrides and create_archive_indexes.
_extract_fenced_markdown_body() {
    local template_path="$1" dest_path="$2"
    if ! awk '/^```markdown$/{flag=1; next} /^```$/{if(flag){closed=1; exit}} flag{print} END{exit !closed}' "$template_path" > "$dest_path"; then
        echo "✗ ERROR: ${template_path} has no closing \`\`\` fence — cannot extract body" >&2
        rm -f "$dest_path"
        exit 1
    fi
}

create_user_overrides() {
    local overrides_path="${WORKING_DIR}/memory/user/USER_OVERRIDES.md"
    if [ -f "$overrides_path" ]; then
        return 0
    fi
    local template_path="${COMMON_SPECS_DIR}/templates/USER_OVERRIDES.template.md"
    mkdir -p "${WORKING_DIR}/memory/user"

    _extract_fenced_markdown_body "$template_path" "$overrides_path"

    local today
    today=$(date -u +"%Y-%m-%d")
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/<YYYY-MM-DD>/${today}/" "$overrides_path"
    else
        sed -i "s/<YYYY-MM-DD>/${today}/" "$overrides_path"
    fi

    # Bootstrap-collected compliance value — only written if non-default.
    if [ "$COMPLIANCE_PRESET" != "none" ]; then
        local escaped_preset
        escaped_preset="$(_sed_escape_replacement "$COMPLIANCE_PRESET")"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/^# compliance: <preset>.*/compliance: ${escaped_preset}/" "$overrides_path"
        else
            sed -i "s/^# compliance: <preset>.*/compliance: ${escaped_preset}/" "$overrides_path"
        fi
    fi

    # Bootstrap-collected extensions — append-after-anchor (mirrors the PROFILE.md
    # technique below), then drop the now-superseded commented placeholder lines.
    if [ -n "$EXTENSIONS" ]; then
        local OV_EXT_SED_SCRIPT="/^# extensions:/a\\
extensions:"
        local ov_ext
        IFS=',' read -ra EXT_ARRAY_OV <<< "$EXTENSIONS"
        for ov_ext in "${EXT_ARRAY_OV[@]}"; do
            OV_EXT_SED_SCRIPT="${OV_EXT_SED_SCRIPT}\\
  - ${ov_ext}"
        done
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "$OV_EXT_SED_SCRIPT" "$overrides_path"
            sed -i '' -e "/^# extensions:/d" -e "/^#   - <ext>\$/d" "$overrides_path"
        else
            sed -i "$OV_EXT_SED_SCRIPT" "$overrides_path"
            sed -i -e "/^# extensions:/d" -e "/^#   - <ext>\$/d" "$overrides_path"
        fi
    fi
}

# Pre-scaffold empty memory/archive/<category>/ARCHIVE_INDEX.md for each
# tiered category on fresh install (fresh installs get these by default, not
# lazily on first rotation). Idempotent per category —
# never overwrites an existing ARCHIVE_INDEX.md (rotation may have populated it).
create_archive_indexes() {
    local template_path="${COMMON_SPECS_DIR}/templates/ARCHIVE_INDEX.template.md"
    local today category label hot_file archive_file archive_dir index_path
    today=$(date -u +"%Y-%m-%d")

    for category in sessions decisions feedback; do
        case "$category" in
            sessions)  label="Sessions";  hot_file="sessions/session_state.md" ;;
            decisions) label="Decisions"; hot_file="decisions/decisions.md" ;;
            feedback)  label="Feedback";  hot_file="feedback/feedback.md" ;;
        esac
        archive_file="${category}-archive.md"
        archive_dir="${WORKING_DIR}/memory/archive/${category}"
        index_path="${archive_dir}/ARCHIVE_INDEX.md"
        if [ -f "$index_path" ]; then
            continue
        fi
        mkdir -p "$archive_dir"
        _extract_fenced_markdown_body "$template_path" "$index_path"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' -e "s/<Category>/${label}/" -e "s/<YYYY-MM-DD>/${today}/g" \
                -e "s#<HotFile>#${hot_file}#" -e "s#<ArchiveFile>#${archive_file}#g" "$index_path"
            sed -i '' "/^- <ENTRY-ID>/d" "$index_path"
        else
            sed -i -e "s/<Category>/${label}/" -e "s/<YYYY-MM-DD>/${today}/g" \
                -e "s#<HotFile>#${hot_file}#" -e "s#<ArchiveFile>#${archive_file}#g" "$index_path"
            sed -i "/^- <ENTRY-ID>/d" "$index_path"
        fi
    done
}

# ---------------------------------------------------------------------------
# MIGRATION MODE helpers (v4.0.0, step-8
# adversarial round) — data-safety fixes shared by the pre-flight idempotency
# check and the real migration path below.
# ---------------------------------------------------------------------------

# Blank out (never delete — must preserve line numbers) fenced ```...```
# code-block content before searching for a stale @-import, so a documented
# EXAMPLE of the old import syntax doesn't false-positive and permanently
# defeat idempotency detection (Finding 9).
_strip_fenced_code_blocks() {
    awk '
        /^```/ { f = !f; print ""; next }
        f { print ""; next }
        { print }
    ' "$1"
}

# All 1-based line numbers of a stale @-import line, whole-line-anchored so
# prose mentions and HTML comments don'\''t false-positive (Finding 6), and
# ALL matches reported, not just the first (Finding 10). Empty output if none.
_find_stale_claude_imports() {
    _strip_fenced_code_blocks "$1" | grep -nE '^[[:space:]]*@[A-Za-z0-9_./-]*MEMORY_PROTOCOL\.md[[:space:]]*$' | cut -d: -f1
}

# A bare "first 3 bytes are ---" check is satisfied by a truncated/corrupted
# PROFILE.md, permanently misclassifying it as already-migrated (Finding 5).
# Require an actual closing --- fence within the first 4096 bytes.
_has_real_yaml_frontmatter() {
    local file="$1" head rest
    head="$(head -c 4096 "$file" 2>/dev/null || true)"
    case "$head" in
        ---*) ;;
        *) return 1 ;;
    esac
    rest="${head:3}"
    case "$rest" in
        *$'\n'---*) return 0 ;;
        *) return 1 ;;
    esac
}

# Second-granularity timestamps collide on a fast/back-to-back re-run — never
# crash (Python's shutil.copytree) or silently nest into an existing dir
# (Bash's cp -r) on a collision; find the next free name instead
# (Findings 1/2/12).
_unique_backup_destination() {
    local base="$1" candidate="$1" n=2
    while [ -e "$candidate" ]; do
        candidate="${base}-${n}"
        n=$((n + 1))
    done
    printf '%s' "$candidate"
}

# --backup-location under memory/ itself would plant a permanent nested copy
# inside the very tree it's meant to safeguard (Finding 11).
_refuse_if_backup_location_unsafe() {
    local working_dir="$1" backup_location="$2" memory_real backup_parent_real
    memory_real="$(cd "${working_dir}/memory" 2>/dev/null && pwd -P || true)"
    backup_parent_real="$(cd "$(dirname "$backup_location")" 2>/dev/null && pwd -P || true)"
    if [ -n "$memory_real" ] && [ -n "$backup_parent_real" ]; then
        case "$backup_parent_real" in
            "$memory_real"|"$memory_real"/*)
                echo "✗ ERROR: --backup-location (${backup_location}) is inside memory/ — refusing."
                echo "  A backup must live OUTSIDE the tree it's backing up. Pick a location outside ${memory_real}."
                exit 1
                ;;
        esac
    fi
}

# Replace whatever currently exists at $2 (symlink, file, or directory) with
# a fresh copy of $1 — never write THROUGH a symlink (Findings 3/4) and
# never silently nest inside an unexpected directory at this path (Finding 7).
_safe_copy_file() {
    local src="$1" dst="$2"
    if [ -L "$dst" ] || [ -f "$dst" ]; then
        rm -f "$dst"
    elif [ -d "$dst" ]; then
        rm -rf "$dst"
    fi
    cp "$src" "$dst"
}

# Set `key` in USER_OVERRIDES.md to `line` ("key: value"), touching nothing
# else. Order: replace a live line; else uncomment+replace the template's
# commented line; else insert right after the OPENING `---` — inside the
# frontmatter block, where a YAML-frontmatter-only reader (protocol §1.1)
# will find it (awk, not sed, for GNU/BSD-portable single-match addressing).
upsert_override_key() {
    local path="$1" key="$2" line="$3" has_live has_commented tmp
    tmp="${path}.tmp.$$"
    has_live=$(grep -cE "^${key}: " "$path" 2>/dev/null || true)
    has_commented=$(grep -cE "^# ${key}:" "$path" 2>/dev/null || true)
    if [ "${has_live:-0}" -gt 0 ]; then
        awk -v key="$key" -v line="$line" '$0 ~ "^" key ": " && !done { print line; done=1; next } { print }' "$path" > "$tmp" && mv "$tmp" "$path"
    elif [ "${has_commented:-0}" -gt 0 ]; then
        awk -v key="$key" -v line="$line" '$0 ~ "^# " key ":" && !done { print line; done=1; next } { print }' "$path" > "$tmp" && mv "$tmp" "$path"
    else
        awk -v line="$line" '/^---$/ && !done { print; print line; done=1; next } { print }' "$path" > "$tmp" && mv "$tmp" "$path"
    fi
}

# ============================================================
# VERIFY-ONLY / STATUS MODE
# ============================================================

if [ "$VERIFY_ONLY" = true ]; then
    echo "=========================================="
    echo "Ultimate Memory Stack — General-Edition"
    echo "Version: ${STACK_VERSION}"
    echo "Working directory: ${WORKING_DIR}"
    echo "=========================================="

    if [ ! -d "${WORKING_DIR}/memory" ]; then
        echo "✗ No memory/ directory found at ${WORKING_DIR}"
        echo "  Run setup.sh without --verify to install"
        exit 1
    fi

    if [ ! -f "${WORKING_DIR}/memory/MEMORY_INDEX.md" ]; then
        echo "✓ Setup scaffold present at ${WORKING_DIR}"
        echo ""
        echo "ℹ️  Activation wizard has not run yet."
        echo "    Open your agent harness from ${WORKING_DIR} (e.g. Claude Code or OpenClaw), paste the activation prompt from:"
        echo "    ${WORKING_DIR}/ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md"
        echo "    Then re-run --verify."
        exit 0
    fi

    echo "Compliance preset: ${COMPLIANCE_PRESET}"
    echo "Extensions: ${EXTENSIONS:-none}"
    echo ""

    # T1-T9 self-test (basic check)
    [ -f "${WORKING_DIR}/memory/sessions/session_state.md" ] && echo "✓ T1: session_state.md exists" || echo "✗ T1: MISSING"
    [ -f "${WORKING_DIR}/memory/MEMORY_INDEX.md" ] && echo "✓ T2: MEMORY_INDEX.md exists" || echo "✗ T2: MISSING"

    # Audit log check (preset-dependent)
    if [ -f "${WORKING_DIR}/memory/security/audit_log.jsonl" ]; then
        AUDIT_LINES=$(wc -l < "${WORKING_DIR}/memory/security/audit_log.jsonl")
        echo "✓ Audit log exists (${AUDIT_LINES} entries; preset-dependent)"
    else
        if [ "$COMPLIANCE_PRESET" = "none" ]; then
            echo "ℹ️  Audit log not initialized (compliance: none — OPT-IN; this is OK)"
        else
            echo "✗ Audit log MISSING (expected for compliance: ${COMPLIANCE_PRESET})"
        fi
    fi

    # Tier detection
    echo ""
    echo "Deployment tier:"
    command -v node &> /dev/null && echo "  Node.js: $(node --version)" || echo "  Node.js: NOT installed"
    command -v python3 &> /dev/null && echo "  Python: $(python3 --version)"

    exit 0
fi

# ============================================================
# CHANGE-PRESET MODE
# ============================================================

if [ "$MODE" = "change-preset" ]; then
    echo "→ Changing compliance preset to: ${COMPLIANCE_PRESET}"

    if [ ! -f "${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md" ]; then
        echo "✗ ERROR: PROFILE.md not found; not a valid deployment"
        exit 1
    fi

    # v4.0.0: write to USER_OVERRIDES.md — PROFILE.md is regenerable and no
    # longer authoritative for this value. Create the file first if this
    # deployment predates it (e.g. never re-installed since v4.0.0 shipped).
    OVERRIDES_PATH="${WORKING_DIR}/memory/user/USER_OVERRIDES.md"
    [ ! -f "$OVERRIDES_PATH" ] && create_user_overrides

    # Backup before mutating (belt and suspenders — mirrors the pre-v4.0.0 PROFILE.md backup)
    cp "$OVERRIDES_PATH" "${OVERRIDES_PATH}.backup.$(date +%Y%m%d-%H%M%S)"

    # Log change to audit log
    CHANGE_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    AUDIT_PATH="${WORKING_DIR}/memory/security/audit_log.jsonl"
    [ ! -f "$AUDIT_PATH" ] && touch "$AUDIT_PATH"  # initialize if first audit event
    echo "{\"ts\":\"${CHANGE_TS}\",\"actor\":\"migration-script\",\"actor_session\":0,\"action\":\"preset-change\",\"entry_id\":\"<system>\",\"entry_path\":\"memory/\",\"entry_category\":\"system\",\"entry_summary\":\"Compliance preset changed to ${COMPLIANCE_PRESET}\",\"outcome\":\"success\"}" >> "$AUDIT_PATH"

    upsert_override_key "$OVERRIDES_PATH" "compliance" "compliance: ${COMPLIANCE_PRESET}"

    echo "✓ Preset changed to ${COMPLIANCE_PRESET} (memory/user/USER_OVERRIDES.md)"
    echo "→ Next session, Claude will re-validate existing entries against new detection patterns"
    echo "→ Entries failing new validation will route to quarantine for review"
    exit 0
fi

# ============================================================
# MIGRATION MODE — v3.6 IDEMPOTENCY + DRY-RUN PRE-CHECK
# ============================================================
# Runs BEFORE any write in the script (including the .deployment-info clear
# below) so both the already-migrated no-op and --dry-run can guarantee zero
# writes (step-zero already-migrated detection + idempotency
# requirement). Read-only: safe to run even against the installed copy,
# before the self-reference guard gets a chance to refuse it.

if [ "$MODE" = "migrate" ] && [ "$MIGRATE_FROM" = "v3.6" ]; then
    RULES_FILE="${WORKING_DIR}/.claude/rules/memory_protocol.md"
    EXTENDED_FILE="${WORKING_DIR}/memory/MEMORY_PROTOCOL_EXTENDED.md"
    OVERRIDES_FILE="${WORKING_DIR}/memory/user/USER_OVERRIDES.md"
    PROFILE_FILE="${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md"
    CLAUDE_MD_FILE="${WORKING_DIR}/CLAUDE.md"
    SHIPPED_PROFILE_PRECHECK="${SCRIPT_DIR}/PROFILE.md"

    RULES_OVERSIZED=false
    if [ ! -f "$RULES_FILE" ] || [ "$(wc -c < "$RULES_FILE")" -ge 15000 ]; then
        RULES_OVERSIZED=true
    fi
    PROFILE_HAS_FRONTMATTER=false
    [ -f "$PROFILE_FILE" ] && _has_real_yaml_frontmatter "$PROFILE_FILE" && PROFILE_HAS_FRONTMATTER=true
    STALE_IMPORT_LINES=""
    [ -f "$CLAUDE_MD_FILE" ] && STALE_IMPORT_LINES="$(_find_stale_claude_imports "$CLAUDE_MD_FILE")"

    ALREADY_MIGRATED=true
    [ "$RULES_OVERSIZED" = true ] && ALREADY_MIGRATED=false
    [ -f "$EXTENDED_FILE" ] || ALREADY_MIGRATED=false
    [ -f "$OVERRIDES_FILE" ] || ALREADY_MIGRATED=false
    [ "$PROFILE_HAS_FRONTMATTER" = true ] || ALREADY_MIGRATED=false
    [ -n "$STALE_IMPORT_LINES" ] && ALREADY_MIGRATED=false

    if [ "$ALREADY_MIGRATED" = true ]; then
        echo "✓ Already migrated to v${STACK_VERSION} — nothing to do."
        exit 0
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "→ DRY RUN: v3.6 → v${STACK_VERSION} migration plan (no writes will be made):"
        # These three always happen once migration proceeds past the
        # already-migrated gate — unconditional overwrites in the shared
        # copy flow below, not gated on the file's current state (the old
        # preview under-reported this as conditional — step-8 adversarial
        # round Finding 4).
        echo "  - refresh the vendored ultimate-memory-stack/ scaffold (common-specs/, general-edition/)"
        echo "  - refresh .claude/rules/memory_protocol.md"
        echo "  - refresh memory/MEMORY_PROTOCOL_EXTENDED.md"
        [ -f "$OVERRIDES_FILE" ] || echo "  - create memory/user/USER_OVERRIDES.md"
        if [ -f "$PROFILE_FILE" ] && ! cmp -s "$PROFILE_FILE" "$SHIPPED_PROFILE_PRECHECK"; then
            echo "  - archive existing PROFILE.md (differs from the shipped default) and regenerate"
        fi
        echo "  - create per-category ARCHIVE_INDEX.md files where absent (tiering scaffold)"
        if [ -n "$STALE_IMPORT_LINES" ]; then
            WHERE="$(echo "$STALE_IMPORT_LINES" | sed 's/^/CLAUDE.md:/' | paste -sd, -)"
            echo "  - DETECTED: stale @-import at ${WHERE} — will NOT be auto-edited; see MIGRATION_v3.6_to_v4.0.md for the exact line(s) to remove"
        fi
        if [ -d "${WORKING_DIR}/.openclaw" ]; then
            echo "  - DETECTED: .openclaw/ present — the OpenClaw adapter's own overwrite semantics are unchanged by this migration; its own backups apply"
        fi
        PREVIEW_BACKUP="$(_unique_backup_destination "${WORKING_DIR}/memory.backup.v3.6.<timestamp>")"
        echo "→ Backup would be created at: ${PREVIEW_BACKUP}/"
        exit 0
    fi
elif [ "$MODE" = "migrate" ] && [ "$MIGRATE_FROM" = "v2.0" ] && [ "$DRY_RUN" = true ]; then
    # v2.0's --dry-run used to be silently ignored (a real migration ran
    # anyway) — step-8 adversarial round Finding 13. Now a genuine preview.
    PREVIEW_BACKUP_LOCATION="${BACKUP_LOCATION:-${WORKING_DIR}/memory.backup.v2.<timestamp>}"
    echo "→ DRY RUN: v2.0 → v${STACK_VERSION} migration plan (no writes will be made):"
    echo "  - back up memory/ to ${PREVIEW_BACKUP_LOCATION}/"
    echo "  - delegate schema migration to the Claude Code wizard (per MIGRATION_v2_to_v3.md)"
    echo "  - refresh the vendored ultimate-memory-stack/ scaffold, rules copy, USER_OVERRIDES/tiering scaffold (same conditional items as any re-install)"
    exit 0
fi

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================

echo "=========================================="
echo "Ultimate Memory Stack — General-Edition Setup"
echo "Version: ${STACK_VERSION}"
echo "Working directory: ${WORKING_DIR}"
echo "Compliance preset: ${COMPLIANCE_PRESET}"
echo "Extensions: ${EXTENSIONS:-none}"
echo "Mode: ${MODE}"
echo "=========================================="

# Verify common-specs exists
[ ! -d "${COMMON_SPECS_DIR}" ] && { echo "✗ common-specs/ not found"; exit 1; }

# Check writable working dir
[ ! -d "${WORKING_DIR}" ] && { echo "✗ Working dir does not exist: ${WORKING_DIR}"; exit 1; }
[ ! -w "${WORKING_DIR}" ] && { echo "✗ Working dir not writable: ${WORKING_DIR}"; exit 1; }

# Detect Claude Code
command -v claude &> /dev/null || echo "⚠️  Claude Code CLI not in PATH"

# Clear any prior completion certificate up-front: a crashed re-install must not
# leave a stale .deployment-info claiming a configured install. It is rewritten
# at the very end on success only (parity with setup.py's stale_marker handling).
if [ -f "${WORKING_DIR}/.deployment-info" ]; then
    rm -f "${WORKING_DIR}/.deployment-info"
fi

# Self-reference guard (adversarial-round finding, 2026-07-14): SCRIPT_DIR is
# wherever THIS script happens to be running from. If that's the INSTALLED
# copy inside WORKING_DIR/ultimate-memory-stack/general-edition/, then
# SCRIPT_DIR and the install target are the same directory — the "differs
# from shipped" archive check below (cmp against SCRIPT_DIR/PROFILE.md)
# compares the file to itself (always equal, so a hand-edited PROFILE.md is
# never archived), and the wipe step then deletes common-specs/ and tries to
# cp -r FROM the path it just deleted, crashing and permanently destroying
# the directory. Refuse before any of that runs. --change-preset/--verify/
# --status already exit above and don't reach this point.
# `|| true` is required, not cosmetic: under `set -e`, a plain assignment whose
# command substitution ends in a failing command (the `cd` when the directory
# doesn't exist yet — the normal fresh-install case) aborts the whole script.
INSTALLED_GENERAL_EDITION="$(cd "${WORKING_DIR}/ultimate-memory-stack/general-edition" 2>/dev/null && pwd -P || true)"
THIS_SCRIPT_DIR="$(cd "${SCRIPT_DIR}" && pwd -P)"
if [ -n "$INSTALLED_GENERAL_EDITION" ] && [ "$THIS_SCRIPT_DIR" = "$INSTALLED_GENERAL_EDITION" ]; then
    echo "✗ ERROR: this is the INSTALLED copy of setup.sh, running against its own directory."
    echo "  ${SCRIPT_DIR} IS the install target — there is no separate shipped source to refresh from."
    echo "  To re-install or add extensions, run the ORIGINAL package's setup.sh (the one you"
    echo "  cloned/downloaded), not the copy inside ${WORKING_DIR}."
    echo "  To change the compliance preset on this existing install, use --change-preset instead"
    echo "  (safe to run from the installed copy)."
    exit 1
fi

# ============================================================
# MIGRATION MODE
# ============================================================

if [ "$MODE" = "migrate" ]; then
    if [ ! -d "${WORKING_DIR}/memory" ]; then
        echo "✗ No existing memory/ at ${WORKING_DIR}"
        exit 1
    fi

    if [ "$MIGRATE_FROM" = "v3.6" ]; then
        # v3.6.x → v4.0.0: the already-migrated
        # no-op and --dry-run were handled above, before any write — reaching
        # here means a real migration is proceeding. Backup name is version-
        # specific (was hardcoded "v2" for every --migrate-from value, a bug
        # this branch fixes for v3.6 without touching the v2.0 path below).
        [ -z "$BACKUP_LOCATION" ] && BACKUP_LOCATION="${WORKING_DIR}/memory.backup.v3.6.$(date +%Y%m%d-%H%M%S)"
        _refuse_if_backup_location_unsafe "$WORKING_DIR" "$BACKUP_LOCATION"
        BACKUP_LOCATION="$(_unique_backup_destination "$BACKUP_LOCATION")"
        echo "→ Migrating v3.6 → v${STACK_VERSION}"
        echo "→ Backup: ${BACKUP_LOCATION}"
        cp -r "${WORKING_DIR}/memory" "${BACKUP_LOCATION}"
        echo "✓ Backup complete"

        # Disclosure-only detections (§2.3): never auto-edited, never fixed here.
        if [ -f "${WORKING_DIR}/CLAUDE.md" ]; then
            STALE_IMPORT_LINES_REAL="$(_find_stale_claude_imports "${WORKING_DIR}/CLAUDE.md")"
            if [ -n "$STALE_IMPORT_LINES_REAL" ]; then
                WHERE_REAL="$(echo "$STALE_IMPORT_LINES_REAL" | sed 's/^/CLAUDE.md:/' | paste -sd, -)"
                echo "⚠️  ${WHERE_REAL} still imports MEMORY_PROTOCOL.md — this doubles the eager-load cost"
                echo "    since .claude/rules/memory_protocol.md already auto-loads every session."
                echo "    Delete that line from CLAUDE.md by hand (never auto-edited)."
            fi
        fi
        if [ -d "${WORKING_DIR}/.openclaw" ]; then
            echo "ℹ️  .openclaw/ detected — this migration only covers the general-edition Claude Code vault."
            echo "    The OpenClaw adapter's own overwrite semantics are unchanged by v4.0.0; its own backups apply."
        fi
        echo "→ Continuing with the standard refresh (rules copy, EXTENDED, USER_OVERRIDES, PROFILE, tiering scaffold)..."
    else
        # v2.0 (unchanged from pre-v4.0.0 behavior — acceptance criterion (b)).
        [ -z "$BACKUP_LOCATION" ] && BACKUP_LOCATION="${WORKING_DIR}/memory.backup.v2.$(date +%Y%m%d-%H%M%S)"
        _refuse_if_backup_location_unsafe "$WORKING_DIR" "$BACKUP_LOCATION"
        BACKUP_LOCATION="$(_unique_backup_destination "$BACKUP_LOCATION")"
        echo "→ Migrating v${MIGRATE_FROM} → v${STACK_VERSION}"
        echo "→ Backup: ${BACKUP_LOCATION}"
        cp -r "${WORKING_DIR}/memory" "${BACKUP_LOCATION}"
        echo "✓ Backup complete"
        echo "→ Schema migration via Claude Code wizard (per MIGRATION_v2_to_v3.md)"
    fi
fi

# ============================================================
# FILE COPY / SCAFFOLD
# ============================================================

echo "→ Copying memory stack files..."

mkdir -p "${WORKING_DIR}/ultimate-memory-stack" "${WORKING_DIR}/.claude/rules"

# v4.0.0 (unified existing-scaffold behavior): archive
# anything user-touched, THEN refresh. A pre-v4.0.0 vault may have a
# hand-edited PROFILE.md — archive it (with a migration notice) BEFORE the
# regenerable general-edition/ tree gets wiped below, so the edit is never
# silently lost. Compared against the SHIPPED source about to be copied,
# never a version stamp the user could have edited away.
INSTALLED_PROFILE="${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md"
SHIPPED_PROFILE="${SCRIPT_DIR}/PROFILE.md"
if [ -f "$INSTALLED_PROFILE" ] && ! cmp -s "$INSTALLED_PROFILE" "$SHIPPED_PROFILE"; then
    ARCHIVE_DIR="${WORKING_DIR}/memory/archive"
    mkdir -p "$ARCHIVE_DIR"
    ARCHIVE_PATH="${ARCHIVE_DIR}/PROFILE.pre-upgrade.$(date -u +"%Y%m%d-%H%M%S").md"
    cp "$INSTALLED_PROFILE" "$ARCHIVE_PATH"
    echo "⚠️  Existing PROFILE.md differs from the shipped default — archived to ${ARCHIVE_PATH}"
    echo "   PROFILE.md is regenerable as of v4.0.0; your edits are not auto-applied."
    echo "   Compare $(basename "$ARCHIVE_PATH") against the new PROFILE.md, then port any values you"
    echo "   want to keep into memory/user/USER_OVERRIDES.md (create it if it doesn't exist yet —"
    echo "   see common-specs/templates/USER_OVERRIDES.template.md for the format)."
fi

# cp -r re-run nesting guard — v4.0.0: archive-then-refresh, not refuse (§3.4a)
if [ -d "${WORKING_DIR}/ultimate-memory-stack/common-specs" ]; then
    echo "⚠️  Existing common-specs at ${WORKING_DIR}/ultimate-memory-stack/common-specs — wiping for clean install"
    rm -rf "${WORKING_DIR}/ultimate-memory-stack/common-specs"
fi
cp -r "${COMMON_SPECS_DIR}" "${WORKING_DIR}/ultimate-memory-stack/common-specs"

if [ -d "${WORKING_DIR}/ultimate-memory-stack/general-edition" ]; then
    echo "⚠️  Existing general-edition at ${WORKING_DIR}/ultimate-memory-stack/general-edition — wiping for clean install"
    rm -rf "${WORKING_DIR}/ultimate-memory-stack/general-edition"
fi
cp -r "${SCRIPT_DIR}" "${WORKING_DIR}/ultimate-memory-stack/general-edition"

# Copy the package-root VERSION file into the scaffold (#14 re-audit follow-on)
# so a re-run of the COPIED installer reads the real version, not a fallback.
[ -f "${SCRIPT_DIR}/../VERSION" ] && cp "${SCRIPT_DIR}/../VERSION" "${WORKING_DIR}/ultimate-memory-stack/VERSION"

_safe_copy_file "${COMMON_SPECS_DIR}/MEMORY_PROTOCOL.md" "${WORKING_DIR}/.claude/rules/memory_protocol.md"
chmod 644 "${WORKING_DIR}/.claude/rules/memory_protocol.md"  # normalize permissions

# Initialize memory/ directories
mkdir -p "${WORKING_DIR}/memory/"{sessions,decisions,feedback,projects,security,references,user,archive,quarantine}

# Extended protocol reference — on-demand only, vault root, NEVER .claude/rules/ (would recreate eager-load cost)
_safe_copy_file "${COMMON_SPECS_DIR}/MEMORY_PROTOCOL_EXTENDED.md" "${WORKING_DIR}/memory/MEMORY_PROTOCOL_EXTENDED.md"

# Initialize audit log based on preset
case "$COMPLIANCE_PRESET" in
    none)
        # Audit log is OPT-IN; don't auto-create
        echo "ℹ️  Audit log: OPT-IN (compliance: none — default OFF)"
        echo "   Enable later via PROFILE.md edit: audit_log: true"
        ;;
    enterprise|custom)
        touch "${WORKING_DIR}/memory/security/audit_log.jsonl"
        touch "${WORKING_DIR}/memory/quarantine/quarantine_log.jsonl"
        INIT_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        echo "{\"ts\":\"${INIT_TS}\",\"actor\":\"migration-script\",\"actor_session\":0,\"action\":\"initialize\",\"entry_id\":\"<bootstrap>\",\"entry_path\":\"memory/\",\"entry_category\":\"system\",\"entry_summary\":\"General-edition v${STACK_VERSION} deployment initialized; preset=${COMPLIANCE_PRESET}; extensions=${EXTENSIONS:-none}\",\"outcome\":\"success\"}" >> "${WORKING_DIR}/memory/security/audit_log.jsonl"
        echo "✓ Audit log initialized for compliance: ${COMPLIANCE_PRESET}"
        ;;
esac

echo "✓ Memory directory structure initialized"

# Keep the vendored package + install markers out of the user's git history
# (only when the target is a git repo); memory/ is their data and stays tracked.
if [ -d "${WORKING_DIR}/.git" ]; then
    GITIGNORE="${WORKING_DIR}/.gitignore"
    if ! grep -qF "# >>> ultimate-memory-stack >>>" "$GITIGNORE" 2>/dev/null; then
        [ -s "$GITIGNORE" ] && printf '\n' >> "$GITIGNORE"
        cat >> "$GITIGNORE" <<'GITIGNORE_EOF'
# >>> ultimate-memory-stack >>>
# Installer artifacts + the vendored package (regenerable). The user's
# memory vault (the data) is intentionally left tracked — not ignored here.
ultimate-memory-stack/
.deployment-info
.ums-manifest.json
# <<< ultimate-memory-stack <<<
GITIGNORE_EOF
        echo "✓ .gitignore updated (package scaffold + install markers ignored; memory/ left tracked)"
    fi
fi

# v4.0.0: compliance/extensions choices are USER choices — they land in
# USER_OVERRIDES.md (create-once, never rewritten again), not PROFILE.md.
# PROFILE.md's frontmatter carries only the shipped default and is never
# edited by the installer (it stays regenerable — see PROFILE.md §2.1).
create_user_overrides
echo "✓ memory/user/USER_OVERRIDES.md ready"

# v4.0.0 hot/cold tiering: pre-scaffold empty
# ARCHIVE_INDEX.md files for the 3 tiered categories.
create_archive_indexes
echo "✓ memory/archive/{sessions,decisions,feedback}/ARCHIVE_INDEX.md ready"

# ============================================================
# T3+ FEATURE SETUP
# ============================================================

if python3 -c "import cryptography" 2>/dev/null; then
    echo "→ Code Execution detected"
    echo "→ HMAC secret generation: available via setup.py --generate-hmac-secret (signing itself NOT IMPLEMENTED)"
    echo "  Run 'python3 setup.py --generate-hmac-secret' if needed"
fi

# ============================================================
# WRITE DEPLOYMENT-INFO MARKER
# ============================================================

INSTALL_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "${WORKING_DIR}/.deployment-info" <<EOF
deployment_path: ${WORKING_DIR}
edition: ${EDITION}
compliance_preset: ${COMPLIANCE_PRESET}
extensions: ${EXTENSIONS:-none}
installed_at: ${INSTALL_TS}
stack_version: "${STACK_VERSION}"
EOF
echo "✓ Deployment-info marker written to ${WORKING_DIR}/.deployment-info"

# ============================================================
# COMPLETION
# ============================================================

echo ""
echo "=========================================="
echo "✓ General-edition setup complete"
echo "=========================================="
echo ""

# Effective tier summary at install completion
echo "Effective tier detection:"
command -v node &> /dev/null && echo "  Node.js:      available  (T2 features active)" || echo "  Node.js:      NOT installed  (T2 features dormant)"
python3 -c "import cryptography" 2>/dev/null && echo "  cryptography: available  (entry signing NOT IMPLEMENTED; secret generation only)" || echo "  cryptography: NOT installed"
command -v ollama &> /dev/null && echo "  Ollama:       available  (T1 semantic search ready)" || echo "  Ollama:       NOT installed  (T1 semantic dormant)"
echo ""
echo "Active feature surface: 20 Tier A + 12 Tier B (edition-configured)"
echo "Dormant Tier C (9 designed-in): see common-specs/TIER_C_ACTIVATION.md for per-tool activation steps"
echo ""

# Harness-aware next steps (Option C): when the top-level installer launches this
# script it exports UMS_PARENT=1 and prints its own harness-correct summary, so
# suppress this per-edition block (and the old "Run: claude" assumption) when
# parented. Standalone runs print a harness-neutral block.
if [ "${UMS_PARENT:-}" != "1" ]; then
    echo "Next steps:"
    echo "  1. cd ${WORKING_DIR}"
    echo "  2. Open your agent harness in this directory (e.g. Claude Code or OpenClaw)"
    echo "  3. Paste the activation prompt from:"
    echo "     ${WORKING_DIR}/ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md"
    echo "  4. Answer setup wizard"
    echo "  5. Verify (after wizard completes):"
    echo "     WORKING_DIR=${WORKING_DIR} bash ${SCRIPT_DIR}/setup.sh --verify"
    echo ""
    echo "Compliance: ${COMPLIANCE_PRESET}"
    echo "Extensions: ${EXTENSIONS:-none}"
    echo ""
    echo "To change preset later: ./setup.sh --change-preset=<new>"
    echo "See INSTALL.md for details."
fi

exit 0
