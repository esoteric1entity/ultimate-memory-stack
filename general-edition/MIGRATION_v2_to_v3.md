# Migration v2.0 → v3.0 — General-Edition

> **File:** `general-edition/MIGRATION_v2_to_v3.md`
> **Version:** 1.1 — 2026-07-11
> **Status:** stable — procedure spec (automation requires T2+ / Node.js; a T0 manual path is included)
> **Audience:** Existing v2.0 general-context deployments upgrading to v3.0

---

## Purpose

Procedure for upgrading an existing v2.0 memory stack deployment to v3.0 general-edition. The safeguards required depend on your compliance preset choice.

---

## Pre-Migration Checklist

### Required before starting

- [ ] **Backup the entire `memory/` directory**
   ```bash
   cp -r memory/ memory.backup.v2.$(date +%Y%m%d-%H%M%S)/
   ```
- [ ] **Verify v2.0 stack is operational**
- [ ] **Determine target compliance preset** for v3.0 — see `overrides/compliance-presets.override.md`
- [ ] **Determine optional extensions** (gdpr, soc2, pci-dss) if needed

### Recommended

- [ ] Read this MIGRATION doc end-to-end
- [ ] Notify users of brief downtime (~5-30 min)
- [ ] Have rollback plan ready (Phase E below)

---

## Migration Path

### Phase A: Pre-flight (T0 manual)

1. **Backup**
   ```bash
   cp -r memory/ memory.backup.v2.$(date +%Y%m%d-%H%M%S)/
   ```

2. **Stop active sessions**

3. **Verify v2.0 schema_version**

### Phase B: Schema migration (T2+ automated; T0 manual fallback)

#### Automated path (T2+)

```bash
bash general-edition/setup.sh --migrate-from=v2.0 --compliance=<your-preset> --extensions=<comma-separated>

# Examples:
bash general-edition/setup.sh --migrate-from=v2.0 --compliance=none
bash general-edition/setup.sh --migrate-from=v2.0 --compliance=enterprise --extensions=soc2,gdpr
```

The migration script:
1. Scans every memory file under `memory/`
2. Adds YAML frontmatter to entries lacking it:
   ```yaml
   ---
   id: <derived-or-generated>
   created_at: <file-mtime>
   last_updated: <file-mtime>
   source_agent: orchestrator    # default for legacy
   source_session: 0              # pre-v3.0
   status: active
   schema_version: "2.0"          # legacy
   valid_at: <file-mtime>          # auto-default per general-edition behavior
   ---
   ```
3. Preserves entry body verbatim
4. If user selected `compliance: enterprise`: initializes audit_log + quarantine (matches preset behavior)
5. If user selected `compliance: none`: audit log defaults OFF; quarantine still initialized (always-on per B2)
6. Logs migration to audit log (or to a one-time migration record if audit is off)
7. Validation pass; quarantines failures per preset patterns

#### Manual path (T0)

No script needed — migrate by hand:
1. Back up `memory/` (Phase A, if you haven't already).
2. Copy the package into your workspace as `ultimate-memory-stack/` (containing `common-specs/` + `general-edition/`).
3. Paste the activation prompt from `ultimate-memory-stack/common-specs/BOOTSTRAP_PROMPT.md`. It detects the existing v2.0 `memory/`, proposes a migration plan — add SCHEMA_A18 frontmatter to legacy entries (the fields shown in the automated path above) and restructure projects into per-project memory-banks — and **waits for your approval before writing anything**.
4. Approve the plan; the agent migrates non-destructively (your backup is untouched) and runs the self-test.

> **Older package layouts:** installs made under pre-v4.0 guides may have `common-specs/` and `general-edition/` copied directly at the workspace root instead of vendored as `ultimate-memory-stack/`. Both layouts keep working — use whichever location exists; to match current docs, move the two folders under a new `ultimate-memory-stack/` folder (a pure move — your `memory/` data is not involved).

(Entry signing is not implemented, so there is no keypair step.)

### Phase C: General-edition-specific setup

1. **Activate user-selected compliance preset**
   - Edit `general-edition/PROFILE.md` `compliance:` field
   - If `custom`: prepare `overrides/compliance.override.md` with ≥1 override (custom complexity floor)

2. **Enable audit log per preset**
   - Default OFF for `compliance: none`
   - Default ON for `compliance: enterprise`
   - Configurable for `custom`

3. **Activate optional extensions** (if user enabled)
   - For each enabled extension in `EXTENSIONS/`, the corresponding behaviors activate

4. **HMAC secret generation (optional; signing itself is NOT IMPLEMENTED)**
   - Entry signing does not exist in this release — nothing signs or verifies
   - `setup.py --generate-hmac-secret` writes a secret only when you pass that flag
     explicitly; a default install generates nothing
   - The secret is currently unused; it only pre-provisions a key for a future release

5. **Re-scan legacy entries**
   - For `compliance: none`: only universal standing-rule detection (secrets, basic PII)
   - For `compliance: enterprise`: broad PII detection — may flag entries
   - Flagged entries → quarantine queue (non-blocking; user reviews via toast)

### Phase D: Verification

```bash
# Self-test
bash general-edition/setup.sh --verify

# Check effective preset
cat general-edition/PROFILE.md | grep "compliance:"

# If audit log enabled, check migration entry
cat memory/security/audit_log.jsonl 2>/dev/null | head -3

# Check quarantine
ls memory/quarantine/ 2>/dev/null
```

### Phase E: Rollback

Migration is non-destructive — Phase A backed up `memory/` before any change. To roll back:

```bash
# 1. Stop the agent / close the session, then move the migrated tree aside
mv memory memory.failed.$(date +%Y%m%d-%H%M%S)

# 2. Restore the v2.0 backup taken in Phase A
mv memory.backup.v2.<timestamp> memory

# 3. (Optional) remove the v3 scaffold if you don't want it
rm -f .claude/rules/memory_protocol.md
```

Your v2.0 state is fully recovered — the backup was never modified.

---

## Migration Risks (General-Edition)

| Risk | Mitigation |
|------|------------|
| User picks `compliance: none` but data should be `enterprise` | Re-run setup.sh --change-preset=enterprise; re-validation pass quarantines newly flagged entries |
| User accidentally enables extensions that don't fit context | Disable by editing the `extensions:` field in `general-edition/PROFILE.md`, then re-run `setup.sh --verify` |
| Pattern-key promotion threshold differs from v2.0 default | v3.0 default for general is ≥5; user can adjust in PROFILE.md if needed |
| Audit log audit gap (off in v2.0 → on in v3.0) | Document the gap explicitly; no auto-backfill possible |
| HMAC secret derivation differs across machines | If multi-machine, decide whether to share HMAC secret OR have per-machine secrets |

---

## General-Edition Migration Notes

| Aspect | General-edition |
|--------|-----------------|
| Compliance preset | User-selectable |
| Audit log | Optional (preset-dependent) |
| Cryptographic signature | NOT IMPLEMENTED (HMAC intended) |
| Quarantine workflow | Non-blocking |
| PHI/HIPAA re-scan | Not applicable — PHI detection is not selectable in general-edition |
| Required IP/Legal review | Public-release readiness per `PRIVACY_REVIEW.md` |

> This public package ships the general-edition only. HIPAA/PHI is out of scope for this edition.

---

## Expected Migration Output

```
Ultimate Memory Stack — Migration Complete
==========================================
From version: 2.0
To version: 3.0 (general-edition)
Backup location: memory.backup.v2.2026-05-15-143000/
Migration timestamp: 2026-05-15T14:30:42Z

Compliance preset: <user-selected>
Extensions: <enabled list>

Files migrated: <N>
Initialized:
  - audit_log.jsonl (if preset requires)
  - quarantine/ directory

Re-scan results:
  - Entries flagged: <T> (per active detection patterns)
  - Action: Review via toast at next session start

Effective tier: <T0–T4>
Active features: <list>
Dormant features: <list with unlock requirements>

Next steps:
  1. Review quarantine queue (if non-empty)
  2. Verify mirror parity (if you mirror to a second location)
  3. Begin first v3.0 session
```

---

## Cross-References

- `PROFILE.md` (general-edition defaults)
- `DEPLOYMENT.md` (fresh-install path)
- `PRIVACY_REVIEW.md` (public-release readiness)
- `overrides/compliance-presets.override.md` (preset selection)
- `EXTENSIONS/` (optional extensions)
- `setup.sh` / `setup.ps1` / `setup.py`
- `../common-specs/MEMORY_PROTOCOL.md` §13 (general migration procedure)
- (no institutional migration guide is published)
