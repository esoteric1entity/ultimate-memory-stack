# Detection Patterns — `enterprise` Preset (GDPR + SOC2 Baseline)

> **Preset:** `compliance: enterprise`
> **Purpose:** Broad PII detection (names, addresses, contact info, business identifiers) + consent tracking enforcement. GDPR Article 32 + SOC2 Trust Services Criteria baseline.
> **Note:** Audit logging (B1) is required in the `enterprise` preset.
> **Companion:** SCHEMA_compliance_profile.md §5.3 (`enterprise` preset behaviors)
> **Inherits:** All patterns from `detection_patterns_none.md` (secrets/credentials NEVER allowed regardless of preset)
> **Does NOT inherit:** `detection_patterns_healthcare.md` patterns. Enterprise is PII-focused, NOT PHI-focused. PHI/HIPAA detection is biotech-edition-reserved — not selectable in general-edition (the installer refuses the `healthcare` preset and extension).

---

## What this preset detects (in addition to `none`)

Broad Personally Identifiable Information (PII) profile + business-identifier patterns:

1. **Names** — heuristic detection of first-last name patterns (flagged, NOT auto-redacted to preserve usability)
2. **Email addresses** — RFC 5322-shaped patterns
3. **Phone numbers** — international + US formats
4. **Physical addresses** — heuristic (street number + name + city + state/zip)
5. **Government identifiers** — SSN (inherited from `none`), EIN, foreign government IDs
6. **Business identifiers** — internal employee IDs, customer IDs, account numbers
7. **IP addresses** — IPv4 + IPv6 (under GDPR, IPs are PII when linkable to individuals)
8. **Date of birth** — direct or implied from age in personal context
9. **Consent tracking violations** — entries lacking consent metadata when consent_basis is required

## What this preset does NOT detect

- PHI (MRN, specimen IDs, genomic identifiers, clinical data) — those are in `detection_patterns_healthcare.md`
- PHI/HIPAA detection is biotech-edition-reserved — not available in general-edition (the installer refuses the `healthcare` preset and extension). A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

## Detection rules

### Pattern: Email addresses

**Regex:**
```regex
\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b
```

**Severity:** MEDIUM (emails are commonly in technical documentation legitimately)
**Action:** WARN-AND-LOG (do not auto-redact by default — too disruptive; flagged for user review)
**Notes:** Enterprise deployments may auto-redact via override; default is warn-only.

### Pattern: Phone numbers

**Regex:**
```regex
# US: (NNN) NNN-NNNN or NNN-NNN-NNNN or NNN.NNN.NNNN
\b(\(\d{3}\)\s*|\d{3}[-.\s]?)\d{3}[-.\s]?\d{4}\b

# International E.164
\+\d{1,3}[-.\s]?\d{1,14}\b
```

**Severity:** MEDIUM
**Action:** WARN-AND-LOG
**Notes:** False-positive prone for version numbers / IDs in some formats. Context-aware detection (require "phone", "tel", "contact" within 30 chars) reduces this.

### Pattern: Names (heuristic — first-last)

**Regex:**
```regex
\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b
```

**Severity:** LOW (extremely high false-positive rate — any two capitalized words match)
**Action:** LOG-ONLY (no warning unless context suggests person — e.g., near "Mr.", "Ms.", "Dr.", "by", "from")
**Notes:** Name detection is fundamentally hard without entity-recognition. Conservative default; rely on user review for enterprise deployments concerned about names.

**Enhanced detection (context-aware):**
```regex
# Title + name
\b(Mr|Mrs|Ms|Mx|Dr|Prof)\.\s+[A-Z][a-z]+(\s+[A-Z][a-z]+){1,2}\b

# "By <name>" / "from <name>" / "to <name>"
\b(by|from|to|with|for)\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\b
```

**Severity:** MEDIUM (titles + position context reduce false positives)
**Action:** WARN-AND-LOG

### Pattern: Physical addresses

**Regex (heuristic):**
```regex
# Street address
\b\d{1,5}\s+([A-Z][a-z]+\s+){1,3}(St|Street|Ave|Avenue|Blvd|Boulevard|Rd|Road|Ln|Lane|Dr|Drive|Way|Ct|Court|Pl|Place)\.?\b

# City, State ZIP (US)
\b[A-Z][a-z]+(\s[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}(-\d{4})?\b
```

**Severity:** MEDIUM
**Action:** WARN-AND-LOG
**Notes:** Combined with name detection, addresses elevate risk. Cross-pattern combination escalates severity to HIGH (multi-pattern entity).

### Pattern: EIN (Employer Identification Number)

**Regex:**
```regex
\b\d{2}-\d{7}\b
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — EIN]`
**Notes:** Catches the EIN format (XX-XXXXXXX); false-positive overlap with phone-like formats minimized by the dash placement.

### Pattern: Internal employee / customer IDs

**Configurable per deployment.** Defaults to common formats:

```regex
# EMP-NNNN or EMPLOYEE-NNNN format
\b(EMP|EMPLOYEE|EMPID)[-_]\d{3,8}\b

# CUSTOMER-NNNN format
\b(CUST|CUSTOMER|ACCT|ACCOUNT)[-_]\d{4,10}\b
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN (most enterprise deployments want these redacted)
**Replacement:** `[REDACTED — internal ID]`
**Notes:** Override via `<edition>/overrides/detection_patterns_enterprise.override.md` to match your organization's actual ID format.

### Pattern: IP addresses

**Regex:**
```regex
# IPv4
\b(\d{1,3}\.){3}\d{1,3}\b

# IPv6 (simplified)
\b([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b
```

**Severity:** LOW (most IPs in technical documentation are legitimate; e.g., 127.0.0.1, public service IPs)
**Action:** LOG-ONLY
**Notes:** Under GDPR, IPs become PII when linked to individuals (e.g., in user activity logs). The detection is informational; auto-redaction is too disruptive. Custom preset can elevate to WARN-AND-LOG if needed.

### Pattern: Date of birth (DOB)

**Regex:**
```regex
\b(DOB|date of birth|born|birthday)[:\s]+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — DOB]`

### Pattern: Consent tracking violations

**Detection:** For entries with `source_agent: webfetch` or `tags: contains "user-content"`, check for `consent_basis` field in frontmatter:

- If `compliance: enterprise` AND entry lacks `consent_basis: <value>` → flag
- If `consent_revoked_at` is set AND entry status is still `active` → flag (entry should be in pending-discard state)

**Severity:** HIGH (consent violation is a regulatory issue, not a data issue)
**Action:** QUARANTINE-PENDING-USER-REVIEW
**Notes:** Unique to enterprise/custom presets. Healthcare uses implicit BAA-based consent; enterprise requires explicit per-entry consent tracking.

### Pattern: SSN (inherited from `none`)

See `detection_patterns_none.md` — `none` preset already detects SSN format. Enterprise inherits.

---

## Cross-pattern escalation

Some combinations elevate severity:

| Combination detected within 200 chars | Escalated severity | Action |
|---------------------------------------|-------------------|--------|
| Name + Email | HIGH (PII profile of an individual) | REDACT-AND-WARN both |
| Name + Phone | HIGH | REDACT-AND-WARN both |
| Name + Address | HIGH | REDACT-AND-WARN both |
| Name + DOB | CRITICAL (full identity profile) | REDACT-AND-WARN + QUARANTINE |
| Email + Phone | MEDIUM | WARN-AND-LOG both |
| SSN + Name | CRITICAL | REDACT + QUARANTINE |

**Implementation note:** Cross-pattern detection requires a windowed scan (200-char window around each pattern hit). This is more compute-intensive than single-pattern regex. At T0, the scan is simple O(n²) within entry; at T2+ (Node.js), a streaming-window scan is more efficient.

---

## Severity → Action mapping (`enterprise` preset)

| Severity | Default action |
|----------|----------------|
| CRITICAL | REDACT + QUARANTINE-PENDING-USER-REVIEW |
| HIGH | REDACT-AND-WARN (most patterns) |
| MEDIUM | WARN-AND-LOG |
| LOW | LOG-ONLY |

**Key difference from healthcare:** Most enterprise PII patterns default to WARN-AND-LOG rather than auto-redact. Rationale: enterprise contexts often legitimately need to USE PII (e.g., support ticket includes customer's name). Warn the user; let them decide.

## Consent tracking

When `compliance: enterprise`, entries gain optional frontmatter fields:

```yaml
---
consent_basis: gdpr-explicit | gdpr-legitimate-interest | contract | legal-obligation | none
consent_at: <YYYY-MM-DD>                # when consent was obtained
consent_revoked_at: <YYYY-MM-DD>        # when consent was revoked (triggers discard within 24h)
consent_party_pointer: <reference to consent record, NOT the party themselves>
---
```

- `consent_revoked_at` set → entry routes to quarantine within 24 hours; user reviews; default disposition is DISCARD per GDPR right-to-be-forgotten
- The actual consent record (signature, IP, timestamp, etc.) is stored OUTSIDE the memory stack (in a compliance-management system); the memory stack just tracks the pointer

## Integration points

- **MEMORY_PROTOCOL.md §4** — Validation-on-read fires PII detection
- **MEMORY_PROTOCOL_EXTENDED.md §E3.4** — Bi-temporal handling tracks consent revocation timestamps
- **SCHEMA_audit_log.md §4** — Detection + consent events log as audit entries
- **SCHEMA_quarantine.md §6** — `pii-detected` and consent-violation reason codes
- **SCHEMA_compliance_profile.md §5.3** — `enterprise` preset behaviors

## Maintenance

- GDPR amendments (e.g., GDPR 2.0 if/when adopted) require pattern updates
- New jurisdictional regimes (e.g., CCPA additions, EU AI Act, India DPDP) may extend the pattern set — accommodate via override files initially, promote to baseline if widely adopted
- Cross-pattern combinations should be regularly reviewed — false-positive rates evolve with content patterns

## Open questions

1. **Names detection sophistication** — Regex-based name detection is weak. Should `enterprise` deployments invest in entity-recognition models at T3+? Lean: optional integration via override.
2. **Pseudonymized data** — If data is pseudonymized (e.g., names replaced with stable hashes), should detection flag the hashes? Lean: NO — pseudonymized data is GDPR-compliant, but the link table is the sensitive artifact (kept outside memory stack).
3. **Cross-pattern detection performance** — Windowed scan is O(n²) in entry length. At very large entries (10K+ chars), this may be slow. Optimization: at T2+, use streaming windowed analysis.
4. **Consent revocation cascade** — If entry A references entry B via `related:`, and B is revoked/discarded, does A also get flagged? Likely YES for cascading consent integrity. Defer to operational tuning.
5. **Multi-jurisdictional consent** — A single entry may serve users in EU (GDPR) + US (CCPA) + other regions. Should consent_basis support multiple values? Lean: YES, array-valued. Schema update needed in a future revision.

## Cross-references

- `SCHEMA_compliance_profile.md` §5.3 (`enterprise` preset)
- `SCHEMA_audit_log.md` (detection + consent events log)
- `SCHEMA_quarantine.md` §6 (PII detected + consent-violation reason codes)
- `detection_patterns_none.md` (inherited — secrets/credentials)
- `detection_patterns_healthcare.md` (sister preset — PHI-focused; enterprise is PII-focused; combine via `custom` preset)
- **Regulatory:** GDPR Article 32 (security of processing), Article 17 (right to erasure), SOC2 Trust Services Criteria
