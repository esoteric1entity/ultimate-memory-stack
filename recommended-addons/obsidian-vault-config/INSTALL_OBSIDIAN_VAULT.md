# Manual Config — Obsidian Vault for Ultimate Memory Stack

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, or you want full manual control
> **Upstream:** https://obsidian.md/

---

## Prerequisites

> **Note:** Obsidian config is the only v3.5 addon that does NOT require Python install — it's pure markdown + JSON config. No `python3-venv` or `uv venv` needed for this addon. The Python venv note (see the LLMLingua installer notes) applies only to the 3 pip-install addons (LLMLingua / Graphiti / Graphify).



1. **Ultimate Memory Stack v3.6.0 (or later) is installed** at your working directory
2. **Obsidian desktop app installed** from https://obsidian.md/ — this Skill does NOT install Obsidian itself
3. **Vault location chosen:**
   - Recommended: `<working-dir>/memory/` — vault root = memory directory; unified view
   - Alternative: `<working-dir>/` — broader scope including specs + memory + code
   - Alternative: new folder
   - Alternative: existing Obsidian vault

---

## Step-by-Step Manual Config

### Step 1 — Decide vault path

Save your choice as `VAULT_PATH` for use below.

### Step 2 — Ensure `.obsidian/` structure exists

```bash
mkdir -p "<VAULT_PATH>/.obsidian"
```

(If you've already opened the folder in Obsidian, `.obsidian/` will exist already.)

### Step 3 — Copy templates

```bash
mkdir -p "<VAULT_PATH>/.templates"
cp -r <path-to>/recommended-addons/obsidian-vault-config/templates/* "<VAULT_PATH>/.templates/"
```

Verify:
```bash
ls -la "<VAULT_PATH>/.templates/"
# Expected: 4 top-level *.md + memory_bank/ subfolder
ls -la "<VAULT_PATH>/.templates/memory_bank/"
# Expected: 6 *.md files (projectbrief, productContext, activeContext, systemPatterns, techContext, progress)
```

### Step 4 — Drop community plugin recommendations

```bash
cp <path-to>/recommended-addons/obsidian-vault-config/obsidian_config/community-plugins.json \
   "<VAULT_PATH>/.obsidian/community-plugins.json"
```

### Step 5 — (Optional) Drop hotkey configuration

```bash
cp <path-to>/recommended-addons/obsidian-vault-config/obsidian_config/hotkeys.json \
   "<VAULT_PATH>/.obsidian/hotkeys.json"
```

### Step 6 — (Optional) Register vault in PROFILE.md

Edit `<working-dir>/<edition>/PROFILE.md`:

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

### Step 7 — Open vault in Obsidian + install plugins

1. Launch Obsidian
2. File → Open Vault → select `<VAULT_PATH>`
3. Settings → Community Plugins → "Turn on community plugins"
4. Browse → search + install each recommended plugin:
   - Dataview (for queries)
   - Templater (for variable expansion in templates)
   - Tasks (for cross-vault checkbox tracking)
   - Excalidraw (for diagrams in DEC entries)
5. Enable each plugin after install
6. Settings → Templater → set "Template folder location" to `.templates`

### Step 8 — Try a template

In Obsidian:
1. Ctrl/Cmd-P → "Templater: Create new note from template"
2. Select `DEC_template`
3. Verify frontmatter pre-populated with `created_at`, `source_agent`, `schema_version: "3.0"`, etc.

### Step 9 — Log activation

Append VET-### entry to `<working-dir>/memory/security/vetting_log.md` per SKILL.md Step 8 template.
Append DEC-### entry to `<working-dir>/memory/decisions/decisions.md` per the documentation discipline in MEMORY_PROTOCOL §16.

---

## Optional: Wire Wiki-Links to the Memory Protocol Wiki-Link Convention (EXTENDED §E2)

Obsidian's `[[ID]]` syntax matches MEMORY_PROTOCOL_EXTENDED.md §E2 wiki-link sync convention. To enable two-way sync:

1. **Manual sync (T0-T1):** When you reference `[[DEC-046]]` in body, also add to YAML frontmatter `related: [DEC-046]`
2. **Auto-sync (T2+):** When Node.js indexer is available, it parses `[[ID]]` from body and populates `related:` automatically

For now (T0-T1), Dataview can help you find orphan inline links:

```dataview
TABLE WITHOUT ID
  file.link AS "File",
  filter(file.inlinks, (l) => !contains(this.related, l)) AS "Inline links missing from related[]"
FROM "memory"
WHERE file.inlinks
```

Paste this into any note to surface mismatches between inline `[[ID]]` and YAML `related:`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `.templates/` not showing in Obsidian | Hidden folder ignored | Settings → Files & Links → Excluded Files → check; or rename to `templates/` (non-hidden) |
| Templater doesn't see templates | Template folder location not set | Settings → Templater → Template folder location → `.templates` |
| Dataview queries return empty | Index not built | Wait 10-30 seconds after vault open; or Settings → Dataview → "Force refresh" |
| Plugin install fails (network) | Corporate firewall blocking GitHub | Manual install via .zip from plugin's GitHub release page |
| Hotkeys don't work | Existing binding conflict | Settings → Hotkeys → search for command → check for conflict; resolve |

---

## Cross-References

- `SKILL.md`, `README.md`
- `templates/` — 10 SCHEMA_A18-compliant templates
- `obsidian_config/community-plugins.json` — plugin recommendations
- `obsidian_config/hotkeys.json` — pre-configured hotkeys
- `obsidian_config/README.md` — plugin + hotkey reference docs
- Upstream: https://obsidian.md/
