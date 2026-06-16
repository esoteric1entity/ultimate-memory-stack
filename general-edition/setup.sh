#!/bin/bash
# Ultimate Memory Stack — General-Edition Setup Script (Linux/Mac/WSL)
# Version: 1.1 — 2026-06-16
# Tier: T2+ (requires Bash; HMAC keys at T3+ via Python/Code Execution)
# Author: see /AUTHORS.md
# License: Apache-2.0 (general-edition is the public-distribution candidate; biotech-edition is private per PRIVACY_REVIEW.md)

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
    STACK_VERSION="3.6.2"
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
        --help)
            echo "Ultimate Memory Stack — General-Edition Setup"
            echo ""
            echo "Usage:"
            echo "  ./setup.sh                                       # Fresh install with wizard"
            echo "  ./setup.sh --compliance=none                     # Fresh install with compliance preset"
            echo "  ./setup.sh --compliance=enterprise --extensions=soc2,gdpr"
            echo "  ./setup.sh --migrate-from=v2.0                   # Migrate from v2.0"
            echo "  ./setup.sh --change-preset=enterprise            # Change preset on existing deploy"
            echo "  ./setup.sh --verify                              # Run self-test"
            echo "  ./setup.sh --status                              # Show current state"
            echo ""
            echo "Compliance presets: none | enterprise | custom   (PHI/healthcare = biotech-edition only)"
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

# Validate compliance preset (PHI/healthcare is biotech-edition only — refuse here)
case "$COMPLIANCE_PRESET" in
    healthcare)
        echo "✗ ERROR: PHI/healthcare compliance is part of the institutional biotech-edition, not the public general-edition."
        echo "  The general-edition does not ship PHI/HIPAA compliance. See CONTRIBUTING.md for institutional adoption."
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
                echo "✗ ERROR: the 'healthcare' extension is biotech-edition only (PHI), not in the public general-edition."
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

# Custom preset complexity floor
if [ "$COMPLIANCE_PRESET" = "custom" ]; then
    if [ ! -f "${SCRIPT_DIR}/overrides/compliance.override.md" ]; then
        echo "✗ ERROR: 'custom' preset requires overrides/compliance.override.md"
        echo "  The custom preset needs explicit configuration with ≥1 override."
        echo "  Pick a base preset (none/enterprise) and add overrides."
        exit 1
    fi
fi

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

    # Backup PROFILE.md
    cp "${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md" "${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md.backup.$(date +%Y%m%d-%H%M%S)"

    # Log change to audit log
    CHANGE_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    AUDIT_PATH="${WORKING_DIR}/memory/security/audit_log.jsonl"
    [ ! -f "$AUDIT_PATH" ] && touch "$AUDIT_PATH"  # initialize if first audit event
    echo "{\"ts\":\"${CHANGE_TS}\",\"actor\":\"migration-script\",\"action\":\"preset-change\",\"entry_id\":\"<system>\",\"entry_summary\":\"Compliance preset changed to ${COMPLIANCE_PRESET}\",\"outcome\":\"success\"}" >> "$AUDIT_PATH"

    # Edit PROFILE.md compliance field (sed in-place; OS-aware)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^compliance: .*/compliance: ${COMPLIANCE_PRESET}/" "${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md"
    else
        sed -i "s/^compliance: .*/compliance: ${COMPLIANCE_PRESET}/" "${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md"
    fi

    echo "✓ Preset changed to ${COMPLIANCE_PRESET}"
    echo "→ Next session, Claude will re-validate existing entries against new detection patterns"
    echo "→ Entries failing new validation will route to quarantine for review"
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
[ ! -w "${WORKING_DIR}" ] && { echo "✗ Working dir not writable"; exit 1; }

# Detect Claude Code
command -v claude &> /dev/null || echo "⚠️  Claude Code CLI not in PATH"

# ============================================================
# MIGRATION MODE
# ============================================================

if [ "$MODE" = "migrate" ]; then
    [ -z "$BACKUP_LOCATION" ] && BACKUP_LOCATION="${WORKING_DIR}/memory.backup.v2.$(date +%Y%m%d-%H%M%S)"

    if [ ! -d "${WORKING_DIR}/memory" ]; then
        echo "✗ No existing memory/ at ${WORKING_DIR}"
        exit 1
    fi

    echo "→ Migrating v${MIGRATE_FROM} → v${STACK_VERSION}"
    echo "→ Backup: ${BACKUP_LOCATION}"
    cp -r "${WORKING_DIR}/memory" "${BACKUP_LOCATION}"
    echo "✓ Backup complete"
    echo "→ Schema migration via Claude Code wizard (per MIGRATION_v2_to_v3.md)"
fi

# ============================================================
# FILE COPY / SCAFFOLD
# ============================================================

echo "→ Copying memory stack files..."

mkdir -p "${WORKING_DIR}/ultimate-memory-stack" "${WORKING_DIR}/.claude/rules"

# cp -r re-run nesting guard
if [ -d "${WORKING_DIR}/ultimate-memory-stack/common-specs" ]; then
    echo "✗ ERROR: ${WORKING_DIR}/ultimate-memory-stack/common-specs already exists"
    echo "  Remove with: rm -rf ${WORKING_DIR}/ultimate-memory-stack/  (for clean re-install)"
    exit 1
fi
cp -r "${COMMON_SPECS_DIR}" "${WORKING_DIR}/ultimate-memory-stack/common-specs"

if [ -d "${WORKING_DIR}/ultimate-memory-stack/general-edition" ]; then
    echo "✗ ERROR: ${WORKING_DIR}/ultimate-memory-stack/general-edition already exists"
    echo "  Remove with: rm -rf ${WORKING_DIR}/ultimate-memory-stack/  (for clean re-install)"
    exit 1
fi
cp -r "${SCRIPT_DIR}" "${WORKING_DIR}/ultimate-memory-stack/general-edition"

# Copy the package-root VERSION file into the scaffold (#14 re-audit follow-on)
# so a re-run of the COPIED installer reads the real version, not a fallback.
[ -f "${SCRIPT_DIR}/../VERSION" ] && cp "${SCRIPT_DIR}/../VERSION" "${WORKING_DIR}/ultimate-memory-stack/VERSION"

cp "${COMMON_SPECS_DIR}/MEMORY_PROTOCOL.md" "${WORKING_DIR}/.claude/rules/memory_protocol.md"
chmod 644 "${WORKING_DIR}/.claude/rules/memory_protocol.md"  # normalize permissions

# Initialize memory/ directories
mkdir -p "${WORKING_DIR}/memory/"{sessions,decisions,feedback,projects,security,references,user,archive,quarantine}

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
        echo "{\"ts\":\"${INIT_TS}\",\"actor\":\"migration-script\",\"action\":\"initialize\",\"entry_id\":\"<bootstrap>\",\"entry_summary\":\"General-edition v${STACK_VERSION} deployment initialized; preset=${COMPLIANCE_PRESET}\",\"outcome\":\"success\"}" >> "${WORKING_DIR}/memory/security/audit_log.jsonl"
        echo "✓ Audit log initialized for compliance: ${COMPLIANCE_PRESET}"
        ;;
esac

echo "✓ Memory directory structure initialized"

# Update PROFILE.md with selected compliance preset
if [ "$COMPLIANCE_PRESET" != "none" ]; then
    PROFILE_PATH="${WORKING_DIR}/ultimate-memory-stack/general-edition/PROFILE.md"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s/^compliance: none$/compliance: ${COMPLIANCE_PRESET}/" "$PROFILE_PATH"
    else
        sed -i "s/^compliance: none$/compliance: ${COMPLIANCE_PRESET}/" "$PROFILE_PATH"
    fi
fi

# Activate extensions
if [ -n "$EXTENSIONS" ]; then
    echo "→ Activating extensions: ${EXTENSIONS}"
    # Extensions are activated by being listed in PROFILE.md `extensions:` field
    # Per MEMORY_PROTOCOL.md §6.2 application
fi

# ============================================================
# T3+ FEATURE SETUP
# ============================================================

if python3 -c "import cryptography" 2>/dev/null; then
    echo "→ Code Execution detected"
    echo "→ HMAC secret generation: defer to Python script if signatures activated"
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
python3 -c "import cryptography" 2>/dev/null && echo "  cryptography: available  (T3 HMAC/Ed25519 ready)" || echo "  cryptography: NOT installed  (T3 signatures dormant)"
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
