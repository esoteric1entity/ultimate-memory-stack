---
name: config-obsidian-vault
description: Configure an Obsidian vault to work with the Ultimate Memory Stack. Drops SCHEMA_A18-compliant templates (DEC, VET, FB, session heartbeat, memory bank set), recommends community plugins (Dataview, Templater, Tasks, Excalidraw), pre-configures hotkeys for memory workflows, and optionally registers the vault as the canonical view of the memory/ directory. Does NOT install the Obsidian app itself (user installs from obsidian.md). Use when the user asks to set up Obsidian for their memory stack, configure templates, or wire Obsidian to view memory entries.
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["ideal-first design", "documentation discipline", "OpenClaw research — Obsidian PKM patterns", "convergent adoption of Obsidian-style wiki-links + frontmatter across peer deployments", "recommended addon"]
edition: any (general + biotech both supported)
tier: B (recommended; not auto-installed but lightweight to set up)
license: MIT (Obsidian app is freeware for personal use; templates here are licensed Apache-2.0)
upstream_url: https://obsidian.md/
pre_install_required: Obsidian desktop app (user installs from obsidian.md — NOT part of this Skill's scope)
no_python_install: true
no_pip_audit_required: true
---

# Configure Obsidian Vault for Ultimate Memory Stack — Skill Workflow

When this Skill is invoked (typically via `/config-obsidian-vault` slash command or when the user asks Claude to set up Obsidian for the memory stack), execute the workflow below **IN ORDER**.

**Distinct from the 3 PASS-vetted installer Skills (LLMLingua / Graphiti / Graphify):** this Skill installs NO Python packages and runs NO pip-audit. It configures a folder (the Obsidian vault) with templates and plugin recommendations. The Obsidian app itself is user-installed from obsidian.md.

---

## Step 0 — Confirm Install Intent + Pre-Install Check

```
👋 You're about to configure an Obsidian vault for your memory stack.

What this does:
  - Drops 10 SCHEMA_A18-compliant templates into <vault>/.templates/
    (DEC, VET, FB, session heartbeat, 6 memory-bank files)
  - Pre-configures community plugin recommendations (.obsidian/community-plugins.json)
  - Pre-configures hotkeys for memory workflows (.obsidian/hotkeys.json)
  - Optionally registers the vault as the canonical view of your memory/ directory

What this does NOT do:
  - Install the Obsidian desktop app (you do that from https://obsidian.md/)
  - Install Python packages (Obsidian is a desktop app, not a library)
  - Modify your memory/ files (templates only; existing entries untouched)

Pre-install check: do you have Obsidian installed?
  - If yes, where will the vault live? (e.g., your memory/ directory itself is a great choice)
  - If no, please install from https://obsidian.md/ first, then re-invoke this Skill

Continue? [Y/n]:
```

If user says no, stop gracefully. If user lacks Obsidian, halt and reference obsidian.md.

---

## Step 1 — Identify Vault Location

```
Where should the Obsidian vault live?

Common options:
  (a) Use memory/ directly — vault root = your memory/ directory; gives unified browse of all memory entries
  (b) Use working-dir root — vault root = working directory; broader scope including specs + memory + code
  (c) New folder — create a fresh vault folder (specify path)
  (d) Existing vault — register templates into an existing Obsidian vault (specify path)
```

Save as `VAULT_PATH`. **Recommend (a)** for tightest coupling to the memory stack.

---

## Step 2 — Verify Vault Has `.obsidian/` Structure

Check whether `<VAULT_PATH>/.obsidian/` exists:

```bash
ls -la "<VAULT_PATH>/.obsidian/" 2>/dev/null
```

If missing:
- User has not yet opened the vault in Obsidian → ask user to open the folder in Obsidian once (this creates `.obsidian/`), then re-invoke
- OR proceed and let this Skill create the directory; Obsidian will adopt it on next open

If present, proceed.

---

## Step 3 — Copy Templates to Vault

```bash
mkdir -p "<VAULT_PATH>/.templates"
cp -r <path-to-this-skill>/templates/* "<VAULT_PATH>/.templates/"
```

Templates included (all SCHEMA_A18 frontmatter pre-populated):

| Template | Purpose | Where to use it in Obsidian |
|---|---|---|
| `DEC_template.md` | Decision entry (DEC-XYZ) with full documentation discipline | Templater hotkey → new decision |
| `VET_template.md` | Vetting log entry (VET-XYZ) | Templater hotkey → new vetting record |
| `FB_template.md` | Feedback entry (FB-XYZ) | Templater hotkey → capture user correction |
| `session_heartbeat_template.md` | Heartbeat section for session_state.md per §4 | Insert mid-session before /compact |
| `memory_bank/projectbrief_template.md` | SCHEMA_A3 #1 — project goal scope | New project initialization |
| `memory_bank/productContext_template.md` | SCHEMA_A3 #2 — why this project exists | New project initialization |
| `memory_bank/activeContext_template.md` | SCHEMA_A3 #3 — current state | New project initialization |
| `memory_bank/systemPatterns_template.md` | SCHEMA_A3 #4 — architectural decisions | New project initialization |
| `memory_bank/techContext_template.md` | SCHEMA_A3 #5 — tech stack | New project initialization |
| `memory_bank/progress_template.md` | SCHEMA_A3 #6 — what's working / what's left | New project initialization |

---

## Step 4 — Drop Community Plugin Recommendations

```bash
cp <path-to-this-skill>/obsidian_config/community-plugins.json "<VAULT_PATH>/.obsidian/community-plugins.json"
```

This file lists 4 recommended community plugins. Obsidian will surface them in Settings → Community Plugins on next open:

| Plugin | Why |
|---|---|
| **Dataview** | Query memory entries by frontmatter (e.g., "all FINAL DECs from sessions 5-10") |
| **Templater** | Variable expansion in templates (`<% tp.date.now() %>` for `created_at`) |
| **Tasks** | Track checkboxes across vault — useful for "open observations" / "pending DECs" |
| **Excalidraw** | Embed diagrams in DEC entries (architecture sketches) |

User opens Obsidian → Settings → Community Plugins → "Turn on community plugins" → Browse → install each.

**Important:** Obsidian's community plugins are user-installed at their discretion. This Skill only RECOMMENDS via the JSON file — it cannot install plugins programmatically.

---

## Step 5 — Drop Hotkey Configuration (Optional)

```
Want pre-configured hotkeys for memory workflows?
  (a) Yes — copy hotkeys.json with bindings for new-DEC, new-VET, new-FB, heartbeat
  (b) No — keep Obsidian defaults
```

If yes:
```bash
cp <path-to-this-skill>/obsidian_config/hotkeys.json "<VAULT_PATH>/.obsidian/hotkeys.json"
```

See `obsidian_config/README.md` in this Skill folder for the hotkey binding details.

---

## Step 6 — Register Vault in `<edition>/PROFILE.md` (Optional)

```
Register this vault as the canonical Obsidian view of the memory stack?
  (a) Yes — adds an addons.obsidian block to PROFILE.md; documents the vault path
  (b) No — vault is configured; PROFILE.md untouched
```

If yes, add to `<working-dir>/<edition>/PROFILE.md`:
```yaml
addons:
  obsidian:
    enabled: true
    vault_path: <VAULT_PATH>
    templates_path: <VAULT_PATH>/.templates
    config_source: recommended-addons/obsidian-vault-config/
    recommended_plugins:
      - dataview
      - templater
      - tasks
      - excalidraw
```

---

## Step 7 — Verify Setup

Manual verification (no smoke_test.py — there's no executable to test):

```bash
# Check templates landed:
ls -la "<VAULT_PATH>/.templates/"
# Expected: 4 top-level templates + memory_bank/ subfolder with 6 files

# Check plugin recommendations:
cat "<VAULT_PATH>/.obsidian/community-plugins.json" 2>/dev/null
# Expected: array with dataview, templater, tasks, excalidraw

# Check hotkeys if Step 5 ran:
cat "<VAULT_PATH>/.obsidian/hotkeys.json" 2>/dev/null
```

If all 3 commands return expected content, configuration is complete.

---

## Step 8 — Log Activation

Append to `<working-dir>/memory/security/vetting_log.md`:

```markdown
### VET-###: Obsidian vault configured (no Python install; config-only)

---
id: VET-###
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
subject: Obsidian vault config (templates + plugin recommendations + optional hotkeys)
verdict: ACTIVATED
pipeline: config-obsidian-vault Skill v1.0
---

- **Date:** <today>
- **Verdict:** ACTIVATED (Tier B recommended; no Python install; config-only)
- **Vault path:** <VAULT_PATH>
- **Templates installed:** 10 (4 top-level + 6 memory-bank)
- **Plugin recommendations dropped:** dataview, templater, tasks, excalidraw
- **Hotkeys configured:** [yes | no]
- **PROFILE.md registered:** [yes | no]
- **Tags:** tier-b, activation, obsidian, addon, config-only
```

Append corresponding DEC-### entry with full documentation discipline.

---

## Step 9 — Brief User on Operational Notes

```
✅ Obsidian vault configured at <VAULT_PATH>

What's there now:
  - .templates/ — 10 SCHEMA_A18-compliant templates ready for use
  - .obsidian/community-plugins.json — 4 plugin recommendations
  - .obsidian/hotkeys.json — pre-configured hotkeys (if Step 5 ran)
  - PROFILE.md — vault registered as memory-stack canonical view (if Step 6 ran)

Next steps for you:
  1. Open <VAULT_PATH> in Obsidian (File → Open Vault)
  2. Settings → Community Plugins → "Turn on community plugins"
  3. Install the 4 recommended plugins (browse → search → install → enable)
  4. Settings → Templater → set "Template folder location" to .templates
  5. Try the templates: Ctrl/Cmd-P → "Templater: Create new note from template" → pick DEC_template

Memory protocol integration:
  - Wiki-links [[DEC-XXX]] are auto-recognized in Obsidian
  - Frontmatter is queryable via Dataview (see .templates/DEC_template.md for example queries)
  - Heartbeat snapshots: paste session_heartbeat_template into session_state.md before /compact
```

---

## Compliance Cross-References

| Step | Action | Decision authority |
|---|---|---|
| 0 | Intent + pre-install check | Documentation discipline |
| 1 | Vault location | Ideal-first design (recommend memory/ root for tightest coupling) |
| 2 | `.obsidian/` structure check | Ideal-first design (validate precondition) |
| 3 | Templates copy | Documentation discipline (templates carry full SCHEMA_A18 + documentation structure) |
| 4 | Plugin recommendations | OpenClaw research identified Obsidian as recommended addon |
| 5 | Hotkeys (optional) | Ideal-first design |
| 6 | PROFILE.md registration (optional) | Tier B/C addon registration |
| 7 | Manual verify | Ideal-first design (validate before declaring done) |
| 8 | Log activation | Auditability + documentation discipline |
| 9 | Hand-off | Ideal-first design |

---

## What This Skill CANNOT Do

- **Cannot install the Obsidian desktop app** — user must download from https://obsidian.md/ separately
- **Cannot install community plugins programmatically** — Obsidian requires user to enable + install via in-app UI
- **Cannot modify existing memory entries** — templates are for NEW entries; existing entries are untouched
- **Cannot enforce template usage** — Obsidian doesn't have a "must use template" mode; user discipline required
- **Cannot wire bi-temporal queries directly** — Dataview must be installed + queries written; templates contain example queries
- **Cannot work without Obsidian installed** — Step 0 enforces precondition
- **Cannot validate that wiki-links resolve** without Obsidian opening the vault (Obsidian builds its graph at open time)
