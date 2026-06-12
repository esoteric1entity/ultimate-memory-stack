# Audit Quarantine Skill — Core Deliverable

> **Status:** ✅ v3.5 Ultimate ready (Skill artifact planned for v3.1, shipped in v3.5)
> **Tier:** A (CORE deliverable — required for memory hygiene completeness; not opt-in)
> **Edition:** any (biotech + general both supported; different UX defaults per edition, B2)
> **Last updated:** 2026-05-28

---

## What This Skill Does

The Audit Quarantine Skill is the **review side** of MEMORY_PROTOCOL §5.3 Quarantine Routing. While §5.3 captures HOW entries enter quarantine (validation-on-read failures, signature failures, PHI detection, Lint HIGH/CRITICAL findings), this Skill is HOW they exit.

**Origin story:**
- An earlier release cycle identified the gap: "/audit-quarantine Skill not yet packaged"
- The behavioral protocol was captured in MEMORY_PROTOCOL §5.3, with a Skill artifact planned for v3.1
- This Skill closes that gap
- Shipped here as the v3.5 closeout deliverable

**What's included:**

```
core/audit-quarantine-skill/
├── SKILL.md                           # 9-step Claude-executable workflow
├── README.md                          # This file
├── INSTALL_AUDIT_QUARANTINE_SKILL.md   # Manual fallback guide
└── scripts/
    └── review_quarantined.py          # Standalone Python entry point (non-Skill use)
```

---

## How It Works

### High-level workflow (per SKILL.md)

1. **Confirm intent** — clarify what review will entail
2. **Load quarantined entries** — scan `memory/quarantine/`
3. **Read quarantine log** — get full routing provenance from `quarantine_log.jsonl`
4. **Interactive review** — present each entry; user decides approve/reject/defer
5. **Apply approval decisions** — move entries back to original categories
6. **Apply rejection decisions** — delete files; preserve provenance in logs
7. **Update quarantine log** — append resolution actions
8. **Update audit log** — single source of truth across all memory hygiene
9. **Summary report** + optional pattern promotion

### Decision matrix per entry

| User decision | File action | Frontmatter change | Logs updated |
|---|---|---|---|
| **APPROVE** | Move back to original category | `status: quarantined → active`, `quarantine_resolved_at: <today>`, `quarantine_resolution: approved-after-review` | quarantine_log + audit_log |
| **REJECT** | Delete the file | — (file gone) | quarantine_log (resolution: rejected) + audit_log (action: delete) |
| **DEFER** | Leave in quarantine | — (no change) | quarantine_log (resolution: deferred, with optional reason) |

---

## Edition-Specific UX (B2)

### Biotech edition (`compliance: healthcare`)
- Full review workflow REQUIRED
- Each entry MUST receive explicit decision (no silent skips)
- DEFER requires user-supplied reason (audit trail completeness)
- Approved entries trigger PHI re-scan before release

### General edition (`compliance: none` or `enterprise`)
- Same workflow available
- AT SESSION START: optional toast — "X entries quarantined since last session — review?"
- DEFER allowed without comment
- Lower friction default

---

## Documentation Discipline

### Purpose

Provide the **review side** of MEMORY_PROTOCOL §5.3 Quarantine Routing. When entries are quarantined (write-time), they need a deterministic path back to active status (or to permanent deletion). This Skill is that path.

### Rationale

- The Skill artifact was planned in an earlier cycle and deliberately deferred to keep that release clean; it ships now.
- **Per the B2 quarantine UX design:** biotech-edition needs full workflow per HIPAA forensic completeness; general-edition needs lighter toast UX. One Skill, two presets.
- **Per MEMORY_PROTOCOL §5.3:** "Biotech edition UX: Surface quarantine via `/audit-quarantine` slash command — review workflow with batch approve/reject. Entries cannot be released without explicit user approval." — this is the concrete implementation.
- **Per the ideal-first design principle:** decision matrix is clean (3 actions × 2 editions = 6 cells documented); no hidden behaviors.
- **Per the surface-only Lint extension (Option C):** Step 9 surfaces patterns for promotion to standing rules.

### Sound reasoning

1. **Per the security-first standing rule:** auditability is required; this Skill writes to BOTH quarantine_log + audit_log for cross-referenced traceability
2. **Per the ideal-first design principle:** the 9-step workflow has one happy path; edge cases (recurring patterns, batch operations) are surfaced as optional steps, not branches
3. **Per the documentation discipline standing rule:** SKILL.md + this README + INSTALL_AUDIT_QUARANTINE_SKILL.md carry all 5 required elements
4. **Per the B2 quarantine UX design:** edition-aware UX without code duplication — one workflow, edition-aware defaults
5. **Per the Lint surface-only principle:** the Skill's optional Step 9 (pattern promotion) presents suggestions; never auto-promotes
6. **Per the v3.1 plan:** delivers the planned Skill artifact at the documented scope
7. Ships in the core batch

### Scope — CAN

- List quarantined entries with full provenance
- Present each entry interactively (or batch-mode)
- Apply user decisions: APPROVE / REJECT / DEFER
- Move APPROVED entries back to original category
- DELETE REJECTED entries (file gone)
- Preserve provenance in quarantine_log + audit_log
- Surface recurring patterns for optional promotion to standing rules
- Operate edition-aware (biotech full workflow vs general toast option)
- Work both as a Skill (via `/audit-quarantine`) and as a Python script (`scripts/review_quarantined.py`)

### Scope — CANNOT

- Quarantine new entries (write-side; that's MEMORY_PROTOCOL §5.3)
- Validate post-approval safety (user judgment + optional re-vet, not in scope)
- Auto-resolve conflicts (every decision is explicit by design)
- Rotate audit_log.jsonl (MEMORY_PROTOCOL §11 handles)
- Operate without `memory/quarantine/` existing (precondition)
- Recover REJECTED entries — deletion is permanent (quarantine_log keeps the FACT, not the content)
- Bypass biotech-edition requirements (DEFER without reason is BLOCKED in biotech)
- Replace MEMORY_PROTOCOL §3 conflict resolution hierarchy

---

## Installation

### Recommended: via Skill (no install needed)

The Skill ships ready-to-invoke as `/audit-quarantine`. No installation required beyond the v3.5 base stack.

### Standalone Python script

For non-Skill use, the `scripts/review_quarantined.py` provides an equivalent CLI:

```bash
python scripts/review_quarantined.py <working-dir> [--edition biotech|general] [--mode interactive|batch]
```

See `INSTALL_AUDIT_QUARANTINE_SKILL.md` for manual usage.

---

## Cross-References

- Security-first principle (auditability requirement)
- Plan-first principle (this Skill executes the v3.1 plan)
- Ideal-first design principle
- Documentation discipline standing rule
- B2 quarantine UX (biotech workflow vs general toast)
- Tier C designed-in framework
- Karpathy Lint surface-only principle
- v3.5 release trajectory
- MEMORY_PROTOCOL §5.3 (Quarantine Routing — write-side; this Skill is read-side)
- MEMORY_PROTOCOL §5.4 (bi-temporal supersession on resolution)
- MEMORY_PROTOCOL §11 (audit_log rotation policy)
- MEMORY_PROTOCOL §17 (healthcare compliance — PHI re-scan on biotech approval)
- SCHEMA_A18 (entry frontmatter)
- `audit_log.jsonl` canonical format
- `quarantine_log.jsonl` schema (companion to this Skill)
