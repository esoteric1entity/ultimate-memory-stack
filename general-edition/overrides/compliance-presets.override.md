# Override — Compliance Presets (General-Edition Implementation)

> **File:** `general-edition/overrides/compliance-presets.override.md`
> **Version:** 1.0 — 2026-05-15
> **Overrides:** `common-specs/SCHEMA_compliance_profile.md` §5 (Preset Definitions)
> **Override mechanism:** Per B4 — implementation details for the 4 presets in general-edition context
> **Status:** stable
> **Design basis:** B7 ⭐ (3-preset hybrid + custom); custom complexity floor (≥1 override required)

---

## §5 Preset Definitions — General-Edition Implementation

This section REPLACES `common-specs/SCHEMA_compliance_profile.md` §5 with general-edition-specific implementation details. The presets selectable in general-edition are `none` / `enterprise` / `custom`; this file specifies HOW they work in general-edition. The shared common-spec also defines a `healthcare` preset value, but it is biotech-edition-reserved and **not selectable in general-edition** (the setup wizard refuses it with an "institutional edition only" message) — see §5.2.

> **Where the active preset value comes from (v4.0.0):** the installer writes the bootstrap-selected preset to `memory/user/USER_OVERRIDES.md` (not `PROFILE.md` — that file is now regenerable and holds only the shipped default, `none`). `USER_OVERRIDES.md`, if present, wins. See `PROFILE.md` §2.1.

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
  [2] enterprise — GDPR + SOC2 baseline
  [3] custom — advanced (requires writing compliance.override.md)

Your choice [1]: _

✓ Compliance preset set to `none`. Audit log will be OPT-IN (default OFF).
  You can change this later by editing PROFILE.md.
```

### §5.2 HIPAA / PHI Workloads — Institutional Edition (Planned)

The general-edition does **not** offer a selectable `healthcare` preset. The
setup wizard accepts `none`, `enterprise`, and `custom` only; selecting a
HIPAA/healthcare path is refused with an "institutional edition only" message.

A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

**For comparison only** (this describes the planned institutional edition; it is
not selectable here): the institutional edition is designed to provide
HIPAA-grade, non-overridable PHI defaults and a blocking quarantine workflow,
versus the general-edition's broad-PII `enterprise` preset with non-blocking
toast UX. The `healthcare` detection-pattern value still lives in the shared
schema (biotech-edition-reserved; not selectable in general-edition) so the
future institutional edition can consume it.

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
> [1] none — solo dev / personal projects (recommended)
  [2] enterprise — GDPR + SOC2 baseline
  [3] custom — advanced (requires writing compliance.override.md)

Your choice [1]: 2

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
    [5] Multiple (combine)

  Your choice [1]: _
```

### §5.4 `custom` Preset (General-Edition Implementation)

**Activation behavior:**
- Selected ONLY if user has explicit, sophisticated compliance needs
- Bootstrap REJECTS bare `compliance: custom` — requires user to provide ≥1 override (custom complexity floor)

**Custom configuration requirements:**
- User MUST inherit from a base preset (`none` / `enterprise`)
- User MUST provide ≥1 override at `overrides/compliance.override.md`
- Setup wizard guides user through composing the override

**Setup wizard UX for `custom`:**
```
Q: Compliance preset selection
Your choice [3]: 3

⚠️ Custom preset selected. This requires you to provide explicit configuration.

Step 1: Which base preset should `custom` inherit from?
  [1] none (start permissive, add restrictions)
  [2] enterprise (start with GDPR+SOC2, customize)

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

A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.

Within general-edition today, the strictest available path is the `enterprise`
preset (broad PII detection + required audit log + consent tracking). Full
HIPAA-grade, non-overridable defaults are reserved for the planned institutional
edition above.

---

## §Cross-References

- Parent: `../../common-specs/SCHEMA_compliance_profile.md` §5 (overridden by this file)
- `../PROFILE.md` (general-edition defaults + user-selectable choices)
- `../EXTENSIONS/` (optional regulatory profile add-ons: GDPR / SOC2 / PCI-DSS)
- `../../common-specs/detection_patterns_none.md` / `_healthcare.md` / `_enterprise.md`
- Design notes: B7 ⭐ 3-preset hybrid + custom; custom complexity floor (≥1 override required)
