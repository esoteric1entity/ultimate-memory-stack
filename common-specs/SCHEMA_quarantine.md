# Schema — Quarantine Workflow (B2)

> **File:** `common-specs/SCHEMA_quarantine.md`
> **Version:** 1.0 — stable
> **Status:** stable — cross-validated against MEMORY_PROTOCOL.md §4 + EXTENDED §E3.3
> **Authors:** see /AUTHORS.md


---

## 1. Purpose

When a memory entry fails validation (frontmatter integrity, signature verification, PHI detection, content_sha256 mismatch, manual flag), the system needs a place to **isolate it without losing forensic evidence**, surface it to the user, and route the disposition (release or discard) through an explicit approval workflow.

The quarantine layer answers:
- *Where do bad entries go?* (`memory/quarantine/`)
- *Who decides release vs discard?* (user, with user-approval UX)
- *What history is preserved?* (full original entry + quarantine reason + audit trail)
- *Can a quarantined entry be analyzed without polluting the memory vault?* (yes — quarantine directory is isolated; orchestrator does NOT load quarantined entries into context unless explicitly requested)

This is the **load-bearing defense against memory poisoning** (the maintainer's prompt-injection incident 2026-05-12-001).

---

## 2. Rationale

### Why quarantine and not delete?

- **Forensic value:** A deleted bad entry leaves no trail. Quarantine preserves the entry, the reason it was flagged, the timestamp, and the actor that flagged it.
- **False-positive recovery:** Validation rules are heuristic. PHI detectors fire on false positives (the word "genomic" in a non-PHI context). Quarantine lets the user release entries that are actually safe.
- **Pattern learning:** Multiple quarantines on similar entries surface attack patterns or detector calibration issues. Deletion loses this signal.

### Quarantine review UX

Quarantined entries surface at session start (a one-line toast: *"X entries quarantined since last session — review?"*), and the user reviews them via the `/audit-quarantine` slash command — a review workflow with batch approve/reject. Entries CANNOT be released without explicit user approval; the friction is the point.

### Why an explicit approval workflow (no auto-release)?

- **Trust boundary:** The system that flagged an entry as suspicious cannot be the same system that decides to trust it again. User-in-the-loop is the trust anchor.
- **Audit completeness:** Release decisions are themselves audit-worthy events. They get logged with `release_approver: user`.
- **Consistency:** Release always requires explicit user approval; there is no auto-release path.

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| Memory poisoning is a real attack class | OWASP `[OWASP-ASI06]`, arXiv:2503.03704 (MINJA) | OWASP standard + peer-reviewed paper |
| Quarantine + user approval is convergent production pattern | Security/compliance survey | Multi-system pattern observation |
| Validation-on-read fires false positives on PHI detectors | Coding-agent research + clinical NLP literature | Domain knowledge |
| A real prompt-injection incident during development validated the need | internal incident record | First-hand operational event |
| Access controls for sensitive data require approval workflows | Access-control best practice | Security design principle |
| Auto-release would violate trust boundary | Defense-in-depth principle (the maintainer's OpenClaw expertise) | Security design principle |

**Caveats:**
- Quarantine UX details (`/audit-quarantine` workflow specifics) need user testing during early deployments. Drafted here as a design contract; actual UX refined operationally.
- False-positive rate of validation-on-read is unknown until the stack runs in production. Future versions may add tuning knobs.

---

## 4. Schema Definition

### Directory layout

```
memory/quarantine/
├── quarantine_log.jsonl         # Per-edition log of all quarantine events
├── <category>/                  # Subdirectory mirroring memory/<category>/
│   ├── DEC-099.md               # Quarantined entry (full original content preserved)
│   ├── FB-045.md
│   └── ...
└── README.md                    # Edition-specific quarantine-usage docs
```

The `<category>` subdirectory preserves the original entry's category (decisions, feedback, security, etc.) so release-back-to-source has an unambiguous path.

### Per-quarantine-entry file format

Each quarantined entry is a markdown file with the original entry's content PLUS a quarantine metadata header injected at the top of the frontmatter:

```markdown
---
id: DEC-099
created_at: 2026-05-13
last_updated: 2026-05-14
status: quarantined                    # Set by quarantine action
schema_version: "3.0"
confidence: TENTATIVE
# --- ORIGINAL FRONTMATTER PRESERVED BELOW ---
source_agent: webfetch
source_session: 8
source_uri: https://example.com/...
# ... rest of original frontmatter ...
# --- QUARANTINE METADATA (injected) ---
quarantined_at: 2026-05-14T10:30:45Z
quarantined_by: warden                  # Actor that triggered quarantine
quarantine_reason: signature-mismatch   # See §6 reason codes
quarantine_session: 8
quarantine_audit_entry_id: <UUID-or-ts-of-corresponding-audit-log-line>
---

[Original entry body — preserved verbatim]
```

The original body is preserved verbatim. Frontmatter is augmented with quarantine metadata but original fields are NOT modified (except `status: quarantined`).

### quarantine_log.jsonl format

A JSONL log specifically for quarantine events. Cross-referenced with the main audit log (`memory/security/audit_log.jsonl`) via shared timestamps + entry IDs. This file is a denormalized view for quarantine-focused queries.

```jsonl
{
  "ts": "2026-05-14T10:30:45Z",
  "entry_id": "DEC-099",
  "original_path": "memory/decisions/decisions.md",
  "quarantine_path": "memory/quarantine/decisions/DEC-099.md",
  "category": "decisions",
  "triggered_by": "warden",
  "trigger_session": 8,
  "reason_code": "signature-mismatch",
  "reason_details": "Frontmatter content_sha256 declared 8b1a... but body computes f3c4...",
  "validation_layer": "L2-compliance",          // Which architecture layer caught it
  "validator_id": "validate-on-read",            // Specific validator within layer
  "disposition": "pending",                       // pending | released | discarded
  "disposition_ts": null,
  "disposition_approver": null,
  "disposition_reason": null
}
```

When disposition occurs (release or discard), the original line is NOT modified (append-only); a new entry is appended:

```jsonl
{
  "ts": "2026-05-14T11:00:00Z",
  "entry_id": "DEC-099",
  "disposition": "released",
  "disposition_approver": "user",
  "disposition_reason": "false-positive — content_sha256 mismatch was due to whitespace normalization",
  "released_to": "memory/decisions/decisions.md"
}
```

This way, the quarantine_log.jsonl is itself append-only and forensically clean.

---

## 5. Workflow — Quarantine Lifecycle

### Step 1: Validation Failure Detected (per MEMORY_PROTOCOL.md §4)

A validator (frontmatter / signature / PHI / consistency) returns FAILURE for an entry on read.

### Step 2: Quarantine Routing (per MEMORY_PROTOCOL_EXTENDED.md §E3.3)

The orchestrator:
1. Reads the failed entry's body (one last time, in a sandboxed scope — DO NOT load into general context)
2. Computes the quarantine path: `memory/quarantine/<category>/<entry-id>.md`
3. Writes the entry with augmented frontmatter (per §4 above)
4. Appends to `memory/quarantine/quarantine_log.jsonl`
5. Sets the original entry's `status: quarantined` in its source file (the body and other frontmatter fields are preserved in BOTH the source file AND the quarantine copy, intentionally redundant for forensic reasons)
6. Logs the event to the main audit log per `SCHEMA_audit_log.md` §4 (action: `quarantine`)

### Step 3: User Notification

- At next session start: quarantined entries surface in the greeting, plus a one-line toast: *"3 entries quarantined since last session — review?"*
- User invokes `/audit-quarantine` slash command to enter the review workflow
- Review UI shows: entry summary, quarantine reason, original frontmatter, recommended disposition
- User selects per-entry: APPROVE-RELEASE / DISCARD / DEFER
- Batch approve/reject for multiple similar entries
- Non-blocking by default — the user can defer and work normally; the queue can optionally be configured to block new writes until it is reviewed once unreviewed entries exceed a configurable threshold

### Step 4: Disposition Execution

**On RELEASE:**
1. User explicitly approves entry for release
2. Compute content_sha256 of body; write back to original entry path (`memory/<category>/<file>.md`)
3. Set `status: active` in frontmatter; remove quarantine-injected metadata
4. Move quarantine copy to `memory/quarantine/.archive/<category>/<entry-id>_<release-ts>.md` (preserve forensic copy)
5. Append disposition to `quarantine_log.jsonl`
6. Log to main audit log (action: `release`)

**On DISCARD:**
1. User explicitly approves discard
2. Move quarantine copy to `memory/quarantine/.archive/discarded/<category>/<entry-id>_<discard-ts>.md` (preserve forensic copy)
3. Original entry: `status: discarded` (NOT deleted — preserved for audit; entry is just inert)
4. Append disposition to `quarantine_log.jsonl`
5. Log to main audit log (action: `discard`)

**On DEFER:**
- Entry remains quarantined
- Re-surfaced at next session start
- No log change (just deferred)
- A warning surfaces if an entry is deferred longer than a configurable stale-deferral threshold

---

## 6. Reason Codes (enum)

| Code | Triggers when |
|------|---------------|
| `frontmatter-invalid` | YAML parse failure, missing required fields, schema_version mismatch |
| `signature-mismatch` | Layer 6 (C4) signature verification fails (T3+ only) |
| `content_sha256-mismatch` | Frontmatter declares X, body computes Y (per SCHEMA_A18 CAS / B3) |
| `phi-detected` | PHI detector fired (PHI detection is reserved for the planned institutional edition) |
| `pii-detected` | Compliance preset `enterprise` or `custom` PII detector fired |
| `consistency-failure` | Cross-entry consistency check failed (e.g., supersedes references a non-existent entry) |
| `provenance-suspicious` | source_agent: webfetch + last_validated absent (suspicious external entry) |
| `manual` | User or agent explicitly flagged the entry for review |
| `cascade-quarantine` | An entry derived from an already-quarantined entry (propagation defense) |

---

## 7. Worked Example — A Quarantine Event End-to-End

**Setup:** WebFetch returns a markdown blob that gets ingested as a memory entry. The blob contains a hidden prompt injection that the orchestrator's validation-on-read catches.

**T+0:** Orchestrator reads entry; signature verification fails (Layer 6 active at T3+)
```jsonl
// audit_log.jsonl
{"ts":"2026-05-14T10:30:45Z","actor":"orchestrator","actor_session":8,"action":"read","entry_id":"WEB-007","entry_path":"memory/references/web_articles.md","entry_category":"references","entry_summary":"WEB-007: Article on memory architecture by ... [TRUNCATED]","outcome":"failure","failure_reason":"signature-mismatch","read_context":"tier-3-on-demand"}
```

**T+1ms:** Orchestrator triggers quarantine routing
```jsonl
// quarantine_log.jsonl (new entry)
{"ts":"2026-05-14T10:30:45.001Z","entry_id":"WEB-007","original_path":"memory/references/web_articles.md","quarantine_path":"memory/quarantine/references/WEB-007.md","category":"references","triggered_by":"orchestrator","trigger_session":8,"reason_code":"signature-mismatch","reason_details":"Ed25519 signature on entry does not verify against signer public key","validation_layer":"L6-signatures","validator_id":"ed25519-verify","disposition":"pending","disposition_ts":null,"disposition_approver":null,"disposition_reason":null}
```

**T+2ms:** Quarantined entry written to `memory/quarantine/references/WEB-007.md`; original entry's `status: quarantined` set

**T+3ms:** Audit log entry for the quarantine action
```jsonl
// audit_log.jsonl
{"ts":"2026-05-14T10:30:45.003Z","actor":"orchestrator","actor_session":8,"action":"quarantine","entry_id":"WEB-007","entry_path":"memory/references/web_articles.md","entry_category":"references","content_sha256_before":"abc123...","entry_summary":"WEB-007: Article on memory architecture by ... [TRUNCATED]","outcome":"success","quarantine_reason":"signature-mismatch","quarantine_destination":"memory/quarantine/references/WEB-007.md"}
```

**T+15min (later in session):** The user invokes `/audit-quarantine`
- Review UI shows WEB-007 with reason "signature-mismatch"
- The user reviews; entry content shows attempted prompt injection
- The user selects DISCARD

**T+15min+5sec:** Disposition logged
```jsonl
// quarantine_log.jsonl (append)
{"ts":"2026-05-14T10:45:05Z","entry_id":"WEB-007","disposition":"discarded","disposition_approver":"user","disposition_reason":"confirmed prompt injection attempt; not a false positive","discarded_to":"memory/quarantine/.archive/discarded/references/WEB-007_2026-05-14T10-45-05Z.md"}
```

**Forensic recovery later:** The user wants to know what happened to WEB-007
```bash
jq 'select(.entry_id == "WEB-007")' memory/quarantine/quarantine_log.jsonl
```

Returns both the original quarantine event AND the discard disposition. Full forensic trail intact.

---

## 8. Scope — CAN / CANNOT

### CAN
- Isolate suspicious entries without losing forensic evidence
- Surface entries to user via the `/audit-quarantine` review workflow and a session-start toast
- Track disposition decisions in append-only quarantine_log.jsonl
- Preserve original entry verbatim in quarantine directory
- Optionally block writes when the quarantine queue exceeds a configurable threshold (forcing review)
- Integrate with audit log (every quarantine action produces an audit entry)
- Support cascade quarantine (if entry X is quarantined and entry Y is derived from X, quarantine Y too)
- Provide forensic recovery via jq / grep / Python queries

### CANNOT
- Automatically classify suspicious vs benign (validation rules detect; user decides disposition)
- Auto-release entries without user approval (trust boundary; explicit approval required)
- Encrypt quarantined content (still plain markdown; Layer 6 signatures detect tampering if active)
- Replace the validation layers (this catches what they flag; doesn't catch what they miss)
- Prevent a privileged user from manually editing quarantine files (filesystem access bypasses application controls; Layer 6 detects tampering when active)
- Operate without `memory/quarantine/` directory existing (created during bootstrap or first quarantine event)

### Edition fit

- Quarantine queue is NON-BLOCKING by default (optionally configured to block once unreviewed entries exceed a threshold); `/audit-quarantine` is the canonical review path; one-line toast at session start; user can defer; cryptographic signatures optional (C4 at T3)

### Deployment tier

- **T0** base: directory structure + JSONL log + frontmatter mutation works on any filesystem
- **T2** enhanced: file-watcher detects quarantine directory growth; alerts when queue size exceeds threshold
- **T3** enhanced: signature verification (C4) provides the most reliable trigger for quarantine

---

## 9. Migration Strategy

### From v2.0 (no quarantine layer)

v2.0 had no quarantine. v3.0 introduces it at bootstrap. **No retroactive quarantine of historical entries** — the quarantine system starts fresh.

A bootstrap entry initializes the system:
- Create `memory/quarantine/` directory
- Initialize empty `quarantine_log.jsonl`
- Create per-category subdirectories on first quarantine event (lazy creation)
- Log the initialization to audit log

If a user wants to retroactively scan existing v2.0 entries for poisoning (e.g., after the 2026-05-12-001 incident), run a one-time validator across all entries; quarantine the failures normally.

---

## 10. Open Questions

1. **Queue-blocking threshold** — what queue size should trigger write-blocking when enabled? Lower forces more review (good for compliance); higher reduces interruption (better for daily flow). Defer to operational experience.
2. **Cascade quarantine depth** — if entry X is quarantined and 100 entries reference X, do they ALL get quarantined? Probably no (too aggressive). Likely: flag for re-validation rather than full quarantine. A future design decision.
3. **False-positive feedback loop** — when user RELEASES a quarantined entry as "false positive", should the validator that flagged it get the signal? E.g., adjust thresholds, learn the pattern. Probably yes but mechanism is unclear. Lean: log false-positive reason, surface to user at consolidation, manual tuning only at v3.0.
4. **Discard vs delete distinction** — discard sets `status: discarded` but preserves file. Delete would actually remove. Is `delete` ever exposed? Probably NO in v3.0 — too risky. Discard is the user-facing primitive; actual file removal is admin/CLI only.
5. **Quarantine of audit log entries themselves** — what if the audit log is tampered? Layer 6 signatures (C4) would catch it. But the entries are append-only JSONL, not memory entries with full frontmatter. Different schema, different quarantine path? Likely: log-tampering events route to a dedicated `memory/security/incidents/` directory rather than quarantine. Deferred to a later schema revision.

---

## 11. Cross-References

- **Design basis:** quarantine included by default (B2); memory-poisoning defenses (B8)
- **Protocol integration:** `MEMORY_PROTOCOL.md` §4 (validation-on-read triggers), EXTENDED §E3.3 (quarantine routing)
- **Audit log integration:** `SCHEMA_audit_log.md` (every quarantine event produces an audit log entry; action codes `quarantine` / `release` / `discard`)
- **Compliance integration:** `SCHEMA_compliance_profile.md` §detection-patterns (compliance preset determines what triggers quarantine)
- **Cryptographic integration:** C4 signatures (signature failure is a primary quarantine trigger at T3+)
- **Edition profiles:** `<edition>/PROFILE.md` (selects quarantine UX/behavior)
- **Source research:** memory-poisoning defense research, validation-on-read pattern research
