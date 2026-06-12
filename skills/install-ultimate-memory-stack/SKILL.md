---
name: install-ultimate-memory-stack
description: Interactive installer for the Ultimate Memory Stack v3.6.0. Detects which editions are actually present and offers only those (the public package ships general-edition; biotech-edition is a separate institutional package). Walks the user through edition confirmation, compliance preset (general-edition supports none/enterprise/custom — PHI/healthcare is institutional biotech-edition only), optional extensions (gdpr/soc2/pci-dss), consumer agent topology registration, and deployment-tier detection. Then copies common-specs + chosen edition into the working directory, installs memory_protocol.md to .claude/rules/, initializes the memory/ structure (+ audit log + quarantine per preset), and runs the verify self-test. Use when the user asks to install, deploy, set up, or activate the Ultimate Memory Stack.
version: "1.0"
authors: ["see /AUTHORS.md"]
decision_authority: ["ideal-first design", "documentation discipline", "compliance presets", "Tier C designed-in", "modular consumer architecture"]
edition: any
license: Apache-2.0
---

# Install Ultimate Memory Stack v3.6.0 — Skill Workflow

When this skill is invoked (typically via `/install-ultimate-memory-stack` slash command or when the user asks Claude to install/deploy/activate the memory stack), execute the workflow below **IN ORDER**. Treat each step as required unless the user explicitly opts to skip.

This skill is one of the primary install methods, alongside the manual copy and the script-based installs.

---

## Step 0 — Confirm Install Intent

Greet the user briefly and confirm intent:

```
👋 You're about to install the Ultimate Memory Stack v3.6.0 in:
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

## Step 1 — Locate Source Package

Ask the user for the location of the Ultimate Memory Stack source package:

```
Where is the Ultimate Memory Stack source package located?

You need a folder containing:
  - common-specs/ (the universal foundation)
  - At least one of: biotech-edition/ OR general-edition/

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
3. Confirm at least one edition directory (`biotech-edition/` or `general-edition/`) exists
4. If validation fails, explain what's missing and ask again (up to 3 retries before suggesting Method A manual install)

Save this as `SOURCE_PATH` for use in subsequent steps.

---

## Step 2 — Select Edition

First check which edition directories actually exist at `SOURCE_PATH` and offer only those (the public package ships `general-edition/` only; biotech-edition is a separate institutional package). If only one edition is present, confirm it rather than presenting a choice. Ask:

```
Which edition do you want to install?

  [1] biotech-edition — HIPAA-active, non-overridable.
                        Recommended for: healthcare R&D, regulated biotech contexts.

  [2] general-edition — User-configurable compliance.
                        Recommended for: software dev, research, writing, education, B2B SaaS, enterprise.

Pick 1 or 2:
```

Validate input is exactly `1` or `2`. Save as `EDITION` (`biotech` or `general`).

Verify that the chosen edition directory exists at `<SOURCE_PATH>/<edition>-edition/`. If not, surface the error and stop.

---

## Step 3 — Compliance Preset Selection (general-edition only)

If `EDITION == general`, ask:

```
Compliance preset?

  [1] none — solo dev / personal projects / no regulatory exposure (RECOMMENDED for most)
  [2] healthcare — HIPAA-adjacent work (volunteer clinical, side consulting)
  [3] enterprise — Business-customer PII, SOC2 prep, GDPR awareness
  [4] custom — Multiple regimes; requires overrides/compliance.override.md

Pick 1, 2, 3, or 4:
```

Validate input. Save as `COMPLIANCE_PRESET`.

If user picks `4` (custom), additionally verify that `<SOURCE_PATH>/general-edition/overrides/compliance.override.md` exists. Custom requires ≥1 explicit override; if missing, refuse and ask user to either provide that file or pick a base preset.

If `EDITION == biotech`, automatically set `COMPLIANCE_PRESET = healthcare` (non-overridable in biotech-edition). Tell user: "Biotech-edition locks compliance to `healthcare`. Continuing with `healthcare` preset."

---

## Step 4 — Extensions (general-edition only, optional)

If `EDITION == general`, ask:

```
Compliance extensions? (optional, comma-separated; or "none")

  - healthcare — HIPAA detection without biotech-edition's mandatory enforcement
  - gdpr — EU jurisdiction + consent tracking + right-to-be-forgotten
  - soc2 — SOC2 Trust Services Criteria audit-ready evidence
  - pci-dss — Payment card data context (aggressive PAN detection)

Most users start with NONE. Compose multiple if needed (e.g., "soc2,gdpr").

Your selection:
```

Parse the comma-separated list. Validate each extension name against the allowed set: `{healthcare, gdpr, soc2, pci-dss}`. Save as `EXTENSIONS` (list, possibly empty).

If `EDITION == biotech`, skip this step (extensions not applicable).

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

For `biotech` edition (audit is REQUIRED):
```bash
touch "<MEMORY_DIR>/security/audit_log.jsonl"
touch "<MEMORY_DIR>/quarantine/quarantine_log.jsonl"
```

For `general` edition with preset `none`: SKIP this step (audit is OPT-IN).
For `general` edition with preset `healthcare/enterprise/custom`: create both files.

Append initialization entry to audit_log.jsonl (if created):
```json
{"ts":"<ISO-8601-UTC>","actor":"install-skill","actor_session":0,"action":"initialize","entry_id":"<bootstrap>","entry_path":"memory/","entry_category":"system","entry_summary":"Ultimate Memory Stack v3.6.0 deployment initialized via Skill installer; edition=<EDITION>; preset=<COMPLIANCE_PRESET>; extensions=<EXTENSIONS>","outcome":"success"}
```

Report appropriately based on what was initialized.

### 7f. Update PROFILE.md with selected preset + extensions (general edition only)

Use Edit tool to modify `<STACK_DIR>/general-edition/PROFILE.md`:
- Set `compliance: <COMPLIANCE_PRESET>` (was `compliance: none`)
- Add `extensions:` list if extensions were selected

Skip for biotech-edition (preset is locked).

---

## Step 8 — Setup Wizard

This is per BOOTSTRAP_PROMPT.md Step 7. Ask the user in order, saving answers to indicated files:

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

Create `<MEMORY_DIR>/sessions/session_state.md` with Session 1 — Initial Setup:

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
Initial setup via Skill installer. Ultimate Memory Stack v3.6.0 deployed:
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
✅ Ultimate Memory Stack v3.6.0 — INSTALLED
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
4. Log the failure event if audit log exists (for biotech-edition forensic completeness)

---

## Skill Constraints + Trust Boundaries

- This skill operates with Read / Write / Edit / Bash tools as needed
- It does NOT modify files outside the working directory + ~/.config/keys/ (if T3+ key generation)
- For biotech-edition: audit log creation is mandatory; this skill cannot bypass the biotech compliance lock
- For custom preset: refuses to proceed without `overrides/compliance.override.md`
- All file operations are reversible via the backup created in Step 11 (if migration mode)

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

When this skill is updated, bump `version:` in the frontmatter + record changes here. Treat the skill itself like any other memory stack artifact — schema_version compatibility matters.

---

## Testing Notes

**v1.0 STABLE** — executed end-to-end on 2026-06-10 (fresh-install scenario: T2 machine, general-edition, preset=none, no extensions). All file operations verified; templates instantiate cleanly; **T1–T9 self-test: 9/9 PASS**.

Remaining test scenarios for future versions:

1. **HIPAA install scenario** — empty working directory + biotech-edition (requires the institutional package)
2. **Edge cases:**
   - SOURCE_PATH doesn't exist (error handling)
   - Custom preset without override file (rejection path)
   - Mid-install interruption (rollback behavior)
3. **Document bugs found** via GitHub Issues
