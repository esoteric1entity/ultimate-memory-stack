# How to Install the `install-ultimate-memory-stack` Skill

> **Skill version:** 1.8 — see `SKILL.md` frontmatter + changelog for the authoritative version  ·  **This guide revised:** 2026-07-14
> **Audience:** Users who want to register the Ultimate Memory Stack Skill installer in Claude Code
> **Status:** STABLE — v1.0 validated end-to-end 2026-06-10 (fresh install, general-edition; T1–T9 all pass); v1.1–v1.4 added existing-store data-safety (backup + preserve), `$HOME`/system-dir install guards (canonicalised in v1.4), and harness-agnostic wording — see SKILL.md changelog.

---

## What This Skill Does

Once registered with Claude Code, this skill lets you install the Ultimate Memory Stack v3.6.2 with a single slash command: `/install-ultimate-memory-stack`. See `SKILL.md` (in this same directory) for the full workflow specification.

This is one of several install methods (alongside the manual drag-and-drop, the script `setup-memory-stack.sh`, and the agent flow in `INSTALL_AGENT.md`) — see `../../INSTALL.md` (Claude Code Skill installer) for the user-facing description.

---

## One-Time Skill Registration

Claude Code reads skills from a designated skills directory (commonly `~/.claude/skills/` on Unix systems, `%USERPROFILE%\.claude\skills\` on Windows). You need to copy this skill's directory there ONCE; after that, the skill is available via slash command in every Claude Code session.

### Method 1: Drag-and-drop (simplest)

1. **Open your Claude Code skills directory** in your file manager:
   - **Mac/Linux:** `~/.claude/skills/` (create it if it doesn't exist via Finder/Files)
   - **Windows:** `%USERPROFILE%\.claude\skills\` (create if needed via File Explorer; show hidden files first)

2. **Drag the directory** `install-ultimate-memory-stack` (the directory containing this `INSTALL_SKILL.md` + `SKILL.md`) into the skills directory.

3. **Verify the structure**:
   ```
   ~/.claude/skills/
   └── install-ultimate-memory-stack
       ├── SKILL.md
       └── INSTALL_SKILL.md
   ```

4. **Restart Claude Code** (close + reopen) OR run `/reload-skills` if your Claude Code version supports it.

### Method 2: Command line (Bash / PowerShell)

**Bash (Mac/Linux/WSL):**
```bash
mkdir -p ~/.claude/skills
cp -r /path/to/skills/install-ultimate-memory-stack ~/.claude/skills/
```

**PowerShell (Windows):**
```powershell
mkdir -Force ~/.claude/skills
Copy-Item -Recurse "<path-to>\ultimate-memory-stack\skills\install-ultimate-memory-stack" "~\.claude\skills\"
```

Restart Claude Code after copying.

### Verification

After restart, in Claude Code:

```
/install-ultimate-memory-stack
```

**Expected:** The skill triggers and asks "You're about to install the Ultimate Memory Stack v3.6.2..." (Step 0 of the workflow).

If the slash command isn't recognized, see [Troubleshooting](#troubleshooting) below.

---

## How to Invoke the Skill

After registration:

### Option A: Slash command (preferred)

```
/install-ultimate-memory-stack
```

Claude Code recognizes the skill and runs the workflow from `SKILL.md`.

### Option B: Natural language

You can also say things like:
- "Install the Ultimate Memory Stack"
- "Set up the memory stack here"
- "Deploy the v3.6.2 memory stack in this directory"

Claude should map these to the skill automatically (based on the `description:` field in SKILL.md's frontmatter).

---

## What You Need Before Running the Skill

The skill itself doesn't require additional infrastructure — but for the installation it triggers, you need:

1. **Claude Code installed** ✅ (you have it if you're running this skill)
2. **Working directory** where the memory stack will be installed (the directory you're currently in when you invoke the skill)
3. **The Ultimate Memory Stack source package** — the skill will ask for its location at Step 1
   - This is typically a folder containing `common-specs/` + the shipped `general-edition/` directory
   - It can live anywhere: a local git clone, your downloads folder, a removable drive, a network share — wherever you have the unpacked source files
   - The skill will validate that the path you provide contains the required directories before proceeding
4. **Pre-install decisions made** — edition, compliance preset (general only), extensions (general only), sub-agent topology

---

## Security + Trust

This skill performs file-system operations: directory creation, file copying, file editing. By Claude Code's security model, you'll see permission prompts for each operation. Approve them as the skill requests.

The skill does NOT:
- Modify files outside the working directory + `~/.config/keys/` (only if T3+ key generation invoked)
- Make network requests
- Execute arbitrary code outside the documented workflow
- Bypass the installer's compliance-preset gate (PHI/healthcare is not selectable in the general-edition)

The skill DOES:
- Read your source package files
- Copy them into your working directory
- Create `.claude/rules/memory_protocol.md` for auto-loading
- Initialize `memory/` directory + audit log + quarantine
- Ask you setup wizard questions (identity, projects, preferences, consumer agent topology, deployment tier)
- Run a self-test

Like any third-party skill, review it before registering: `SKILL.md` in this directory is the entire workflow specification — security-conscious users should read it end-to-end before granting permissions.

---

## Troubleshooting

### Symptom: Slash command not recognized after registration

**Cause:** Skill directory isn't being read by Claude Code OR you didn't restart after copying.

**Fix:**
1. Verify the skill is at the expected location (`~/.claude/skills/install-ultimate-memory-stack/SKILL.md`)
2. Close Claude Code completely (not just minimize)
3. Reopen Claude Code
4. Try the slash command again
5. If still failing: check Claude Code's known skill directory in its docs/config — it may be a different path on your system

### Symptom: Skill triggers but fails at Step 1 (locate source package)

**Cause:** You provided a path that doesn't contain `common-specs/` + edition directory.

**Fix:**
1. Locate the Ultimate Memory Stack source package on your system
2. Verify it contains: `<path>/common-specs/` AND the shipped `<path>/general-edition/` (the institutional `biotech-edition/` is a separate package and is not part of this public release)
3. Provide the correct path when the skill retries the question

### Symptom: Skill runs but Claude doesn't have Write/Bash tool permissions

**Cause:** Claude Code's permission settings restrict skill operations.

**Fix:**
1. Review your Claude Code permission settings (`claude permissions` or via UI)
2. Grant the skill access to Read, Write, Edit, Bash tools
3. Re-run the skill

### Symptom: Skill completes but `/install-ultimate-memory-stack` not callable in future sessions

**Cause:** Skill not properly registered OR Claude Code's skill cache invalidated.

**Fix:**
1. Verify skill files still exist at `~/.claude/skills/install-ultimate-memory-stack/`
2. Restart Claude Code
3. If still failing: try re-copying the skill directory (sometimes file metadata helps)

---

## Updating the Skill

If a new version of `install-ultimate-memory-stack` is released:

1. Delete the old skill directory: `rm -rf ~/.claude/skills/install-ultimate-memory-stack`
2. Copy the new version into place
3. Restart Claude Code

The skill is stateless — there's no migration needed between versions. Each invocation reads the current SKILL.md fresh.

---

## Uninstalling the Skill

To remove the skill (does NOT remove already-installed memory stacks; just the installer):

```bash
# Bash
rm -rf ~/.claude/skills/install-ultimate-memory-stack

# PowerShell
Remove-Item -Recurse "~\.claude\skills\install-ultimate-memory-stack"
```

Restart Claude Code. The slash command will no longer be available.

---

## When to Use This Skill vs Other Install Methods

| Install Method | Use When |
|----------------|----------|
| **This skill (`/install-ultimate-memory-stack`)** | You have Skills enabled in Claude Code + want native slash-command UX |
| **Manual drag-and-drop** (Door 4 in INSTALL.md — Manual walkthrough) | You want minimum dependencies + are comfortable copying files |
| **Bash `setup-memory-stack.sh`** (Door 1a) | You're on Linux/Mac/WSL + prefer one-command CLI |
| **PowerShell `setup-memory-stack.ps1`** (Door 1b) | You're on Windows + have Python 3.8+ (PowerShell wrapper; core install delegates to Python) |
| **Python setup.py** (Door 1c in INSTALL.md — Secondary and advanced options) | You have Python + want cryptographic key generation built in |

This skill is the **easiest UX** when available but has a dependency on Skills being enabled in your Claude Code instance.

---

## Status + Tracking

- **Skill version:** 1.4 (authoritative version in `SKILL.md` frontmatter + changelog); v1.0 baseline validated end-to-end 2026-06-10 (T1–T9 pass)
- **Cross-reference:** `SKILL.md` (the actual workflow); `../../INSTALL.md` (Claude Code Skill installer — user-facing description)

---

## Cross-References

- `SKILL.md` — the actual skill workflow (this directory)
- `../../INSTALL.md` (Claude Code Skill installer) — user-facing description in the install guide
- `../../README.md` — deployable package overview
- `../../common-specs/BOOTSTRAP_PROMPT.md` — the underlying activation prompt the skill executes
