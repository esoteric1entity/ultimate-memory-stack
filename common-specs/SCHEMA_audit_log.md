# Schema — Audit Log (B1, JSONL Format)

> **File:** `common-specs/SCHEMA_audit_log.md`
> **Version:** 1.0 — stable
> **Status:** stable — cross-validated against MEMORY_PROTOCOL.md §5.2
> **Authors:** see /AUTHORS.md


---

## 1. Purpose

Provide a **tamper-evident, append-only audit trail** of all memory read/write operations across the Ultimate Memory Stack. The audit log answers:

- *Who* modified entry X? (`actor` field)
- *When* did they modify it? (`ts` field)
- *What* did the entry look like before/after? (`content_sha256_before` / `content_sha256_after`)
- *Why* was it modified? (action_type + `reason` field — optional)
- *Was the operation successful?* (`outcome` field)

This is the load-bearing forensic capability for biotech-edition HIPAA §164.312(b) compliance (audit controls) and for general-edition post-incident investigation.

---

## 2. Rationale

### Why JSONL specifically?

| Option | Pros | Cons |
|--------|------|------|
| **JSONL append-only** (chosen) | Grep-friendly. No DB driver needed at T0. Crash-safe (append-only). Each line is a complete record (no multi-line parsing). Streamable. | Slightly larger than binary. No native query language (must use jq / grep / Python). |
| SQLite | Indexable, query-able with SQL | Requires driver (T2+). Locking issues with concurrent writers. Binary format — not git-diffable. |
| CSV | Spreadsheet-friendly | Quote escaping is painful. Schema drift across rows. No nested fields. |
| YAML or markdown table | Human-readable | Slow to parse at scale. Multi-line records break grep. |
| Binary log (Protocol Buffers, etc.) | Compact | Opaque without tooling. Corruption risk if write interrupted. |

**Decision:** JSONL. Append-only is the critical property — once a line is written, it never gets rewritten. Corruption from interrupted writes is limited to the last line.

### Why append-only?

- **Integrity:** A modify-able audit log isn't an audit log. If actor X can rewrite history, the trail is useless.
- **Crash safety:** Append-only writes survive partial-write failures gracefully (the partial last line gets discarded on next parse).
- **Concurrent safety:** Append operations are atomic at the filesystem level for files <PIPE_BUF (typically 4 KiB) on POSIX systems. Each log entry is well under that limit.

### Why log summaries, not full content?

Per the B1 design decision: log size manageability + PHI safety.

- **Size:** A 10K-entry memory with full-body logs becomes unwieldy fast. Summaries (first 200 chars) keep the log practical for years.
- **PHI safety:** Even if Layer 2 (compliance) detects PHI in an entry and redacts the body, logging the full body would re-leak it into the audit trail. Summaries (200 chars max) limit this risk.
- **Cryptographic integrity:** Layer 6 signatures (C4 at T3) sign the audit log entries themselves — chain-of-custody at the log level, not entry level.

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| HIPAA §164.312(b) requires audit controls | HHS regulatory text | Federal regulation |
| Audit log is convergent production pattern | Letta + Copilot + security survey | Multi-vendor convergence |
| Append-only JSONL is crash-safe | POSIX `O_APPEND` semantics + atomic writes for entries < PIPE_BUF | Operating system primitive |
| Summary logging avoids PHI re-leakage | Security survey + a real prompt-injection incident during development | Vulnerability research + incident data |
| Letta and 5 production memory systems log audit-style | Letta audit pattern + security survey | Industry pattern |
| Cryptographic chain-of-custody via Layer 6 (C4) | C4 architecture spec | Architectural choice |

**Caveats:**
- JSONL append-atomicity guarantee is platform-specific (POSIX vs Windows). Windows NTFS may have weaker guarantees for concurrent appenders; on the maintainer's workstation (single-writer typical), this is not a concern. Multi-writer deployments need to verify atomic-append support on their platform.
- Summary length (200 chars) is a heuristic. Future versions may refine it based on practical PHI-leak audits.

---

## 4. Schema Definition

### Common core fields (every JSONL entry)

```jsonl
{
  "ts": "2026-05-14T15:30:00Z",
  "actor": "orchestrator",
  "actor_session": 7,
  "action": "write",
  "entry_id": "DEC-024",
  "entry_path": "memory/decisions/decisions.md",
  "entry_category": "decisions",
  "content_sha256_before": "8b1a9...",
  "content_sha256_after": "f3c4e...",
  "entry_summary": "DEC-024: Tier A — 20 features approved as definite includes for...",
  "outcome": "success"
}
```

(In actual JSONL form, this is a single line with no whitespace between fields.)

### Field definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `ts` | ISO 8601 timestamp (UTC, Zulu) | YES | When the action occurred. UTC for log timezone neutrality. |
| `actor` | enum | YES | `orchestrator` / `warden` / `sentinel` / `vault` / `clerk` / `user` / `webfetch` / `external-tool-output` / `migration-script` / `system` |
| `actor_session` | integer | YES | Session number from session_state.md |
| `action` | enum | YES | `read` / `write` / `create` / `delete` / `quarantine` / `release` / `migrate` / `validate` |
| `entry_id` | string | YES | The memory entry's ID (DEC-NNN, FB-NNN, VET-NNN, etc.) or `<file-only>` if file-level action |
| `entry_path` | string | YES | Relative path from memory/ root |
| `entry_category` | enum | YES | `sessions` / `decisions` / `feedback` / `projects` / `security` / `references` / `user` / `archive` / `quarantine` |
| `content_sha256_before` | hex string | If `action ∈ {write, delete, quarantine}` | Hash of entry body BEFORE this action |
| `content_sha256_after` | hex string | If `action ∈ {write, create, release, migrate}` | Hash of entry body AFTER this action |
| `entry_summary` | string (max 200 chars) | YES | First 200 characters of entry body, redacted per compliance profile |
| `outcome` | enum | YES | `success` / `failure` / `partial` / `blocked` |
| `failure_reason` | string | If `outcome ∈ {failure, partial, blocked}` | Short reason code; not free-form prose |
| `reason` | string (optional) | NO | Optional human-readable reason for the action (e.g., "supersession of DEC-001"); free-form |
| `client_signature` | base64 (optional) | NO | If Layer 6 (C4) active at T3+, Ed25519/HMAC signature of this log entry's content |

### Action-specific fields

For `action: read`:
```jsonl
{
  ...common fields...,
  "read_context": "tier-2-load" | "validation" | "user-query" | "agent-spawn"
}
```

For `action: quarantine`:
```jsonl
{
  ...common fields...,
  "quarantine_reason": "validation-failed" | "signature-mismatch" | "phi-detected" | "manual",
  "quarantine_destination": "memory/quarantine/<category>/<entry-id>.md"
}
```

For `action: release` (from quarantine):
```jsonl
{
  ...common fields...,
  "release_approver": "user" | "warden",  // who approved
  "release_destination": "memory/<category>/<file>.md"  // where it's going
}
```

For `action: migrate`:
```jsonl
{
  ...common fields...,
  "migration_from_version": "2.0",
  "migration_to_version": "3.0",
  "migration_script": "MIGRATION_v2_to_v3.md"
}
```

### Canonical formatting requirements (locked)

All audit_log.jsonl writes — across Bash `setup.sh`, Python `setup.py`, runtime orchestrator writes, and agent-spawned writes — MUST conform to:

| Field | Canonical format | Rationale |
|---|---|---|
| **`ts`** | ISO 8601 UTC with `Z` suffix, **second-precision only** (no microseconds). Example: `"2026-05-26T17:40:34Z"` | Sub-second precision is unneeded for HIPAA forensics; eliminates Bash/Python timestamp drift |
| **`entry_id` sentinels** | `<bootstrap>` for install/init events · `<system>` for other system events (non-entry-related) · `<file-only>` for file-level actions · actual entry IDs (e.g., `DEC-024`, `FB-007`) for entry-related events | Per-action semantic clarity; matches Bash canonical |
| **JSON line format** | **Compact** — no whitespace between key-value pairs. Python: `json.dumps(entry, separators=(",", ":"))`. Bash: emit as compact literal. | Grep-friendly; consistent across automation scripts; reduces storage |
| **Line terminator** | Single `\n` (LF). No CRLF even on Windows. | POSIX-compatible; matches existing convention |

**Reference implementation:** Bash `setup.sh` (both editions) is the canonical reference. Python `setup.py` aligns via the 3-knob fix: (a) `entry_id` parameter on `log_audit_event`, (b) `datetime.now(timezone.utc).replace(microsecond=0)` for ts, (c) `json.dumps(entry, separators=(",", ":"))` for the emit.

**Why second-precision (not microsecond):** HIPAA §164.312(b) requires audit controls but does not mandate sub-second granularity. Single-machine writes from the reference deployments will not produce >1 entry per second except in extreme circumstances; if needed, an order-tiebreak via line position or a future `seq` field can be added without breaking existing logs.

**Validation:** Cross-script drift was observed during validation — a Bash writer and a Python writer disagreed on sentinel, spacing, and timestamp precision. The canonical format above resolves it; all writers MUST conform.

---

## 5. Worked Example (Full Session Audit Trail)

A short session of writes producing audit lines:

```jsonl
{"ts":"2026-05-14T10:00:01Z","actor":"orchestrator","actor_session":8,"action":"read","entry_id":"session_state","entry_path":"memory/sessions/session_state.md","entry_category":"sessions","entry_summary":"Session 7 — Continued (Post-Compaction)...","outcome":"success","read_context":"tier-1-load"}
{"ts":"2026-05-14T10:15:30Z","actor":"orchestrator","actor_session":8,"action":"write","entry_id":"DEC-024","entry_path":"memory/decisions/decisions.md","entry_category":"decisions","content_sha256_before":"a1b2c3d4...","content_sha256_after":"e5f6g7h8...","entry_summary":"DEC-024: Tier A — 20 features approved as definite includes...","outcome":"success","reason":"heartbeat-update"}
{"ts":"2026-05-14T10:30:45Z","actor":"warden","actor_session":8,"action":"quarantine","entry_id":"DEC-099","entry_path":"memory/decisions/decisions.md","entry_category":"decisions","content_sha256_before":"x9y8z7w6...","entry_summary":"DEC-099: Suspicious entry detected — content_sha256 mismatch vs signature...","outcome":"success","quarantine_reason":"signature-mismatch","quarantine_destination":"memory/quarantine/decisions/DEC-099.md"}
{"ts":"2026-05-14T11:00:00Z","actor":"user","actor_session":8,"action":"release","entry_id":"DEC-098","entry_path":"memory/quarantine/decisions/DEC-098.md","entry_category":"quarantine","content_sha256_after":"k1l2m3n4...","entry_summary":"DEC-098: Tier C — false positive on PHI detector for the word 'genomic'...","outcome":"success","release_approver":"user","release_destination":"memory/decisions/decisions.md","reason":"manual-review-cleared"}
```

A forensic query (using `jq`) — "show all quarantine events in May 2026":
```bash
jq 'select(.action == "quarantine" and (.ts | startswith("2026-05")))' audit_log.jsonl
```

---

## 6. Scope — CAN / CANNOT

### CAN
- Provide tamper-evident, append-only audit trail
- Support forensic queries via grep/jq/Python (no DB required)
- Track provenance (`actor`, `actor_session`) for every memory operation
- Enable HIPAA §164.312(b) audit controls compliance for biotech edition
- Enable post-incident investigation across the memory stack
- Support cryptographic chain-of-custody when Layer 6 (C4) active at T3+
- Rotate by date (`audit_log_2026-05.jsonl`, `audit_log_2026-06.jsonl`, ...) at 50,000-line threshold
- Survive concurrent writes (POSIX atomic appends for entries <4 KiB)
- Co-exist with all editions and compliance presets

### CANNOT
- Log full entry content (only summaries — max 200 chars)
- Provide a query language (you use jq / grep / Python)
- Encrypt log content (Layer 6 signs but does not encrypt)
- Replace OS-level audit logging (e.g., Windows Event Log, Linux auditd) — those operate at the system level; this is application-level
- Prevent log tampering by a privileged user (filesystem-level access can still corrupt; use Layer 6 signatures for tamper evidence)
- Provide real-time alerting (consume the log with a downstream tool for that)

### Edition fit

- **Biotech-edition:** REQUIRED on every write. Read events also logged (for forensic completeness). Cryptographic signing (C4 at T3+) strongly recommended. Retention: minimum 1 year for HIPAA forensic requirements.
- **General-edition:** OPT-IN; default OFF. User enables via `audit_log: true` in compliance profile. Cryptographic signing optional. Retention: configurable, default 90 days.

### Deployment tier

- **T0** base: JSONL append-only works on any filesystem
- **T2** enhanced: file-watcher daemon for real-time anomaly detection
- **T3** enhanced: cryptographic signing of log entries (Layer 6 / C4)
- **T3** enhanced: Code-executed audit-log compaction (a natural future enhancement)

---

## 7. File Organization + Rotation

### Active log location
`memory/security/audit_log.jsonl` — current month's log; append-only

### Rotation
At 50,000 lines (or end-of-month, whichever first):
- Rename to `memory/security/audit_log_<YYYY-MM>.jsonl`
- Compress to `memory/security/audit_log_<YYYY-MM>.jsonl.gz` after 3 months
- Move to `memory/archive/audit_log_<YYYY-MM>.jsonl.gz` after 1 year (biotech: indefinite retention; general: configurable)

### Multi-month forensic queries
```bash
# All quarantine events across all months
zgrep '"action":"quarantine"' memory/security/audit_log_*.jsonl.gz | jq .
```

---

## 8. Migration Strategy

### From v2.0 (no audit log)

v2.0 had no audit log. v3.0 introduces it. **No migration of historical data is possible** — the audit trail starts fresh at v3.0 bootstrap.

A one-time migration entry is logged at bootstrap:
```jsonl
{"ts":"2026-MM-DDTHH:MM:SSZ","actor":"migration-script","actor_session":0,"action":"migrate","entry_id":"<file-only>","entry_path":"memory/","entry_category":"system","entry_summary":"v2.0 → v3.0 migration — audit log starts fresh; no historical data carried over","outcome":"success","migration_from_version":"2.0","migration_to_version":"3.0","migration_script":"MIGRATION_v2_to_v3.md"}
```

This sets the "audit trail begins here" anchor for forensic investigations.

---

## 9. Open Questions

1. **Read logging granularity** — biotech logs every read; general defaults off. But: should "Tier 1 auto-load" reads be logged separately from "user-query" reads? Currently distinguished via `read_context` field, but the granularity could be finer (e.g., file-load vs entry-by-entry-read). Defer to operational experience.
2. **Compaction strategy for the log itself** — at scale, even compressed JSONL grows. Should there be periodic summarization? E.g., monthly summary entries that compress 50K lines to 1 summary line? Probably yes for general edition; probably NO for biotech (lose forensic detail). Defer to a future schema revision.
3. **Signature scheme integration timing** — C4 (cryptographic signatures) activates at T3. Until T3, log entries are unsigned. Does the **first signed log entry** include a hash of all prior unsigned entries (to chain integrity)? Probably yes for biotech. To be documented in a future revision.
4. **Anomaly detection** — should the audit log have a companion daemon that watches for unusual patterns (e.g., 100 reads/min, multiple quarantine events, unsigned entries when signing is required)? Designed-in but probably activates at T2+ (Node.js file-watcher). Cross-ref future work.
5. **Multi-deployment audit aggregation** — if the user runs the stack on multiple machines, do their audit logs aggregate? Out of scope for v3.0 (single-deployment scope by design), but worth noting.

---

## 10. Cross-References

- **Design basis:** B1 audit log (per-edition policy: required for healthcare-locked editions, opt-in for general)
- **Protocol integration:** `MEMORY_PROTOCOL.md` §5.2 (when to write to audit log) + §4.1 (validation-on-read triggers audit entries)
- **Quarantine integration:** `SCHEMA_quarantine.md` (quarantine events log to audit log)
- **Compliance integration:** `SCHEMA_compliance_profile.md` §audit-defaults (preset-specific audit policy)
- **Cryptographic integration:** C4 (Layer 6 signatures sign audit entries when active at T3)
