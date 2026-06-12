---
name: audit-quarantine
description: Interactive review workflow for quarantined memory entries. Lists entries quarantined per MEMORY_PROTOCOL §5.3 validation-on-read failures, presents each for review (approve/reject/defer), batch-processes user decisions, and logs all actions to audit_log.jsonl. Use when the user asks to review quarantine, audit memory hygiene, or process quarantined entries.
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["ideal-first design", "documentation discipline", "quarantine UX (biotech workflow vs general toast)", "Tier C designed-in framework", "Option C extension"]
target_edition: any (biotech + general both supported with different UX defaults)
tier: A (core deliverable — required for memory hygiene completeness)
license: Apache-2.0
edition_behavior:
  biotech: full review workflow with batch ops; entries cannot be released without explicit user approval (per B2 quarantine UX)
  general: same review workflow OR toast-only notification at session start (user preference)
references_protocol: MEMORY_PROTOCOL §5.3 (Quarantine Routing) — implements the review side of §5.3 workflow
---

# Audit Quarantine — Skill Workflow

When this Skill is invoked (typically via `/audit-quarantine` slash command or when the user asks to review quarantined entries), execute the workflow below **IN ORDER**.

This Skill implements the **review side** of MEMORY_PROTOCOL §5.3 Quarantine Routing — §5.3 captures HOW entries enter quarantine; this Skill is HOW they exit.

---

## Step 0 — Confirm Invocation Intent

```
👋 Audit Quarantine review workflow.

This will:
  - List all entries currently in memory/quarantine/
  - Present each for your review (approve to release / reject to delete / defer)
  - Log all actions to memory/security/audit_log.jsonl
  - Update memory/quarantine/quarantine_log.jsonl with resolution outcomes

Quarantine entries arrive here per MEMORY_PROTOCOL §5.3:
  - Validation-on-read failures (per §4.1)
  - Signature verification failures (Tier C C4)
  - PHI detection in non-biotech entries (per §17)
  - Lint HIGH/CRITICAL findings (per §10.5 Option C checks)

Continue? [Y/n]:
```

If user says no, stop gracefully.

---

## Step 1 — Load Quarantined Entries

```bash
# Find all quarantined entries
find <working-dir>/memory/quarantine -name "*.md" -type f
```

For each found entry:
1. Read the file
2. Parse SCHEMA_A18 frontmatter — specifically:
   - `id` (entry identifier)
   - `created_at` / `last_updated`
   - `source_agent`
   - `quarantine_reason` (added when entry was routed to quarantine)
   - `quarantine_ts` (when routed)
   - Original category (parent directory hierarchy: `quarantine/<category>/<entry-id>.md`)
3. Display summary line: `<entry-id> · <category> · <quarantine_reason> · <age-in-days>`

Save the list as `QUARANTINED_ENTRIES` for subsequent steps.

---

## Step 2 — Read Quarantine Log for Provenance

```bash
# Read quarantine_log.jsonl for each entry's routing history
cat <working-dir>/memory/quarantine/quarantine_log.jsonl
```

For each entry in `QUARANTINED_ENTRIES`, find matching log lines (by `entry_id`). This provides the FULL routing history — why the entry was quarantined, what validation failed, when, and by which agent.

Surface this context to the user during review (Step 3) so they have full provenance before deciding.

---

## Step 3 — Interactive Review

For each entry in `QUARANTINED_ENTRIES`:

```
─────────────────────────────────────────────────────────────
ENTRY: <entry-id>
Category: <original category>
Quarantined: <date> (N days ago)
Reason: <quarantine_reason>
Routing agent: <source_agent>

ENTRY CONTENT:
<first 500 chars or full content if shorter>
...

QUARANTINE LOG CONTEXT:
<matching jsonl lines from quarantine_log.jsonl>

Action?
  (a) APPROVE — release back to original category; clear quarantine status
  (b) REJECT — delete the entry; preserve quarantine_log.jsonl record
  (c) DEFER — leave in quarantine; revisit later
  (d) DETAIL — show full entry content (if truncated above)
  (e) SKIP TO END — process remaining entries with one decision

Choice: 
```

Save user decision as `<entry-id>: action` for batch processing.

---

## Step 4 — Apply Approval Decisions

For each entry marked APPROVE:

```bash
# Move file back to original category
ORIGINAL_CATEGORY=$(parse frontmatter for original category — typically derived from quarantine subdirectory)
mv <working-dir>/memory/quarantine/<category>/<entry-id>.md <working-dir>/memory/<original-category>/<entry-id>.md

# Update frontmatter: status quarantined → active
# Update content_sha256 (since file content changed location/metadata)
# Write updated entry back
```

Per MEMORY_PROTOCOL §5.4 bi-temporal supersession — APPROVED entries get:
- `status: active` (was `quarantined`)
- `last_updated: <today>` (preserves history)
- `quarantine_reason:` field stays as audit trail
- `quarantine_resolved_at: <today>`
- `quarantine_resolution: approved-after-review`

---

## Step 5 — Apply Rejection Decisions

For each entry marked REJECT:

```bash
# Delete the entry file
rm <working-dir>/memory/quarantine/<category>/<entry-id>.md
```

The deletion is captured in:
- `quarantine_log.jsonl` (new line: `{"action":"reject","entry_id":"...","resolution_ts":"..."}`)
- `audit_log.jsonl` (new line: `{"action":"delete","entry_id":"...","reason":"user-rejected-quarantine"}`)

Per the ideal-first design and documentation discipline principles: rejected entries leave a provenance trail in both logs. The file is gone but the audit chain knows it existed.

---

## Step 6 — Update Quarantine Log

For each decision (APPROVE / REJECT / DEFER), append a new line to `memory/quarantine/quarantine_log.jsonl`:

```jsonl
{"ts":"<UTC>","actor":"orchestrator","session":<N>,"action":"<approve|reject|defer>","entry_id":"<id>","entry_category":"<category>","resolution":"<resolution-reason>","prior_quarantine_reason":"<original-reason>"}
```

Format follows the canonical JSONL format: compact JSON, second-precision timestamp, `entry_id` sentinels.

---

## Step 7 — Update Audit Log

For each decision, also append to `memory/security/audit_log.jsonl`:

```jsonl
{"ts":"<UTC>","actor":"orchestrator","session":<N>,"action":"audit-quarantine-review","entry_id":"<id>","outcome":"<approve|reject|defer>","decision_basis":"<user-supplied or inferred reason>"}
```

This provides ONE central audit view spanning all memory hygiene actions, not just quarantine-specific.

---

## Step 8 — Summary Report

After all entries processed:

```
═════════════════════════════════════════════════════
✅ Audit Quarantine Review Complete
═════════════════════════════════════════════════════

Total entries reviewed: <N>
  ✓ Approved:    <count>  (released back to original categories)
  ✗ Rejected:    <count>  (deleted; provenance preserved in logs)
  ⏸ Deferred:    <count>  (remain in quarantine)
  ⏭ Skipped:     <count>  (if user chose SKIP TO END mid-review)

Logs updated:
  - memory/quarantine/quarantine_log.jsonl: +<N> lines
  - memory/security/audit_log.jsonl:        +<N> lines

Next steps:
  1. Run `/lint-memory` to verify no NEW quarantine candidates surfaced after this review
  2. If deferred entries remain, schedule a follow-up review (typically within 30 days)
  3. Consider promoting recurring quarantine patterns to standing rules (Option C Lint Check 11)
```

---

## Step 9 — Optional: Promote Patterns to Standing Rules

If multiple quarantined entries share a common `quarantine_reason`:

```
ℹ️ I noticed N entries were quarantined for: "<recurring reason>"

This may indicate a pattern worth promoting to a standing rule.

Promote to standing rule?
  (a) Yes — draft a DEC entry with the recurring pattern
  (b) Not yet — let me see more recurrences first
  (c) No — these are one-off occurrences
```

If yes, draft a DEC-### entry with full documentation discipline (all 5 elements) and present to user for review.

---

## Edition-Specific Behavior (Per B2 Quarantine UX)

### Biotech edition (compliance: healthcare)
- Full review workflow REQUIRED (cannot skip)
- Each entry MUST receive explicit decision (no DEFER without comment)
- DEFER requires user-supplied reason (audit trail completeness)
- Approved entries trigger PHI re-scan before release

### General edition (compliance: none / enterprise)
- Same workflow available
- AT SESSION START: optional toast notification "X entries quarantined since last session — review?"
- User can choose: review now (full workflow) or defer (toast persists next session)
- DEFER allowed without comment

---

## Compliance Cross-References

| Step | Action | Decision authority |
|---|---|---|
| 0 | Intent confirmation | documentation discipline |
| 1 | Load quarantined entries | MEMORY_PROTOCOL §5.3 |
| 2 | Read quarantine log | auditability principle |
| 3 | Interactive review | B2 (workflow UX) |
| 4 | Apply approvals | MEMORY_PROTOCOL §5.4 (bi-temporal supersession) |
| 5 | Apply rejections | preserve provenance even on delete |
| 6 | Update quarantine_log | canonical JSONL format |
| 7 | Update audit_log | auditability principle + B1 |
| 8 | Summary report | validate before declaring done |
| 9 | Promote patterns (optional) | Option C Lint Check 11 |

---

## What This Skill CANNOT Do

- **Cannot quarantine new entries** — that's MEMORY_PROTOCOL §5.3 (write-side); this Skill is review-side only
- **Cannot validate entry safety after approval** — user judgment is required; Sentinel re-vetting is a separate manual step if user wants additional verification
- **Cannot auto-resolve conflicts** — every approval/rejection is an explicit user decision per the surface-only philosophy shared with Lint
- **Cannot rotate audit_log.jsonl** — that's per MEMORY_PROTOCOL §11 file size limits; this Skill only APPENDS
- **Cannot operate without memory/quarantine/ existing** — Step 1 enforces precondition
- **Cannot recover deleted entries** — REJECT is permanent; quarantine_log.jsonl preserves the FACT of the entry's existence but NOT its content (by design per privacy)
- **Cannot batch-approve without user review** — even SKIP-TO-END requires one explicit "skip = defer all remaining" decision
