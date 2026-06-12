# EXTENSION — Healthcare Profile (for General-Edition)

> **File:** `general-edition/EXTENSIONS/healthcare-profile.md`
> **Version:** 1.0 — 2026-05-15
> **Compose with:** ANY base preset (most often `enterprise` or `none`)
> **Activates:** HIPAA detection + audit + quarantine workflow (similar to biotech-edition but with general-edition UX)
> **Status:** DRAFT

---

## Purpose

For general-edition users who want HIPAA-grade compliance WITHOUT biotech-specific institutional context (no NGS workflows, no <your-institution>-specific specimen patterns, no biotech-edition mandatory enforcement).

Common use cases:
- Solo healthcare provider doing personal consulting
- Software engineer building healthcare apps (needs HIPAA awareness during development)
- Researcher with occasional HIPAA-adjacent work
- Anyone wanting "HIPAA without committing to biotech-edition"

If your context IS biotech R&D at a HIPAA-regulated institution → use biotech-edition instead (mandatory enforcement, blocking quarantine, <your-institution>-style patterns).

---

## What This Extension Adds

### Detection patterns activated

- All of `../common-specs/detection_patterns_healthcare.md` Layer 1 (universal HIPAA Safe Harbor identifiers)
- NO Layer 2 (institution-specific) — that's biotech-edition territory

### Behavior changes from base preset

| Aspect | Base preset (any) | + healthcare-profile EXTENSION |
|--------|-------------------|-------------------------------|
| PHI detection | OFF (`none`) / OPT-IN | ON (mandatory once extension enabled) |
| Redaction-on-detection | N/A or warn-only | Mandatory redact + warn |
| Audit log | Per base preset | FORCE ON when extension enabled |
| Quarantine triggers | Per base | ADD `phi-detected` reason code |
| Delete semantics | Per base | OVERRIDE to tombstone + 30-day retention |
| WebFetch entries | Per base | OVERRIDE to `preliminary` status |
| Cryptographic signatures | Per base | RECOMMEND Ed25519 (when T3) |

### Frontmatter fields added (if not already present)

```yaml
compliance_extension: healthcare
phi_detection_active: true
phi_redaction_active: true
```

## Activation

```bash
# At bootstrap:
setup.sh --compliance=enterprise --extensions=healthcare

# Or via PROFILE.md edit:
compliance: enterprise
extensions:
  - healthcare
```

When activated, MEMORY_PROTOCOL.md §17 (Healthcare Compliance Profile) becomes ACTIVE — same as if `compliance: healthcare` was set, but composed on top of the base preset.

## Difference from `compliance: healthcare` Base Preset

- **As base preset:** healthcare IS the active preset; all general-edition behavior matches.
- **As EXTENSION:** healthcare patterns layer on top of another preset (e.g., enterprise + healthcare = GDPR/SOC2 patterns PLUS HIPAA patterns simultaneously).

Use the extension when you need MULTIPLE compliance regimes active.

## Worked Examples

**Example A:** Researcher in EU does occasional HIPAA-adjacent work (multi-jurisdiction).
- Base: `compliance: enterprise` (GDPR + SOC2 baseline)
- Extension: `healthcare-profile.md` ADDED
- Result: GDPR consent tracking + PII detection + HIPAA PHI detection all active simultaneously

**Example B:** Solo software developer building a healthcare app (no production PHI, but needs HIPAA awareness during dev).
- Base: `compliance: none`
- Extension: `healthcare-profile.md` ADDED
- Result: Just standing-rule + universal PHI detection (lightweight; no GDPR overhead)

## Standing Rules (Cannot Be Overridden)

Same as universal standing rules from `common-specs/MEMORY_PROTOCOL.md` §7:
- NEVER store PHI in memory files (regardless of preset)
- NEVER include patient data in audit log entry summaries
- If unsure whether data is PHI, treat as PHI

## Cross-References

- `../../common-specs/detection_patterns_healthcare.md` (Layer 1 patterns)
- `../../common-specs/SCHEMA_compliance_profile.md` §5 (preset definitions)
- `../../common-specs/MEMORY_PROTOCOL.md` §17 (healthcare profile activation)
- `../../biotech-edition/PROFILE.md` (if you need stricter biotech-grade enforcement instead)
- B7 compliance preset design
- HIPAA §164.312 / §164.514(b)
