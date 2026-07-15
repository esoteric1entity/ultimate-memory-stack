# Archive Index — Template

> **Purpose:** Scaffolding for `memory/archive/<category>/ARCHIVE_INDEX.md` — the cold-side index for a tiered category (`sessions/`, `decisions/`, `feedback/`). One line per archived entry; loaded on demand, never eagerly. Nothing is ever deleted — rotation moves an entry's full section here (per MEMORY_PROTOCOL.md §11's remedy) and records a one-liner pointer back to it.
> **Schema:** v3.0 — index file, not a memory entry (no SCHEMA_A18 per-entry frontmatter; list items only)
> **Companion:** `MEMORY_PROTOCOL.md` §11 (rotation triggers), `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (full rotation + rehydration procedure)

---

```markdown
# Archive Index — <Category>

> **Schema Version:** 3.0
> **Created:** <YYYY-MM-DD>
> **Last Updated:** <YYYY-MM-DD>
> **Entries:** 0 (initial)

Rotated-out entries from `<HotFile>`, one line each. Nothing here is deleted — every entry's full content lives in `<ArchiveFile>` in this directory.

---

## Entries

- <ENTRY-ID> (<YYYY-MM-DD>): <one-line summary, ≤300B> → `<ArchiveFile>#<entry-id-anchor>`

---

## Rehydration

If this category becomes active again: read this file's entries, copy the ones still relevant back into `<HotFile>` (verbatim, from `<ArchiveFile>`), then update both files' entry counts. Trigger: a paused topic reactivates, or a rehydrated entry is explicitly requested.
```

---

## Usage notes

- **Created empty on fresh install** (from this template) at each tiered category's archive location — not lazily on first rotation. A vault that never rotates anything just keeps an empty index; no code path requires it to be non-empty.
- **One-liner cap:** ≤300 bytes per entry (`MEMORY_PROTOCOL_EXTENDED.md` §Tiering R5).
- **Never edit an archived entry's body.** `<category>-archive.md` is append-only — a full rotated section is cut from the hot file and appended here verbatim. If a fact later changes, supersede it in the hot file per the normal bi-temporal rule (§5 B5); the OLD entry rotates here unchanged when its turn comes.
- **Count parity:** this file's entry count must match the hot-side pointer line in `<category>/<category-file>.md`'s header ("Older entries: ... (N entries)") and the `MEMORY_INDEX.md` category row's archived count. Lint's `archive-count-drift` check catches drift; `archive-unindexed` catches an archive file with sections this index doesn't list.

## Cross-references

- `MEMORY_PROTOCOL.md` §11 (File Size Limits — the rotation triggers)
- `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (full procedure, worked example, rehydration)
- `SCHEMA_lint.md` §13 (Tiering Checks — `archive-unindexed`, `archive-count-drift`, `archive-index-missing`, `entry-over-cap`)
- `MEMORY_INDEX.template.md` (the hot-side category row this index's count feeds)
