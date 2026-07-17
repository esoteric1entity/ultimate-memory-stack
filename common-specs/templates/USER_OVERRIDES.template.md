# User Overrides — Template

> **Purpose:** Initial scaffolding for `memory/user/USER_OVERRIDES.md` — the ONE file the installer creates once and never writes to again. Values here override `<edition>/PROFILE.md`'s frontmatter defaults; PROFILE.md itself becomes a regenerable artifact the installer may refresh freely on upgrade.
> **Schema:** v3.0 — config file, not a memory entry (frontmatter only; no SCHEMA_A18 per-entry metadata)
> **Companion:** `MEMORY_PROTOCOL.md` §1.1 (read order), `MEMORY_PROTOCOL_EXTENDED.md` §E4.3 (full mechanics)
> **Precedence:** USER_OVERRIDES.md values > `<edition>/PROFILE.md` frontmatter. Absent USER_OVERRIDES.md → PROFILE.md defaults apply (Door-4 manual installs never run an installer and may never have this file — that is a supported state, not a broken one).

---

```markdown
---
schema_version: "3.0"
created_at: <YYYY-MM-DD>
---

# This file is USER-OWNED. The installer creates it once (if absent) and never
# writes to it again — not even to reformat it. Comments, key order, and blank
# lines are yours; edit freely. Unknown or commented-out keys are always
# preserved and ignored, never stripped.

# --- Values the installer writes at bootstrap (edit freely after) ---
# compliance: <preset>          # written here only if you chose something other than PROFILE.md's shipped default (none)
# extensions:                   # written here only if you selected any at bootstrap
#   - <ext>

# --- Everything else PROFILE.md defines — uncomment any line below to override it ---
# audit_log: opt-in
# audit_log_retention_days: 90
# quarantine_ux: toast
# pattern_key_threshold: 5
# crypto_signatures: hmac-optional
# delete_semantics: hard
# delete_recovery_window_days: 7
# expires_at_default_days: 28
# eager_set_budget_bytes: 80000   # advisory eager-load nudge threshold (MEMORY_PROTOCOL_EXTENDED.md §E12); shipped default lives in PROFILE.md
```

---

## Usage notes

- **Never overwritten by the installer.** On install/upgrade: absent → created from this template (with any bootstrap-collected values live, per the block above); present → untouched, byte-for-byte, forever. Re-running the installer, upgrading, or re-installing over an existing scaffold never touches this file.
- **PROFILE.md is regenerable.** Unlike this file, `<edition>/PROFILE.md` holds shipped defaults, not your configuration, and may be freely refreshed on install/upgrade. If you edited PROFILE.md directly under the pre-v4.0.0 model, the next install/upgrade archives your edited copy to `memory/archive/PROFILE.pre-upgrade.<date>.md` and prints a migration notice — port the values you care about into this file instead of re-editing PROFILE.md.
- **Unknown keys are safe.** The protocol reads this file's frontmatter defensively — reordered keys, extra comments, and keys it doesn't recognize are preserved and ignored, never stripped or "normalized" away.
- **Absence is a valid state, not an error.** Door-4 (manual, no installer) users may never have this file — PROFILE.md's shipped defaults apply and nothing halts.

## Cross-references

- `MEMORY_PROTOCOL.md` §1.1 (read order: PROFILE.md frontmatter, then this file)
- `MEMORY_PROTOCOL_EXTENDED.md` §E4.3 (full overrides-pattern mechanics + installer contract)
- `<edition>/PROFILE.md` (the regenerable defaults source)
- `<edition>/overrides/generic-conflict-resolution.override.md` (precedence rule restated)
