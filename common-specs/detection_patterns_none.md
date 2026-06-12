# Detection Patterns — `none` Preset

> **Preset:** `compliance: none`
> **Purpose:** Baseline secrets/credentials hygiene only. NO regulatory PII/PHI detection. Lowest friction.

> **Companion:** SCHEMA_compliance_profile.md §5.1 (`none` preset behaviors)
> **Status:** ALWAYS active regardless of preset selection — these are the universal standing rules (MEMORY_PROTOCOL.md §7) which `none` preset extends to its detection set

---

## What this preset detects

**Only standing-rule violations** — items that NEVER belong in memory files under any compliance posture:

1. Passwords
2. API keys / access tokens / OAuth secrets / bearer tokens
3. Private cryptographic keys (RSA, Ed25519, etc.)
4. Database connection strings with embedded credentials
5. Cloud provider credentials (AWS, GCP, Azure)
6. SSN-format strings (XXX-XX-XXXX)
7. Credit card numbers (PAN — Primary Account Number, Luhn-checksum-valid)
8. Certificate file contents (PEM-formatted, etc.)
9. Recovery / backup codes (typically 8-12 digit alphanumeric)

## What this preset does NOT detect

- Names, emails, addresses, phone numbers (no PII detection)
- MRNs, specimen IDs, genomic identifiers (no PHI detection)
- Business secrets, internal employee IDs (no enterprise patterns)
- Consent tracking fields (no GDPR-aware patterns)

## Detection rules

### Pattern: Embedded passwords

**Regex (case-insensitive):**
```regex
(password|passwd|pwd)[\s]*[=:][\s]*["']?[^"'\s]{4,}["']?
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — password pattern]`
**Notes:** Catches `password=mypw123`, `passwd: "secret"`, `pwd = 'abc'`. Allows variable names like `passwordVariable` (no `=` follows).

### Pattern: API keys / access tokens

**Regex examples (common formats):**
```regex
# Generic API key
(api[_-]?key|access[_-]?token|secret[_-]?key)[\s]*[=:][\s]*["']?[A-Za-z0-9_\-]{16,}["']?

# AWS Access Key ID
AKIA[0-9A-Z]{16}

# AWS Secret Access Key (heuristic)
[\s][A-Za-z0-9/+=]{40}[\s]?

# GitHub Personal Access Token
ghp_[A-Za-z0-9]{36}

# OpenAI / Anthropic API key
sk-[A-Za-z0-9_\-]{40,}

# Slack tokens
xox[bpoars]-[A-Za-z0-9-]{10,48}

# Stripe keys
[ps]k_(test|live)_[A-Za-z0-9]{24,}
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — API key/token pattern]`

### Pattern: Private cryptographic keys

**Regex (PEM blocks):**
```regex
-----BEGIN (RSA |EC |DSA |ENCRYPTED |OPENSSH |PRIVATE )?PRIVATE KEY-----
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** Full PEM block replaced with `[REDACTED — private key block]`

### Pattern: Database connection strings with credentials

**Regex examples:**
```regex
# Postgres / MySQL with creds
(postgres|postgresql|mysql)://[^:]+:[^@]+@[^/\s]+/[^\s]+

# MongoDB
mongodb(\+srv)?://[^:]+:[^@]+@[^/\s]+

# JDBC
jdbc:\w+://[^?\s]+\?.*password=[^&\s]+
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — connection string with embedded credentials]`

### Pattern: SSN format

**Regex:**
```regex
\b\d{3}-\d{2}-\d{4}\b
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — SSN format]`
**Notes:** False-positive prone (e.g., software version "1.234-56-7890" could match). Always log the surrounding context for review.

### Pattern: Credit card numbers (Luhn-valid PAN)

**Detection approach:**
1. Find 13-19 digit strings (with optional spaces/dashes)
2. Apply Luhn checksum
3. If valid → REDACT

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — credit card number]`

### Pattern: Cloud provider credentials

**Regex:**
```regex
# AWS Access Key
AKIA[0-9A-Z]{16}

# GCP service account JSON (key field)
"private_key": "-----BEGIN PRIVATE KEY-----[^"]+

# Azure storage account key (base64, 88 chars)
[A-Za-z0-9+/]{86}==
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN

### Pattern: Recovery / backup codes

**Regex (heuristic — 8-12 char alphanumeric, dash-separated quads or runs):**
```regex
\b[A-Z0-9]{4}[-\s]?[A-Z0-9]{4}[-\s]?[A-Z0-9]{4}\b
```

**Severity:** MEDIUM (high false-positive rate; alphanumeric IDs of this shape exist legitimately)
**Action:** WARN-AND-LOG (do not auto-redact; user review)

---

## Severity → Action mapping

| Severity | Default action (none preset) |
|----------|------------------------------|
| CRITICAL | REDACT-AND-WARN (auto-redact; alert user) |
| HIGH | REDACT-AND-WARN |
| MEDIUM | WARN-AND-LOG (no auto-redact; user reviews) |
| LOW | LOG-ONLY |

## Action definitions

- **REDACT-AND-WARN:** Replace matched content with `[REDACTED — <reason>]` in any memory write. Surface a one-line warning to user. Log event to audit log (per SCHEMA_audit_log).
- **WARN-AND-LOG:** Do not redact; preserve content. Surface a warning to user. Log event to audit log.
- **LOG-ONLY:** Silent log entry; no user-facing warning. Useful for low-confidence patterns where false-positive rate would be annoying.

## Integration points

- **MEMORY_PROTOCOL.md §4.1** — Validation-on-read fires these patterns when entries are loaded
- **MEMORY_PROTOCOL.md §5.2** — Audit log captures detection events
- **SCHEMA_quarantine.md §6** — `pii-detected` reason code routes flagged entries to quarantine (general edition only fires for CRITICAL severity at `none` preset)
- **SCHEMA_compliance_profile.md §5.1** — This file defines the `none` preset's detection scope

## Maintenance

- Patterns evolve. New API key formats appear (vendor releases new key prefix conventions). When updating:
  - Bump file version in header
  - Add the new pattern with severity + action
  - Document the source (vendor security docs URL)
  - Log a DEC entry referencing the update
- Test new patterns against a known-good corpus before deploying

## Cross-references

- `SCHEMA_compliance_profile.md` §4.3 (preset → pattern file mapping), §5.1 (`none` preset behavior)
- `MEMORY_PROTOCOL.md` §7 (standing rules — universal across presets), §4.1 (validation-on-read)
- `SCHEMA_audit_log.md` (detection events log here)
- `SCHEMA_quarantine.md` (CRITICAL-severity detections may quarantine the entry)

## Open questions

1. **False-positive rate for SSN format** — common in version strings, sequence IDs. Should `none` preset auto-redact (current) or just warn? Operational experience will tune.
2. **Recovery code pattern** — high false-positive. Currently MEDIUM/WARN. Acceptable?
3. **Vendor-specific key formats** — new vendors emerge; how to keep patterns current? Probably community-maintained pattern updates with explicit DEC capture.
