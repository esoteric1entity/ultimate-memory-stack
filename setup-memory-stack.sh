#!/bin/bash
# ==============================================================================
# Ultimate Memory Stack v3.6.2 — top-level installer (Linux / macOS / WSL)
# Apache-2.0 © 2026 esoteric1entity. A PDuk Brainworks project.
# ==============================================================================
#
# Usage (run from the directory where the stack should live, or use --target):
#   ./setup-memory-stack.sh                              # default: general-edition + all addons
#   ./setup-memory-stack.sh --minimal                    # core only (no addons)
#   ./setup-memory-stack.sh --addon memory-graphiti      # core + selected addon(s)
#   ./setup-memory-stack.sh --addon memory-vault --addon memory-graphiti
#   ./setup-memory-stack.sh --no-templater               # skip Obsidian Templater auto-enable
#   ./setup-memory-stack.sh --edition general            # explicit edition
#   ./setup-memory-stack.sh --target ~/my-workspace      # install somewhere else
#   ./setup-memory-stack.sh --yes                        # non-interactive (accept defaults)
#   ./setup-memory-stack.sh --help
#
# Pass-through flags forwarded to general-edition/setup.sh:
#   --compliance=<none|enterprise|custom>
#   --extensions=<csv>
#   --migrate-from=<old_version>
#   --backup-location=<path>
#   --skip-wizard
#
# Addons (registered as Claude Code Skills for user to invoke):
#   memory-vault       — Obsidian vault config (recommended-addons/obsidian-vault-config)
#   memory-graphiti    — bi-temporal knowledge graph (recommended-addons/graphiti-installer)
#   memory-graphify    — code symbol graph (recommended-addons/graphify-installer)
#   memory-llmlingua   — prompt compression (recommended-addons/llmlingua-installer)
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Version is single-sourced from the package-root VERSION file (#14 fix)
if [ -f "$SCRIPT_DIR/VERSION" ]; then
    STACK_VERSION="$(tr -d ' \r\n' < "$SCRIPT_DIR/VERSION")"
else
    STACK_VERSION="3.6.2"
fi

# ---------- arg parsing ----------
EDITION="general"
MINIMAL=false
SKIP_TEMPLATER=false
ASSUME_YES=false
TARGET_ARG=""
ADDONS=()
REGISTERED=()
REGISTERED_SKILLS=()
PASS_THROUGH=()
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --edition=*)        EDITION="${1#*=}"; shift ;;
        --edition)          EDITION="$2"; shift 2 ;;
        --minimal)          MINIMAL=true; shift ;;
        --addon=*)          ADDONS+=("${1#*=}"); shift ;;
        --addon)            ADDONS+=("$2"); shift 2 ;;
        --no-templater)     SKIP_TEMPLATER=true; shift ;;
        --target=*)         TARGET_ARG="${1#*=}"; shift ;;
        --target|-t)        TARGET_ARG="$2"; shift 2 ;;
        --yes|-y)           ASSUME_YES=true; shift ;;
        --help|-h)          SHOW_HELP=true; shift ;;
        *)                  PASS_THROUGH+=("$1"); shift ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    sed -n '4,35p' "$0"
    exit 0
fi

# ---------- target resolution (DETECT + CONFIRM) ----------
OPENCLAW_WS="$HOME/.openclaw/workspace"
TARGET="$TARGET_ARG"

if [ -z "$TARGET" ]; then
    TARGET="$(pwd)"
    if [ "$ASSUME_YES" = false ] && [ -t 0 ]; then
        echo "▶ Where should the memory stack be installed?"
        DEFAULT_CHOICE=1
        echo "    [1] Current directory:           $(pwd)"
        if [ -d "$OPENCLAW_WS" ]; then
            echo "    [2] OpenClaw workspace (found):  $OPENCLAW_WS"
        fi
        echo "    [3] Custom path"
        if [ "$(pwd)" = "$SCRIPT_DIR" ]; then
            echo "  ⚠ The current directory is the package itself — installing here would mix"
            echo "    your memory data into the package tree (and into its git history)."
            if [ -d "$OPENCLAW_WS" ]; then DEFAULT_CHOICE=2; else DEFAULT_CHOICE=3; fi
        fi
        read -r -p "  Choice [${DEFAULT_CHOICE}]: " CHOICE
        CHOICE="${CHOICE:-$DEFAULT_CHOICE}"
        case "$CHOICE" in
            1) TARGET="$(pwd)" ;;
            2) TARGET="$OPENCLAW_WS" ;;
            3) read -r -p "  Path: " TARGET ;;
            *) echo "❌ Invalid choice" >&2; exit 1 ;;
        esac
    fi
fi

# Expand ~ and make absolute (creating the directory if needed)
TARGET="${TARGET/#\~/$HOME}"
mkdir -p "$TARGET"
TARGET="$( cd "$TARGET" && pwd )"

# Guard: never install into the package itself without explicit consent
if [ "$TARGET" = "$SCRIPT_DIR" ]; then
    if [ "$ASSUME_YES" = false ] && [ -t 0 ]; then
        read -r -p "  ⚠ Really install INTO the package directory itself? [y/N]: " CONFIRM
        case "$CONFIRM" in
            y|Y) : ;;
            *) echo "Aborted — run from your working directory, or pass --target <dir>."; exit 1 ;;
        esac
    else
        echo "❌ Refusing to install into the package directory itself ($SCRIPT_DIR)." >&2
        echo "   Run from your working directory, or pass --target <dir>." >&2
        exit 1
    fi
fi

# Existing-install handling (memory/ data is never touched by a re-install)
if [ -f "$TARGET/.ums-manifest.json" ] || [ -d "$TARGET/memory" ]; then
    echo "ℹ Existing install detected at $TARGET"
    if [ -f "$TARGET/.ums-manifest.json" ]; then
        grep -o '"version": *"[^"]*"' "$TARGET/.ums-manifest.json" | head -1 | sed 's/^/    manifest: /'
    fi
    # The scaffolded spec tree is product-owned and regenerable — refresh it so the
    # edition setup can re-copy cleanly. memory/ (user data) is never touched.
    if [ -d "$TARGET/ultimate-memory-stack/common-specs" ]; then
        if [ "$ASSUME_YES" = false ] && [ -t 0 ]; then
            read -r -p "    Refresh the scaffolded specs in place? memory/ data is not touched. [Y/n]: " REFRESH
            case "$REFRESH" in
                n|N) echo "Aborted — nothing changed."; exit 1 ;;
            esac
        fi
        rm -rf "$TARGET/ultimate-memory-stack"
        echo "    ↻ Scaffolded spec tree refreshed (memory/ untouched)."
    fi
    echo "    (Upgrading from a v2.0 deployment? Use --migrate-from=v2.0 instead.)"
fi

export WORKING_DIR="$TARGET"
# Option C: tell the edition setup it's running under the top-level installer, so
# it suppresses its own "Next steps" block — this script prints the single
# harness-correct summary below.
export UMS_PARENT=1

# ---------- harness detection (BEFORE we create anything, so we detect the
# user's pre-existing harness rather than our own artifacts) ----------
HARNESS="generic"
if { [ -f "$TARGET/AGENTS.md" ] && [ -f "$TARGET/SOUL.md" ]; } || [ "$TARGET" = "$OPENCLAW_WS" ]; then
    HARNESS="openclaw"
elif [ -d "$TARGET/.claude" ]; then
    HARNESS="claude-code"
fi

# ---------- precondition checks ----------
if [ ! -d "$SCRIPT_DIR/$EDITION-edition" ]; then
    echo "❌ Edition '$EDITION' not found at $SCRIPT_DIR/$EDITION-edition" >&2
    echo "   Available editions:" >&2
    for d in "$SCRIPT_DIR"/*-edition; do
        [ -d "$d" ] && echo "     - ${d##*/}" >&2
    done
    exit 1
fi

if ! command -v bash >/dev/null 2>&1; then
    echo "❌ bash is required but not installed." >&2
    exit 1
fi

# ---------- run base install ----------
echo "▶ Ultimate Memory Stack v${STACK_VERSION} — ${EDITION}-edition install"
echo "  Install target: ${TARGET}"
echo

# Invoke by absolute path WITHOUT cd — the edition script derives WORKING_DIR
# from the exported env var (falling back to the caller's pwd).
bash "$SCRIPT_DIR/$EDITION-edition/setup.sh" "${PASS_THROUGH[@]}"

# ---------- addon registration ----------
if [ "$MINIMAL" = true ]; then
    echo
    echo "↷ Skipping addons (--minimal). Base install complete."
    echo "  To install addons later, re-run with:  ./setup-memory-stack.sh --addon <name>"
else
    # Default addon set (when no explicit --addon flags given)
    if [ ${#ADDONS[@]} -eq 0 ]; then
        ADDONS=("memory-vault" "memory-graphiti" "memory-graphify" "memory-llmlingua")
    fi

    # Addon-name → package-directory lookup. Deliberately a case statement,
    # not an associative array: macOS ships bash 3.2, which has no `declare -A`.
    addon_dir() {
        case "$1" in
            memory-vault)     echo "recommended-addons/obsidian-vault-config" ;;
            memory-graphiti)  echo "recommended-addons/graphiti-installer" ;;
            memory-graphify)  echo "recommended-addons/graphify-installer" ;;
            memory-llmlingua) echo "recommended-addons/llmlingua-installer" ;;
            *)                echo "" ;;
        esac
    }

    SKILLS_DIR="$TARGET/.claude/skills"
    mkdir -p "$SKILLS_DIR"

    echo
    echo "▶ Registering addons (Claude Code Skills)"
    # Claude Code discovers skills as .claude/skills/<name>/SKILL.md, where
    # <name> is the SKILL.md frontmatter `name:` field. (#12 fix, 2026-06-11:
    # the previous flat install-<addon>.md copies were never discoverable,
    # and the printed slash-command hints didn't match the real names —
    # every advertised addon command was dead.)
    for addon in "${ADDONS[@]}"; do
        DIR="$(addon_dir "$addon")"
        if [ -z "$DIR" ]; then
            echo "  ⚠ Unknown addon: $addon (skipping)"
            continue
        fi
        SRC="$SCRIPT_DIR/$DIR/SKILL.md"
        if [ ! -f "$SRC" ]; then
            echo "  ⚠ Skill file not found for $addon at $SRC (skipping)"
            continue
        fi
        SKILL_NAME="$(sed -n 's/^name:[[:space:]]*//p' "$SRC" | head -1 | tr -d '\r')"
        if [ -z "$SKILL_NAME" ]; then
            echo "  ⚠ ${addon}: SKILL.md has no name: frontmatter (skipping)"
            continue
        fi
        mkdir -p "$SKILLS_DIR/$SKILL_NAME"
        cp "$SRC" "$SKILLS_DIR/$SKILL_NAME/SKILL.md"
        if [ "$SKIP_TEMPLATER" = true ] && [ "$addon" = "memory-vault" ]; then
            # Appended AFTER the file body — prepending broke the YAML
            # frontmatter (file no longer started with ---).
            printf '\n<!-- Installed with --no-templater: skip the Templater community-plugins auto-enable step. -->\n' >> "$SKILLS_DIR/$SKILL_NAME/SKILL.md"
            echo "  ✓ ${addon} → /${SKILL_NAME} (Templater auto-enable skipped)"
        else
            echo "  ✓ ${addon} → /${SKILL_NAME}"
        fi
        REGISTERED+=("$addon")
        REGISTERED_SKILLS+=("$SKILL_NAME")
    done
fi

# ---------- harness registration ----------
REG_NOTE="none"
PROTOCOL_SRC="$TARGET/ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md"
if [ -f "$PROTOCOL_SRC" ]; then
    mkdir -p "$TARGET/.claude/rules"
    cp "$PROTOCOL_SRC" "$TARGET/.claude/rules/memory_protocol.md"
    REG_NOTE=".claude/rules/memory_protocol.md"
fi

# ---------- install manifest ----------
MANIFEST="$TARGET/.ums-manifest.json"
INSTALLED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ADDON_JSON=""
for a in "${REGISTERED[@]}"; do ADDON_JSON="${ADDON_JSON}\"${a}\", "; done
ADDON_JSON="[${ADDON_JSON%, }]"
cat > "$MANIFEST" <<EOF
{
  "package": "ultimate-memory-stack",
  "version": "${STACK_VERSION}",
  "edition": "${EDITION}",
  "installed_at": "${INSTALLED_AT}",
  "install_door": "script",
  "harness_detected": "${HARNESS}",
  "minimal": ${MINIMAL},
  "addons": ${ADDON_JSON},
  "source_package": "${SCRIPT_DIR}",
  "registered": "${REG_NOTE}"
}
EOF

# ---------- summary ----------
echo
echo "✅ Ultimate Memory Stack v${STACK_VERSION} — install complete"
echo
echo "Summary:"
echo "  Edition:    ${EDITION}"
echo "  Addons:     ${REGISTERED[*]:-none}"
echo "  Workspace:  ${TARGET}"
echo "  Harness:    ${HARNESS}"
echo "  Registered: ${REG_NOTE}"
echo "  Manifest:   .ums-manifest.json"
echo
echo "Next steps:"
STEP=1
echo "  ${STEP}. Open your agent harness in this directory"; STEP=$((STEP+1))
if [ ${#REGISTERED_SKILLS[@]} -gt 0 ]; then
    echo "  ${STEP}. Invoke each addon Skill to complete its install:"; STEP=$((STEP+1))
    for skill in "${REGISTERED_SKILLS[@]}"; do
        echo "       /${skill}"
    done
fi
echo "  ${STEP}. Validate the install:  $SCRIPT_DIR/verify.sh $TARGET"
case "$HARNESS" in
    openclaw)
        echo
        echo "  OpenClaw workspace detected — for deep integration (9 root files), run the"
        echo "  OpenClaw adapter: see core/openclaw-adapter/QUICKSTART.md in the cloned package" ;;
    generic)
        echo
        echo "  Using another harness? Point it at memory/ + the protocol from your AGENTS.md —"
        echo "  see INSTALL_AGENT.md in the package for the harness-agnostic wiring steps." ;;
esac
echo
