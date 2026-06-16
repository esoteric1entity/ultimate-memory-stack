---
name: install-ultimate-memory-stack
version: "1.3"
description: Interactive installer for the Ultimate Memory Stack v3.6.1. The public package ships general-edition only; a HIPAA/PHI-focused institutional edition is planned for a future release (not yet available — see CONTRIBUTING.md). Confirms general-edition, then walks the user through compliance preset (none/enterprise/custom), optional extensions (gdpr/soc2/pci-dss), consumer agent topology registration, and deployment-tier detection. Then copies common-specs + general-edition into the working directory, installs memory_protocol.md to .claude/rules/, initializes the memory/ structure (+ audit log + quarantine per preset), and runs the verify self-test. Use when the user asks to install, deploy, set up, or activate the Ultimate Memory Stack.
authors: ["see /AUTHORS.md"]
decision_authority: ["ideal-first design", "documentation discipline", "compliance presets", "Tier C designed-in", "modular consumer architecture"]
edition: any
license: Apache-2.0
---

# Install Ultimate Memory Stack v3.6.1 — Skill Workflow

When this skill is invoked (typically via `/install-ultimate-memory-stack` slash command or when the user asks Claude to install/deploy/activate the memory stack), execute the workflow below **IN ORDER**. Treat each step as required unless the user explicitly opts to skip.

This skill is one of the primary install methods, alongside the manual copy and the script-based installs.

---

## Step 0 — Confirm Install Intent

**First, refuse unsafe install locations.** Before anything else, check the current working directory:

```bash
case "$PWD" in
  "$HOME"|/|/etc|/usr|/var|/root|/tmp|/bin|/sbin)     echo "REFUSE" ;;
  /etc/*|/usr/*|/var/*|/root/*|/tmp/*|/bin/*|/sbin/*) echo "REFUSE" ;;
  *)                                                  echo "OK" ;;
esac
```

If this returns `REFUSE`, **STOP** and tell the user:

> ⚠️ Refusing to install into `<PWD>`. The installer scaffolds `memory/`, `.claude/`, and `ultimate-memory-stack/` into the current directory — installing into your home or a system directory would scatter these across it. `cd` into a dedicated project directory first, then re-run `/install-ultimate-memory-stack`.

Do not proceed until the working directory is a project directory (not `$HOME` or a system path).

Then greet the user briefly and confirm intent:

```
👋 You're about to install the Ultimate Memory Stack v3.6.1 in:
    <current working directory>

This will:
  - Copy common-specs/ + your chosen edition into your working directory
  - Create .claude/rules/memory_protocol.md (auto-loads each Claude Code session)
  - Initialize the memory/ directory structure (9 subdirs)
  - Set up audit log + quarantine (per edition + preset)
  - Run a setup wizard to populate user profile + projects + preferences
  - Run a self-test (T1–T9) to verify everything's good

Continue? [Y/n]:
```

If the user says no, stop gracefully and explain how to invoke this skill again.

---

## Step 0.5 — Existing-store safety gate (DATA-SAFETY — do this BEFORE any write)

**Before copying or creating anything,** check the working directory for an existing memory store — a prior Ultimate Memory Stack install, *or* the user's own `memory/` at this path:

```bash
ls -d "<WORKING_DIR>/memory" 2>/dev/null            # existing memory store?
cat "<WORKING_DIR>/.ums-manifest.json" 2>/dev/null  # prior install manifest?
```

If `<WORKING_DIR>/memory/` **or** `<WORKING_DIR>/.ums-manifest.json` exists, this is a **re-install / install-over-existing-data**, NOT a fresh install. The user's accumulated memory is irreplaceable — you MUST NOT overwrite it. Do all of the following:

1. **Back up first**, before any write:
   ```bash
   cp -r "<WORKING_DIR>/memory" "<WORKING_DIR>/memory.backup.$(date -u +%Y%m%d-%H%M%SZ)"
   ```
2. **Tell the user plainly:** an existing memory store was found and backed up to `memory.backup.<ts>/`, and their data will be preserved.
3. **Switch to PRESERVE mode** for the rest of this skill. The product-owned spec tree (`common-specs/`, `<edition>-edition/`) is regenerable and may be refreshed, but **every user-data file is create-only-if-absent — NEVER overwritten.** This binds Steps 7e, 8, and 9: when a target user-data file (`session_state.md`, `MEMORY_INDEX.md`, `user_profile.md`, project briefs, `feedback.md`, audit/quarantine logs) already exists, **skip it** (the existing data is authoritative) or ask the user before touching it — do not `Write` over it.

If neither is found, this is a fresh install — proceed normally.

> This mirrors what the shell installer (`setup-memory-stack.sh`) and the agent flow (`INSTALL_AGENT.md` Step 1.2) already do; the skill door must match them.

---

## Step 1 — Locate Source Package

Ask the user for the location of the Ultimate Memory Stack source package:

```
Where is the Ultimate Memory Stack source package located?

You need a folder containing:
  - common-specs/ (the universal foundation)
  - general-edition/ (the edition shipped publicly)
    (biotech-edition/ is the separate institutional package, if you have it)

Common locations (substitute your actual path):
  - A local git clone (Linux/Mac): ~/projects/ultimate-memory-stack
  - A local git clone (Windows): C:\Projects\ultimate-memory-stack
  - Your downloads folder: ~/Downloads/ultimate-memory-stack
  - A removable / external drive: <drive>:/path/to/ultimate-memory-stack
  - A network share: <share-path>/ultimate-memory-stack
  - Any other directory where you have the unpacked source files

Path:
```

Validate the response:
1. Read the directory listing at the provided path
2. Confirm `common-specs/` exists at that path
3. Confirm `general-edition/` exists (the edition shipped publicly)
4. If validation fails, explain what's missing and ask again (up to 3 retries before suggesting Method A manual install)

Save this as `SOURCE_PATH` for use in subsequent steps.

---

## Step 2 — Confirm Edition

First check which edition directories actually exist at `SOURCE_PATH` and confirm — do not present a choice. The public package ships `general-edition/` only (a HIPAA/PHI-focused institutional edition is planned for a future release, not yet available — see CONTRIBUTING.md), so skip any menu and confirm general-edition. `EDITION` is always `general`.

```
Installing the general-edition (the public package).
Continuing with general-edition...
```

Verify that the general-edition directory exists at `<SOURCE_PATH>/general-edition/`. If not, surface the error and stop.

---

## Step 3 — Compliance Preset Selection (general-edition only)

Ask:

```
Compliance preset?

  [1] none — solo dev / personal projects / no regulatory exposure (RECOMMENDED for most)
  [2] enterprise — Business-customer PII, SOC2 prep, GDPR awareness
  [3] custom — Multiple regimes; requires overrides/compliance.override.md

Pick 1, 2, or 3:
```

Validate input. Save as `COMPLIANCE_PRESET`.

If user picks `3` (custom), additionally verify that `<SOURCE_PATH>/general-edition/overrides/compliance.override.md` exists. Custom requires ≥1 explicit override; if missing, refuse and ask user to either provide that file or pick a base preset.

---

## Step 4 — Extensions (optional)

Ask:

```
Compliance extensions? (optional, comma-separated; or "none")

  - gdpr — EU jurisdiction + consent tracking + right-to-be-forgotten
  - soc2 — SOC2 Trust Services Criteria audit-ready evidence
  - pci-dss — Payment card data context (aggressive PAN detection)

Most users start with NONE. Compose multiple if needed (e.g., "soc2,gdpr").

Your selection:
```

Parse the comma-separated list. Validate each extension name against the allowed set: `{gdpr, soc2, pci-dss}`. Save as `EXTENSIONS` (list, possibly empty).

---

## Step 5 — Consumer Agent Topology

Ask:

```
Consumer agent topology — what sub-agents will use this memory stack?

The memory stack is brand-protected (canonical schemas, protocols) but consumer-pluggable
(your specific sub-agent names are registered here).

Examples:
  - Reference 4-agent example: "warden, sentinel, vault, clerk"
  - Custom architecture: any names of your own, matching pattern [a-z][a-z0-9-]*
  - No sub-agents: "none" (you'll just use standard slots: user, orchestrator, webfetch, etc.)

Your agents (comma-separated, or "none"):
```

Parse the comma-separated list. Validate each name against `[a-z][a-z0-9-]*`. Save as `CONSUMER_AGENTS`.

These will be added to the user_profile.md as registered consumer-defined `source_agent` slots.

---

## Step 6 — Auto-Detect Deployment Tier

Use Bash (or available shell) to probe infrastructure:

```bash
# Check Node.js
node --version 2>/dev/null

# Check Python crypto availability
python3 -c "import cryptography; print(cryptography.__version__)" 2>/dev/null

# Check Ollama
ollama --version 2>/dev/null

# Check Skills availability (this skill itself runs, so Skills must be on — implies T4 partial)
```

Determine `EFFECTIVE_TIER` based on results:
- T0: no Node.js, no Python crypto, no Ollama
- T1: Ollama OR Transformers.js available
- T2: Node.js available
- T3: Python crypto available (Code Execution)
- T4: Skills enabled (we know this because skill is running) + Anthropic Dreaming beta (ask if uncertain)

Report findings to user:

```
Detected deployment tier: T<X>

Active at this tier:
  - <list of activated features>

Designed-in but dormant (activate when infrastructure unblocks):
  - <list>

Proceeding with install...
```

---

## Step 7 — Execute Installation

This is the file-copy + scaffold step. Use Read, Write, Edit tools as needed.

> **Re-install (Step 0.5 PRESERVE mode):** the spec copy in 7b is regenerable (safe to refresh), and `mkdir -p` (7d) / `touch` (7e) are non-destructive — but never `Write` over an existing user-data file. Honor the gate below in 7e, 8, and 9.

### 7a. Set target paths
- `WORKING_DIR` = current working directory (where the user is)
- `STACK_DIR` = `<WORKING_DIR>/ultimate-memory-stack`
- `CLAUDE_RULES_DIR` = `<WORKING_DIR>/.claude/rules`
- `MEMORY_DIR` = `<WORKING_DIR>/memory`

### 7b. Copy common-specs/ + chosen edition

Use Bash:
```bash
mkdir -p "<STACK_DIR>"
cp -r "<SOURCE_PATH>/common-specs" "<STACK_DIR>/common-specs"
cp -r "<SOURCE_PATH>/<EDITION>-edition" "<STACK_DIR>/<EDITION>-edition"
```

Report: "✓ Files copied"

### 7c. Install memory_protocol.md to .claude/rules/

```bash
mkdir -p "<CLAUDE_RULES_DIR>"
cp "<STACK_DIR>/common-specs/MEMORY_PROTOCOL.md" "<CLAUDE_RULES_DIR>/memory_protocol.md"
```

Report: "✓ memory_protocol.md installed to .claude/rules/ (auto-loads each session)"

### 7d. Initialize memory/ directory structure

```bash
mkdir -p "<MEMORY_DIR>/sessions"
mkdir -p "<MEMORY_DIR>/decisions"
mkdir -p "<MEMORY_DIR>/feedback"
mkdir -p "<MEMORY_DIR>/projects"
mkdir -p "<MEMORY_DIR>/security"
mkdir -p "<MEMORY_DIR>/references"
mkdir -p "<MEMORY_DIR>/user"
mkdir -p "<MEMORY_DIR>/archive"
mkdir -p "<MEMORY_DIR>/quarantine"
```

Report: "✓ memory/ directory structure initialized (9 subdirs)"

### 7e. Initialize audit log + quarantine log (preset-dependent)

For preset `none`: SKIP this step (audit is OPT-IN).
For preset `enterprise/custom`: create both files:
```bash
touch "<MEMORY_DIR>/security/audit_log.jsonl"
touch "<MEMORY_DIR>/quarantine/quarantine_log.jsonl"
```

Append initialization entry to audit_log.jsonl (if created):
```json
{"ts":"<ISO-8601-UTC>","actor":"install-skill","actor_session":0,"action":"initialize","entry_id":"<bootstrap>","entry_path":"memory/","entry_category":"system","entry_summary":"Ultimate Memory Stack v3.6.1 deployment initialized via Skill installer; edition=<EDITION>; preset=<COMPLIANCE_PRESET>; extensions=<EXTENSIONS>","outcome":"success"}
```

Report appropriately based on what was initialized.

### 7f. Update PROFILE.md with selected preset + extensions

Use Edit tool to modify `<STACK_DIR>/general-edition/PROFILE.md`:
- Set `compliance: <COMPLIANCE_PRESET>` (was `compliance: none`)
- Add `extensions:` list if extensions were selected

> **PRESERVE mode (Step 0.5):** on a re-install, if `PROFILE.md` already carries user customizations (a `compliance:`/`extensions:` value different from the package default, or hand-added fields), do **NOT** blindly reset it — show the user the current values and confirm before editing. The spec tree is regenerable, but an edited PROFILE is the user's configuration.

---

## Step 8 — Setup Wizard

This is per BOOTSTRAP_PROMPT.md Step 7. Ask the user in order, saving answers to indicated files:

> **PRESERVE mode (Step 0.5):** if a target file already exists (`user_profile.md`, a project's `projectbrief.md`, `feedback.md`), do **NOT** overwrite it — the existing content is the user's real data. Skip it, or show the user the existing content and ask before changing anything. Only write these files when they are absent (fresh install).

> **Explicit guard:** before writing ANY file in 8a–8c, check existence first — never overwrite user data:
> ```bash
> [ -e "<target_file>" ] && echo "EXISTS — preserve: do NOT Write/Edit; show the user and ask first" || echo "ABSENT — safe to create"
> ```
> Apply to `user_profile.md`, each project's `projectbrief.md`, and `feedback.md`.

### 8a. Identity (→ memory/user/user_profile.md)

Ask:
- Name + role + organization
- Primary tech stack / languages / frameworks
- Domain
- Response style preferences (brief vs detailed, technical level)

Write user_profile.md with SCHEMA_A18 frontmatter + content.

### 8b. Active Projects (→ memory/projects/<slug>/memory-bank/projectbrief.md per project)

Ask:
- List of active projects (1 per line, slug + brief description)
- Goal + status for each

For each project, create the 6-file Cline-convention memory bank directory + populate projectbrief.md with skeleton.

### 8c. Pet Peeves (→ memory/feedback/feedback.md)

Ask:
- Things to NEVER do
- Things to ALWAYS do

Create initial feedback entries with SCHEMA_A18 frontmatter.

### 8d. Save Consumer Agent Topology (→ memory/user/user_profile.md)

Already captured in Step 5. Append to user_profile.md as `registered_consumer_agents: [<list>]`.

### 8e. Save Deployment Tier (→ memory/user/user_profile.md)

Already detected in Step 6. Append to user_profile.md as `deployment_tier: T<X>` + per-feature breakdown.

---

## Step 9 — Initialize session_state.md + MEMORY_INDEX.md

> **PRESERVE mode (Step 0.5) — this is the highest-risk step.** Create `session_state.md` and `MEMORY_INDEX.md` **ONLY if they do not already exist.** If either is present, leave it **completely untouched** — an existing store already holds accumulated session history and a populated index, and overwriting them with a fresh "Session 1" / empty-counts template is exactly the data loss this gate exists to prevent. Skip to Step 10 in that case.

For a fresh install (neither file exists), create `<MEMORY_DIR>/sessions/session_state.md` with Session 1 — Initial Setup:

```markdown
# Session State

> **Schema Version:** 3.0
> **Current Session:** 1
> **Date:** <ISO-DATE>

---

## Session 1 — Initial Setup (<DATE>)

---
id: SESSION-001
created_at: <DATE>
last_updated: <DATE>
valid_at: <DATE>
source_agent: install-skill
source_session: 1
status: active
schema_version: "3.0"
---

### Session Summary
Initial setup via Skill installer. Ultimate Memory Stack v3.6.1 deployed:
- Edition: <EDITION>
- Compliance preset: <COMPLIANCE_PRESET>
- Extensions: <EXTENSIONS>
- Consumer agents: <CONSUMER_AGENTS>
- Effective tier: T<X>

### Next Steps
- Start working in Claude Code; session_state will heartbeat automatically
- Memory protocol auto-loaded via .claude/rules/memory_protocol.md
```

Create `<MEMORY_DIR>/MEMORY_INDEX.md` with empty counts per template at `common-specs/templates/MEMORY_INDEX.template.md`.

---

## Step 10 — Run T1–T9 Self-Test

Per `MEMORY_PROTOCOL.md §1.3`:

Silently check:
- **T1:** session_state.md exists with Schema Version header
- **T2:** MEMORY_INDEX.md exists; counts non-negative
- **T3:** Session number ≥ previous (no regression — N/A for fresh install)
- **T4:** No memory file exceeds size limit (N/A for fresh install)
- **T5:** All files referenced in MEMORY_INDEX.md exist
- **T6:** Schema versions ≤ protocol version
- **T7:** No PII/PHI patterns detected (fresh install: should be clean)
- **T8:** All entries have valid SCHEMA_A18 frontmatter
- **T9:** Edition profile loaded; override-file map resolves

Report results. All pass → proceed to Step 11. Any failure → surface to user with remediation suggestion.

---

## Step 11 — Greet + Confirm Install Complete

Final summary:

```
========================================
✅ Ultimate Memory Stack v3.6.1 — INSTALLED
========================================

Edition: <EDITION>
Compliance: <COMPLIANCE_PRESET>
Extensions: <EXTENSIONS or "none">
Consumer agents: <CONSUMER_AGENTS or "none">
Effective tier: T<X>

What was created:
  ✓ <WORKING_DIR>/ (spec package)
  ✓ <WORKING_DIR>/.claude/rules/memory_protocol.md (auto-loaded)
  ✓ <WORKING_DIR>/memory/ (9 subdirs initialized)
  ✓ <WORKING_DIR>/memory/sessions/session_state.md (Session 1)
  ✓ <WORKING_DIR>/memory/MEMORY_INDEX.md
  ✓ Audit log + quarantine log (per preset)
  ✓ User profile + project briefs + feedback (from wizard)

Self-test: ALL PASS ✅

What's next:
  - Just start working. Memory protocol auto-loads every session.
  - At session end, say "update session state" — Claude will record progress.
  - Re-validate any time: run the package's `verify.sh` from the package root, or ask Claude to re-run the T1–T9 self-test per MEMORY_PROTOCOL.md.
  - Read USER_CHEAT_SHEET_core.md (in common-specs/) for daily best practices.
  - Need help? Read INSTALLATION_GUIDE.md or your edition's DEPLOYMENT.md.
```

---

## Error Handling

If any step fails:
1. Surface the specific error to the user
2. Roll back partial changes if possible (especially file copies that may have partially succeeded)
3. Provide remediation:
   - "Try Method A manual install per INSTALLATION_GUIDE.md §4"
   - "Try Method B Bash install per INSTALLATION_GUIDE.md §5"
   - "Check that SOURCE_PATH exists and contains common-specs/ + edition/"
4. Log the failure event if an audit log exists

---

## Skill Constraints + Trust Boundaries

- This skill operates with Read / Write / Edit / Bash tools as needed
- It does NOT modify files outside the working directory + ~/.config/keys/ (if T3+ key generation)
- For custom preset: refuses to proceed without `overrides/compliance.override.md`
- When an existing store is detected (Step 0.5), it is backed up to `memory.backup.<ts>/` before any write, and user-data files are never overwritten — so an install-over-existing-data is recoverable. (Fresh installs create no backup because there is nothing yet to preserve.)

---

## Cross-References

- `INSTALLATION_GUIDE.md` §6 (this skill's section in the install guide)
- `BOOTSTRAP_PROMPT.md` §The Activation Prompt (the Manual / Bash equivalent workflow)
- `common-specs/MODULARITY.md` (consumer agent topology rationale)
- `common-specs/SCHEMA_compliance_profile.md` §5 (preset definitions)

---

## Skill Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 DRAFT | 2026-05-15 | Initial implementation |
| 1.0 STABLE | 2026-06-10 | Public-readiness fixes (edition-availability detection in Step 2; genericized internal refs); executed end-to-end (fresh install, general-edition, preset=none, T2) — T1–T9 self-test 9/9 PASS → promoted DRAFT → STABLE |
| 1.1 | 2026-06-15 | **Data-safety fix.** Added Step 0.5 existing-store gate: a re-install over an existing `memory/` now backs it up (`memory.backup.<ts>/`) and preserves it. Steps 7e/8/9 are now create-if-absent — the skill no longer overwrites `session_state.md`, `MEMORY_INDEX.md`, `user_profile.md`, project briefs, or `feedback.md` on an existing store (the prior behavior silently reset accumulated memory to empty templates). Corrected the false "reversible via backup" claim. Brings the skill door in line with `setup-memory-stack.sh` + `INSTALL_AGENT.md`, which already preserved user data. |
| 1.2 | 2026-06-15 | **Public-offer alignment.** Removed the public biotech-edition offer (Step 2 edition menu → confirm general-edition; `EDITION` always `general`) and the healthcare compliance-preset + healthcare extension offers, all of which the installer refuses (general-edition install rejects healthcare/biotech with "institutional edition only"). Deleted the dead biotech branches in Steps 3, 4, 7e, 7f, Error Handling, and Skill Constraints. General-edition now offers `none/enterprise/custom` presets + `gdpr/soc2/pci-dss` extensions only. Honest disclosures kept and de-overpromised: a HIPAA/PHI-focused institutional edition is planned for a future release (not yet available — see CONTRIBUTING.md). |
| 1.3 | 2026-06-16 | **Data-safety hardening + Door-3 alignment (v3.6.1).** Added a Step 0 guard refusing installs into `$HOME` / system directories (`/`, `/etc`, `/usr`, `/var`, `/root`, `/tmp`). Made the Step 0.5 PRESERVE guard explicit in Step 8 (per-file `[ -e ]` existence check before any Write; never overwrite user data) + a Step 7f note to confirm before resetting a user-customized `PROFILE.md`. No behavior change for fresh installs. |

When this skill is updated, bump `version:` in the frontmatter + record changes here. Treat the skill itself like any other memory stack artifact — schema_version compatibility matters.

---

## Testing Notes

**v1.0 STABLE** — executed end-to-end on 2026-06-10 (fresh-install scenario: T2 machine, general-edition, preset=none, no extensions). All file operations verified; templates instantiate cleanly; **T1–T9 self-test: 9/9 PASS**.

Remaining test scenarios for future versions:

1. **HIPAA install scenario** — empty working directory + the institutional edition (a HIPAA/PHI-focused institutional edition is planned for a future release, not yet available — see CONTRIBUTING.md)
2. **Edge cases:**
   - SOURCE_PATH doesn't exist (error handling)
   - Custom preset without override file (rejection path)
   - Mid-install interruption (rollback behavior)
3. **Document bugs found** via GitHub Issues
