# EXTENSION — GDPR Profile (for General-Edition)

> **File:** `general-edition/EXTENSIONS/gdpr-profile.md`
> **Version:** 1.0 — 2026-05-15
> **Compose with:** Most commonly `enterprise` base preset; can compose with `none` or `custom`
> **Activates:** GDPR consent tracking + right-to-be-forgotten enforcement + EU-jurisdiction patterns
> **Status:** stable — ships with UMS v4.0.0

---

## Purpose

GDPR-specific compliance for general-edition deployments in or serving EU jurisdictions. Adds explicit consent tracking, automatic discard on consent revocation, and EU-data-subject handling patterns.

Common use cases:
- EU-based developer or organization
- Non-EU organization serving EU data subjects (e.g., SaaS with EU users)
- Cross-jurisdictional context (US + EU operations)

---

## What This Extension Adds

### Detection patterns activated

- All of `../common-specs/detection_patterns_enterprise.md` PII patterns
- ADD EU-specific patterns: IBAN, EU national IDs, EU passport numbers

### Behavior changes

| Aspect | Base preset | + gdpr-profile EXTENSION |
|--------|-------------|--------------------------|
| Consent tracking | Per base | **EXPLICIT REQUIRED** for all entries with PII |
| Right-to-be-forgotten | Per base | **AUTOMATIC** discard within 24h on consent revocation |
| Audit log | Per base | FORCE ON + retention minimum 7 years (GDPR Article 30) |
| Delete semantics | Per base | OVERRIDE to hard delete + 7-day recovery window |
| Data subject access requests | N/A | EXPORT support: structured dump of all entries matching subject |
| Cross-border data transfer | N/A | Flag entries with `data_subject_jurisdiction` field |

### Frontmatter fields added

```yaml
compliance_extension: gdpr
consent_basis: gdpr-explicit | gdpr-legitimate-interest | gdpr-contract | gdpr-legal-obligation | gdpr-vital-interests | gdpr-public-task
consent_at: <YYYY-MM-DD>
consent_revoked_at: <YYYY-MM-DD>          # auto-set when revocation occurs
consent_party_pointer: <external-record-ref>  # NOT the party themselves
data_subject_jurisdiction: eu-member-state-code (e.g., "DE", "FR", "NL")
data_subject_export_supported: true       # supports DSAR (data subject access request)
```

### Consent revocation workflow

When `consent_revoked_at` is set:
1. Within 24h: entry automatically routes to quarantine with reason_code `consent-revoked`
2. Surfaces via toast at next session start (non-blocking UX)
3. User reviews; default disposition is DISCARD (per GDPR right-to-be-forgotten)
4. Discard preserves entry in `memory/quarantine/.archive/discarded/` for forensic recovery (matches the B2 quarantine workflow behavior)

### Data Subject Access Request (DSAR) support

If a data subject requests their data:
1. Query memory across all categories for entries with `data_subject_pointer: <subject-ref>`
2. Generate structured dump (JSON or markdown) of all matching entries
3. Audit log captures the DSAR event
4. Standard turnaround: 30 days max per GDPR Article 12(3)

## Activation

```bash
# At bootstrap:
setup.sh --compliance=enterprise --extensions=gdpr

# Or via PROFILE.md edit:
compliance: enterprise
extensions:
  - gdpr
```

## Cross-Pattern Composition Examples

| Composition | Result |
|-------------|--------|
| `enterprise` + `gdpr` | Broad PII + explicit consent + RTBF (most common EU scenario) |
| `none` + `gdpr` | Lightweight consent tracking without broad PII detection |
| `enterprise` + `gdpr` + `soc2` | EU SaaS with SOC2 audit requirements |

## Standing Rules (Universal Floor)

- NEVER store: passwords, API keys, credit cards (universal)
- NEVER store: PHI — PHI/HIPAA handling is out of scope for this edition

## Risks + Mitigations

| Risk | Mitigation |
|------|------------|
| User forgets to set `consent_basis` on entry with PII | Detection flags entries with PII + missing consent_basis; quarantine routes for review |
| Consent revocation arrives late (e.g., user notification delayed) | 24h automatic processing window; audit log captures revocation timing for forensic |
| DSAR export accidentally leaks unrelated entries | Query precision uses `data_subject_pointer` exact match, not heuristics |
| Cross-border data transfer compliance | `data_subject_jurisdiction` field surfaces for review; transfer compliance is user's responsibility |

## Cross-References

- `../../common-specs/detection_patterns_enterprise.md` (base PII patterns)
- `../../common-specs/SCHEMA_compliance_profile.md` §5.3 (enterprise preset)
- `../../common-specs/MEMORY_PROTOCOL_EXTENDED.md` §E3.4 (bi-temporal supersession — used for consent revocation history)
- B7 compliance preset design (3-preset hybrid)
- GDPR Article 30 (audit/records of processing)
- GDPR Article 17 (right to erasure)
- GDPR Article 32 (security of processing)
