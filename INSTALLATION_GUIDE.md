# Ultimate Memory Stack v3.6.1 — Installation Guide

> **The deep guide** — prerequisites, pre-install decisions, every install method step-by-step, multi-machine deployment, v2→v3 migration. In a hurry? [`INSTALL.md`](./INSTALL.md) is the fast path.

> **File:** `INSTALLATION_GUIDE.md`
> **Guide revision:** 3.0 — 2026-06-11 (updated for UMS v3.6.0: shipped install skill, top-level entry scripts, general-edition packaging)
> **Status:** Comprehensive multi-method install instructions
> **Authors:** see /AUTHORS.md

---

## How to Use This Guide

This guide is **prescriptive** — leave nothing up for guesses. Every step has:
- What you need before starting
- Exact actions to take
- Expected output at each step
- What to do if something fails

**Start here:** Read §1 (Quick Reference) to pick your install method. Then jump to the relevant method's section. After install, run §8 (Post-Install Verification).

---

## §1. Quick Reference — Pick Your Install Method

> These methods are the install "doors" of the Agent Architect Stack convention. Two doors live mostly outside this guide: **marketplace install** (Claude Code: `/plugin marketplace add esoteric1entity/ultimate-memory-stack`, then `/install-ultimate-memory-stack` — §6 covers the skill it runs) and **agent-executed install** — point any capable agent at [`INSTALL_AGENT.md`](./INSTALL_AGENT.md) and say "install this."

### Three Primary Methods (recommended for most users)

| Method | Works on | Prerequisites beyond Claude Code | User actions | Time |
|--------|----------|----------------------------------|--------------|------|
| **A. Manual Drag-and-Drop** | Windows / Mac / Linux | None | 4 actions | ~5 min total |
| **B. Bash `setup-memory-stack.sh`** | Mac / Linux / WSL | Bash 4.0+ (standard) | 1 command | ~30 sec + wizard |
| **C. Claude Code Skill** | Anywhere with Skills enabled | Skills capability enabled | 1 slash command | ~5 sec + wizard |

These three cover ~95% of user contexts.

### Secondary Methods (kept available, see Appendix §17)

| Method | Works on | Prerequisites | Why secondary |
|--------|----------|---------------|---------------|
| **D. PowerShell `setup-memory-stack.ps1`** | Windows | Python 3.8+ (the core install delegates to setup.py) | Requires Python — not a fully "native Windows" option yet. Slated for native-PowerShell rewrite. |
| **E. Python `setup.py`** | Anywhere with Python 3.8+ | Python 3.8+ + optional `cryptography` for T3 | Power-user option with crypto key generation built in. Most users don't need this. |

If you don't already have Python installed, use Method A or B instead.

### Tier Detection (optional pre-check)

If you want to know what features will be available at install time:

```bash
# Linux/Mac/WSL (bash)
node --version 2>/dev/null && echo "✓ T2+ (Node.js)" || echo "T0 or T1 only"
python3 -c "import cryptography" 2>/dev/null && echo "✓ T3+ (Python crypto)" || echo "T2 or lower"
```

```powershell
# Windows PowerShell
node --version                     # version prints -> T2+ (Node.js)
python -c "import cryptography"    # no error -> T3+ (Python crypto)
```

Don't have these? No problem — the system runs fine at T0; higher-tier features activate automatically when their infrastructure unblocks.

---

## §2. Prerequisites (Universal — All Methods)

### Required (everyone)
- **Claude Code CLI installed.** Verify: `claude --version`. Get it from https://claude.ai/code
- **Writable working directory** (~50 MB total for memory + audit logs)
- **The deployable package** (this directory) accessible:
  - Cloned via git, OR
  - Copied from a source-of-truth location (e.g., a network share or backed-up drive), OR
  - Extracted from a release archive

### Method-specific prerequisites (only if you pick that method)
- **Method B (Bash):** Bash 4.0+ — standard on Linux/Mac/WSL
- **Method C (Skill):** Skills capability enabled in Claude Code
- **Methods D/E (secondary):** See Appendix §17

---

## §3. Pre-Install Decisions

Before ANY install method, decide:

### Decision 1: Edition

This package ships the **general-edition** — suited to software dev, research, writing, education, B2B SaaS, and enterprise contexts, with compliance preset flexibility (see Decision 2). A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

**Copy `common-specs/` + `general-edition/` into your working directory.**

### Decision 2: Compliance Preset

| Preset | If you need |
|--------|-------------|
| **`none`** | No regulatory exposure (personal projects, hobby code, learning) |
| **`enterprise`** | Business-customer PII, SOC2 prep, GDPR awareness |
| **`custom`** | Multiple regulatory regimes (advanced — requires `overrides/compliance.override.md`) |

**Pick `none` if unsure.** You can change later — no need to commit upfront.

### Decision 3: Extensions (general-edition only, optional)

Optional add-ons that compose with base preset (per `EXTENSIONS/`):
- `gdpr` — EU jurisdiction + consent tracking
- `soc2` — SOC2 Trust Services Criteria audit-ready evidence
- `pci-dss` — Payment card data context

**You can enable multiple.** Most users start with NONE.

### Decision 4: Consumer Agent Topology

If you have sub-agents (e.g., Warden, Sentinel, Vault, Clerk in an orchestrated setup), register them at the wizard. Otherwise, answer "none" — standard slots (`user`, `orchestrator`, etc.) cover everything.

### Decision 5: Deployment Tier (auto-detected when possible)

You don't need to know this upfront — setup will detect. For reference:
- T0 = no infrastructure (everyone has this)
- T1 = + Ollama (semantic search)
- T2 = + Node.js (hybrid retrieval, graph backend)
- T3 = + Code Execution (cryptographic signatures, advanced compaction)
- T4 = + Skills + Anthropic Dreaming beta (full ideal state)

---

## §4. Method A — Manual Drag-and-Drop (PRIMARY — Recommended for Most Users)

**Use this when:**
- You don't have automation tooling installed (no Bash on Windows, no Python, no Skills)
- You prefer visual file management (Finder / Explorer / Files)
- You want to understand what's being deployed
- You're on Windows without WSL

**This method requires only:** a file manager (Finder on Mac / File Explorer on Windows / Files on Linux) and Claude Code itself. NO shell commands needed.

### Total: 4 user actions, ~5 minutes

### Step 1 — Pick (or create) your working directory

This is where your memory stack will live. Examples:

| OS | Suggested working directory |
|----|-----------------------------|
| Mac | `~/Documents/my-memory-deployment/` or any project folder |
| Windows | `C:\Users\<you>\Documents\my-memory-deployment\` |
| Linux | `~/projects/my-memory-deployment/` |

Create this folder if it doesn't exist (right-click in your file manager → New Folder).

### Step 2 — Copy 2 folders into the working directory via drag-and-drop

In your file manager:

1. **Open the source package location** (e.g., your local copy of the `ultimate-memory-stack/` package)
2. **Select `common-specs/`** — drag into your working directory
3. **Select `general-edition/`** — drag into your working directory

After this step, your working directory contains:

```
my-memory-deployment/
├── common-specs/         (the universal foundation)
└── general-edition/      (the edition profile + overrides + setup)
```

**Mac tip:** Use Finder; hold Option to copy (instead of move). Or use Cmd+C / Cmd+V.
**Windows tip:** Use File Explorer; Ctrl+Drag to copy. Or right-click → Copy → paste in working dir.
**Linux tip:** Use your file manager (Files / Nautilus / Dolphin) with same drag-and-drop semantics.

### Step 3 — Open Claude Code in the working directory

In a terminal (or your launcher):

```
claude
```

OR launch the Claude Code app and use its working-directory selector to point to your working directory.

**Expected:** Claude Code session opens with your working directory as the active context.

### Step 4 — Paste the activation prompt + answer setup wizard

Copy the **entire activation prompt below** (the text inside the gray code block) and paste it into Claude Code chat. This single paste tells Claude to do all the scaffolding work — create `.claude/rules/memory_protocol.md`, initialize the `memory/` directory structure, set up audit log + quarantine, and run the setup wizard.

**The activation prompt** (verbatim — also available in `common-specs/BOOTSTRAP_PROMPT.md`):

```
You are deploying the Ultimate Memory Stack v3.6.1 in this working directory.

The complete spec lives in `common-specs/` plus your edition's profile in `<edition>/`. Read those files for full detail. This prompt is the activation entry point — it doesn't duplicate the schemas, it activates them.

---

### Step 1 — Confirm Edition

This package ships the **general-edition**. Confirm with me: "Deploying the general-edition in this directory — confirm?"

Wait for my answer. Then load `general-edition/PROFILE.md` to determine which common-spec sections are active, which overrides apply, and which compliance preset is in effect.

Ask "Which compliance preset — none, enterprise, or custom?" Save the answer to my user profile.

If `custom`: ask which regulations apply — GDPR, SOC2, PCI-DSS. HIPAA/PHI is not a general-edition option. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

---

### Step 2 — Verify Directory Structure

Confirm or create the following structure (this is the common spec; edition profiles may add subdirectories):

```
.claude/
  rules/
    memory_protocol.md           ← Auto-loaded each session (copy from common-specs/MEMORY_PROTOCOL.md)
memory/
  MEMORY_INDEX.md                ← Master registry (per common-specs/MEMORY_PROTOCOL.md §Index)
  sessions/
    session_state.md             ← Lifeline file (per SCHEMA_A18 entry format)
  user/
    user_profile.md              ← Who you're working with
  decisions/
    decisions.md                 ← Settled choices with confidence levels
  projects/                      ← One subdir per project (SCHEMA_A3)
    <slug>/
      memory-bank/               ← Cline 6-file convention
        projectbrief.md
        productContext.md
        systemPatterns.md
        techContext.md
        activeContext.md
        progress.md
  feedback/
    feedback.md                  ← User corrections that should change my behavior
  security/
    vetting_log.md               ← Audit trail
    audit_log.jsonl              ← If audit log enabled (B1)
  references/
    references.md                ← File location pointers
  archive/                       ← Superseded content
  quarantine/
    quarantine_log.jsonl         ← If quarantine enabled (B2)
ultimate-memory-stack/           ← The spec itself, read-mostly during operation
  common-specs/                  ← Universal schemas + protocol + architecture
  general-edition/               ← The active edition shipped in this package
```

---

### Step 3 — Apply the Memory Protocol

Read `common-specs/MEMORY_PROTOCOL.md`. It contains the operational rules: when to load files (Tier 1/2/3), context budget, conflict resolution hierarchy, file size limits, standing rules, risk scoring, cascade failure detection, self-test suite. Do not duplicate that file's content here — load it and follow it.

Copy `MEMORY_PROTOCOL.md` to `.claude/rules/memory_protocol.md` so Claude Code auto-loads it each session.

---

### Step 4 — Apply Edition Profile + Overrides

Read `general-edition/PROFILE.md`. It declares:
- Which common-spec features are active (e.g., audit log: required vs opt-in)
- Compliance preset (`none` / `enterprise` / `custom` for general; the `healthcare` preset is biotech-edition-reserved and not selectable in general-edition)
- Override-file map — each line says "override file X applies override Y" (the B4 override-file convention)
- Pattern-key recurrence threshold (general ≥5)
- Cryptographic signature scheme (HMAC for general, activates at T3)
- Audit log retention policy
- Quarantine UX pattern (one-line toast)

Apply each `.override.md` file listed in PROFILE.md. The override pattern: if `common-specs/X.md` and `general-edition/overrides/X.override.md` both exist, the override's sections REPLACE the common-spec's sections of the same name (other sections inherit).

---

### Step 5 — Apply Schemas

Read all schema files in `common-specs/`:
- `SCHEMA_A3_per_project_memory_bank.md` — per-project memory bank structure
- `SCHEMA_A18_per_entry_metadata.md` — YAML frontmatter for every memory entry
- `SCHEMA_audit_log.md` — JSONL audit log format (B1)
- `SCHEMA_quarantine.md` — quarantine queue + release workflow (B2)
- `SCHEMA_compliance_profile.md` — 3-preset compliance hybrid + custom (B7)

Every new memory entry MUST carry SCHEMA_A18 frontmatter (id, created_at, source_agent, pattern_key, recurrence_count, confidence, status, content_sha256, etc.). Use the schema's worked example as a template.

---

### Step 6 — Initialize Memory Vault

If `memory/` is empty (first deployment):
1. Create directory structure (Step 2)
2. Initialize `memory/sessions/session_state.md` with Session 1 — Initial Setup (include Schema Version: 3.0)
3. Initialize `memory/MEMORY_INDEX.md` with empty counts
4. Run the setup wizard (Step 7) to populate `user_profile.md` and `project_context.md`

If `memory/` exists (upgrading from v2.0):
1. Detect schema version of existing files
2. Migrate per `general-edition/MIGRATION_v2_to_v3.md` (separate file) — adds YAML frontmatter to existing entries, restructures projects into per-project subdirs
3. Preserve all FINAL decisions, security entries, user profile, standing rules — these survive any migration
4. Tell me the migration plan BEFORE executing. Wait for approval.

---

### Step 7 — Setup Wizard (first deployment only)

Ask me these questions in order. Save my answers to the indicated files:

1. **Identity** (→ `user/user_profile.md`)
   - Name + role + organization
   - Primary tech stack / languages / frameworks
   - Domain (biotech R&D? data science? web dev? other?)
   - How do I prefer responses (brief vs detailed, technical level)?

2. **Active Projects** (→ `projects/<slug>/memory-bank/projectbrief.md` per project)
   - List active projects (1 per line, brief description each)
   - For each: high-level goal + current status

3. **Compliance** (→ `user/user_profile.md` + active compliance profile)
   - Compliance preset: none / enterprise / custom
   - If `custom`: which regulations apply (GDPR, SOC2, PCI-DSS)?
   - HIPAA/PHI is not a general-edition option. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

4. **Pet Peeves** (→ `feedback/feedback.md` as initial entries — the canonical location)
   - Anything you should NEVER do
   - Anything you should ALWAYS do
   - Common AI behaviors you find annoying

   These become FB-NNN entries with pattern_key. Do NOT also place them in `user/user_profile.md` — feedback.md is the single source of truth.

5. **Consumer Agent Topology** (→ `user/user_profile.md`)
   - What sub-agent names will be using this memory stack? (e.g., warden / sentinel / vault / clerk for orchestrated setups; or "none" if no sub-agents)
   - These names register as valid `source_agent` slots in SCHEMA_A18 frontmatter. Standard slots (`user`, `orchestrator`, etc.) always available.

6. **Deployment Tier** (→ saved internally for tier-gate decisions)
   - Code Execution: enabled or blocked?
   - Node.js available: yes or no?
   - Skills: enabled or blocked?
   - Anthropic beta access: enabled or none?

   Some Tier C features auto-activate based on these answers; others stay designed-in but dormant.

---

### Step 8 — Run Self-Test

Per `MEMORY_PROTOCOL.md §Self-Test`, run T1–T9 silently. Only report failures.

If T1 fails (no session_state.md): CRITICAL — stop.
If T7 fails (PII/PHI detected): CRITICAL — refuse to load the affected file.
If T8 fails (invalid SCHEMA_A18 frontmatter on any entry): WARNING — flag affected entries.
If T9 fails (edition profile / override map doesn't resolve): WARNING — fall back to common-specs defaults.
Other failures: warn but proceed.

---

### Step 9 — Greet and Orient

Brief greeting:
- Confirm edition deployed
- Confirm compliance preset active
- Summary of what was scaffolded (X files created / verified)
- "Where would you like to start? Try `/help` or ask me about your projects."

If migrating from v2.0: also list what changed (new frontmatter, new per-project memory bank, new audit/quarantine/signature options).

---

### Ongoing Operation

After bootstrap, the system runs on `MEMORY_PROTOCOL.md` rules (auto-loaded every session). Bootstrap is one-time. You don't paste this prompt again.

When I say "update session state" / "wrap up" / "save state" / "end session" — execute the Session End protocol in MEMORY_PROTOCOL.md.

When I ask about a project, load its memory-bank (Tier 2).
When I correct you, append to feedback.md and apply immediately.
When we make a technical decision, append to decisions.md with confidence level + DEC-### id if it's significant enough to track.
When 30 min passes during active work, heartbeat to session_state.md.
When errors cascade (3 unrelated in 5 min), STOP and report.

That's the contract. Everything else is in the protocol + schemas.
```

**What Claude does next** (handles automatically — just confirm any permission prompts as they appear):
- Reads `MEMORY_PROTOCOL.md` from the common-specs/ folder
- Creates `.claude/rules/memory_protocol.md` (copying the protocol there)
- Creates the `memory/` directory structure (9 subdirectories)
- Initializes `audit_log.jsonl` + `quarantine_log.jsonl` files
- Asks you the 6 setup wizard questions
- Runs the T1–T9 self-test
- Greets you with a "Last session we [setup]..." message

**Note:** the canonical activation prompt lives in `common-specs/BOOTSTRAP_PROMPT.md` (the section labeled "## The Activation Prompt"); the copy above is provided for convenience. If the two ever differ, the BOOTSTRAP_PROMPT.md version is authoritative — paste from that file when in doubt.

### Done

After Step 4 completes (~3-5 minutes including answering wizard questions), your memory stack is operational.

**Verify with the next session:** Close Claude Code. Reopen in the working directory. Claude should greet you with a "Last session we [setup]..." line. That confirms session_state.md was created properly.

### If something doesn't work

See §10 Troubleshooting. The most common issue is "Claude doesn't see the memory" — usually because `.claude/rules/memory_protocol.md` wasn't created. Verify the file exists by looking in your working directory's `.claude/rules/` folder (you may need to enable "Show hidden files" in your file manager — `.claude/` starts with a dot).

---

## §5. Method B — Bash `setup-memory-stack.sh` (PRIMARY — Mac / Linux / WSL)

**Use this when:** You're on Mac, Linux, or WSL — and want one-command install.

### Prerequisites for this method
- Bash 4.0+ (standard on Mac and Linux; WSL on Windows works too)
- The deployable package accessible
- Optional: Python 3.8+ + `cryptography` for T3+ cryptographic features

### Mac note

The setup scripts declare `#!/bin/bash`, so they run correctly under bash even though macOS defaults to zsh. If you see "permission denied", the execute bit isn't set — run `chmod +x` on the script, or invoke it as `bash <script>` (interpreter invocation doesn't require the execute bit).

### Steps

**Step 1: Navigate to your working directory** (where you want the stack installed — the install lands in the directory you run from):

```bash
cd /path/to/your-working-directory
```

**Step 2: Run the top-level setup script by its path:**

```bash
/path/to/ultimate-memory-stack/setup-memory-stack.sh                  # full install (all addons)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --minimal       # core only (no addons)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --addon memory-vault --addon memory-graphiti
/path/to/ultimate-memory-stack/setup-memory-stack.sh --no-templater  # skip Obsidian Templater auto-enable
/path/to/ultimate-memory-stack/setup-memory-stack.sh --compliance=enterprise --extensions=soc2,gdpr
/path/to/ultimate-memory-stack/setup-memory-stack.sh --migrate-from=v2.0
/path/to/ultimate-memory-stack/setup-memory-stack.sh --target ~/my-workspace   # explicit target
/path/to/ultimate-memory-stack/setup-memory-stack.sh --yes          # non-interactive (accept defaults)
/path/to/ultimate-memory-stack/setup-memory-stack.sh --help          # full flag list
```

The script confirms the install target interactively (auto-detecting an OpenClaw workspace if present), refuses to install into its own package directory, refreshes only product-owned files on re-install (your `memory/` data is never touched), and writes a `.ums-manifest.json` recording what it did.

> Advanced: `general-edition/setup.sh` can be run directly (`cd general-edition && ./setup.sh`); it accepts the same pass-through flags plus `--verify`, `--status`, and `--change-preset=<preset>`.

**Expected output (default preset `none`):**

```
==========================================
Ultimate Memory Stack — General-Edition Setup
Version: 3.6.1
Working directory: <working-dir>
Compliance preset: none
Extensions: none
Mode: fresh-install
==========================================

→ Copying memory stack files...
ℹ️  Audit log: OPT-IN (compliance: none — default OFF)
   Enable later via PROFILE.md edit: audit_log: true
✓ Memory directory structure initialized
✓ Deployment-info marker written to <working-dir>/.deployment-info

==========================================
✓ General-edition setup complete
==========================================

Effective tier detection:
  Node.js:      available  (T2 features active)
  cryptography: NOT installed  (T3 signatures dormant)
  Ollama:       NOT installed  (T1 semantic dormant)

Next steps:
  1. cd <working-dir>
  2. Run: claude
  3. Paste activation prompt from:
     <working-dir>/ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md
  4. Answer setup wizard
```

(Tier-detection lines vary by machine. With `--compliance=enterprise|custom` the audit-log lines become "✓ Audit log initialized for compliance: `<preset>`".)

**Step 3: Open Claude Code + paste activation prompt + answer wizard**

Same as Method A Step 4.

**Step 4: Verify:**

```bash
/path/to/ultimate-memory-stack/verify.sh    # run from the working directory; or pass it as an argument
```

Expected: ends with `✅ All checks passed — Ultimate Memory Stack v3.6.1 install is valid.` If anything fails, see §10 Troubleshooting.

**Total time: ~30 sec for script + ~2-3 min for wizard.**

---

## §6. Method C — Claude Code Skill Installer (PRIMARY)

**Status:** ✅ **AVAILABLE** — the install skill ships in `skills/install-ultimate-memory-stack/` (see `skills/install-ultimate-memory-stack/INSTALL_SKILL.md` for how to register the skill itself; v1.0 STABLE, validated end-to-end).

**Use this when:** You have Skills enabled in Claude Code and want the native slash-command experience.

### What the install looks like

```
> /install-ultimate-memory-stack

Welcome to the Ultimate Memory Stack installer.

Edition? [general]: general

Compliance preset? [none / enterprise / custom]: none

Extensions? (comma-separated, or 'none'): none

Consumer agent topology? (list agent names, or 'none'): none

[The skill handles everything else automatically]

✓ Files copied to working directory
✓ memory_protocol.md installed to .claude/rules/
✓ Memory directory structure initialized
✓ Setup wizard complete

Self-test: All T1–T9 checks passed.

Your memory stack is operational. Type any message to begin.
```

### Why this is the easiest method

- **1 user action:** type `/install-ultimate-memory-stack`
- **Auto-prompted decisions:** edition + preset + extensions + topology all via inline UI
- **No file management:** the skill handles all file operations
- **Native Claude Code UX:** consistent with other skill-based workflows
- **Security-reviewed:** the skill passed security review before release

### What this method requires

- Claude Code with Skills capability enabled

**Total time: ~30 seconds + wizard prompts.**

---

## §7. Multi-Machine Deployment

If deploying to multiple machines (e.g., a desktop and a laptop, or team-member setups):

### Pattern: Independent per-machine deployments

Each machine is independent. Memory entries do NOT auto-sync (single-deployment scope by design).

**Steps per machine:**
1. Copy `common-specs/` + your chosen edition to the target machine (drag-and-drop via shared folder; git clone; archive transfer)
2. Run your preferred install method on that machine
3. Setup wizard runs per machine — user profile + projects + topology may differ

### Pattern: Source-of-truth + work mirror

Used when you want **one canonical location** + working mirrors on multiple machines.

**Setup pattern:**
- **Canonical location** — a stable, slow-changing location (network share, backed-up drive, git repo origin, removable drive). Houses the master copy of the `ultimate-memory-stack/` package.
- **Mirror locations** — each working machine has a copy at a consistent logical path.
- **Drift detection** — byte-parity verification via file size / hash comparison.

**Pick paths that fit YOUR environment.** Common patterns:
- Canonical on a network share, mirrors on local SSDs of each machine
- Canonical on an external drive, mirrors on internal drives
- Canonical in a private git repo, mirrors via `git clone` per machine
- Canonical on one local drive, mirror on another (single-machine setup)

For other deployments without explicit mirroring, just keep ONE canonical source and copy from there as needed.

---

## §8. Post-Install Verification

After ANY install method, verify these:

### Verification A: Self-Test (T1–T9)

**Method A users:** Just confirm the activation prompt's self-test passed (Claude reports it inline).

**Method B users** (and any method, from the package root):
```bash
./verify.sh                      # run from the working directory
./verify.sh /path/to/working-dir # or pass the working directory as an argument
```

**Method C users:** the install skill runs the self-test as its final step and reports results inline; you can also run `verify.sh` above at any time.

**Expected output (verify.sh, preset `none`):** sectioned `[T1]`–`[T7]` checks (memory dirs, edition profile, audit logs per preset, common-specs, registered skills, bootstrap prompt), ending with:
```
✅ All checks passed — Ultimate Memory Stack v3.6.1 install is valid.
```

(The edition-level alternative `general-edition/setup.sh --verify` prints a shorter check: T1/T2 lines, an audit-log status line, and a "Deployment tier:" section.)

All checks green = good. Any failure = see §10 Troubleshooting.

### Verification B: Session Greeting

Close Claude Code. Reopen in working directory.

**Expected:** Claude greets you with "Last session we [setup]. Ready to continue with [active project] or work on something else?"

If you DON'T see this, `.claude/rules/memory_protocol.md` isn't being auto-loaded. See §10.

### Verification C: Memory Write Test

In Claude Code, say: "Remember that my preferred test framework is jest."

**Expected:** Claude writes an entry. Verify by opening `memory/feedback/feedback.md` — should see a markdown entry with YAML frontmatter (id, dates, source_agent: user) and content mentioning jest.

### Verification D: PII Detection (`enterprise` preset or `gdpr` extension only)

With the `enterprise` preset (or `gdpr` extension) active, say: "Test detection: my fake customer SSN is 123-45-6789 (testing only)."

**Expected:** Claude flags the PII, routes the entry to quarantine (non-blocking toast notification in general-edition), and the audit log captures the attempt.

---

## §9. Migration v2.0 → v3.x (Upgrading Existing Deployments)

If you have an existing v2.0 memory stack:

**Pre-migration:**
1. **Backup `memory/` directory.** Drag-and-drop a copy to a safe location, name it `memory.backup.v2.<date>/`.
2. **Read your edition's `MIGRATION_v2_to_v3.md`** for edition-specific safeguards.

**Run migration** (pick a method):

```bash
# Method B (Bash)
./setup.sh --migrate-from=v2.0 --backup-location=memory.backup.v2.$(date +%Y%m%d-%H%M%S)

# Method A (Manual) — copy in the current package files alongside v2.0, then paste a migration prompt
# (Activation prompt at BOOTSTRAP_PROMPT.md handles migration if v2.0 is detected)
```

**What happens:**
1. Backup created
2. v2.0 entries get YAML frontmatter added (legacy fields preserved)
3. Audit log initialized (biotech REQUIRED, general per preset)
4. Quarantine directory initialized
5. Re-validation pass on legacy entries — failures route to quarantine
6. PROFILE.md created with selected preset

**Post-migration:**
1. Review quarantine queue (entries from re-validation)
2. Verify with self-test
3. Test a few memory writes
4. Keep backup until confident; then optionally remove

**Migration is non-destructive** — backup preserves v2.0 for full rollback.

---

## §10. Troubleshooting

### Symptom: "Claude doesn't reference memory at session start"

**Cause:** `.claude/rules/memory_protocol.md` isn't auto-loaded.

**Fix:**
1. Verify file exists at `<working-dir>/.claude/rules/memory_protocol.md` (you may need to show hidden files)
2. Verify Claude Code is running from the working directory (not a parent)
3. If activation prompt was used: manually paste it again — Claude should re-create the file

### Symptom: Setup script (Method B) fails with "common-specs not found"

**Cause:** You ran the setup script from the wrong directory.

**Fix:** Run from inside the edition's directory (`cd general-edition && ./setup.sh`). The script expects `../common-specs/` to exist.

### Symptom: Method B fails on Mac with "permission denied"

**Cause:** Execute bit not set on the script.

**Fix:** Run `chmod +x <script>` then re-run, or invoke it as `bash <script>` (interpreter invocation doesn't require the execute bit).

### Symptom: "Audit log MISSING" (compliance preset enterprise/custom)

**Cause:** These presets enable the audit log by default; setup should have created it. (With preset `none` the audit log is OPT-IN — a missing log is normal, not an error.)

**Fix:** Re-run setup, OR manually create:
- Drag-and-drop create empty file `memory/security/audit_log.jsonl` (any text editor — save empty file)
- Drag-and-drop create empty file `memory/quarantine/quarantine_log.jsonl`

### Symptom: PII detection misfiring (false positives)

**Cause:** Layer 2 patterns may be too aggressive for your context.

**Fix:** Tune the active detection patterns (`common-specs/detection_patterns_<preset>.md`, or `general-edition/overrides/generic-examples.override.md`) to your formats. Run verify after.

### Symptom: Quarantine queue growing without review

**Cause:** Detection firing on legitimate content.

**Fix:**
- Run `/audit-quarantine` to review the queue
- Detection patterns may need tuning OR change preset to less aggressive

### Symptom: Compliance preset 'custom' rejected at install

**Cause:** The `custom` preset requires `overrides/compliance.override.md` with ≥1 explicit override.

**Fix:** Create `general-edition/overrides/compliance.override.md` with at least one section override. See `general-edition/overrides/compliance-presets.override.md` §5.4 for example.

### Symptom: Setup wizard never completed

**Cause:** Interrupted; activation prompt not pasted.

**Fix:** Re-paste activation prompt from `BOOTSTRAP_PROMPT.md`. Wizard re-runs from where it stopped.

---

## §11. Edition Switching

This package ships the **general-edition** only. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md. For day-to-day regulatory tuning within the general-edition, use compliance-preset switching (§12) rather than an edition change.

Edition is a structural choice — not a simple preset change. When a future edition becomes available, the recommended path between editions would be:
1. Backup current deployment: copy `memory/` to `memory.backup.<date>/` via drag-and-drop
2. Run a fresh install with the target edition
3. Manually port memory entries from backup, then re-verify detection under the new edition's posture
4. Test thoroughly before discarding backup

**There's no automated `--change-edition`** — intentional, since editions have fundamentally different compliance posture.

---

## §12. Compliance Preset Switching (General-Edition Only)

**To change preset on existing general-edition deployment:**

```bash
# Method B (Bash)
./setup.sh --change-preset=enterprise

# Method A (Manual) — edit general-edition/PROFILE.md directly
# Change the line "compliance: <old>" to "compliance: <new>"
# Save the file. Next Claude session re-validates entries against new patterns.
```

**What happens:**
1. PROFILE.md backed up automatically (Method B)
2. PROFILE.md updated with new preset
3. Audit log captures the change
4. Existing entries re-validated against new patterns at next session
5. Failed validations route to quarantine

**This is reversible** — change back with the same command.

**By design, the planned institutional edition would not change preset** — it is locked to `healthcare`. (That edition is planned for a future release, not yet available; see CONTRIBUTING.md.)

---

## §13. Uninstall + Cleanup

To completely remove the memory stack from a working directory:

**Method A (Drag-and-drop, all OSes):**
1. **Backup first** if you want to preserve memory: drag `memory/` to a backup location named `memory-stack-backup-<date>/`
2. Delete `memory/` directory
3. Delete the copied `common-specs/` and `general-edition/` directories (or the copied `ultimate-memory-stack/` folder, if your install created one)
4. Delete `.claude/rules/memory_protocol.md` (the rest of `.claude/` may have other rules — only delete `memory_protocol.md`)

**Method B (Bash):**
```bash
# Backup first
cp -r memory/ ~/memory-stack-backup-$(date +%Y%m%d-%H%M%S)/

# Remove everything
rm -rf .claude/rules/memory_protocol.md
rm -rf memory/
rm -rf common-specs/ general-edition/ ultimate-memory-stack/   # whichever of these your install method copied here
```

**Caution:** Once removed, memory entries are gone unless backed up.

---

## §14. Getting Help

- **General questions:** Read `common-specs/USER_CHEAT_SHEET_core.md` first; then your edition's addendum
- **Architecture questions:** Read `common-specs/ARCHITECTURE.md`
- **Compliance / preset questions:** Read `common-specs/SCHEMA_compliance_profile.md` + your edition's `PROFILE.md`
- **Migration questions:** Read your edition's `MIGRATION_v2_to_v3.md`
- **Privacy/IP questions:** Read your edition's `PRIVACY_REVIEW.md`
- **Modularity questions:** Read `common-specs/MODULARITY.md`

---

## §15. Design Principles

This guide follows the project's standing documentation principles:
- **Ideal-first design with tier markers** — document the full feature set; mark what each tier requires
- **Prescriptive documentation** — leave nothing up for guesses
- **Modular consumer architecture** — common-specs foundation + edition overlays, composing without core modification
- **Manual, Bash, and Skill installs are first-class; PowerShell / Python are secondary**

---

## §16. Cross-References

- `README.md` (this directory — package overview)
- `common-specs/BOOTSTRAP_PROMPT.md` (the activation prompt)
- `common-specs/MEMORY_PROTOCOL.md` (operational rules)
- `common-specs/USER_CHEAT_SHEET_core.md` (user best practices)
- `<edition>/DEPLOYMENT.md` (edition-specific install details)
- `<edition>/MIGRATION_v2_to_v3.md` (upgrade procedure)
- `<edition>/PROFILE.md` (active defaults + decisions)

---

## §17. Appendix — Secondary / Advanced Options

These methods exist but are NOT the recommended path for most users.

### §17.1 Method D — PowerShell `setup-memory-stack.ps1` (Windows)

**Status:** The core install DELEGATES to Python — requires Python 3.8+ in PATH. This means a fresh Windows user without Python can't use it as a true "Windows-native" option.

**When to use:** You're on Windows AND have Python installed AND prefer PowerShell over a Python prompt.

**Prerequisites:**
- PowerShell 5.1+ (standard on Windows 10+)
- Python 3.8+ in PATH
- Execution policy allowing local scripts:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

**Steps** (run from your working directory — the install lands in the directory you run from):
```powershell
cd "<path to your working directory>"
& "<path to>\ultimate-memory-stack\setup-memory-stack.ps1"
# Or with options:
& "<path to>\ultimate-memory-stack\setup-memory-stack.ps1" -Compliance enterprise -Extensions "soc2,gdpr"
# Flags: -Edition, -Minimal, -Addon, -NoTemplater, -Compliance, -Extensions, -MigrateFrom, -SkipWizard, -Help
```

**Future plan:** Rewrite the PowerShell path as native PowerShell (no Python dependency) — promote to a primary install method for Windows users without Python.

---

### §17.2 Method E — Python `setup.py` (Cross-Platform Advanced)

**When to use:**
- You're a developer with Python 3.8+ already installed
- You want T3+ cryptographic key generation built into install
- You want the most feature-complete setup automation

**Prerequisites:**
- Python 3.8+ (`python3 --version`)
- Optional: `cryptography` package (`pip install cryptography`) for HMAC key generation at T3+

**Steps** (run from your working directory — `setup.py` installs into the current directory by default; the `WORKING_DIR` env var or `--working-dir` flag override it):

```bash
cd /path/to/your-working-directory

# Default install (compliance preset: none)
python3 /path/to/ultimate-memory-stack/general-edition/setup.py

# With options
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --compliance=enterprise --extensions=soc2,gdpr

# Generate HMAC signing secret (T3+)
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --generate-hmac-secret

# Other flags
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --help
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --verify
python3 /path/to/ultimate-memory-stack/general-edition/setup.py --change-preset=enterprise
```

**T3+ Crypto Key Generation Path:**

When Code Execution + the `cryptography` package are available, this method generates an HMAC signing secret at install:

```bash
python3 setup.py --generate-hmac-secret
```

**Action required after generation:** store the secret in your password manager. (Ed25519 offline-key entry signing is part of the planned institutional edition. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.)

---

**Total time for Methods D / E: ~30 sec setup + ~2-3 min wizard.**

---

## §18. Recommended Addons + Core Skills

> These components ship as part of v3.6.1.

### §18.1 What the Addons Add Beyond the Base Stack

After the base stack install (Methods A/B/C/D/E above), the package includes **6 additional components**:

| # | Component | Path | Tier | Time |
|---|---|---|---|---|
| 1 | **Obsidian vault config** | `recommended-addons/obsidian-vault-config/` | B | ~5 min after Obsidian app installed |
| 2 | **LLMLingua installer** | `recommended-addons/llmlingua-installer/` | C (opt-in) | ~10 min |
| 3 | **Graphiti installer** | `recommended-addons/graphiti-installer/` | C (opt-in) | ~15 min |
| 4 | **Graphify installer** | `recommended-addons/graphify-installer/` | C (opt-in) | ~10 min |
| 5 | **Audit Quarantine Skill** | `core/audit-quarantine-skill/` | A | auto-available |
| 6 | **OpenClaw General Edition Adapter** | `core/openclaw-adapter/` | A (for OpenClaw target) | ~15 min |

### §18.2 Per-Component Quick Reference

| # | Skill command | Vetting | Critical note |
|---|---|---|---|
| 1 | `/config-obsidian-vault` | n/a (config-only) | Install Obsidian app from https://obsidian.md/ first |
| 2 | `/install-llmlingua` | Security-reviewed | Exact pin `llmlingua==0.2.2`; planned migration → SecurityLingua in a future release |
| 3 | `/install-graphiti` | Security-reviewed | Set `GRAPHITI_TELEMETRY_ENABLED=false` BEFORE first import; CVE-2026-32247 patched ≥0.29.1; Kuzu backend recommended |
| 4 | `/install-graphify` | Security-reviewed | Pin `graphifyy==0.8.21` (DOUBLE-y); CLI command is `graphify` (single-y) by design; website https://graphify.net/ |
| 5 | `/audit-quarantine` | n/a (built-in) | Edition-aware: one-line toast (general default); the fuller quarantine review workflow belongs to the planned institutional edition |
| 6 | `/install-openclaw-adapter` | n/a (built-in) | Requires OpenClaw harness installed at target; adapter generates 9 root files |

### §18.3 Install Order Recommendation

```
1. Obsidian vault config (#1)   — easiest, no Python install
2. LLMLingua installer (#2)     — independent, smallest surface
3. Graphiti installer (#3)      — independent, LLM provider decision
4. Graphify installer (#4)      — independent, L1 bash-guard config
5. OpenClaw adapter (#6)        — only if deploying to OpenClaw harness
```

Audit-Quarantine (#5) auto-available; use `/audit-quarantine` when needed.

### §18.4 Two Install Modes Per Addon

| Mode | How | Pros | Cons |
|---|---|---|---|
| **A. Claude Code Skill** | Copy folder to `~/.claude/skills/` → restart Claude Code → `/install-<addon>` | Structured + logged + error-checked | Requires Skills capability |
| **B. Manual standalone** | `cd <addon>-installer/` + follow `INSTALL_<NAME>.md` | No Claude Code prerequisite | Manual log discipline required |

Both produce identical installed state.

### §18.5 Post-Install Validation (After All Installs)

After installing addons, run each addon's smoke test, then re-run the base verification (`./verify.sh` from the package root, or §8) to confirm the stack is still healthy. If you deploy to multiple machines, also verify that a memory entry written on one machine is readable on another.
