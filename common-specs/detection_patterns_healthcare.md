# Detection Patterns — `healthcare` Preset (HIPAA-Active)

> **Note:** The `healthcare` preset is **biotech-edition-reserved — not selectable in general-edition** (the installer refuses it). This file defines the preset's PHI-detection behavior for the planned institutional edition. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

> **Preset:** `compliance: healthcare`
> **Purpose:** Full HIPAA §164.312 PHI detection. PHI redacted on sight; warnings + audit log on every detection.

> **Companion:** SCHEMA_compliance_profile.md §5.2 (`healthcare` preset behaviors), MEMORY_PROTOCOL.md §17 (healthcare compliance profile)
> **Inherits:** All patterns from `detection_patterns_none.md` (secrets/credentials NEVER allowed regardless of preset)

---

## What this preset detects (in addition to `none`)

Full HIPAA Protected Health Information (PHI) profile:

1. **Patient identifiers** — MRN, hospital account numbers, patient IDs
2. **Specimen identifiers** — accession numbers, specimen IDs, container IDs
3. **Genomic data** — variant calls linked to identifiers, sample IDs, sequencing run IDs, FASTQ header lines
4. **Clinical data** — diagnosis codes (ICD-10, SNOMED) in patient contexts, treatment records, prescription names linked to patients, pathology report identifiers
5. **Lab results identifiers** — accession-prefixed result blobs
6. **Date-of-service** for treatment-specific contexts (per HIPAA Safe Harbor)
7. **HIPAA-flagged file paths** — paths containing `PHI`, `patient`, `clinical`, `HIPAA`, `MRN`, `accession`, or institution-specific PHI keywords
8. **De-identification leakage** — quasi-identifiers (ZIP3, age >89, rare diagnosis combinations) that could re-identify

## Universal vs configurable patterns

This preset has TWO layers:

### Layer 1 — Universal HIPAA patterns
Always active. Reflect HIPAA Safe Harbor identifiers (45 CFR §164.514(b)).

### Layer 2 — Institution-specific patterns
Configurable via PROFILE.md or compliance.override.md. Reflect the specific formats your institution uses (e.g., <your-institution>-specific specimen ID patterns).

---

## Layer 1 — Universal HIPAA patterns

### Pattern: MRN (Medical Record Number)

Multiple common formats — institutions vary. Generic detection heuristics:

```regex
# Pure numeric MRN, 7-10 digits
\bMRN[:#\s]+\d{7,10}\b

# Alpha-prefixed MRN
\b(MRN|MR|HRN)[:#\s]+[A-Z]{1,3}\d{6,9}\b

# Bare numeric in MRN context (line contains "patient" or "MRN" within 50 chars)
\b\d{7,10}\b[\s\S]{0,50}(patient|MRN|medical record)
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — MRN/patient identifier]`
**Notes:** False-positive prone for unrelated numeric strings. The "context within 50 chars" rule reduces false positives.

### Pattern: Specimen IDs / Accession numbers

```regex
# Generic accession pattern (alphanumeric prefix + sequence)
\b[A-Z]{2,4}\d{4,8}\b[\s\S]{0,50}(specimen|sample|accession)

# Pure numeric accession (7-12 digits in specimen context)
\b\d{7,12}\b[\s\S]{0,50}(specimen|accession|sample|aliquot)

# Container ID with alpha-numeric prefix
\b(SPC|SP|ACC|SAMPLE|SMP)[-_]\d{6,10}\b
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — specimen/accession ID]`

### Pattern: Genomic identifiers

```regex
# FASTQ header line
^@[A-Za-z0-9_:]+(\s[12]:[YN]:\d+:[ACGTN]+)?$

# Sequencing run ID (Illumina format)
\b\d{6}_[A-Z0-9]+_\d{4}_[A-Z0-9]+\b

# Sample ID linked to genomic data
\b[A-Z]{2,5}\d{4,8}[-_]?(L|S|R)\d{1,3}\b[\s\S]{0,50}(sequenced|sequencing|FASTQ|variant)

# Variant call linked to patient context
\bchr\d+:\d+[ACGTN]>[ACGTN]\b[\s\S]{0,100}(patient|MRN|specimen)
```

**Severity:** CRITICAL
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — genomic identifier]`
**Notes:** Variant calls alone are NOT PHI per HIPAA; they become PHI when LINKED to patient identifiers. The "context within 100 chars" requirement is critical.

### Pattern: Clinical data linked to patients

```regex
# ICD-10 code in patient context
\b[A-Z]\d{2}(\.\d{1,4})?\b[\s\S]{0,50}(patient|MRN|diagnosis|condition)

# Medication name + dosage in patient context (heuristic — captures common prescription formats)
\b[A-Z][a-z]+(in|ol|am|ate|ide|ane)\s+\d+\s*(mg|mcg|g|ml|IU)\b[\s\S]{0,50}(patient|MRN|prescription|prescribed)

# Lab result blob with linked identifier
\b(WBC|RBC|HGB|PLT|GLU|CHOL):\s*\d+\.\d+\b[\s\S]{0,100}(patient|MRN|specimen)
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN
**Replacement:** `[REDACTED — clinical data with patient context]`

### Pattern: Date-of-service in treatment contexts (HIPAA Safe Harbor)

```regex
# Date in treatment context (any date format within 50 chars of treatment keywords)
\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b[\s\S]{0,50}(treated|diagnosed|admitted|discharged|visit|appointment|surgery|procedure)
```

**Severity:** HIGH
**Action:** WARN-AND-LOG (do not auto-redact — too many false positives in general writing)
**Notes:** Dates alone aren't PHI; dates LINKED to specific patient treatment are. This pattern errs toward warning for review.

### Pattern: HIPAA-flagged file paths

**Detection:** Any file path that contains, case-insensitive, any of:
- `PHI`
- `patient`
- `clinical`
- `HIPAA`
- `MRN`
- `accession`
- `specimen`
- `genom` (catches "genomic", "genome")
- Institution-specific keywords (from PROFILE.md)

**Severity:** HIGH (the path itself is a context signal)
**Action:** WARN-AND-LOG
**Notes:** Path-based detection is a heuristic — the file's CONTENT determines actual PHI presence. The path warning prompts the user to verify whether content actually contains PHI.

### Pattern: De-identification leakage (quasi-identifiers)

Quasi-identifiers per HIPAA §164.514(b) Safe Harbor:
- ZIP codes (full 5-digit; 3-digit OK if population >20K)
- Ages >89 (must be aggregated as "90+")
- Rare diagnosis codes in combination with other quasi-identifiers
- Dates of birth (year alone OK)

```regex
# ZIP code (5-digit)
\b\d{5}(-\d{4})?\b[\s\S]{0,50}(patient|address|zip)

# Age >89
\b(9\d|1\d{2})\s*(year|yo)\b[\s\S]{0,50}(patient|individual)

# Date of birth
\b(DOB|date of birth|birth date)[:\s]+(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})\b
```

**Severity:** HIGH
**Action:** REDACT-AND-WARN (for DOB)
**Action:** WARN-AND-LOG (for ZIP, age — context-dependent)
**Replacement:** `[REDACTED — quasi-identifier]`

---

## Layer 2 — Institution-specific patterns

Configurable per deployment. Default for biotech-edition deployments NOT at your institution: leave Layer 2 empty until user configures.

### <your-institution>-specific example (biotech-edition deployment at your institution)

If/when configured, may include:
- <your-institution>-specific specimen ID format (e.g., `[NN]-[NNNNNN]-[N]`)
- <your-institution>-specific accession format
- <your-institution> report-ID patterns
- <your-institution> customer-account-ID patterns

**Where configured:** `<edition>/overrides/detection_patterns_healthcare.override.md` per B4 override-file convention.

---

## Severity → Action mapping (`healthcare` preset)

| Severity | Default action |
|----------|----------------|
| CRITICAL | REDACT-AND-WARN + ROUTE-TO-QUARANTINE-PENDING-USER-REVIEW |
| HIGH | REDACT-AND-WARN (most cases) OR WARN-AND-LOG (context-dependent like dates, ZIPs) |
| MEDIUM | WARN-AND-LOG |
| LOW | LOG-ONLY |

**Difference from `none` preset:** CRITICAL detections in healthcare also trigger quarantine routing (per SCHEMA_quarantine.md §6 `phi-detected` reason code). The entry is flagged for user review before any further use.

## Action: ROUTE-TO-QUARANTINE-PENDING-USER-REVIEW

When PHI is detected with CRITICAL severity:
1. Redact the matched content in the entry body
2. Set entry status to `quarantined` per SCHEMA_quarantine.md
3. Append quarantine event to `quarantine_log.jsonl` with reason `phi-detected`
4. Append audit log event per SCHEMA_audit_log.md (action: `quarantine`, quarantine_reason: `phi-detected`)
5. Surface to user via `/audit-quarantine` workflow (biotech edition) or one-line toast (general edition)
6. Entry cannot be loaded into context until user approves release

## Integration points

- **MEMORY_PROTOCOL.md §4.1** — Validation-on-read fires PHI detection
- **MEMORY_PROTOCOL.md §17** — Healthcare compliance profile (this preset is its detection set)
- **SCHEMA_audit_log.md §4** — Detection events log as audit entries
- **SCHEMA_quarantine.md §6** — `phi-detected` reason code
- **SCHEMA_compliance_profile.md §5.2** — `healthcare` preset behaviors

## Standing rules (NEVER overridable regardless of preset)

- **NEVER** store PHI in memory files — even with `compliance: none`, PHI is forbidden
- **NEVER** log PHI to audit log entry summaries (max 200 chars; redact PHI before summarizing)
- If unsure whether data is PHI, **treat it as PHI** (precautionary principle)

## Maintenance

- HIPAA Safe Harbor identifiers (§164.514(b)) are stable; patterns rarely change
- Institution-specific patterns evolve as customers change ID formats; capture changes via override files
- New diagnosis coding systems (e.g., when ICD-11 displaces ICD-10) require pattern updates
- Every pattern change logs a DEC entry with source documentation

## Open questions

1. **Free-text PHI risk** — Patient names, addresses, etc. in unstructured prose. Detection is hard (false positives high). Currently relying on context (file paths, surrounding keywords) rather than entity-recognition. Future work: integrate medical NLP model at T3+ when Code Exec available.
2. **Variant call sensitivity** — Variant calls alone aren't PHI but become PHI when linked. Current pattern uses "context within 100 chars" heuristic. Is this tight enough? Operational experience will tune.
3. **Quasi-identifier combinations** — A single ZIP isn't PHI; ZIP + age + rare-diagnosis IS. Current pattern checks each individually. Cross-pattern combination detection would require structured analysis beyond regex.
4. **De-identified clinical research data** — If a deployment uses CONFIRMED-DEIDENTIFIED data (e.g., research datasets with no linkage), should detection be relaxed? Lean: NO — still defensive; user can release via quarantine workflow if they're confident.
5. **Cross-institution pattern sharing** — Should there be a community-maintained patterns repo for healthcare? Probably yes long-term; v3.0 scope is single-institution.

## Cross-references

- `SCHEMA_compliance_profile.md` §5.2 (`healthcare` preset)
- `MEMORY_PROTOCOL.md` §17 (Healthcare Compliance Profile section)
- `SCHEMA_quarantine.md` §6 (reason code `phi-detected`)
- `SCHEMA_audit_log.md` (detection events log)
- `detection_patterns_none.md` (inherited — secrets/credentials still active)
- **Regulatory:** HIPAA §164.312 (technical safeguards), §164.514(b) (Safe Harbor identifiers)
