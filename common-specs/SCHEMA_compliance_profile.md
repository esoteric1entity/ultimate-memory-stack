# Schema — Compliance Profile (B7: 3-Preset Hybrid + Custom)

> **File:** `common-specs/SCHEMA_compliance_profile.md`
> **Version:** 1.0 — stable
> **Status:** stable — cross-validated against MEMORY_PROTOCOL_EXTENDED.md §E4.2 + MEMORY_PROTOCOL.md §17
> **Authors:** see /AUTHORS.md


---

## 1. Purpose

Define a **compliance preset** system that:
- Lets users select a regulatory posture appropriate for their deployment context (solo developer / enterprise / power user with custom needs)
- Maps each preset to concrete behaviors (detection patterns, redaction rules, audit defaults, delete semantics, quarantine triggers)
- Is **non-overridable for biotech edition** (preset is locked to `healthcare`)
- Is **fully configurable for general edition** (user picks at bootstrap; can change later)
- Avoids both over-simplification (single HIPAA switch) and over-complication (4-toggle matrix where users mis-configure)

This is the **B7 ⭐ feature** — a load-bearing design decision.

---

## 2. Rationale

### Why 3 presets + custom (vs alternatives)?

The research surfaced a real design tension on compliance toggle granularity. The options considered:

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Single HIPAA toggle** | Trivial UX | Doesn't cover GDPR/SOC2/PCI-DSS; conflates "regulated" with "HIPAA" | ❌ Rejected — over-simplifies |
| **4-toggle matrix** (HIPAA/GDPR/SOC2/PCI-DSS individually) | Maximally configurable | Users mis-configure; combinations have non-obvious interactions; high cognitive load | ❌ Rejected — over-complicates |
| **3 presets + custom** ⭐ (chosen) | Covers ~95% of real deployment shapes; advanced users still have escape hatch | Slight discoverability cost (must read about presets) | ✅ CHOSEN |
| No compliance layer | Lowest friction | Cannot ship a biotech edition; cannot honor HIPAA | ❌ Rejected — disqualifies biotech use case |

**Decision:** 3-preset hybrid. Matches real-world deployment shapes:
- `none` = solo developer, personal projects, no regulatory exposure
- `healthcare` = HIPAA-active full Section 11 healthcare profile
- `enterprise` = GDPR + SOC2 baseline (provenance + audit + consent tracking)
- `custom` = power users via `<edition>/overrides/compliance.override.md`

### Why biotech edition has `healthcare` non-overridable?

Per the project's design philosophy and the B7 preset decision:

- The biotech edition exists specifically to serve healthcare/biotech R&D contexts (regulated R&D work, similar regulated R&D)
- Allowing the user to disable HIPAA detection in biotech edition would create a footgun: deployments self-identify as biotech but operate without PHI safeguards
- Non-overridability is a deliberate trust constraint — *"if you picked biotech, you opted into HIPAA. Pick general if you don't want HIPAA."*

### Why general edition defaults to `none`?

- Most general-edition use cases are non-regulated (personal projects, open-source contribution, hobby work)
- Compliance detection has a friction cost (toasts, quarantines, redactions); defaulting to `none` keeps general edition lightweight
- Users who DO have regulatory exposure in general-edition map it to the `enterprise` preset (GDPR + SOC2 baseline) or `custom` — that's a thoughtful act, not an accidental one. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

### Why `custom` exists at all?

Real-world compliance configurations sometimes need fine-grained control:
- GDPR-only deployments in EU
- SOC2-only enterprise deployments
- Compliance requirements that combine partial features (e.g., HIPAA audit + GDPR consent but not full HIPAA redaction)
- Edge cases not covered by the 3 presets

`custom` is an escape hatch — most users never touch it. Power users can compose specific behaviors via `<edition>/overrides/compliance.override.md`.

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| HIPAA §164.312(a-e) defines technical safeguards | HHS regulatory text | Federal regulation |
| GDPR Article 32 requires "appropriate technical and organizational measures" | EU GDPR text | EU regulation |
| SOC2 Trust Services Criteria require access controls + audit | AICPA TSC | Industry standard |
| Real deployments cluster around 3 shapes (none / healthcare / enterprise) | Compliance survey | Industry observation |
| Over-configuration causes mis-configuration | Defense-in-depth principle + the maintainer's OpenClaw experience | Security design principle |
| Non-overridable preset for biotech avoids footgun | Trust boundary principle | Security design principle |

**Caveats:**
- The 3-preset design covers ~95% of cases per the survey observation, not 100%. The remaining ~5% need `custom`.
- `custom` is INTENTIONALLY harder to use — power-user feature. Documentation discourages casual use.
- This schema documents the framework; specific detection patterns within each preset refine during real deployments.

---

## 4. Schema Definition

### 4.1 Preset enum

```yaml
compliance: <preset-name>
```

Where `<preset-name>` is one of:
- `none` — no regulatory detection; standard secrets/credentials hygiene only
- `healthcare` — full HIPAA Section 11 profile (**biotech-edition-reserved; not selectable in general-edition** — the value is defined here because the future biotech edition consumes it)
- `enterprise` — GDPR + SOC2 baseline
- `custom` — fully configured via `<edition>/overrides/compliance.override.md`

### 4.2 Preset behavior matrix

Each preset has concrete behaviors across 8 dimensions:

| Dimension | `none` | `healthcare` | `enterprise` | `custom` |
|-----------|--------|--------------|--------------|----------|
| **PII detection** | OFF | ON (PHI-focused) | ON (broad PII) | configured |
| **PHI detection** | OFF | ON (MRN, specimens, genomic, clinical) | OFF (unless custom adds) | configured |
| **Redaction-on-detection** | N/A | redact + warn + log | warn + log | configured |
| **Audit log** | OPT-IN default OFF | REQUIRED ON (biotech) / DEFAULT ON (general) | REQUIRED ON | configured |
| **Quarantine triggers** | manual + signature-mismatch only | PHI detection + signature-mismatch + frontmatter | PII detection + signature-mismatch + consent-violation | configured |
| **Delete semantics** | hard delete | tombstone + 30-day retention | hard delete with 7-day recovery window | configured |
| **Consent tracking** | none | implicit via HIPAA | EXPLICIT (consent_at, consent_revoked_at in frontmatter) | configured |
| **External data flags** | none | webfetch entries quarantined pending validation | webfetch entries logged for review | configured |

### 4.3 Detection pattern definitions

Each preset references a detection pattern file:

| Preset | Pattern file |
|--------|-------------|
| `none` | `common-specs/detection_patterns_none.md` (just secrets/credentials) |
| `healthcare` | `common-specs/detection_patterns_healthcare.md` (PHI patterns) |
| `enterprise` | `common-specs/detection_patterns_enterprise.md` (broad PII patterns) |
| `custom` | `<edition>/overrides/detection_patterns_custom.md` (user-defined) |



### 4.4 Custom preset structure

When `compliance: custom`, the user provides:

```markdown
# <edition>/overrides/compliance.override.md

---
compliance: custom
base_preset: enterprise           # Inherits from a base preset, then overrides
---

## Detection — Override

# (Inherit `enterprise` defaults)

PII detection: ON
PHI detection: ADD (specifically: MRN format only, not full healthcare profile)
Custom patterns:
- SSN format (XXX-XX-XXXX) — REDACT
- Internal employee IDs (EMP-NNNN format) — REDACT
- Customer email addresses — LOG ONLY (do not redact)

## Audit Log — Override

# (Inherit `enterprise`: REQUIRED ON)

Read logging: OFF (override default of ON for enterprise) — too noisy for our workflow

## Quarantine — Override

# (Inherit `enterprise`)

Add trigger: emails detected → log only, no quarantine
Remove trigger: signature-mismatch (we don't use Layer 6 signatures)
```

The `custom` preset is a thin layer on top of one of the 3 base presets — `none`, `healthcare`, or `enterprise`. Pure-from-scratch custom is not supported (too much complexity); users must inherit from a base.

---

## 5. Preset Behavior Details

### 5.1 `none` (lowest friction)

**Active behaviors:**
- Secrets/credentials hygiene only (passwords, API keys, tokens, cert files — NEVER stored regardless of preset)
- No PII/PHI detection
- Audit log: OPT-IN, default OFF (user enables manually in PROFILE.md if desired)
- Quarantine triggers: manual flag + signature-mismatch (if Layer 6 active at T3+)
- Delete = hard delete (no tombstone)
- No consent tracking
- WebFetch entries: ingested normally, no automatic quarantine

**Standing rules (ALWAYS active, cannot be overridden):**
- No passwords, API keys, tokens, secrets in memory files
- No credit card numbers, SSN-format strings
- These are non-negotiable across all presets

**Best for:**
- Solo developers working on personal/hobby projects
- Open-source contribution work
- General R&D in non-regulated domains
- Code projects where memory captures architectural decisions but never customer or patient data

### 5.2 `healthcare` (HIPAA-active)

**Active behaviors:**
- Full PHI detection (MRN format, specimen IDs, accession numbers, hospital IDs, genomic identifiers, clinical data flags)
- Redaction-on-sight (substitute `[REDACTED — PHI detected]` in any memory write)
- Warning to user when PHI detection fires
- Audit log: REQUIRED (biotech edition, non-overridable)
- Quarantine triggers: PHI detection + signature-mismatch + frontmatter validation
- Delete = tombstone with 30-day retention (per HIPAA forensic requirements)
- Consent tracking: implicit via HIPAA covered entity context
- WebFetch entries: quarantined pending orchestrator validation (suspicious external source by default)

**Detection patterns (per `common-specs/detection_patterns_healthcare.md`):**
- MRN format: variable across institutions (your institution may use NN-NNNNNN-N); detector uses configurable regex
- Specimen IDs: institution-specific patterns (<your-institution>: alpha-numeric prefix + sequence)
- Accession numbers: 7-12 digit numeric strings in specific contexts
- Genomic identifiers: variant calls (e.g., chr1:12345A>G), sequencing run IDs, sample IDs
- Clinical data: ICD-10 codes in specific contexts, prescription names linked to patients
- HIPAA-flagged file paths: contains `PHI`, `patient`, `clinical`, `HIPAA`, `MRN` keywords

**Best for:**
- Biotech R&D (regulated R&D context)
- Healthcare provider deployments
- Bioinformatics work with potential PHI exposure
- Any context where HIPAA §164.312 technical safeguards apply

### 5.3 `enterprise` (GDPR + SOC2 baseline)

**Active behaviors:**
- Broad PII detection (names, addresses, email, phone, identifiers, business secrets)
- Warning + log (NOT redact) — enterprise often wants the data, just tracked
- Audit log: REQUIRED ON
- Quarantine triggers: PII detection + signature-mismatch + consent-violation
- Delete = hard delete with 7-day recovery window (GDPR right-to-be-forgotten compliant)
- **Consent tracking: EXPLICIT** — entries can carry `consent_at` / `consent_revoked_at` in frontmatter; consent revocation triggers automatic deletion
- WebFetch entries: logged with `external_source: true` flag for compliance review

**Detection patterns (per `common-specs/detection_patterns_enterprise.md`):**
- Names: heuristic detection (first-last patterns; flagged for review, not redacted)
- Emails: regex `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- Phone numbers: international formats
- Address: heuristic detection
- Identifiers: SSN format, EIN format, government IDs
- Business secrets: configurable per deployment

**Best for:**
- Enterprise software development
- B2B SaaS contexts
- GDPR-regulated EU deployments
- SOC2-audited organizations
- Any context where PII tracking + consent is a regulatory requirement

### 5.4 `custom`

Inherits from one base preset (`none` / `healthcare` / `enterprise`), then overrides specific dimensions. See §4.4.

**Power-user only.** Most users should NOT use `custom` — pick the closest base preset and adjust expectations.

**Best for:**
- Multi-jurisdictional compliance (e.g., HIPAA + GDPR simultaneously)
- Industry-specific compliance not covered by presets (e.g., FERPA for education)
- Research deployments with non-standard data sensitivity profiles
- Power users who understand the implications

---

## 6. PROFILE.md Integration

Each edition's PROFILE.md declares the active compliance preset:

### Biotech edition

```yaml
# biotech-edition/PROFILE.md

---
edition: biotech
compliance: healthcare              # NON-OVERRIDABLE by design (B7)
compliance_overridable: false
audit_log: required                 # Non-overridable for biotech
quarantine_ux: workflow             # /audit-quarantine slash command
pattern_key_threshold: 3
crypto_signatures: ed25519-recommended
delete_semantics: tombstone-30-day
---
```

### General edition

```yaml
# general-edition/PROFILE.md

---
edition: general
compliance: none                    # DEFAULT; user-selectable at bootstrap
compliance_overridable: true
compliance_choices_at_bootstrap:
  - none      (recommended for solo dev / personal projects)
  - enterprise (recommended for business/regulated work)
  - custom    (advanced — requires writing compliance.override.md)
  # healthcare is biotech-edition-reserved (not selectable in general-edition)
audit_log: opt-in                   # Configurable
quarantine_ux: toast                # One-line approval toast
pattern_key_threshold: 5
crypto_signatures: hmac-optional
delete_semantics: hard
---
```

---

## 7. Worked Example — General Edition User Picks `enterprise`

A user installs general edition for personal projects but starts doing GDPR-relevant consulting work that touches EU customer PII.

**At bootstrap, user selects:** `compliance: enterprise`

**Behavior after selection:**
- Detection patterns from `detection_patterns_enterprise.md` activate (broad PII)
- Audit log enables (REQUIRED ON for enterprise preset)
- Quarantine triggers extend to include PII detection + consent-violation
- Delete semantics shift to hard delete with 7-day recovery window (GDPR right-to-be-forgotten compliant)
- WebFetch entries logged with `external_source: true` for compliance review

**Their general edition now carries the enterprise GDPR + SOC2 baseline** — while retaining general-edition UX (one-line toast for quarantine, less friction overall).

If they later want to revert: they can change `compliance: enterprise` → `compliance: none` in their PROFILE.md, which:
- Deactivates broad PII detection
- Audit log retains historical entries but stops adding new ones (unless explicitly re-enabled)
- Quarantined entries remain quarantined (require manual disposition)
- A migration note is logged

> A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

---

## 8. Worked Example — `custom` Preset

A research lab needs broad PII detection plus GDPR-style consent tracking for their EU collaborators, with a couple of project-specific additions.

```markdown
# general-edition/overrides/compliance.override.md

---
compliance: custom
base_preset: enterprise
---

## Consent Tracking — Add

Entries that originate from EU collaborator data MUST carry consent_at / consent_revoked_at:
- consent_at: when collaborator gave consent
- consent_revoked_at: if consent revoked, entry gets discarded within 24 hours

Add to SCHEMA_A18 frontmatter (custom field):
- consent_basis: gdpr-collaborator | internal | both
- consent_party_email: <pointer to consent record, NOT the party themselves>

## Audit Log — Override

(Inherit `enterprise`: REQUIRED ON)

Add field: every entry includes consent_basis in entry_summary if applicable.

## Quarantine — Override

(Inherit `enterprise`)

Add trigger: GDPR consent revocation → automatic quarantine pending discard
```

This composes enterprise PII detection + GDPR-style consent → covers their regulatory profile. (PHI/HIPAA detection is biotech-edition-reserved — not selectable in general-edition; a HIPAA/PHI-focused institutional edition is planned for a future release, not yet available. See CONTRIBUTING.md.)

---

## 9. Scope — CAN / CANNOT

### CAN
- Provide 3 well-tested presets covering ~95% of deployment shapes
- Honor HIPAA §164.312 technical safeguards (via `healthcare` preset)
- Support GDPR Article 32 + SOC2 baseline (via `enterprise` preset)
- Allow power-user customization via `custom` preset (inherits from a base)
- Enforce non-overridability for biotech edition (`healthcare` locked)
- Integrate with audit log (B1), quarantine (B2), pattern detection, signature verification (C4)
- Be changed by user (general edition) at any time with explicit migration logging
- Co-exist with all 7 architecture layers (Layers 0-6 + adjacent tools)

### CANNOT
- Substitute for legal review — preset selection is a guidance tool, not regulatory advice. Users in regulated industries must verify with their compliance officer.
- Cover every conceivable compliance regime (FERPA, FedRAMP, ITAR, etc.) without `custom`
- Auto-detect compliance requirements from working directory or organization context (user must explicitly select)
- Provide encryption (compliance is about controls + audit + redaction, not data-at-rest encryption — defer to OS-level encryption)
- Stop a user with filesystem access from manually editing PROFILE.md to disable detection — but Layer 6 signatures (C4) detect tampering

### Edition fit

- **Biotech-edition:** `compliance: healthcare` ONLY (non-overridable). User cannot select another preset.
- **General-edition:** none/enterprise/custom available at bootstrap; healthcare is biotech-edition-reserved (not selectable in general-edition). User selects; can change later with logging.

### Deployment tier

- **T0:** All preset behaviors work (detection patterns are regex/heuristic, no infrastructure needed)
- **T2+:** Optional file-watcher to detect compliance violations in real-time
- **T3:** Cryptographic signatures (C4) chain integrity-check the compliance configuration itself

---

## 10. Migration Strategy

### From v2.0 (had a partial healthcare profile)

v2.0's `memory_protocol.md` had a "Healthcare Compliance Profile" section that loosely corresponds to v3.0's `healthcare` preset. The migration:

1. **Biotech edition deployments:** Auto-set `compliance: healthcare` (non-overridable). No user interaction needed.
2. **General edition deployments:** At bootstrap, prompt user to select a general-edition preset (`none` / `enterprise` / `custom`). If their v2.0 deployment had compliance detection active, default the prompt to `enterprise` (GDPR + SOC2 baseline) and let them change. Save choice to PROFILE.md. (A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.)
3. **No-compliance v2.0 deployments:** Default to `compliance: none`; prompt user to confirm.

Migration is logged to audit log per `SCHEMA_audit_log.md` §4 (action: `migrate`).

---

## 11. Open Questions

1. **`custom` complexity floor** — should `custom` require the user to write a minimum viable override file (with at least 1 override), or can it be `compliance: custom` with empty override (just inherits base)? Lean: require ≥1 override to prevent accidental "I picked custom but didn't configure" footgun.
2. **Preset change during active session** — if a general-edition user changes `compliance: none` → `compliance: enterprise` mid-session, what happens to entries written in the prior preset? Probably: re-validate them at next session start (re-scan with new detection patterns). Performance cost on big deployments. Defer.
3. **Multi-preset support** — can a deployment have multiple presets active simultaneously (e.g., different presets for different projects)? Lean: NO for v3.0 — keeps semantics simple. Phase 4+ consideration.
4. **Detection pattern updates** — patterns will evolve (new PHI formats, GDPR amendments, etc.). How does an existing deployment receive pattern updates? Lean: detection_patterns_*.md files versioned; user pulls updates manually; old patterns still work but log a warning.
5. **Custom preset audit transparency** — `custom` lets a sophisticated user weaken compliance (e.g., relax PII detection while claiming an `enterprise` base). Should custom overrides require a justification text field that gets logged? Lean: YES for any general-edition `custom` built on the `enterprise` base, regardless for `none`. (In general-edition, `custom` inherits from `none` or `enterprise`; the `healthcare` base is biotech-edition-reserved and not selectable in general-edition.)

---

## 12. Cross-References

- **Design basis:** the B7 3-preset hybrid (load-bearing decision)
- **Protocol integration:** `MEMORY_PROTOCOL_EXTENDED.md` §E4.2 (compliance preset application), `MEMORY_PROTOCOL.md` §17 (Healthcare Compliance Profile activation when `compliance: healthcare`)
- **Audit log integration:** `SCHEMA_audit_log.md` (preset changes logged; PHI/PII detection events logged)
- **Quarantine integration:** `SCHEMA_quarantine.md` (preset-specific reason codes; PHI/PII detection triggers quarantine in healthcare/enterprise presets)
- **Detection patterns:** `common-specs/detection_patterns_none.md`, `_healthcare.md`, `_enterprise.md`
- **Edition profiles:** `<edition>/PROFILE.md` selects the active preset
- **Schema integration:** `SCHEMA_A18` may add custom frontmatter fields per preset (e.g., `consent_at`, `consent_basis` for enterprise + custom)
- **Regulatory references:**
  - HIPAA §164.312 (Technical safeguards)
  - GDPR Article 32 (Security of processing)
  - SOC2 Trust Services Criteria
