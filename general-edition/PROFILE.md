---
edition: general
compliance: none
audit_log: opt-in
quarantine_ux: toast
crypto_signatures_scheme: "hmac-sha256"
pattern_key_threshold: 5
eager_set_budget_bytes: 80000
override_file_map:
  - spec_file: "MEMORY_PROTOCOL.md §3 (Conflict Resolution)"
    override_file: "overrides/generic-conflict-resolution.override.md"
  - spec_file: "SCHEMA_compliance_profile.md §5 (Preset Definitions)"
    override_file: "overrides/compliance-presets.override.md"
  - spec_file: "BOOTSTRAP_PROMPT.md Step 7 (Setup Wizard)"
    override_file: "overrides/generic-examples.override.md"
---

# General-Edition Profile

> **File:** `general-edition/PROFILE.md`
> **Version:** 1.1 — stable
> **Status:** stable — **REGENERABLE (v4.0.0):** the installer may overwrite this file freely on install/upgrade. It holds shipped defaults, not your configuration — user customization lives in `memory/user/USER_OVERRIDES.md` instead (create-once, never rewritten; values there take precedence over this file's frontmatter). See §2.1 + `MEMORY_PROTOCOL_EXTENDED.md` §E4.3.
> **Authors:** see /AUTHORS.md
> **Design basis:** memory R&D structure, design philosophy, documentation discipline, per-edition Tier B behaviors (B1/B2/B6/B7/B8), modular consumer architecture

---

## What This File Is

**Purpose:** Declare the general-edition's shipped defaults + override-file map. Loaded by MEMORY_PROTOCOL.md §1.1 (Edition Detection) at every session start, immediately followed by a limited read of `memory/user/USER_OVERRIDES.md` if it exists — those values win on conflict.

**This is the load-bearing file for general-edition.** All behavior divergence from common-spec defaults flows from here or from USER_OVERRIDES.md. Unlike biotech-edition (which has non-overridable defaults), general-edition supports user customization — as of v4.0.0, via USER_OVERRIDES.md rather than by hand-editing this file (this file is now regenerable and hand-edits to it are not preserved across upgrades).

---

## 1. Edition Declaration

```yaml
edition: general
edition_version: "1.0"
schema_version: "3.0"
parent_spec: "../common-specs/"
parent_spec_version: "3.0"
target_audience: "Solo developers, software dev, research, writing, education, B2B SaaS, enterprise contexts without strict regulatory requirements (or those wanting opt-in GDPR/SOC2/PCI-DSS). A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md."
license_posture: "Public release — Apache-2.0"
```

## 2. Defaults + User-Selectable Choices (B7)

```yaml
# Compliance — DEFAULT `none`; user-selectable at bootstrap
compliance: none                    # DEFAULT — user changes at bootstrap if needed
compliance_overridable: true        # User CAN change this
compliance_choices_at_bootstrap:
  - none       # (recommended for solo dev / personal projects)
  - enterprise # (recommended for business/regulated work)
  - custom     # (advanced — requires writing compliance.override.md)
compliance_preset_change_requires_audit: true  # Preset changes log to audit trail even when audit is opt-in

# Audit log — OPT-IN (B1)
audit_log: opt-in                   # User selects ON or OFF at bootstrap (default OFF for `none` preset)
audit_log_default_when_preset_is:
  none: false
  healthcare: true   # biotech-edition-reserved; not selectable in general-edition
  enterprise: true
  custom: configured_via_override
audit_log_format: jsonl-append-only
audit_log_retention_days: 90        # General default; configurable
audit_log_path: "memory/security/audit_log.jsonl"

# Quarantine UX — non-blocking toast (B2)
quarantine_ux: toast                # One-line approval toast at session start
quarantine_blocking_threshold: null # Non-blocking (vs biotech blocking at >5)
quarantine_log_path: "memory/quarantine/quarantine_log.jsonl"
quarantine_max_defer_days: null     # No automatic defer warning

# Pattern-key recurrence — more conservative (B6)
pattern_key_threshold: 5            # Suggest promotion at 5 (vs 3 for biotech)
pattern_key_auto_promote: false     # SUGGEST not auto-promote
pattern_key_promote_target: ".claude/rules/auto_rules.md"

# Cryptographic signatures — HMAC optional (C4)
crypto_signatures: hmac-optional    # HMAC default if user enables
crypto_signatures_scheme: "hmac-sha256"
crypto_signatures_key_management: "session-derived-secret"
crypto_signatures_activates_at_tier: 3  # Code Execution required

# Delete semantics — hard delete with recovery window
delete_semantics: hard              # Hard delete (vs biotech tombstone)
delete_recovery_window_days: 7      # 7-day recovery window per GDPR
delete_audit_required: false        # Opt-in if audit log enabled

# Bi-temporal annotations — available (B5)
bi_temporal_required: false         # Optional per entry
bi_temporal_default_valid_at: created_at  # Auto-default to created_at if omitted
bi_temporal_auto_invalid_at: true   # Auto-set invalid_at when supersession occurs (when feature is used)

# Memory poisoning defenses — full set active (B8, regardless of preset)
memory_poisoning_defenses:
  provenance: required              # source_agent + source_session ALWAYS set
  validation_on_read: required      # Always active
  quarantine_on_validation_fail: required
  cryptographic_signatures: hmac-optional-at-T3

# WebFetch handling — preset-dependent
webfetch_default_status:
  none: active                      # Trust by default
  healthcare: preliminary           # biotech-edition-reserved; not selectable in general-edition (requires validation; matches biotech-edition behavior)
  enterprise: logged                # Logged for review
  custom: configured_via_override

# Validation TTL
expires_at_default_days: 28         # 28 days from last_validated (same as biotech)
revalidation_alert_threshold_days: 7

# Lint operation (Karpathy LLM Wiki pattern — general: monthly suggested, non-blocking)
lint:
  cadence: monthly                  # Auto-suggest frequency (vs biotech weekly)
  mode: suggested                   # Surface as toast at session start; user opts in
  blocking_on_critical: false       # Never block in general-edition
  retention_runs_days: 90           # Lighter default than biotech
  output_path: memory/security/lint_runs.jsonl
  thresholds:
    stale_tentative_sessions: 20    # More lenient than biotech
    stale_webfetch_days: 90
    orphan_minimum_age_sessions: 10
  checks_enabled:
    orphan: true
    broken_ref: true
    stale_tentative: true
    stale_webfetch: true
    contradiction: false            # OPT-IN for general (T3 required + LLM cost)
    missing_concept: false          # OPT-IN for general (T3 required + LLM cost)
```

## 2.1 USER_OVERRIDES Precedence (v4.0.0)

Every value above is a **shipped default**, not your configuration. If `memory/user/USER_OVERRIDES.md` exists, its frontmatter values **override the corresponding value above** — read second, at the same session-start step (MEMORY_PROTOCOL.md §1.1). The installer creates USER_OVERRIDES.md once (from `common-specs/templates/USER_OVERRIDES.template.md`) if absent, and never writes to it again; this file's frontmatter may be freely regenerated on any install/upgrade. If USER_OVERRIDES.md is absent (e.g. a Door-4 manual install that never ran an installer), the defaults above apply directly — this is a supported state, not a halt condition. Full mechanics + the installer's archive-and-migration-notice behavior for a pre-v4.0.0 hand-edited copy of this file: `MEMORY_PROTOCOL_EXTENDED.md` §E4.3.

## 3. Compliance Detection Patterns (selected by active preset)

| Active preset | Detection patterns file |
|---------------|-------------------------|
| `none` | `../common-specs/detection_patterns_none.md` |
| `healthcare` _(biotech-edition-reserved; not selectable in general-edition)_ | `../common-specs/detection_patterns_healthcare.md` (Layer 1 universal; Layer 2 institution-specific via custom override if needed) |
| `enterprise` | `../common-specs/detection_patterns_enterprise.md` |
| `custom` | User-defined at `overrides/detection_patterns_custom.override.md` (must inherit a base preset) |

## 4. Override-File Map (B4)

The following common-spec files have general-edition overrides:

| Common-spec file | Override file | Sections overridden |
|------------------|---------------|---------------------|
| `MEMORY_PROTOCOL.md` §3 (Conflict Resolution) | `overrides/generic-conflict-resolution.override.md` | Conflict resolution hierarchy with preset-dependent compliance rank |
| `SCHEMA_compliance_profile.md` §5 (Preset Definitions) | `overrides/compliance-presets.override.md` | 4 preset implementation details specific to general-edition (workflows, UX patterns, defaults) |
| `BOOTSTRAP_PROMPT.md` Step 7 (Setup Wizard) | `overrides/generic-examples.override.md` | Wizard examples specific to general-edition contexts (software dev, research, writing, education) |

**Override mechanism:** Per the B4 override-file mechanism. Sections present in override REPLACE same-named sections in common-spec.

## 5. Regulatory Extensions (Optional Profile Add-Ons)

Located at `EXTENSIONS/`. Users select one or more at bootstrap (in addition to base preset) for specific regulatory regimes:

| Extension | What it adds | When to enable |
|-----------|--------------|----------------|
| `EXTENSIONS/gdpr-profile.md` | GDPR consent tracking, right-to-be-forgotten enforcement, EU jurisdiction patterns | EU-jurisdiction deployments |
| `EXTENSIONS/soc2-profile.md` | SOC2 Trust Services Criteria — access controls, audit, change management patterns | SOC2-audited organizations |
| `EXTENSIONS/pci-dss-profile.md` | PCI-DSS payment card data security patterns | Deployments handling payment card data |

Extensions compose with base preset. Example: `compliance: enterprise` + `EXTENSIONS/pci-dss-profile.md` = enterprise baseline + PCI-DSS additions.

## 6. Consumer Architecture (Modular)

By design, the consuming Claude architecture is pluggable. General-edition does NOT hardcode sub-agent names. At bootstrap (BOOTSTRAP_PROMPT.md Step 7), the consumer registers their agent topology.

**Common patterns** (illustrative; users register their actual topology):
- Solo developer + Claude Code default: just `user` + `orchestrator` (no sub-agents — use standard slots only)
- reference setup pattern: 4 sub-agents (`warden`/`sentinel`/`vault`/`clerk`)
- Custom: any topology matching `[a-z][a-z0-9-]*` pattern

**Standard slots (always available per SCHEMA_A18 v1.2):** `user`, `orchestrator`, `webfetch`, `external-tool-output`, `migration-script`.

## 7. Tier-Gated Features (Designed-In)

What activates at each deployment tier (same architecture as biotech; different defaults):

| Tier | Infrastructure | General-edition features activated |
|------|----------------|------------------------------------|
| **T0** | Any 9-root-file agent (Claude Code, OpenClaw, etc.) | All Tier A + most Tier B; audit log opt-in; quarantine non-blocking |
| **T1** | + Ollama | + B9 semantic search (opt-in) |
| **T2** | + Node.js | + B11 hybrid retrieval (v2.2 opt-in); B12 error-detector hook; **C9 Transformers.js embeddings as Ollama alternative** |
| **T3** | + Code Execution | + C4 cryptographic signatures (HMAC optional); C6 LLMLingua compression; C2 graph backend; advanced compaction |
| **T4** | + Skills + Anthropic Dreaming | + C1 Auto-Dream; C10 Skill artifacts |

**Tier confirmation at bootstrap:** the setup wizard's deployment-tier question — "Which features are available?" — auto-detects at T2+ if Node.js is available (`node --version` probe).

## 8. Brand-Protected Elements

Same canonical elements as biotech-edition (stack name, layer structure, schemas, protocols, compliance preset system, deployment-tier markers, bi-temporal model, documentation discipline). General-edition does NOT modify these.

What general-edition does ALLOW user to choose:
- Compliance preset (none / enterprise / custom)
- Audit log on/off
- Cryptographic signature scheme (HMAC default)
- Optional regulatory extensions

See `../common-specs/MODULARITY.md` for full brand-protection vs modularity distinction.

## 9. Initial Setup Requirements (BOOTSTRAP_PROMPT.md Step 7)

When deploying general-edition, the setup wizard MUST collect:

1. **Identity** — name, role, primary tech stack, domain
2. **Active projects** — high-level list with goals + status
3. **Compliance preset selection** — none / enterprise / custom (with explanations)
4. **Compliance extensions** (optional) — none / GDPR / SOC2 / PCI-DSS
5. **Pet peeves** — things to NEVER do
6. **Consumer agent topology** — sub-agent names if any (empty for no-sub-agent setup)
7. **Deployment tier** — what infrastructure is available (auto-detect when possible)

## 10. Risks + Mitigations (per the design directive)

| Risk | Mitigation |
|------|------------|
| User realizes they need HIPAA/PHI coverage later | A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md. Preset change between general-edition presets is supported at any time via PROFILE.md edit; audit-log captures preset change; backwards re-validation pass available |
| User picks `custom` without configuring anything | Bootstrap rejects bare `compliance: custom`; requires ≥1 override file present |
| Multiple regulatory contexts (e.g., EU + payment-card data) | Extensions compose — user can enable both `gdpr-profile.md` + `pci-dss-profile.md` simultaneously |
| Audit log opt-in is forgotten by user | Default ON when compliance preset is enterprise; never silent for that preset |
| Hard delete loses data accidentally | 7-day recovery window per delete_recovery_window_days; archived to `memory/archive/discarded/` before purge |
| Public-distribution candidate may inadvertently leak personal info | PRIVACY_REVIEW.md gates public release; review checklist explicit |

## 11. Cross-References

- `memory/user/USER_OVERRIDES.md` (v4.0.0+): user configuration lives here, not in this file — see §2.1
- `common-specs/templates/USER_OVERRIDES.template.md`: the template the installer creates it from
- `PROFILE.md` parent: `../common-specs/` (the universal foundation)
- `MODULARITY.md`: brand-protection vs modular distinction
- `MEMORY_PROTOCOL.md` §1.1 (edition detection loads this file)
- `SCHEMA_compliance_profile.md` §5 (preset definitions)
- `BOOTSTRAP_PROMPT.md` Step 7 (setup wizard reads this file)
- `EXTENSIONS/` (3 selectable regulatory profile add-ons: GDPR / SOC2 / PCI-DSS; the healthcare profile is biotech-edition-reserved and not selectable in general-edition)
- `overrides/` (3 override files for general-specific behavior)
- `B1/B2/B6/B7/B8` (per-edition Tier B configurations)
- `C4/C9` (HMAC signatures + Transformers.js embeddings designed-in)
- `PRIVACY_REVIEW.md` (public-release readiness)
- `DEPLOYMENT.md` (install instructions)
- `MIGRATION_v2_to_v3.md` (simpler path than biotech)

## 12. Status

**Stable.** Active for general-edition deployment when paired with common-spec.

All companion deliverables (overrides, EXTENSIONS, DEPLOYMENT, PRIVACY_REVIEW, MIGRATION, setup scripts) build on this foundation.
