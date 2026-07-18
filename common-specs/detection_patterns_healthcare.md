# Detection Patterns — `healthcare` Preset (HIPAA-Active)

> **Status:** The `healthcare` preset is **not selectable in this edition** — the installer
> refuses it. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet
> available). See CONTRIBUTING.md.

> **Preset:** `compliance: healthcare`
> **Purpose:** HIPAA-aligned PHI detection with redact-on-sight, audit logging, and quarantine
> routing.

The detailed PHI-detection pattern set (the regex library, severity → action mapping, and
quarantine integration) is part of the planned institutional edition and is **not included in this
public release**. This placeholder keeps `healthcare`-preset references resolvable.

## Standing rules (apply in every edition, regardless of preset)

- **NEVER** store PHI in memory files — even under `compliance: none`, PHI is forbidden.
- If unsure whether data is PHI, **treat it as PHI** (precautionary principle).
- Secrets/credentials are never allowed regardless of preset (see `detection_patterns_none.md`).

## Cross-references

- `SCHEMA_compliance_profile.md` §5.2 (`healthcare` preset behaviors)
- `MEMORY_PROTOCOL.md` §17 (Healthcare Compliance Profile)
- `SCHEMA_quarantine.md` §6 (reason code `phi-detected`)
- `detection_patterns_none.md` (inherited — secrets/credentials always active)
