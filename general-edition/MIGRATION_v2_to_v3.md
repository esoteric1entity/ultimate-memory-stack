# Migration v2.0 → v3.0 — General-Edition

> **File:** `general-edition/MIGRATION_v2_to_v3.md`
> **Version:** 1.0 — 2026-05-15
> **Status:** DRAFT — procedure spec; automation requires T2+ (Node.js)
> **Audience:** Existing v2.0 general-context deployments upgrading to v3.0

---

## Purpose

Procedure for upgrading an existing v2.0 memory stack deployment to v3.0 general-edition. Simpler than biotech-edition migration — fewer HIPAA-specific safeguards required (depending on user's preset choice).

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

Same as biotech-edition manual path (see `biotech-edition/MIGRATION_v2_to_v3.md` Phase B), but skip biotech-specific Ed25519 keypair setup.

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

4. **HMAC secret generation (if at T3+)**
   - General-edition uses HMAC by default (not Ed25519)
   - HMAC secret can be session-derived (simpler than keypair management)
   - Or user-provided if they prefer stable HMAC across sessions
   - Setup script generates session-derived secret automatically

5. **Re-scan legacy entries**
   - For `compliance: none`: only universal standing-rule detection (secrets, basic PII)
   - For `compliance: enterprise`: broad PII detection — may flag entries
   - Flagged entries → quarantine queue (non-blocking for general-edition; user reviews via toast)

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

Same as biotech-edition rollback procedure (see biotech `MIGRATION_v2_to_v3.md` Phase E).

---

## Migration Risks (General-Edition)

| Risk | Mitigation |
|------|------------|
| User picks `compliance: none` but data should be `enterprise` | Re-run setup.sh --change-preset=enterprise; re-validation pass quarantines newly flagged entries |
| User accidentally enables extensions that don't fit context | Disable via PROFILE.md edit; setup.sh --change-extensions= |
| Pattern-key promotion threshold differs from v2.0 default | v3.0 default for general is ≥5; user can adjust in PROFILE.md if needed |
| Audit log audit gap (off in v2.0 → on in v3.0) | Document the gap explicitly; no auto-backfill possible |
| HMAC secret derivation differs across machines | If multi-machine, decide whether to share HMAC secret OR have per-machine secrets |

---

## Differences from Biotech-Edition Migration

| Aspect | Biotech-edition | General-edition |
|--------|------------------|-----------------|
| Compliance preset | `healthcare` (locked) | User-selectable |
| Audit log | REQUIRED on migration | Optional (preset-dependent) |
| Cryptographic signature | Ed25519 strongly recommended | HMAC default (or none if T0/T1/T2) |
| Quarantine workflow | Blocking when >5 | Non-blocking |
| HIPAA validation re-scan | Always | Not applicable — PHI detection is biotech-edition-reserved (not selectable in general-edition) |
| Required IP/Legal review | <your-institution>-context per `PRIVACY_REVIEW.md` | Just public-release readiness per `PRIVACY_REVIEW.md` |

> This comparison describes the biotech-edition's locked configuration for reference; this public package ships the general-edition only. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

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
  2. Verify mirror parity (D ↔ C if applicable)
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
- `../biotech-edition/MIGRATION_v2_to_v3.md` (companion for biotech context)
