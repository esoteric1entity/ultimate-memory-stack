# Detection Patterns — `healthcare` Preset (reserved)

> **Status:** `healthcare` is a **reserved preset value**. It is not selectable — the installer
> refuses it. The shipped presets are `none` / `enterprise` / `custom`.

No PHI detection pattern set is defined in this release. This file exists so that
`healthcare`-preset references resolve and so the name is not reused for something else.

Deployments with regulatory requirements use the `enterprise` or `custom` preset.

## Standing rules (apply in every edition, regardless of preset)

- **NEVER** store PHI in memory files — even under `compliance: none`, PHI is forbidden.
- If unsure whether data is PHI, **treat it as PHI** (precautionary principle).
- Secrets/credentials are never allowed regardless of preset (see `detection_patterns_none.md`).

## Cross-references

- `SCHEMA_compliance_profile.md` §5.2 (`healthcare` — reserved value)
- `MEMORY_PROTOCOL.md` §17 (`healthcare` preset — reserved)
- `SCHEMA_quarantine.md` §6 (reason code `phi-detected`)
- `detection_patterns_none.md` (inherited — secrets/credentials always active)
