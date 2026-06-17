# SCHEMA_sync_log — Multi-Machine Sync Event Log Format

> **File:** `common-specs/SCHEMA_sync_log.md`
> **Version:** 1.0 (schema ships now; the sync implementation is a future deliverable)
> **Status:** READY — schema locked for v3.5; sync implementation deferred to Phase 4+
> **Authority:** project design principles — plan-first schema lock, ideal-first design, documentation discipline, v3.5 design-level scope-carve
> **Author:** esoteric1entity
> **Companion docs:** a Phase 4+ multi-machine-sync implementation design note (not yet published)

---

## §1 — Purpose

Define the JSONL format for `memory/security/sync_log.jsonl` — the append-only log of sync events between machines (e.g., a desktop, a NAS, a laptop). Each line captures one sync event with provenance + outcome.

**Why this schema ships in v3.5 even though sync implementation is Phase 4+:**
- Per our plan-first principle: lock the schema BEFORE implementation
- Per our ideal-first principle: design the cleanest format before any code constrains it
- Per the strategic direction for v3.5: Multi-Machine Sync was scope-carved at DESIGN level
- Partial v4.0 schemas were promoted to v3.5; `sync_log` is the first
- Schema readiness lets v4.0 implementation begin from a fixed contract instead of designing+building simultaneously

---

## §2 — Rationale

Memory entries written on one machine must propagate to others without conflicting writes corrupting state. The sync log provides:
1. **Provenance** — which machine originated each change
2. **Conflict detection** — content_sha256 hashing per MEMORY_PROTOCOL §5.1 CAS pattern
3. **Audit trail** — append-only JSONL matching `audit_log.jsonl` pattern
4. **Resumability** — sync state survives across sessions / machine restarts
5. **Bi-temporal compatibility** — supports MEMORY_PROTOCOL §3 B5 supersession semantics

---

## §3 — Sound Reasoning

1. **Per our ideal-first principle:** JSONL append-only matches `audit_log.jsonl` + `quarantine_log.jsonl` + `lint_runs.jsonl` — same operational pattern across all security logs
2. **Per the mirror-discipline pattern:** schema designed to detect drift between machines via content_sha256 hashing
3. **Per MEMORY_PROTOCOL §5.1 CAS:** `content_sha256_before` + `content_sha256_after` fields enable concurrent-write detection (sync conflict detection is a generalization of single-machine CAS)
4. **Per MEMORY_PROTOCOL §3 B5 bi-temporal:** schema supports `valid_at` semantics so superseded entries carry sync history without losing temporal validity
5. **Per the modular consumer architecture:** schema is harness-agnostic — works for Claude Code ↔ OpenClaw sync just as well as Claude Code ↔ Claude Code sync
6. **Per the cross-harness convergence pattern:** schema interoperates with OpenClaw deployments' existing sync conventions (if and when implemented)

---

## §4 — JSONL Line Format

Each line in `memory/security/sync_log.jsonl` is a single JSON object with the following structure:

### §4.1 Required fields (every event)

| Field | Type | Description |
|---|---|---|
| `ts` | string (ISO 8601) | Event timestamp in UTC, second-precision (matches the `audit_log.jsonl` canonical format) |
| `event_id` | string | Unique event identifier — format `SYNC-<YYYYMMDD>-<seq>` (e.g., `SYNC-20260619-0042`) |
| `machine_id` | string | Source machine identifier (e.g., `desktop-1`, `nas-1`, `laptop-1`); defined by your deployment's machine inventory |
| `action` | enum | One of: `push`, `pull`, `conflict_detected`, `conflict_resolved`, `defer`, `error` |
| `entry_ref` | string | Reference to entry being synced — format `<file-path>#<entry-id>` (e.g., `memory/decisions/decisions.md#DEC-048`) |
| `schema_version` | string | Schema version this line conforms to (always `"1.0"` for v3.5) |
| `outcome` | enum | One of: `success`, `failure`, `pending`, `deferred` |

### §4.2 Conditional fields (action-dependent)

| Field | When required | Type | Description |
|---|---|---|---|
| `content_sha256_before` | `action ∈ {push, conflict_detected}` | string (hex) | SHA256 of entry's pre-write state on the source machine |
| `content_sha256_after` | `action ∈ {push, pull, conflict_resolved}` | string (hex) | SHA256 of entry's post-write state |
| `target_machine_id` | `action ∈ {push, conflict_resolved}` | string | Destination machine for the sync event |
| `conflict_detail` | `action == conflict_detected` | object | Subobject describing the conflict (see §4.3) |
| `resolution` | `action == conflict_resolved` | object | Subobject describing how the conflict was resolved (see §4.4) |
| `error_class` | `action == error` OR `outcome == failure` | string | Error classification (e.g., `network`, `permission`, `missing-file`, `schema-mismatch`) |
| `error_message` | `outcome == failure` | string | Human-readable error message |

### §4.3 `conflict_detail` subobject (when `action == conflict_detected`)

```json
{
  "conflict_type": "concurrent_write" | "schema_mismatch" | "missing_target" | "supersession_collision",
  "source_sha256": "<hex>",
  "target_sha256": "<hex>",
  "source_valid_at": "<ISO 8601 timestamp>",
  "target_valid_at": "<ISO 8601 timestamp>",
  "auto_resolvable": true | false
}
```

### §4.4 `resolution` subobject (when `action == conflict_resolved`)

```json
{
  "strategy": "manual_review" | "newest_wins" | "machine_priority" | "user_approved" | "auto_merge",
  "winning_machine": "<machine_id>",
  "final_sha256": "<hex>",
  "user_decision_required": true | false,
  "resolution_ts": "<ISO 8601>"
}
```

### §4.5 Optional fields (provenance enhancements)

| Field | Type | Description |
|---|---|---|
| `session` | integer | Session number when event occurred (matches `source_session` from SCHEMA_A18) |
| `actor` | string | Agent that initiated the event (e.g., `orchestrator`, `vault`, `manual-cli`) |
| `valid_at` | string (ISO 8601) | Bi-temporal validity start per MEMORY_PROTOCOL §3 B5 (matches entry's frontmatter) |
| `parent_event_id` | string | If this event resolves a prior conflict, reference back to the `conflict_detected` event |

---

## §5 — Example JSONL Lines

### §5.1 Successful push from desktop to NAS

```jsonl
{"ts":"2026-07-15T14:32:11Z","event_id":"SYNC-20260715-0001","machine_id":"desktop-1","action":"push","entry_ref":"memory/decisions/decisions.md#DEC-049","schema_version":"1.0","outcome":"success","content_sha256_before":"a1b2c3d4...","content_sha256_after":"e5f6a7b8...","target_machine_id":"nas-1","session":11,"actor":"orchestrator"}
```

### §5.2 Conflict detected

```jsonl
{"ts":"2026-07-15T14:35:22Z","event_id":"SYNC-20260715-0002","machine_id":"desktop-1","action":"conflict_detected","entry_ref":"memory/decisions/decisions.md#DEC-050","schema_version":"1.0","outcome":"pending","content_sha256_before":"f1e2d3c4...","content_sha256_after":"","target_machine_id":"nas-1","conflict_detail":{"conflict_type":"concurrent_write","source_sha256":"f1e2d3c4...","target_sha256":"d4c3b2a1...","source_valid_at":"2026-07-15T14:30:00Z","target_valid_at":"2026-07-15T14:33:45Z","auto_resolvable":false},"session":11,"actor":"orchestrator"}
```

### §5.3 Conflict resolved by user

```jsonl
{"ts":"2026-07-15T14:42:18Z","event_id":"SYNC-20260715-0003","machine_id":"desktop-1","action":"conflict_resolved","entry_ref":"memory/decisions/decisions.md#DEC-050","schema_version":"1.0","outcome":"success","content_sha256_after":"f1e2d3c4...","target_machine_id":"nas-1","resolution":{"strategy":"manual_review","winning_machine":"desktop-1","final_sha256":"f1e2d3c4...","user_decision_required":true,"resolution_ts":"2026-07-15T14:42:18Z"},"parent_event_id":"SYNC-20260715-0002","session":11,"actor":"orchestrator"}
```

### §5.4 Pull from NAS (no conflict)

```jsonl
{"ts":"2026-07-15T15:01:33Z","event_id":"SYNC-20260715-0004","machine_id":"nas-1","action":"pull","entry_ref":"memory/feedback/feedback.md#FB-007","schema_version":"1.0","outcome":"success","content_sha256_after":"a8b7c6d5...","session":11,"actor":"orchestrator"}
```

### §5.5 Deferred (e.g., target machine offline)

```jsonl
{"ts":"2026-07-15T15:15:00Z","event_id":"SYNC-20260715-0005","machine_id":"desktop-1","action":"defer","entry_ref":"memory/security/vetting_log.md#VET-013","schema_version":"1.0","outcome":"deferred","target_machine_id":"nas-2","error_class":"network","error_message":"Target machine unreachable; will retry on next sync trigger","session":11,"actor":"vault"}
```

### §5.6 Error (permission)

```jsonl
{"ts":"2026-07-15T15:20:45Z","event_id":"SYNC-20260715-0006","machine_id":"laptop-2","action":"error","entry_ref":"memory/quarantine/quarantine_log.jsonl","schema_version":"1.0","outcome":"failure","error_class":"permission","error_message":"Write permission denied on target","target_machine_id":"laptop-1","session":11,"actor":"orchestrator"}
```

---

## §6 — Operational Semantics

### §6.1 Append-only

`sync_log.jsonl` is APPEND-ONLY per the same convention as `audit_log.jsonl` + `quarantine_log.jsonl` + `lint_runs.jsonl`. Lines are NEVER modified after writing — corrections are recorded as new lines that reference earlier `event_id` via `parent_event_id`.

### §6.2 Rotation policy

Per MEMORY_PROTOCOL §11 file size limits + the audit_log rotation pattern:
- When `sync_log.jsonl` exceeds 50,000 lines, rotate to `sync_log_<YYYY-MM>.jsonl` (gzip old months)
- Per-edition retention defaults (parallel to audit_log B1 conventions):
  - **biotech-edition:** 365 days minimum (forensic completeness)
  - **general-edition:** 90 days default; user-configurable

### §6.3 Event ID sequencing

Format: `SYNC-<YYYYMMDD>-<seq>` where `seq` is zero-padded 4-digit sequence within the day, starting at `0001`. Each machine assigns sequence numbers from its own counter — collisions across machines are detected by `machine_id` + `event_id` joint uniqueness check.

### §6.4 Bi-temporal compatibility

When an entry has been superseded (per MEMORY_PROTOCOL §3 B5), the sync log captures BOTH the old entry's `invalid_at` event and the new entry's creation as separate sync events with `parent_event_id` linking them. History is preserved across all machines.

### §6.5 CAS detection

Before any `push`, the source machine reads the target's current `content_sha256` and compares to its own pre-write value. If mismatch → emit `conflict_detected` event; do NOT proceed without `conflict_resolved`.

---

## §7 — Implementation Status (v3.5 vs Phase 4+)

| Component | Status in v3.5 |
|---|---|
| **This schema document** | ✅ READY (v1.0) |
| `memory/security/sync_log.jsonl` file creation by adapter | 🟡 Not yet auto-created (Phase 4+) |
| Multi-machine sync IMPLEMENTATION | 🟡 Phase 4+ candidate |
| Conflict resolution UI/Skill | 🟡 Phase 4+ |
| Cross-machine network protocol | 🟡 Phase 4+ |
| Sync agent (auto-sync via cron/heartbeat) | 🟡 Phase 4+ |

**v3.5 deliverable:** This schema document. Implementations consuming it are gated to Phase 4+.

---

## §8 — Scope CAN

- Define the JSONL line format for sync events
- Enable Phase 4+ implementations to start from a fixed schema contract
- Support bi-temporal entry validity per MEMORY_PROTOCOL §3 B5
- Coordinate with `audit_log.jsonl` format (canonical: compact JSON, second-precision ts, `entry_id` sentinels)
- Support both Claude Code ↔ OpenClaw + Claude Code ↔ Claude Code sync (harness-agnostic by design)
- Detect concurrent-write conflicts via CAS hashing

## §9 — Scope CANNOT

- Implement sync mechanics (Phase 4+ scope)
- Mandate a network protocol (TCP/HTTP/USB/SMB — implementation-time choice)
- Mandate a sync trigger (cron / heartbeat / manual — implementation-time choice)
- Resolve conflicts automatically (auto-merge strategies are user-opt-in; default is `manual_review`)
- Replace `audit_log.jsonl` — sync is a SEPARATE concern from local audit; both logs may capture overlapping events
- Validate that target machines are reachable (network concerns are implementation)
- Replace MEMORY_PROTOCOL §3 B5 bi-temporal precedence — schema CARRIES bi-temporal data but conflict resolution still uses §3 hierarchy

---

## §10 — Cross-References

- Plan-first discipline (this schema is the plan)
- Mirror discipline (drift detection between copies)
- Ideal-first design
- Documentation discipline (this doc carries 5 elements at §1, §2, §3, §8, §9)
- Modular consumer architecture (schema is harness-agnostic)
- v4.0 schema extensions (sync_log is the FIRST promoted to v3.5)
- Multi-Machine Sync scope-carve (design-only for v3.5)
- Cross-harness convergence (schema interoperates with OpenClaw conventions)
- v3.5 release trajectory (sync_log shipped as schema-only partial)
- SCHEMA_A18 v1.3 + v1.4 (per-entry frontmatter — sync events reference entry IDs)
- A Phase 4+ multi-machine-sync implementation design note (not yet published)
- MEMORY_PROTOCOL §3 B5 (bi-temporal precedence)
- MEMORY_PROTOCOL §5.1 (CAS concurrency)
- MEMORY_PROTOCOL §5.2 (audit_log format — pattern this schema mirrors)
- MEMORY_PROTOCOL §11 (file size limits + rotation policy)
- `audit_log.jsonl` canonical format (canonical — compact JSON, second-precision)
