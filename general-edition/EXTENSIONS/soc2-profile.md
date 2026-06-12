# EXTENSION — SOC2 Profile (for General-Edition)

> **File:** `general-edition/EXTENSIONS/soc2-profile.md`
> **Version:** 1.0 — 2026-05-15
> **Compose with:** `enterprise` base preset most commonly; can compose with others
> **Activates:** SOC2 Trust Services Criteria — access controls, change management, audit-ready patterns
> **Status:** DRAFT

---

## Purpose

SOC2-specific compliance for general-edition deployments preparing for or maintaining SOC2 Type 1 / Type 2 audits. Adds change management discipline, access control tracking, and audit-ready evidence patterns.

Common use cases:
- B2B SaaS companies pursuing SOC2 certification
- Enterprise software vendors with SOC2-required contracts
- Organizations doing internal SOC2 readiness assessments

---

## What This Extension Adds

### Behavior changes

| Aspect | Base preset | + soc2-profile EXTENSION |
|--------|-------------|--------------------------|
| Audit log | Per base (opt-in for `none`; on for `enterprise`) | **MANDATORY** on every write + every read of security-tagged entries |
| Audit log retention | Per base (90 days general default) | **MINIMUM 1 year** (SOC2 audit window) |
| Change management | N/A | All DEC entries require approver + change-reason metadata |
| Access control tracking | Per base | Log access events for entries tagged `access-controlled` |
| Cryptographic signatures | Per base | RECOMMEND active at T3 for audit chain-of-custody |
| Quarantine workflow | Per base | ADD `soc2-violation` reason_code |

### Frontmatter fields added (for entries tagged `access-controlled` or `change-managed`)

```yaml
compliance_extension: soc2
access_controlled: true | false                # whether this entry requires access tracking
change_approver: <approver-id>                  # who approved this change (for SOC2 change management)
change_reason: <free-text>                      # why this change was made
change_ticket_ref: <external-ticket-id>         # link to external change management system
audit_evidence_category: CC* | A* | C* | I* | P*  # SOC2 Trust Services Criteria reference
```

SOC2 Trust Services Criteria categories:
- CC = Common Criteria (Security)
- A = Availability
- C = Confidentiality
- I = Processing Integrity
- P = Privacy

### Change management discipline

When SOC2 extension is active:
- All DEC entries require `change_approver` field (even if it's `change_approver: <self>` for solo deployments)
- All FB entries that promote to standing rules require approval metadata
- Quarantine release decisions log full approver justification

### Audit-ready evidence patterns

The audit log becomes the primary evidence artifact for SOC2 audits. Required fields:
- Every read of security entry: `action: read`, `read_context: <reason>`, `actor: <agent>`, `actor_session: <N>`
- Every write: `content_sha256_before` + `content_sha256_after` (for integrity)
- Every preset change: explicit log entry with `action: preset-change`, `from_preset: <X>`, `to_preset: <Y>`, `change_approver: <id>`

## Activation

```bash
# At bootstrap:
setup.sh --compliance=enterprise --extensions=soc2

# Or via PROFILE.md edit:
compliance: enterprise
extensions:
  - soc2
```

## Composition with Other Extensions

| Composition | Common scenario |
|-------------|------------------|
| `enterprise` + `soc2` | Most common — SOC2-audited B2B SaaS |
| `enterprise` + `soc2` + `gdpr` | SOC2 + EU jurisdiction |
| `enterprise` + `soc2` + `healthcare` | HIPAA-aware SOC2 (healthcare-adjacent SaaS) |
| `enterprise` + `soc2` + `pci-dss` | SOC2 + payment card handling |

## Standing Rules (Universal Floor + SOC2-Specific)

- Universal: no secrets, no credit cards, no SSN format
- SOC2-specific: `access_controlled` entries cannot be read without audit log entry; refuse silent reads

## Risks + Mitigations

| Risk | Mitigation |
|------|------------|
| User forgets to set `change_approver` on solo deployment | Setup wizard offers `<self>` as default approver for solo contexts; auditable as self-approved |
| Audit log retention exceeds local disk capacity | Rotation policy per SCHEMA_audit_log.md §7; compress + archive monthly |
| Audit chain-of-custody breaks if signatures inactive | Layer 6 (C4) signatures recommended at T3+; without, audit log integrity is filesystem-only |
| SOC2 auditor requests evidence query | Audit log structure supports `jq` queries; auditor receives structured exports |

## SOC2 Audit Preparation

Recommended workflow:
1. Activate `enterprise` + `soc2` from start of audit window
2. Tag all relevant entries with `audit_evidence_category` (CC for security; A for availability; etc.)
3. Maintain change_approver discipline (even for solo deployments)
4. Generate evidence reports via setup script: `setup.sh --soc2-evidence --date-range=YYYY-MM-DD..YYYY-MM-DD`
5. Provide structured audit log dump to external auditor

## Cross-References

- `../../common-specs/SCHEMA_audit_log.md` (audit log structure)
- `../../common-specs/SCHEMA_compliance_profile.md` §5.3 (enterprise preset)
- `../../common-specs/MEMORY_PROTOCOL.md` §5.2 (audit log writes)
- B1 audit log design
- AICPA SOC2 Trust Services Criteria (TSC)
