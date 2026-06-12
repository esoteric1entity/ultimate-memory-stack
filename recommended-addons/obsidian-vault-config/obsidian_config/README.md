# Obsidian Config Files — Plugin + Hotkey Reference

> **Used by:** `SKILL.md` Step 4 + Step 5

---

## `community-plugins.json` — Recommended Plugin List

Drop this file at `<vault>/.obsidian/community-plugins.json` so Obsidian surfaces these 4 plugins in Settings → Community Plugins → "Installed".

| Plugin (manifest ID) | Purpose | Why recommended for memory stack |
|---|---|---|
| `dataview` | Query frontmatter + folder structure with SQL-like syntax | Surface "all FINAL DECs from sessions 5-10" or "orphan VET entries" without manual grep |
| `templater-obsidian` | Variable expansion in templates | Auto-populate `created_at`, `source_session`, `id` when creating new DEC/VET/FB entries |
| `obsidian-tasks-plugin` | Cross-vault checkbox tracking + filtering | Track "open observations" across all files; "pending follow-up actions" |
| `obsidian-excalidraw-plugin` | Embed Excalidraw drawings in notes | Architecture sketches inline in DEC entries |

**Important:** Obsidian doesn't install plugins from this file alone. User must:
1. Open Obsidian → Settings → Community Plugins → "Turn on community plugins"
2. Browse → search plugin → Install → Enable

This file just makes them visible in the "Installed" list as RECOMMENDED.

---

## `hotkeys.json` — Memory-Workflow Bindings

Drop this file at `<vault>/.obsidian/hotkeys.json` to pre-configure 6 hotkeys.

| Binding | Command | Use case |
|---|---|---|
| `Cmd+Shift+T` | `templater-obsidian:insert-templater` | Insert template at cursor (mid-document) |
| `Cmd+Shift+N` | `templater-obsidian:create-new-note-from-template` | Create new DEC/VET/FB from template |
| `Cmd+Shift+K` | `obsidian-tasks-plugin:edit-task` | Edit task status inline |
| `Cmd+L` | `editor:toggle-checklist-status` | Toggle checkbox state |
| `Cmd+Shift+G` | `graph:open` | Open vault graph view (see memory entry relationships) |
| `Cmd+P` | `command-palette:open` | Quick command palette (Obsidian default; included for clarity) |

**Note on `Mod` modifier:** Obsidian uses `Mod` as the OS-appropriate primary modifier — `Cmd` on macOS, `Ctrl` on Windows/Linux.

**Conflict resolution:** If a user already has bindings on these keys, Obsidian shows a conflict warning. They can resolve via Settings → Hotkeys → search for the command → click the binding → modify.

---

## Why These Specific Plugins (Not Others)

Considered + rejected:

| Plugin | Why not |
|---|---|
| Obsidian Git | Sync is a deliberate later-phase scope-carve; don't conflate config with sync mechanism |
| Smart Connections (AI) | Adds LLM dependency that should be Sentinel-vetted first; out of scope for config-only Skill |
| Calendar | Useful but not memory-stack-specific; user can install if desired |
| Kanban | Conflicts with our Markdown kanban convention (`kanban/` folder); avoid duplication |
| Periodic Notes | Tangential to memory-stack semantics |

The 4 selected plugins all have:
- High stars (>3k)
- Active maintenance
- Direct utility for memory-stack workflows
- No additional dependencies beyond Obsidian itself

---

## Cross-References

- `../SKILL.md` Step 4 + Step 5 (these files are inputs)
- `../README.md` (addon-level README)
- `../INSTALL_OBSIDIAN_VAULT.md` Step 4 + Step 5 (manual flow)
