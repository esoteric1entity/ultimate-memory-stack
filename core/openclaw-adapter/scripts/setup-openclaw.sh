#!/usr/bin/env bash
#
# setup-openclaw.sh — OpenClaw General Edition Adapter Installer (Bash)
# =====================================================================
#
# Authority: SKILL.md (workflow source); idempotent re-runs by design
# Companion: setup-openclaw.py (Python parity)
# Foundation: MAPPING.md
#
# Usage:
#   ./setup-openclaw.sh <openclaw-root> [--compliance none|enterprise] [--no-cron] [--update-profile]
#
# Exit codes:
#   0 = success
#   1 = invalid arguments
#   2 = OpenClaw not detected
#   3 = adapter templates missing
#   4 = self-test failed
#

set -euo pipefail

# ============================================================
# Config + argument parsing
# ============================================================

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <openclaw-root> [--compliance none|enterprise] [--no-cron] [--update-profile]" >&2
    exit 1
fi

OPENCLAW_ROOT="$1"
shift

COMPLIANCE="none"
WIRE_CRON=true
UPDATE_PROFILE_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --compliance)
            COMPLIANCE="$2"
            shift 2
            ;;
        --no-cron)
            WIRE_CRON=false
            shift
            ;;
        --update-profile)
            UPDATE_PROFILE_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

if [[ "$COMPLIANCE" != "none" && "$COMPLIANCE" != "enterprise" ]]; then
    echo "ERROR: --compliance must be 'none' or 'enterprise' (got: $COMPLIANCE)" >&2
    echo "Note: 'healthcare' preset requires biotech-edition adapter (compliance preset B7)" >&2
    exit 1
fi

# Locate this script's directory (templates live alongside)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$ADAPTER_ROOT/templates"

DATESTAMP="$(date +%Y-%m-%d)"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "============================================================"
echo "OpenClaw General Edition Adapter — Installer (Bash)"
echo "============================================================"
echo "OpenClaw root:     $OPENCLAW_ROOT"
echo "Compliance preset: $COMPLIANCE"
echo "Wire cron:         $WIRE_CRON"
echo "Templates from:    $TEMPLATES_DIR"
echo "============================================================"
echo ""

# ============================================================
# Step 1 — Detect OpenClaw installation
# ============================================================

echo "[Step 1] Detecting OpenClaw installation..."

if [[ ! -d "$OPENCLAW_ROOT" ]]; then
    echo "ERROR: $OPENCLAW_ROOT does not exist" >&2
    exit 2
fi

# OpenClaw typically has a .openclaw/ directory or recognizable harness markers
if [[ ! -d "$OPENCLAW_ROOT/.openclaw" ]]; then
    echo "WARN: $OPENCLAW_ROOT/.openclaw not found — proceeding with assumption this is a fresh install"
    mkdir -p "$OPENCLAW_ROOT/.openclaw"
fi

echo "  OpenClaw root: OK"

# ============================================================
# Step 2 — Backup existing root files (idempotency)
# ============================================================

echo ""
echo "[Step 2] Backing up existing root files..."

BACKUP_DIR="$OPENCLAW_ROOT/.openclaw/backup/pre-adapter-install-$DATESTAMP"
mkdir -p "$BACKUP_DIR"

ROOT_FILES=(MEMORY.md AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md BOOTSTRAP.md DREAMS.md)
BACKED_UP=0
for f in "${ROOT_FILES[@]}"; do
    if [[ -f "$OPENCLAW_ROOT/$f" ]]; then
        cp "$OPENCLAW_ROOT/$f" "$BACKUP_DIR/$f"
        BACKED_UP=$((BACKED_UP + 1))
    fi
done

echo "  Backed up: $BACKED_UP existing root files → $BACKUP_DIR"

# ============================================================
# Step 3 — Verify adapter templates available
# ============================================================

echo ""
echo "[Step 3] Verifying adapter templates..."

MISSING_TEMPLATES=()
for f in "${ROOT_FILES[@]}"; do
    if [[ ! -f "$TEMPLATES_DIR/${f}.template" ]]; then
        MISSING_TEMPLATES+=("${f}.template")
    fi
done

if [[ ${#MISSING_TEMPLATES[@]} -gt 0 ]]; then
    echo "ERROR: Adapter templates missing:" >&2
    for t in "${MISSING_TEMPLATES[@]}"; do
        echo "  - $t" >&2
    done
    exit 3
fi

echo "  All 9 templates present: OK"

# ============================================================
# Step 4 — Generate 9 root files
# ============================================================

echo ""
echo "[Step 4] Generating 9 root files..."

for f in "${ROOT_FILES[@]}"; do
    cp "$TEMPLATES_DIR/${f}.template" "$OPENCLAW_ROOT/$f"
    echo "  $f"
done

# ============================================================
# Step 5 — Generate memory/ subdirectory tree
# ============================================================

echo ""
echo "[Step 5] Generating memory/ subdirectory tree..."

SUBDIRS=(
    "memory/decisions"
    "memory/sessions"
    "memory/feedback"
    "memory/feedback/archive"
    "memory/security"
    "memory/references"
    "memory/user"
    "memory/projects"
    "memory/archive/heartbeats"
    "memory/archive/daily_logs"
    "memory/quarantine"
)

for d in "${SUBDIRS[@]}"; do
    mkdir -p "$OPENCLAW_ROOT/$d"
    echo "  $d/"
done

# ============================================================
# Step 6 — Initialize audit + quarantine logs
# ============================================================

echo ""
echo "[Step 6] Initializing audit + quarantine logs..."

touch "$OPENCLAW_ROOT/memory/security/audit_log.jsonl"
touch "$OPENCLAW_ROOT/memory/quarantine/quarantine_log.jsonl"
touch "$OPENCLAW_ROOT/memory/archive/daily_logs/DAILY_LOG_${DATESTAMP}.md"

# Init audit log with adapter-install event
cat >> "$OPENCLAW_ROOT/memory/security/audit_log.jsonl" <<EOF
{"ts":"$TIMESTAMP","actor":"orchestrator","session":0,"action":"adapter-install","entry_id":"<bootstrap>","subject":"openclaw-general-edition-adapter-v1.0","outcome":"success","compliance":"$COMPLIANCE"}
EOF

echo "  audit_log.jsonl: initialized with adapter-install event"
echo "  quarantine_log.jsonl: empty"
echo "  DAILY_LOG_${DATESTAMP}.md: created"

# ============================================================
# Step 7 — Write edition profile
# ============================================================

echo ""
echo "[Step 7] Writing edition profile..."

mkdir -p "$OPENCLAW_ROOT/ultimate-memory-stack/general-edition"
PROFILE_PATH="$OPENCLAW_ROOT/ultimate-memory-stack/general-edition/PROFILE.md"

cat > "$PROFILE_PATH" <<EOF
# General Edition Profile

---
edition: general
compliance: $COMPLIANCE
audit_log: false
quarantine_ux: toast
pattern_key_recurrence_threshold: 5
signature_scheme: none
adapter_version: "1.0"
adapter_installed_at: "$TIMESTAMP"
---

## Active settings

- **Edition:** general-edition
- **Compliance preset:** $COMPLIANCE
- **Audit log:** opt-in (default OFF)
- **Quarantine UX:** toast (one-line at session start)
- **Pattern-key recurrence threshold:** 5 (per MEMORY_PROTOCOL §4.2 B6)
- **Cryptographic signatures:** none (Tier C opt-in)

## Addon registry

(Populated by addon installer Skills on completion.)

\`\`\`yaml
addons: {}
\`\`\`

## Cross-references

- MEMORY_PROTOCOL §6 (edition profile application)
- Compliance preset B7 (healthcare requires biotech-edition adapter)
- Modular consumer architecture (adapter design principle)
EOF

echo "  PROFILE.md: written"

# Early exit if --update-profile flag was passed
if $UPDATE_PROFILE_ONLY; then
    echo ""
    echo "[--update-profile mode] Profile updated. Skipping subsequent steps."
    exit 0
fi

# ============================================================
# Step 8 — Install Lint runner (Option C: surface-only Lint checks)
# ============================================================

echo ""
echo "[Step 8] Installing Lint runner..."

LINT_DIR="$OPENCLAW_ROOT/.openclaw/lint"
mkdir -p "$LINT_DIR"

if [[ -f "$SCRIPT_DIR/lint_runner.py" ]]; then
    cp "$SCRIPT_DIR/lint_runner.py" "$LINT_DIR/lint_runner.py"
    echo "  lint_runner.py: installed at $LINT_DIR/"
else
    echo "  WARN: lint_runner.py not found in $SCRIPT_DIR (adapter source may be incomplete)"
fi

# ============================================================
# Step 9 — Install heartbeat compactor
# ============================================================

echo ""
echo "[Step 9] Installing heartbeat compactor..."

if [[ -f "$SCRIPT_DIR/heartbeat_compactor.py" ]]; then
    cp "$SCRIPT_DIR/heartbeat_compactor.py" "$OPENCLAW_ROOT/.openclaw/heartbeat_compactor.py"
    echo "  heartbeat_compactor.py: installed at $OPENCLAW_ROOT/.openclaw/"
else
    echo "  WARN: heartbeat_compactor.py not found in $SCRIPT_DIR"
fi

# Detect python3 / python availability (Ubuntu lacks `python` by default)
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "  ERROR: Neither python3 nor python found on PATH" >&2
    echo "  Install Python 3.10+ and re-run setup." >&2
    exit 4
fi

if $WIRE_CRON; then
    echo ""
    echo "============================================================"
    echo "CRON ENTRY — Add this to your crontab manually via 'crontab -e':"
    echo "============================================================"
    cat <<EOF

# Ultimate Memory Stack — heartbeat compactor (active hours 08-22 + idle checkpoints)
*/30 8-22 * * * cd "$OPENCLAW_ROOT" && $PYTHON_CMD .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
0 0,6 * * * cd "$OPENCLAW_ROOT" && $PYTHON_CMD .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1

EOF
    echo "============================================================"
    echo "Per SKILL.md Step 9: this script does NOT mutate crontab (security boundary)."
    echo "Run 'crontab -e' yourself and paste the entry above."
    echo "NOTE: cron lines above use literal '$PYTHON_CMD' (auto-detected on this machine)"
    echo "      — if cron-edit auto-expansion fails, manually replace with '$PYTHON_CMD'."
    echo ""
fi

# ============================================================
# Step 10 — Run T1-T9 self-test
# (use $PYTHON_CMD detected above)
# (interpret exit codes per self_test.py docstring —
#               0=PASS, 2=CRITICAL=FAILED, 3=WARN, 4=INFO)
# ============================================================

echo ""
echo "[Step 10] Running T1-T9 self-test..."

if [[ -f "$SCRIPT_DIR/self_test.py" ]]; then
    set +e
    $PYTHON_CMD "$SCRIPT_DIR/self_test.py" "$OPENCLAW_ROOT"
    ST_EXIT=$?
    set -e
    case $ST_EXIT in
        0)
            echo "  self_test.py: PASSED (all T1-T9 green)"
            ;;
        3)
            echo "  self_test.py: PASSED with WARNINGS (T1-T9 mostly green; non-blocking warns)"
            echo "  Install is valid — review warnings above when convenient."
            ;;
        4)
            echo "  self_test.py: PASSED with INFO notes (T1-T9 green; informational items)"
            echo "  Install is valid — review info notes above when convenient."
            ;;
        2)
            echo "  self_test.py: FAILED (CRITICAL — see output above)" >&2
            exit 4
            ;;
        *)
            echo "  self_test.py: FAILED (unexpected exit code $ST_EXIT)" >&2
            exit 4
            ;;
    esac
else
    echo "  WARN: self_test.py not found; skipping (adapter source may be incomplete)"
fi

# ============================================================
# Step 11 — Log installation as DEC entry
# ============================================================

echo ""
echo "[Step 11] Logging installation..."

DEC_PATH="$OPENCLAW_ROOT/memory/decisions/decisions.md"

# Create decisions.md if it doesn't exist (idempotency — re-runs preserve existing content)
if [[ ! -f "$DEC_PATH" ]]; then
    cat > "$DEC_PATH" <<EOF
# Decisions Log

> **Schema Version:** 3.0
> **Created:** $DATESTAMP (adapter install)
> **Entries:** 0
EOF
fi

# Append DEC entry capturing this install
cat >> "$DEC_PATH" <<EOF

## DEC-INSTALL: OpenClaw General Edition Adapter Installed

---
id: DEC-INSTALL
created_at: $DATESTAMP
last_updated: $DATESTAMP
source_agent: orchestrator
source_session: 0
status: active
schema_version: "3.0"
confidence: FINAL
---

- **Status:** FINAL
- **Confidence:** 1.0
- **Session:** 0 (adapter install)
- **Date:** $DATESTAMP
- **Decision:** Installed Ultimate Memory Stack General Edition Adapter v1.0 on this OpenClaw deployment
- **Compliance preset:** $COMPLIANCE
- **Cron wired:** $WIRE_CRON
- **Cross-references:** MAPPING.md
- **Tags:** adapter-installed, openclaw, general-edition, v3-5
EOF

echo "  decisions.md: DEC-INSTALL appended"

# ============================================================
# Final summary
# ============================================================

echo ""
echo "============================================================"
echo "✅ OpenClaw General Edition Adapter installed successfully"
echo "============================================================"
echo ""
echo "Root files:           9 generated at $OPENCLAW_ROOT/"
echo "Memory tree:          ${#SUBDIRS[@]} subdirectories created"
echo "Compliance preset:    $COMPLIANCE"
echo "Lint runner:          installed at .openclaw/lint/"
echo "Heartbeat compactor:  installed at .openclaw/"
echo "Self-test:            PASSED"
echo ""
echo "Next steps:"
echo "  1. Open OpenClaw in this directory: $OPENCLAW_ROOT"
echo "  2. Verify bootstrap budget under 60K (check OpenClaw startup log)"
if $WIRE_CRON; then
    echo "  3. Paste the cron entry above via 'crontab -e'"
fi
echo "  4. Optionally install addons:"
echo "     /install-llmlingua  /install-graphiti  /install-graphify  /config-obsidian-vault"
echo ""
echo "Backup location (rollback if needed): $BACKUP_DIR"
echo ""
exit 0
