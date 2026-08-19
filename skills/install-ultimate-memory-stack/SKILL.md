---
name: install-ultimate-memory-stack
version: "1.9"
description: Interactive installer for the Ultimate Memory Stack v4.0.1. The public package ships general-edition only; HIPAA/PHI is out of scope for this edition. Confirms general-edition, then walks the user through compliance preset (none/enterprise/custom), optional extensions (gdpr/soc2/pci-dss), consumer agent topology registration, and deployment-tier detection. Then copies common-specs + general-edition into ultimate-memory-stack/ in the working directory, installs memory_protocol.md to .claude/rules/, initializes the memory/ structure (+ audit log + quarantine per preset), creates memory/user/USER_OVERRIDES.md (create-once, never rewritten — see PROFILE.md §2.1) with the chosen preset/extensions, and runs the verify self-test. Use when the user asks to install, deploy, set up, or activate the Ultimate Memory Stack.
authors: ["see /AUTHORS.md"]
decision_authority: ["ideal-first design", "documentation discipline", "compliance presets", "Tier C designed-in", "modular consumer architecture"]
edition: any
license: Apache-2.0
---

# Install Ultimate Memory Stack v4.0.1 — Skill Workflow

When this skill is invoked (typically via `/install-ultimate-memory-stack` slash command or when the user asks Claude to install/deploy/activate the memory stack), execute the workflow below **IN ORDER**. Treat each step as required unless the user explicitly opts to skip.

This skill is the Claude Code skill door — one of several install methods (the script installs, the agent flow in `INSTALL_AGENT.md`, this Claude Code skill, and the manual copy).

---

## Step 0 — Confirm Install Intent

**First, refuse unsafe install locations.** Before anything else, check the current working directory:

```bash
# Canonicalize first (resolve symlinks via pwd -P) so a path that logically
# isn't $HOME / a system dir but physically resolves into one is still refused.
target="$(cd "$PWD" 2>/dev/null && pwd -P)"; home="$(cd "$HOME" 2>/dev/null && pwd -P)"
case "$target" in
  "$home"|/|/etc|/usr|/var|/root|/tmp|/bin|/sbin)     echo "REFUSE" ;;
  /etc/*|/usr/*|/var/*|/root/*|/tmp/*|/bin/*|/sbin/*) echo "REFUSE" ;;
  *)                                                  echo "OK" ;;
esac
```

If this returns `REFUSE`, **STOP** and tell the user:

> ⚠️ Refusing to install into `<PWD>`. The installer scaffolds `memory/`, `.claude/`, and `ultimate-memory-stack/` into the current directory — installing into your home or a system directory would scatter these across it. `cd` into a dedicated project directory first, then re-run `/install-ultimate-memory-stack`.

Do not proceed until the working directory is a project directory (not `$HOME` or a system path).

Then greet the user briefly and confirm intent:

```
👋 You're about to install the Ultimate Memory Stack v4.0.1 in:
    <current working directory>

This will:
  - Copy common-specs/ + your chosen edition into ultimate-memory-stack/ in your working directory
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

> This mirrors what the shell installer (`setup-memory-stack.sh`) and the agent flow (`INSTALL_AGENT.md` Step 1, existing-install detection) already do; the skill door must match them. If the existing install predates v4.0.0 and the user would rather run a non-interactive script than walk through this conversational flow, point them at `general-edition/MIGRATION_v3.6_to_v4.0.md` (`--migrate-from=v3.6`, `--dry-run`-previewable) — same non-destructive outcome, different door.

---

## Step 1 — Locate Source Package

**First, try to auto-detect the source.** This `SKILL.md` ships inside the package, so the package root is two levels up from it (the directory containing `common-specs/` and `general-edition/`). If both `common-specs/` and `general-edition/` exist there, use that path as `SOURCE_PATH` **without prompting**. Only if auto-detection fails, ask the user:

```
Where is the Ultimate Memory Stack source package located?

You need a folder containing:
  - common-specs/ (the universal foundation)
  - general-edition/ (the edition shipped publicly)

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
4. If validation fails, explain what's missing and ask again (up to 3 retries before suggesting the Door 4 manual install per INSTALL.md)

Save this as `SOURCE_PATH` for use in subsequent steps.

---

## Step 2 — Confirm Edition

First check which edition directories actually exist at `SOURCE_PATH` and confirm — do not present a choice. The public package ships `general-edition/` only (HIPAA/PHI is out of scope for this edition — see CONTRIBUTING.md), so skip any menu and confirm general-edition. `EDITION` is always `general`.

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

Use Bash. On a re-install the two package directories may already exist — remove them first (they are the regenerable spec copy per Step 0.5; this must NEVER touch `<MEMORY_DIR>` or other user data). Without the removal, `cp -r` NESTS the new copy inside the old directory instead of refreshing it, leaving stale spec files in place.

**Archive-before-wipe (v4.0.0):** BEFORE removing, check whether `<STACK_DIR>/<EDITION>-edition/PROFILE.md` exists and differs from the shipped source at `<SOURCE_PATH>/<EDITION>-edition/PROFILE.md` (byte comparison — `cmp -s`, never a version stamp the user could have edited away). If it exists and differs, it was hand-edited under the pre-v4.0.0 model — archive it so the wipe below never silently loses it:
```bash
mkdir -p "<STACK_DIR>"
if [ -f "<STACK_DIR>/<EDITION>-edition/PROFILE.md" ] && ! cmp -s "<STACK_DIR>/<EDITION>-edition/PROFILE.md" "<SOURCE_PATH>/<EDITION>-edition/PROFILE.md"; then
    mkdir -p "<MEMORY_DIR>/archive"
    cp "<STACK_DIR>/<EDITION>-edition/PROFILE.md" "<MEMORY_DIR>/archive/PROFILE.pre-upgrade.$(date -u +%Y%m%d-%H%M%S).md"
fi
rm -rf "<STACK_DIR>/common-specs" "<STACK_DIR>/<EDITION>-edition"
cp -r "<SOURCE_PATH>/common-specs" "<STACK_DIR>/common-specs"
cp -r "<SOURCE_PATH>/<EDITION>-edition" "<STACK_DIR>/<EDITION>-edition"
```
If a copy was archived, tell the user: "Your previous PROFILE.md had customizations — archived to `memory/archive/PROFILE.pre-upgrade.<date>.md`. PROFILE.md is regenerable as of v4.0.0; port any values you want to keep into `memory/user/USER_OVERRIDES.md` (Step 7f creates it if it doesn't exist yet)."

Report: "✓ Files copied"

### 7c. Install memory_protocol.md to .claude/rules/

```bash
mkdir -p "<CLAUDE_RULES_DIR>"
cp "<STACK_DIR>/common-specs/MEMORY_PROTOCOL.md" "<CLAUDE_RULES_DIR>/memory_protocol.md"
```

Report: "✓ memory_protocol.md installed to .claude/rules/ (auto-loads each session)"

**Upgrade-path check:** if the target project's `CLAUDE.md` contains an old at-sign import line pointing at the protocol file, warn the user to remove it — the `.claude/rules/` copy above already auto-loads it, so the old import double-loads the same content. Do NOT auto-edit the user's CLAUDE.md; warn only.

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

Then install the on-demand extended protocol reference to the vault root — **never** to `.claude/rules/` (that would auto-load it every session and recreate the eager-load cost the CORE/EXTENDED split exists to fix):

```bash
cp "<STACK_DIR>/common-specs/MEMORY_PROTOCOL_EXTENDED.md" "<MEMORY_DIR>/MEMORY_PROTOCOL_EXTENDED.md"
```

Report: "✓ MEMORY_PROTOCOL_EXTENDED.md installed to memory/ (on-demand reference, not auto-loaded)"

### 7e. Initialize audit log + quarantine log (preset-dependent)

For preset `none`: SKIP this step (audit is OPT-IN).
For preset `enterprise/custom`: create both files:
```bash
touch "<MEMORY_DIR>/security/audit_log.jsonl"
touch "<MEMORY_DIR>/quarantine/quarantine_log.jsonl"
```

Append the initialization entry **only if the audit log was created above** (enterprise/custom presets; skip for preset `none`):
```json
{"ts":"<ISO-8601-UTC>","actor":"install-skill","actor_session":0,"action":"initialize","entry_id":"<bootstrap>","entry_path":"memory/","entry_category":"system","entry_summary":"Ultimate Memory Stack v4.0.1 deployment initialized via Skill installer; edition=<EDITION>; preset=<COMPLIANCE_PRESET>; extensions=<EXTENSIONS>","outcome":"success"}
```

Report appropriately based on what was initialized.

### 7f. Create USER_OVERRIDES.md (compliance + extensions choices)

**v4.0.0:** `PROFILE.md` is regenerable — the installer never writes to it (see 7b's archive-before-wipe instead). User configuration, including the compliance preset + extensions chosen in Steps 3–4, lives in `<MEMORY_DIR>/user/USER_OVERRIDES.md` — created ONCE, never rewritten again.

- If `<MEMORY_DIR>/user/USER_OVERRIDES.md` already exists: **do nothing.** Never write to it, not even to reformat it — it is user-owned from the moment it exists.
- If absent: Read `common-specs/templates/USER_OVERRIDES.template.md`, extract the fenced ```markdown ... ``` block (that block IS the file body — the surrounding Purpose/Usage-notes/Cross-references sections are documentation for humans, not part of what you write), fill in today's date for `<YYYY-MM-DD>`, then:
  - If `<COMPLIANCE_PRESET>` is not `none`: uncomment the `# compliance: <preset>...` line, set it to `compliance: <COMPLIANCE_PRESET>`.
  - If any extensions were selected: replace the commented `# extensions:` + `#   - <ext>` lines with a live `extensions:` list (one `- <ext>` per selection).
  - Use Write to create `<MEMORY_DIR>/user/USER_OVERRIDES.md` with the result.

> **PRESERVE mode (Step 0.5) still applies, and is now simpler:** the create-once/never-rewrite rule above already IS the preserve behavior for this file — there is no "confirm before editing" judgment call anymore, because the installer never edits an existing USER_OVERRIDES.md at all.

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
Initial setup via Skill installer. Ultimate Memory Stack v4.0.1 deployed:
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
✅ Ultimate Memory Stack v4.0.1 — INSTALLED
========================================

Edition: <EDITION>
Compliance: <COMPLIANCE_PRESET>
Extensions: <EXTENSIONS or "none">
Consumer agents: <CONSUMER_AGENTS or "none">
Effective tier: T<X>

What was created:
  ✓ <WORKING_DIR>/ultimate-memory-stack/ (spec package)
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
  - Need help? Read INSTALL.md or your edition's DEPLOYMENT.md.
```

---

## Error Handling

If any step fails:
1. Surface the specific error to the user
2. Roll back partial changes if possible (especially file copies that may have partially succeeded)
3. Provide remediation:
   - "Try the Door 4 manual install per INSTALL.md (Manual walkthrough)"
   - "Try the Door 1a Bash install per INSTALL.md (Bash install in depth)"
   - "Check that SOURCE_PATH exists and contains common-specs/ + edition/"
4. Log the failure event if an audit log exists

---

## Skill Constraints + Trust Boundaries

- This skill operates with Read / Write / Edit / Bash tools as needed
- It does NOT modify files outside the working directory + ~/.config/keys/ (if T3+ key generation)
- For custom preset: refuses to proceed without `overrides/compliance.override.md`
- When an existing store is detected (Step 0.5), it is backed up to `memory.backup.<ts>/` before any write, and user-data files are never overwritten — so an install-over-existing-data is recoverable. (Fresh installs create no backup because there is nothing yet to preserve.)
- **USER_OVERRIDES.md (v4.0.0):** create-once, never rewritten — if it exists, Step 7f does not touch it under any circumstance. `PROFILE.md` is regenerable; a hand-edited one is archived (7b), never merged or guessed at.

---

## Cross-References

- `INSTALL.md` (Claude Code Skill installer — this skill's section in the install guide)
- `BOOTSTRAP_PROMPT.md` §The Activation Prompt (the Manual / Bash equivalent workflow)
- `common-specs/MODULARITY.md` (consumer agent topology rationale)
- `common-specs/SCHEMA_compliance_profile.md` §5 (preset definitions)
- `common-specs/templates/USER_OVERRIDES.template.md` (Step 7f's source; precedence mechanics: `PROFILE.md` §2.1 + `MEMORY_PROTOCOL_EXTENDED.md` §E4.3)

---

## Skill Versioning

| Version | Date | Changes |
|---------|------|---------|
| 1.0 DRAFT | 2026-05-15 | Initial implementation |
| 1.0 STABLE | 2026-06-10 | Public-readiness fixes (edition-availability detection in Step 2; genericized internal refs); executed end-to-end (fresh install, general-edition, preset=none, T2) — T1–T9 self-test 9/9 PASS → promoted DRAFT → STABLE |
| 1.1 | 2026-06-15 | **Data-safety fix.** Added Step 0.5 existing-store gate: a re-install over an existing `memory/` now backs it up (`memory.backup.<ts>/`) and preserves it. Steps 7e/8/9 are now create-if-absent — the skill no longer overwrites `session_state.md`, `MEMORY_INDEX.md`, `user_profile.md`, project briefs, or `feedback.md` on an existing store (the prior behavior silently reset accumulated memory to empty templates). Corrected the false "reversible via backup" claim. Brings the skill door in line with `setup-memory-stack.sh` + `INSTALL_AGENT.md`, which already preserved user data. |
| 1.2 | 2026-06-15 | **Public-offer alignment.** Removed the public institutional-edition offer (Step 2 edition menu → confirm general-edition; `EDITION` always `general`) and the healthcare compliance-preset + healthcare extension offers, all of which the installer refuses (general-edition install rejects healthcare with "institutional edition only"). Deleted the dead institutional-edition branches in Steps 3, 4, 7e, 7f, Error Handling, and Skill Constraints. General-edition now offers `none/enterprise/custom` presets + `gdpr/soc2/pci-dss` extensions only. Honest disclosures kept and de-overpromised: HIPAA/PHI is out of scope for this edition. |
| 1.3 | 2026-06-16 | **Data-safety hardening + Door-3 alignment (v3.6.1).** Added a Step 0 guard refusing installs into `$HOME` / system directories (`/`, `/etc`, `/usr`, `/var`, `/root`, `/tmp`). Made the Step 0.5 PRESERVE guard explicit in Step 8 (per-file `[ -e ]` existence check before any Write; never overwrite user data) + a Step 7f note to confirm before resetting a user-customized `PROFILE.md`. No behavior change for fresh installs. |
| 1.4 | 2026-06-16 | **Step-0 guard hardening + harness-agnostic wording (v3.6.2).** Canonicalised the Step-0 unsafe-location guard with `pwd -P` so a path that resolves into `$HOME` / a system directory via a symlink is also refused (previously only the literal `$PWD` was matched). Clarified Step 7e (the initialization entry is appended only when the audit log was created — enterprise/custom; skipped for preset `none`). Reframed the skill as one door among several (script / agent / Claude Code skill / manual). No behavior change for fresh installs. |
| 1.5 | 2026-07-10 | **Protocol CORE/EXTENDED split (v4.0.0 eager-load fix).** Step 7c now also warns (never auto-edits) if the target's CLAUDE.md still has an old at-sign import of the protocol file — that content already auto-loads via `.claude/rules/`, so the old import double-loads it. Step 7d now additionally installs `MEMORY_PROTOCOL_EXTENDED.md` to the vault root (`memory/`, never `.claude/rules/`) as an on-demand reference. |
| 1.6 | 2026-07-11 | **Upgrade-path fix.** Step 7b now removes the pre-existing regenerable package directories (`common-specs/`, `<EDITION>-edition/`) before copying. Previously, on a re-install over an existing scaffold, the recursive copy nested the new package inside the old directory, so Step 7c silently re-installed the STALE pre-split protocol and Step 7d could not find the extended protocol file — the eager-load fix never took effect on upgrades via this door. User data (`memory/`) is untouched. No behavior change for fresh installs. |
| 1.7 | 2026-07-11 | **Doc-coherence pass (v4.0.0).** Step 0's "what this will do" summary and the frontmatter description now say the copy lands in `ultimate-memory-stack/` (was ambiguous about the nested layout — matches Step 7b's actual behavior, which was already correct). Retired "Method A/B" install-guide labels in Step 2 validation + Error Handling replaced with the door taxonomy (Door 4 manual / Door 1a Bash) to match the restructured INSTALL.md. No behavior change. |
| 1.8 | 2026-07-14 | **Overrides pattern (v4.0.0) — permanent fix for the 2026-06-15 data-loss debt's remaining PROFILE.md gap.** Step 7b now archives a hand-edited `PROFILE.md` to `memory/archive/PROFILE.pre-upgrade.<date>.md` (byte-compared against the shipped source) BEFORE the regenerable-tree wipe, instead of the wipe silently discarding it. Step 7f no longer edits `PROFILE.md` at all — it creates `memory/user/USER_OVERRIDES.md` from the new template if absent (with the chosen preset/extensions), and never touches it if present. `PROFILE.md` is now fully regenerable; USER_OVERRIDES.md values win on conflict (`PROFILE.md` §2.1, `MEMORY_PROTOCOL_EXTENDED.md` §E4.3). Matches identical behavior added to `setup.sh`/`setup.py` in the same release. No change to Step 0.5's memory/-tree backup-and-preserve machinery. |
| 1.9 | 2026-07-15 | **Migration doc cross-reference (v4.0.0).** Step 0.5 now points users with a pre-v4.0.0 install at `general-edition/MIGRATION_v3.6_to_v4.0.md` as an alternative to this conversational flow — the new `--migrate-from=v3.6` script path (idempotent, `--dry-run`-previewable). No behavior change to this skill's own PRESERVE-mode mechanics. |

When this skill is updated, bump `version:` in the frontmatter + record changes here. Treat the skill itself like any other memory stack artifact — schema_version compatibility matters.

---

## Testing Notes

**v1.0 STABLE** — executed end-to-end on 2026-06-10 (fresh-install scenario: T2 machine, general-edition, preset=none, no extensions). All file operations verified; templates instantiate cleanly; **T1–T9 self-test: 9/9 PASS**.

Remaining test scenarios for future versions:

1. **Edge cases:**
   - SOURCE_PATH doesn't exist (error handling)
   - Custom preset without override file (rejection path)
   - Mid-install interruption (rollback behavior)
2. **Document bugs found** via GitHub Issues
