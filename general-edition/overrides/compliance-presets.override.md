# Override — Compliance Presets (General-Edition Implementation)

> **File:** `general-edition/overrides/compliance-presets.override.md`
> **Version:** 1.0 — 2026-05-15
> **Overrides:** `common-specs/SCHEMA_compliance_profile.md` §5 (Preset Definitions)
> **Override mechanism:** Per B4 — implementation details for the 4 presets in general-edition context
> **Status:** stable
> **Design basis:** B7 ⭐ (3-preset hybrid + custom); custom complexity floor (≥1 override required)

---

## §5 Preset Definitions — General-Edition Implementation

This section REPLACES `common-specs/SCHEMA_compliance_profile.md` §5 with general-edition-specific implementation details. The 4 presets themselves (none / healthcare / enterprise / custom) are defined in the common-spec; this file specifies HOW they work in general-edition.

### §5.1 `none` Preset (General-Edition Default)

**Activation behavior:**
- Selected at bootstrap (Step 7 Q3) if user picks "none — solo dev / personal projects / no regulatory exposure"
- Default if user skips Q3 (matches "lowest friction" principle)
- Can be CHANGED later via PROFILE.md edit + `setup.sh --change-preset=<new>` (or manual edit)

**Active in general-edition with `none`:**
- Detection patterns: `../common-specs/detection_patterns_none.md` only (secrets, credentials, basic identifiers)
- Audit log: OFF by default (user can opt-in via `audit_log: true` in PROFILE.md)
- Quarantine UX: one-line toast at session start
- Quarantine triggers: manual flag + signature-mismatch (if Layer 6 active at T3+)
- Delete semantics: hard delete + 7-day recovery window
- Consent tracking: none (not relevant for non-regulated context)
- WebFetch entries: ingested normally, no quarantine

**Setup wizard UX for `none`:**
```
Q: Compliance preset selection
> [1] none — solo dev / personal projects (recommended)
  [2] healthcare — HIPAA-active
  [3] enterprise — GDPR + SOC2 baseline
  [4] custom — advanced (requires writing compliance.override.md)

Your choice [1]: _

✓ Compliance preset set to `none`. Audit log will be OPT-IN (default OFF).
  You can change this later by editing PROFILE.md.
```

### §5.2 `healthcare` Preset (General-Edition Implementation)

**Activation behavior:**
- Selected at bootstrap if user has HIPAA-relevant work (e.g., personal volunteer work for clinic)
- More aggressive than `none`; mirrors biotech-edition behavior

**Active in general-edition with `healthcare`:**
- Detection patterns: `../common-specs/detection_patterns_healthcare.md` (Layer 1 + Layer 2 if user provides)
- Audit log: ON by default (per `audit_log_default_when_preset_is.healthcare: true`)
- Quarantine UX: toast (general-edition non-blocking) BUT with stronger language
- Quarantine triggers: PHI detection + signature-mismatch + frontmatter
- Delete semantics: tombstone + 30-day retention (matches biotech-edition healthcare)
- Consent tracking: implicit via HIPAA covered entity context
- WebFetch entries: quarantined pending validation (suspicious by default)

**Difference from biotech-edition healthcare:**
- General-edition healthcare is OPT-OUT supported (user picked it; can change to another preset)
- Biotech-edition healthcare is NON-OVERRIDABLE
- General-edition quarantine UX is non-blocking (toast); biotech is blocking (workflow)
- Same detection patterns; different consequences

**Setup wizard UX for `healthcare`:**
```
Q: Compliance preset selection
Your choice [2]: 2

✓ Compliance preset set to `healthcare`.
  ⚠️ This activates HIPAA-grade PHI detection across all memory writes.
  • Audit log will be ON by default (you can configure retention via PROFILE.md)
  • Quarantine triggers on PHI detection (toast UX; non-blocking)
  • Delete semantics: tombstone + 30-day retention
  • Cryptographic signatures: Ed25519 recommended (activates at T3)

  Continue? [Y/n]: _

  ℹ️ Note: If your work is at a regulated biotech/healthcare institution, consider
     deploying biotech-edition instead — it provides HIPAA-grade non-overridable
     defaults and a blocking quarantine workflow.
```

### §5.3 `enterprise` Preset (General-Edition Implementation)

**Activation behavior:**
- Selected at bootstrap if user has business/regulated work (GDPR, SOC2 contexts)
- Broad PII detection without HIPAA-specific PHI focus

**Active in general-edition with `enterprise`:**
- Detection patterns: `../common-specs/detection_patterns_enterprise.md` (broad PII)
- Audit log: ON by default + REQUIRED for compliance
- Quarantine UX: toast with consent-violation reason tracking
- Quarantine triggers: PII detection + signature-mismatch + consent-violation
- Delete semantics: hard delete + 7-day recovery window (GDPR right-to-be-forgotten compliant)
- Consent tracking: EXPLICIT (`consent_at` / `consent_revoked_at` fields in frontmatter)
- WebFetch entries: logged with `external_source: true` flag

**Setup wizard UX for `enterprise`:**
```
Q: Compliance preset selection
Your choice [3]: 3

✓ Compliance preset set to `enterprise`.
  • Broad PII detection (names, emails, addresses, business IDs)
  • Audit log REQUIRED (cannot disable)
  • Consent tracking ENABLED — entries from external sources need consent_basis
  • Hard delete with 7-day GDPR recovery window
  • Cross-pattern escalation (Name+DOB = CRITICAL → quarantine)

  Optional: Add regulatory extensions for specific regimes?
  > [1] None (default)
    [2] GDPR (EU-jurisdiction)
    [3] SOC2 (audit-ready)
    [4] PCI-DSS (payment card)
    [5] Healthcare add-on (HIPAA without biotech specifics)
    [6] Multiple (combine)

  Your choice [1]: _
```

### §5.4 `custom` Preset (General-Edition Implementation)

**Activation behavior:**
- Selected ONLY if user has explicit, sophisticated compliance needs
- Bootstrap REJECTS bare `compliance: custom` — requires user to provide ≥1 override (custom complexity floor)

**Custom configuration requirements:**
- User MUST inherit from a base preset (`none` / `healthcare` / `enterprise`)
- User MUST provide ≥1 override at `overrides/compliance.override.md`
- Setup wizard guides user through composing the override

**Setup wizard UX for `custom`:**
```
Q: Compliance preset selection
Your choice [4]: 4

⚠️ Custom preset selected. This requires you to provide explicit configuration.

Step 1: Which base preset should `custom` inherit from?
  [1] none (start permissive, add restrictions)
  [2] healthcare (start with HIPAA, customize)
  [3] enterprise (start with GDPR+SOC2, customize)

Your choice: _

Step 2: What overrides do you need? Describe in plain text; I'll convert
        to compliance.override.md format.

Examples:
  - "Add SSN format detection (XXX-XX-XXXX)"
  - "Disable audit log read events (only log writes)"
  - "Add consent tracking for entries with source_agent: webfetch"
  - "Use custom retention: 180 days for audit log"

Your overrides (one per line; blank line to finish):
_
```

The wizard generates `overrides/compliance.override.md` from user descriptions. User reviews + saves.

### §5.5 Preset Change Workflow (Mid-Deployment)

User can change preset at any time:

```bash
$ setup.sh --change-preset=<new-preset>
```

Or by editing PROFILE.md directly. On preset change:

1. **Log change to audit trail** (even if audit was OFF, this event is recorded)
2. **Backwards re-validation** — scan all existing memory entries against new preset detection patterns
3. **Quarantine entries** that fail new preset's stricter detection
4. **Notify user** with summary: "X entries quarantined; review via toast/workflow"

### §5.6 Cross-Edition Migration

If user starts with general-edition (`none` preset) and later realizes they need biotech-grade compliance:

Option A: Switch to general-edition `healthcare` preset (lighter friction)
Option B: Migrate to biotech-edition (full HIPAA non-overridable)

Migration tool surfaces this choice at preset-change time with biotech-edition pointer.

---

## §Cross-References

- Parent: `../../common-specs/SCHEMA_compliance_profile.md` §5 (overridden by this file)
- `../PROFILE.md` (general-edition defaults + user-selectable choices)
- `../EXTENSIONS/` (4 optional regulatory profile add-ons)
- `../../common-specs/detection_patterns_none.md` / `_healthcare.md` / `_enterprise.md`
- Design notes: B7 ⭐ 3-preset hybrid + custom; custom complexity floor (≥1 override required)
