# Migration v3.6.x → v4.0.0 — General-Edition

> **File:** `general-edition/MIGRATION_v3.6_to_v4.0.md`
> **Version:** 1.0 — 2026-07-15
> **Status:** stable — one command, non-destructive, with `--dry-run`
> **Audience:** Existing v3.6.0/v3.6.1/v3.6.2 general-edition deployments upgrading to v4.0.0

---

## Purpose

v4.0.0 changes the installed layout: the protocol split into a small always-loaded core plus an on-demand extended reference, `PROFILE.md` became fully regenerable with user configuration moved to `memory/user/USER_OVERRIDES.md`, and hot/cold tiering added a per-category cold index under `memory/archive/`. Pulling the new package code alone does **not** update an already-installed vault — `/plugin update` (or a fresh clone) never touches a project's `.claude/rules/` copy or `memory/`. This doc is the one entry point that brings an existing v3.6.x vault up to the v4.0.0 shape.

Unlike the v2.0→v3.0 migration (a real per-entry schema/frontmatter rewrite), v3.6.x→v4.0.0 is **layout-only** — no entry content changes. The migration script backs up `memory/`, then refreshes exactly the files v4.0.0 added or restructured; every other file in `memory/` is left byte-for-byte untouched.

---

## Pre-Migration Checklist

### Required before starting

- [ ] Nothing manual — the migration script backs up `memory/` itself before any write (Phase A below is automatic, not a separate step you perform first)
- [ ] Know your working directory (the one containing `memory/` and `.claude/rules/`)

### Recommended

- [ ] Read this doc end-to-end once
- [ ] Run `--dry-run` first to preview exactly what will change
- [ ] Windows/PowerShell users: `.\general-edition\setup.ps1 -MigrateFrom v3.6` works the same way (it delegates to `setup.py`) — see the PowerShell form in Phase A below

---

## Migration Path

### Phase A: Automated path (script) — recommended for everyone with Bash, Python, or PowerShell

```bash
# Preview first — writes nothing, just reports the plan:
bash general-edition/setup.sh --migrate-from=v3.6 --dry-run
# or:
python3 general-edition/setup.py --working-dir <your-vault> --migrate-from=v3.6 --dry-run

# Then run it for real:
bash general-edition/setup.sh --migrate-from=v3.6
# or:
python3 general-edition/setup.py --working-dir <your-vault> --migrate-from=v3.6
```

```powershell
# Windows — the .ps1 wrapper delegates to setup.py, same outcome:
.\general-edition\setup.ps1 -MigrateFrom v3.6 -DryRun
.\general-edition\setup.ps1 -MigrateFrom v3.6
```

**Step zero — already-migrated detection.** Before touching anything, the script checks five conditions: the `.claude/rules/memory_protocol.md` copy is under 15,000 bytes, `memory/MEMORY_PROTOCOL_EXTENDED.md` exists, `memory/user/USER_OVERRIDES.md` exists, `PROFILE.md` starts with YAML frontmatter, and `CLAUDE.md` (if present) has no stale `@...MEMORY_PROTOCOL.md` import. If all five already hold, it prints `✓ Already migrated to v4.0.0 — nothing to do.` and exits — **no writes, not even a backup.** This makes a genuinely-already-migrated vault safe to re-run against by mistake; if migration is still needed, re-running is also safe — a second real attempt reuses the same conditional logic and, as of this diff, never collides with or overwrites its own prior backup (see "Migration Risks" below).

**If migration is needed**, the script:

1. **Backs up `memory/`** to `memory.backup.v3.6.<YYYYMMDD-HHMMSS>/` in your working directory — a plain recursive copy, before any other write.
2. **Refreshes `.claude/rules/memory_protocol.md`** from the new core protocol (fixes the stale ~55KB copy that keeps the old eager-load cost alive — a `/plugin update` never does this for you).
3. **Copies `MEMORY_PROTOCOL_EXTENDED.md` into `memory/`** — never into `.claude/rules/`, which would recreate the eager-load cost the split was designed to fix.
4. **Creates `memory/user/USER_OVERRIDES.md`** from the template, if it doesn't already exist. Never touched if present.
5. **Archives your existing `PROFILE.md`** to `memory/archive/PROFILE.pre-upgrade.<YYYYMMDD-HHMMSS>.md` if it differs from the shipped default (byte comparison — never a version-stamp check you could have edited away), then regenerates `PROFILE.md` from the new template. **Values are never auto-ported** — the script prints a notice telling you to compare the archived copy against the new `PROFILE.md` and copy anything you want to keep into `USER_OVERRIDES.md` by hand.
6. **Creates the per-category `ARCHIVE_INDEX.md` tiering scaffold** (`memory/archive/{sessions,decisions,feedback}/ARCHIVE_INDEX.md`) wherever one doesn't already exist. See "Tiering" below for why this has no opt-in prompt.
7. **Detects (never edits) two things**, printed as plain instructions:
   - a stale `@...MEMORY_PROTOCOL.md` import line in your project's `CLAUDE.md`, with its exact line number to delete by hand;
   - the presence of a `.openclaw/` directory (a disclosure only — this migration covers the general-edition Claude Code vault; the OpenClaw adapter's own overwrite semantics and backups are unchanged by v4.0.0).

Nothing else in `memory/` is read or written. Your session history, decisions, feedback, project banks, and every other entry are left exactly as they were.

### Phase B: Manual path (no shell / Door-4 / PowerShell-only users)

The script path above is the recommended one — it's idempotent, previewable, and covers every item. If you can't run Bash or Python directly:

1. **Back up `memory/` yourself first:**
   ```bash
   cp -r memory/ memory.backup.v3.6.$(date +%Y%m%d-%H%M%S)/
   ```
   ```powershell
   Copy-Item -Recurse memory "memory.backup.v3.6.$(Get-Date -Format yyyyMMdd-HHmmss)"
   ```
2. Copy the new `common-specs/MEMORY_PROTOCOL.md` over `.claude/rules/memory_protocol.md`.
3. Copy `common-specs/MEMORY_PROTOCOL_EXTENDED.md` into `memory/MEMORY_PROTOCOL_EXTENDED.md` (vault root of `memory/`, not `.claude/rules/`).
4. If `memory/user/USER_OVERRIDES.md` doesn't exist, copy the fenced body out of `common-specs/templates/USER_OVERRIDES.template.md` into it, filling `<YYYY-MM-DD>` with today's date.
5. If your `general-edition/PROFILE.md` differs from the shipped one, copy it to `memory/archive/PROFILE.pre-upgrade.<timestamp>.md` first, then replace it with the shipped `PROFILE.md`. Compare the archived copy against the new one and port any values you want into `USER_OVERRIDES.md`.
6. For each of `sessions`, `decisions`, `feedback`: if `memory/archive/<category>/ARCHIVE_INDEX.md` doesn't exist, create it from `common-specs/templates/ARCHIVE_INDEX.template.md` (fill `<Category>`, `<YYYY-MM-DD>`, `<HotFile>`, `<ArchiveFile>`; delete the illustrative `<ENTRY-ID>` line).
7. Check your `CLAUDE.md` for a line importing `MEMORY_PROTOCOL.md` (e.g. `@ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md`) and delete it by hand — the `.claude/rules/` copy already auto-loads every session, so the import doubles the cost.

### Phase C: What this migration never touches

- Every file already inside `memory/` other than the five items above — session history, decisions, feedback, project memory-banks, all entry content, byte-for-byte.
- `CLAUDE.md` — detected and reported, never auto-edited.
- `.openclaw/` and anything under it — disclosed, not migrated; that adapter has its own install/backup story, unchanged by this doc.
- A v2.0-shaped vault — go through `MIGRATION_v2_to_v3.md` first; there is no direct v2.0→v4.0.0 path.

### Phase D: Verification

```bash
bash verify.sh <your-vault>
```

`verify.sh`'s existing v4.0.0 checks (protocol core size, `USER_OVERRIDES.md` presence, `PROFILE.md` regenerability marker, tiering `ARCHIVE_INDEX.md` files) **are** the post-migration verification — no separate migration-specific check exists or is needed.

### Phase E: Rollback

Migration is non-destructive — Phase A backed up `memory/` before any change. To roll back:

```bash
# 1. Stop the agent / close the session, then move the migrated tree aside
mv memory memory.failed.$(date +%Y%m%d-%H%M%S)

# 2. Restore the pre-migration backup
mv memory.backup.v3.6.<timestamp> memory

# 3. (Optional) restore your archived PROFILE.md if you want the old one back
cp memory/archive/PROFILE.pre-upgrade.<timestamp>.md general-edition/PROFILE.md
```

Your v3.6.x state is fully recovered — the backup was never modified, and neither was the archived `PROFILE.md`.

---

## Tiering — no opt-in prompt, and why

An earlier design for this migration originally called for an interactive tiering opt-in (default: no), on the theory that creating the `ARCHIVE_INDEX.md` scaffold was a "layout choice." That was written before hot/cold tiering (train step 6) actually shipped. As implemented, `create_archive_indexes()` is unconditional, idempotent, and create-only-if-absent — it runs on every fresh install and every re-install already, with no consent gate anywhere, because it can never overwrite existing data (an empty index file is the only thing it ever creates). Gating migration alone behind a new prompt would have meant: diverging from what re-installs already do, breaking `--dry-run`'s non-interactive guarantee, and adding friction for a change with zero data risk. Migration therefore creates the scaffold the same way any re-install does — automatically, silently, safely.

Nothing about rotation itself is automatic: the first rotation of an already-over-cap file is still a manual, agent-guided step (`MEMORY_PROTOCOL_EXTENDED.md` §Tiering), same as for a vault that migrated any other way.

---

## What moved in v4.0.0

| Old path | New path | Why | User action needed |
|---|---|---|---|
| `core/openclaw-adapter/scripts/lint_runner.py` | `core/shared-tools/lint_runner.py` | It's cross-harness tooling used by every edition, not adapter-specific. | None — a compat shim at the old path keeps old invocations working. |

(This table is a running record — future train steps that relocate a file add a row here, not a new doc.)

---

## Migration Risks (General-Edition)

| Risk | Mitigation |
|------|------------|
| Stale ~55KB rules copy persists silently (a `/plugin update` never touches an installed project) | Migration always refreshes `.claude/rules/memory_protocol.md` unconditionally |
| Stale `CLAUDE.md` `@`-import keeps the double-load bug alive | Detected and printed with the exact line number; never auto-edited — you must delete it by hand |
| `PROFILE.md` hand-edits get lost if you ever ran a naive wipe-and-reinstall | Migration archives a differing `PROFILE.md` before regenerating it, with a notice — nothing is silently discarded |
| `MEMORY_PROTOCOL_EXTENDED.md` accidentally lands in `.claude/rules/` | Migration only ever writes it to `memory/`; `verify.sh` [T1] would catch a regression here |
| Running migration twice re-archives and re-backs-up | Step-zero idempotency detection makes a second (or tenth) run a genuine no-op once all five conditions hold |
| `.openclaw/` present alongside a general-edition vault | Disclosed only — this migration never writes into `.openclaw/`; that adapter's own backup/overwrite behavior is unrelated and unchanged |
| Manual path drifts from what the script actually does | Every manual step above cites the exact template/file the script itself uses — no separate hand-maintained procedure to fall out of sync |

---

## Expected Migration Output

```
→ Migrating v3.6 → v4.0.0
→ Backup: memory.backup.v3.6.20260715-231854/
✓ Backup complete
⚠️  CLAUDE.md:3 still imports MEMORY_PROTOCOL.md — this doubles the eager-load cost
    since .claude/rules/memory_protocol.md already auto-loads every session.
    Delete that line from CLAUDE.md by hand (never auto-edited).
→ Continuing with the standard refresh (rules copy, EXTENDED, USER_OVERRIDES, PROFILE, tiering scaffold)...
→ Copying memory stack files...
⚠️  Existing PROFILE.md differs from the shipped default — archived to memory/archive/PROFILE.pre-upgrade.20260715-231854.md
   PROFILE.md is regenerable as of v4.0.0; your edits are not auto-applied.
✓ memory/user/USER_OVERRIDES.md ready
✓ memory/archive/{sessions,decisions,feedback}/ARCHIVE_INDEX.md ready
✓ Deployment-info marker written

Next steps:
  1. Review the PROFILE.md archive notice above and port any values you want into USER_OVERRIDES.md
  2. Delete the stale CLAUDE.md import line, if one was detected
  3. Run: bash verify.sh <your-vault>
```

---

## Cross-References

- `MIGRATION_v2_to_v3.md` (the v2.0→v3.0 path; go through it first if you're still on v2.0)
- `common-specs/MEMORY_PROTOCOL.md` §11.6 (tiering trigger) and `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (full rotation/rehydration mechanics)
- `common-specs/templates/USER_OVERRIDES.template.md`, `common-specs/templates/ARCHIVE_INDEX.template.md`
- `PROFILE.md` (regenerable as of v4.0.0 — see its own header)
- `verify.sh` (post-migration verification)
- `setup.sh` / `setup.py` (`--migrate-from=v3.6`, `--dry-run`)
- `INSTALL_AGENT.md`, `README.md`, `USER_GUIDE.md` (pointers to this doc for upgrading users)
