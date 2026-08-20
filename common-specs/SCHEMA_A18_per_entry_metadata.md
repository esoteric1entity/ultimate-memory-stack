# SCHEMA_A18 — Per-Entry + File Metadata (YAML Frontmatter)

> **Schema version:** 1.4 · **Status:** stable
> **Scope:** every memory entry (entry-level) and memory file (file-level) in the Ultimate Memory Stack
> **In one sentence:** structured YAML frontmatter that makes every memory entry's provenance, validity, and lifecycle machine-readable while staying human-readable.
>
> Schema version history lives in [`CHANGELOG.md`](../CHANGELOG.md).

---

## 1. Statement of Purpose

Memory entries in our v2.0 stack carry **implicit metadata** — author, date, confidence — embedded in narrative form within each entry. This works for human-readable maintenance but doesn't enable:

- **Provenance tracking** (who wrote this entry? was it the user, the orchestrator, or an external source via WebFetch?)
- **Auto-promotion via recurrence counting** (pattern_key + recurrence_count)
- **Read-time validation** (when was this last validated? has the substantiating evidence changed?)
- **TTL / decay** (when does this expire if not re-validated?)
- **Quarantine state** (is this entry currently flagged as suspect?)
- **CAS-style concurrency** (content_sha256 for safe parallel writes)
- **Memory poisoning defense** (optional cryptographic signature for tamper detection — Wave 3)

A18 introduces **structured YAML frontmatter** at the top of every memory entry to make these fields machine-readable AND human-readable.

**The goal:** convert implicit narrative-buried metadata into structured fields that enable security defenses, automation, and audit — while keeping the memory file fundamentally human-readable.

---

## 2. Rationale

### Why YAML frontmatter specifically?

Three plausible options were considered:

| Option | Pros | Cons |
|--------|------|------|
| **YAML frontmatter** (chosen) | Standard convention (Obsidian, Jekyll, Hugo). Parseable by tools. Human-readable. Doesn't interfere with markdown body. | Adds visual weight at top of every entry. |
| Inline markdown table | Pure markdown, no parser needed | Less standard. Brittle if columns reordered. Mixes structured with prose. |
| Separate sidecar `.meta.json` file per entry | Cleanest separation | Doubles file count. Drift risk between content and metadata. Harder for human author. |

**Decision:** YAML frontmatter. Standard convention wins. The mild visual weight is worth the ecosystem compatibility (Obsidian plugins, parsers, MCP servers all know how to read it).

### Why per-entry, not per-file?

A single file like `decisions.md` contains many entries (DEC-001 through DEC-NNN). Adding frontmatter PER ENTRY (not per file) is necessary because:
- Different entries have different ages, sources, validation status
- Auto-promotion + recurrence tracking work at entry granularity
- Quarantine flags must apply to specific entries, not the whole file

**Implementation:** Each entry starts with `---\n[frontmatter]\n---\n` THEN the entry's narrative body, then a blank line, then the next entry. Standard markdown frontmatter conventions apply at the entry level.

### Why these specific fields?

Each field maps to a concrete research finding:

| Field | Driven by | Why |
|-------|-----------|-----|
| `id` | Existing convention (DEC-NNN, FB-NNN, etc.) | Identifier for cross-references |
| `created_at` | Audit + TTL | When was this born? |
| `last_updated` | Audit | When was it last touched? |
| `last_validated` | Validation-on-read pattern (GitHub Copilot memory docs) | When did we last confirm this is still true? |
| `expires_at` | TTL backstop pattern (Copilot's 28-day heuristic) | When should we re-validate or archive? |
| `source_agent` | Provenance defense vs memory poisoning | Who wrote this — the orchestrator? A sub-agent? The user? WebFetch? |
| `source_session` | Audit | Which session originated this? |
| `source_uri` | Provenance | If from external source, what URI? Critical for WebFetch-sourced entries. |
| `pattern_key` | mem0 ADD/UPDATE/DELETE/NOOP + the PDuk predecessor stack's Pattern-Key/Recurrence-Count | Stable identifier for matching recurring patterns |
| `recurrence_count` | PDuk predecessor stack | How many times has this pattern shown up? Auto-promote at ≥3. |
| `first_seen` / `last_seen` | PDuk predecessor stack | Temporal range of this pattern's occurrences |
| `confidence` | Existing v2.0 (FINAL/TENTATIVE/EXPLORATORY) | Our decision confidence scale |
| `status` | Quarantine workflow | active / superseded / quarantined / archived |
| `content_sha256` | CAS pattern (Anthropic managed-agents memory) | For safe parallel writes per CAS pattern |
| `signature` | Cryptographic provenance (high-assurance deployments) | Optional Ed25519 signature for tamper detection |

Each field has a defensible rationale tied to a specific research finding.

### Alternatives considered and rejected

- **Storing all metadata in `MEMORY_INDEX.md`** — Rejected. Single point of failure. Index would balloon. Per-entry metadata belongs WITH the entry.
- **TOML frontmatter (instead of YAML)** — Rejected. YAML is more widely supported in the markdown ecosystem (Obsidian, MkDocs, Jekyll, Hugo).
- **No frontmatter at all, encode metadata in entry header lines** — Rejected. Loses parser-friendliness. Brittle. Already de facto today and not working well.
- **Sidecar `<entry-id>.meta.yaml` files** — Rejected. Doubles file count. Drift risk.

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| Validation-on-read > time-based TTL | `[GitHubCopilot-MemoryDocs]` | First-party docs |
| Memory poisoning requires provenance + read-time validation | `[OWASP-ASI06]` + `[arXiv-2503.03704]` | OWASP standard + peer-reviewed paper |
| Pattern-Key / Recurrence-Count as auto-promotion gate | PDuk predecessor stack (operational evidence) | Operational artifact |
| CAS-style concurrency via content_sha256 | `[Anthropic2026-ManagedAgentsMemory]` + Letta `memory_replace` | Two-vendor convergence |
| YAML frontmatter is the dominant markdown convention | Obsidian / Jekyll / Hugo / MkDocs ecosystem | De facto standard |
| Cursor's Memories removal lesson — automatic memory needs validation gates | Vendor product reporting | Vendor product failure |

**Caveats:**
- The exact 28-day TTL number is a heuristic (Copilot's choice), not a measured optimum. We adopt the pattern, not the number — make TTL configurable per profile.
- Ed25519 vs HMAC for signature is an open question (see §9) — both have merits. NEITHER is implemented: no signing or verification code exists, and the `signature:` field is reserved.

---

## 4. Schema Definition

### Common core fields (apply to ALL memory entry types)

```yaml
---
id: <ENTRY-ID>                     # e.g., DEC-024, FB-007, VET-009, CR-005
created_at: YYYY-MM-DD             # Required
last_updated: YYYY-MM-DD           # Required, set to created_at if never updated
source_agent: <agent>              # See "source_agent values" below
source_session: <session-number>   # The session in which this was created
status: active                     # active | superseded | quarantined | archived
schema_version: "3.0"              # The schema version this entry conforms to
scope: entry                       # OPTIONAL (defaults to `entry`) — see "scope values" below
---
```

### `scope` field — Frontmatter scope discriminator

The `scope:` field disambiguates whether the YAML frontmatter applies to a **single entry** within a file (entry-level) OR to the **whole file** (file-level). This extends A18 to cover both use cases without spawning a parallel schema.

**Backward compatibility:** If `scope:` is omitted, defaults to `entry`. All entries written before this field existed implicitly have `scope: entry`. No migration needed.

#### Allowed values

| `scope:` value | Applies to | Examples |
|---|---|---|
| `entry` (default) | Single entry within a file | DEC-024 inside `decisions.md`; FB-007 inside `feedback.md` |
| `file` | Generic file-level metadata (fallback) | Any file lacking a more specific scope |
| `index` | Index / master-registry file | `memory/MEMORY_INDEX.md`, OpenClaw `MEMORY.md` |
| `session` | Session state file | `memory/sessions/session_state.md`, OpenClaw `SESSION-STATE.md` |
| `user` | User profile | `memory/user/user_profile.md`, OpenClaw `USER.md` |
| `entry-collection` | File holding multiple `scope: entry` items | `memory/decisions/decisions.md`, `memory/feedback/feedback.md`, `memory/security/vetting_log.md` |
| `daily` | Daily / dated log file | OpenClaw `memory/YYYY-MM-DD.md` |
| `learning` | Lessons / errors / feature-requests file | OpenClaw `.learnings/*.md` |
| `detail` | Domain detail file | OpenClaw `memory/details/*.md`; future Claude Code `memory/details/` subdir |
| `log` | Append-only JSONL log | `memory/security/audit_log.jsonl`, `memory/quarantine/quarantine_log.jsonl` |
| `reference` | Reference index file | `memory/references/references.md` |
| `project-bank` | Per-project memory bank file per SCHEMA_A3 | `memory/projects/<slug>/memory-bank/projectbrief.md` etc. |

The memory stack does NOT enforce semantic meaning beyond the registered enum. Adding a value requires a schema version bump.

#### Where file-level frontmatter goes

In a file that uses `scope: file` (or any file-level value): the frontmatter sits at the **top of the file**, before any narrative content. It is the file's overall metadata. Entry-level frontmatter (per `scope: entry` entries) appears WITHIN the file, prefixing each entry as before.

A file can mix both: top-of-file `scope: entry-collection` metadata + per-entry `scope: entry` frontmatter blocks throughout.

### `loaded_when` field (optional) — Progressive disclosure metadata

Hints the runtime about WHEN a file should be loaded into context. Used by Tier 1/2/3 budget logic and by future heartbeat-driven compaction.

| `loaded_when:` value | Semantics |
|---|---|
| `always` | Loaded at every session start without exception |
| `session-start` | Loaded at session bootstrap (default for Tier 1 files) |
| `tier-1` | Loaded per MEMORY_PROTOCOL §1.2 Tier 1 budget (session_state, user_profile) |
| `tier-2` | Conditional-load per Tier 2 (decisions.md, activeContext.md) |
| `tier-3` | On-demand per Tier 3 (per-project memory-bank files) |
| `on-demand` | Only loaded when explicitly referenced via path or wikilink |
| `query` | Loaded only via memory_search query result |
| `heartbeat-pre-warmed` | Pre-loaded by background compaction agent (future feature) |

If `loaded_when:` is omitted, runtime infers from `scope:` (e.g., `scope: index` → `always`; `scope: detail` → `on-demand`).

### `points_to` field (optional) — Index pointer list

For index files (`scope: index`) that enumerate other files. Used by the runtime to expand a single index reference into a set of available drill-down files without parsing the file body.

```yaml
points_to:
  - memory/decisions/decisions.md
  - memory/sessions/session_state.md
  - memory/feedback/feedback.md
  - memory/user/user_profile.md
```

For non-index files, omit this field (or use empty list). The runtime ignores `points_to` on entries with `scope` other than `index`.

### Access tracking fields (optional) — PageRank-style promotion signal

Three new optional fields that capture **how often an entry is referenced** (read into context, cited inline, returned by memory_search). Used by MEMORY_PROTOCOL §12 (Decision Promotion) to augment the existing recurrence-count rule with an access-frequency signal.

```yaml
access_count: 0                    # Integer — total times this entry has been loaded into context (since creation)
last_accessed: null                # Date YYYY-MM-DD — most recent access; null if never accessed beyond initial creation
recent_sessions: []                # List of last 5 session numbers where this entry was accessed (sliding window)
```

#### Semantics

| Field | Meaning | When incremented/updated |
|---|---|---|
| `access_count` | Total accesses (lifetime counter) | At every Tier 1 / Tier 2 / Tier 3 load + every memory_search query result that surfaces this entry |
| `last_accessed` | Most recent access date | Updated to today's date on every access |
| `recent_sessions` | Last 5 unique session numbers (FIFO sliding window) | Append current session number if not already in list; drop oldest if list exceeds 5 |

**Why these specific fields:** capture both **total access intensity** (`access_count`) AND **temporal recency** (`last_accessed`) AND **session spread** (`recent_sessions`). Together they enable promotion decisions that distinguish "accessed many times in one session" (low signal — flash interest) from "accessed across many sessions" (high signal — durable usefulness).

#### Promotion signal calculation (per MEMORY_PROTOCOL §12)

An entry qualifies for **PageRank-style promotion** when BOTH:
- `access_count` ≥ 5 (heavily-loaded)
- `len(recent_sessions)` ≥ 3 (spread across multiple sessions, not flash-in-one-session)

This is in ADDITION to the existing recurrence-count promotion rule (Pattern-Key/Recurrence-Count) — either signal alone qualifies.

#### Privacy + audit considerations

Access tracking emits NO new entries to the audit log (B1) — counters are aggregate, not per-access records. No new sensitive-data exposure per the compliance profile.

For deployments requiring finer-grained audit, the existing audit log (B1) already captures Tier load events (action: `read`); the access tracking fields here are an aggregate summary of that finer-grained data, not a replacement.

#### Backward compatibility

All three fields are OPTIONAL with sensible defaults (0 / null / empty list). Existing v3.0 entries without these fields are valid; they simply lack the PageRank signal. Runtime may compute counters retroactively from audit_log history if available, or initialize to defaults and accrue from this point forward.

#### Implementation roadmap

- **Shipped: the SCHEMA** — fields documented + validation accepts them
- **Shipped: the PROMOTION RULE** in MEMORY_PROTOCOL §12 — promotion logic uses the fields IF populated
- **NOT yet shipped: the AUTO-INCREMENTER** — runtime hooks that increment counters at Tier loads are a future deliverable; for now, counters update manually or via heartbeat-driven compaction

This is a deliberate **schema-first, mechanism-later** approach, consistent with the stack's ideal-first design philosophy (features are designed in; they activate when their infrastructure unblocks).

### `source_agent` — Modular Definition

`source_agent` is **decoupled** into standard slots (defined by the memory stack) + consumer-defined slots (defined by the consuming agent architecture). The memory stack is a branded module; the consuming architecture is pluggable. See `MODULARITY.md` for the full plug-in pattern.

#### Standard slots (always available; defined by memory stack)

These slots are guaranteed available across all consuming Claude architectures:

- `user` — entered manually or dictated by the human operator
- `orchestrator` — the main agent instance interacting with the user (Claude Code session itself)
- `webfetch` — sourced from external URL via WebFetch (HIGH-RISK; requires extra validation per memory poisoning defenses B8)
- `external-tool-output` — sourced from a non-WebFetch tool result (bash, MCP server output, etc.)
- `migration-script` — sourced from a one-time migration or bootstrap script

#### Consumer-defined slots (defined by consuming Claude architecture)

A consuming architecture may define additional slots for its specific sub-agents. The memory stack accepts ANY string matching pattern `[a-z][a-z0-9-]*` (lowercase alphanumeric with hyphens, must start with a letter). Examples:

**Reference 4-agent example:**
- `warden` — security agent
- `sentinel` — vetting / code review agent
- `vault` — memory operations agent
- `clerk` — PM agent

**Other deployments may define their own (illustrative):**
- `researcher` — research agent
- `data-analyst` — data analysis agent
- `qa-reviewer` — QA review agent
- etc.

**No-sub-agent deployments:** simply use the standard slots (`user`, `orchestrator`, `webfetch`, `external-tool-output`). No consumer-defined slots required.

#### How consuming architectures register their slots

At bootstrap (BOOTSTRAP_PROMPT.md Step 7), the setup wizard asks: "What sub-agent topology does your Claude architecture use?" The consumer provides a list of agent names (or empty for no-sub-agent setup). These are saved to the user profile and become valid `source_agent` values for the deployment.

The memory stack does NOT validate semantic meaning of consumer-defined slots — it only enforces the naming pattern and ensures the slot exists in the registered set for this deployment.

**Brand protection note:** the memory stack's CANONICAL elements (stack name, schemas, layer structure, protocols, compliance presets) are NOT user-changeable. Only the consumer-defined `source_agent` slots are pluggable. Same way SQL is canonical but applications consuming SQL vary.

### Decision-specific additional fields (decisions.md entries)

```yaml
confidence: FINAL                  # FINAL | TENTATIVE | EXPLORATORY
supersedes: DEC-NNN                # Optional — if this replaces a prior decision
related: [DEC-NNN, DEC-NNN]        # Optional — cross-references
tags: [memory, security, ...]      # Optional — tags for grouping
```

### Feedback-specific additional fields (feedback.md entries)

```yaml
pattern_key: <stable.dotted.key>   # e.g., "output.formatting.tables"
recurrence_count: <N>              # Increment when same feedback pattern recurs
first_seen: YYYY-MM-DD
last_seen: YYYY-MM-DD
```

### Security-specific additional fields (vetting_log.md entries)

```yaml
subject: <what was vetted/reviewed>  # Tool name, repo URL, PR ID
verdict: PASS | REVIEW_REQUIRED | FAIL | APPROVE | APPROVE_WITH_NOTES | NEEDS_DISCUSSION | REQUEST_CHANGES
pipeline: <pipeline-name>           # e.g., "warden-sentinel-mode2"
findings_count: <N>                 # Number of distinct findings
```

### Project-specific additional fields (project_context.md entries OR Memory Bank files)

```yaml
project_slug: <slug>                # Required for project entries
project_status: planning | active | paused | complete | archived
memory_bank_path: projects/<slug>/memory-bank/    # Optional — if Memory Bank exists
```

### TTL / validation fields (Wave 1 — all entry types)

```yaml
last_validated: YYYY-MM-DD          # When was citation/state validated against source?
expires_at: YYYY-MM-DD              # 28-day default from last_validated, refresh-on-validation
validation_status: valid | stale | invalidated  # Set by validator
```

### Cryptographic fields (Wave 3 — optional; may be required by compliance profile)

```yaml
content_sha256: <hex>               # Hash of entry body for CAS (see normalization below)
signature:                          # RESERVED — signing is NOT IMPLEMENTED; nothing writes or verifies this
  algorithm: ed25519 | hmac-sha256
  signature: <base64>
  signer: <public-key-id-or-session-id>
  signed_at: YYYY-MM-DD
```

#### `content_sha256` normalization (canonical)

**Canonical computation** — exactly this, no variations. Cross-agent hash reproducibility depends on bit-exact normalization:

```python
# Reference implementation (Python 3.10+) — CANONICAL
def compute_content_sha256(file_text: str) -> str:
    """Compute SHA-256 of entry body per A18 normalization rules."""
    import hashlib
    # 1. Split frontmatter from body on '---' delimiter
    body = file_text.split('---', 2)[2]
    # 2. Strip leading newline(s) introduced by the delimiter framing
    #    (the '---' closing line emits '\n' before the body proper)
    body = body.lstrip('\n')
    # 3. Encode as UTF-8 (no BOM)
    body_bytes = body.encode('utf-8')
    # 4. SHA-256
    return hashlib.sha256(body_bytes).hexdigest()
```

**Normalization rules:**
- **Body extraction:** `file_text.split('---', 2)[2]` (third element after splitting on first 2 `---` delimiters)
- **Leading-newline strip:** `body.lstrip('\n')` — REQUIRED. The `---` closing delimiter is followed by `\n`; whether that `\n` belongs to the delimiter framing or the body was unspecified prior to this fix. Strip it.
- **Encoding:** UTF-8, no BOM
- **Line endings:** LF preserved as-is. Do NOT normalize CRLF↔LF
- **Trailing whitespace:** PRESERVED. Do NOT rstrip
- **Empty lines within body:** PRESERVED

**Why this rule exists:** Without the `lstrip('\n')` step, two agents computing `content_sha256` for the same byte-identical file produce DIFFERENT hashes. This broke cross-machine round-trip verification during release validation — only the `[2].lstrip('\n')` form matched across independent implementations, so it is locked as canonical.

**Edition behavior:**
- **Compliance-profile deployments:** `content_sha256` REQUIRED on every entry. Implementations MUST use this canonical normalization.
- **Default:** `content_sha256` optional; if present, MUST use this canonical normalization.

**Backwards compat:** Prior implementations that did NOT lstrip will have legacy hashes. New writes should use the canonical form; existing hashes are NOT re-computed (would invalidate audit trails). Future validation: compute both forms and accept either during migration window.

**Cross-reference:** MEMORY_PROTOCOL_EXTENDED.md §E3.1 (CAS-Style Concurrency) uses this same normalization for write-time hash comparison.

### Bi-temporal fields (B5 — optional; may be enforced by compliance profile)

```yaml
valid_at: YYYY-MM-DD                # When this fact became true in the world (may predate created_at)
invalid_at: YYYY-MM-DD              # When this fact was superseded (set automatically when supersedes occurs)
```

**Conceptual distinction — four temporal axes, each different:**

| Field | What it answers |
|-------|------------------|
| `created_at` | When was this entry **recorded in our system**? |
| `valid_at` | When did the underlying fact **become true in the world**? (may predate created_at) |
| `expires_at` | When does this entry need **revalidation** (TTL — admin concern)? |
| `invalid_at` | When was the fact **superseded by a contradicting fact**? (factual end of validity) |

**Pattern source:** Graphiti temporal-fact graph (arXiv:2501.13956). Bi-temporal facts retain history rather than deleting — when contradiction arrives, set `invalid_at` on the old fact rather than removing the edge.

**Capabilities enabled:**
- **Point-in-time queries** — "What did we believe on date X?" Filter: `valid_at ≤ X AND (invalid_at IS NULL OR invalid_at > X)`
- **Fact lineage** — walk `supersedes:` chain to see how knowledge evolved over time
- **Audit-grade forensics** — reconstruct memory state at any historical date (critical for high-compliance deployments)
- **History-preserving supersession** — old facts get `invalid_at` set, not deleted; provenance survives

**Edition behavior:**
- **Compliance-profile deployments:** `valid_at` REQUIRED on decision/feedback/security entries. `invalid_at` set automatically when a successor entry has `supersedes: <prior-id>`.
- **Default:** Both fields OPTIONAL. Available to users who value temporal reasoning; safe default is `valid_at = created_at` if omitted.

**Markdown-now, graph-later:**
- T0–T2: bi-temporal annotations in YAML; queries answered by grep + manual reasoning
- T3+ (Code Execution unblocked): Graphiti+Kuzu backend (C2) consumes these fields to answer point-in-time queries in milliseconds
- Adopting the convention NOW (in pure markdown) primes the system for Layer 5 activation without re-migration.

### Cross-reference fields (B4 + Wiki-link convention)

```yaml
related: [DEC-NNN, FB-NNN]          # Canonical YAML cross-references (also seen in §Decision-specific above)
supersedes: DEC-NNN                 # Optional — explicit factual replacement (drives invalid_at)
```

**Supplemental inline syntax (PKM convention):**

Within an entry's narrative body, contributors MAY use the **wiki-link bracket syntax** `[[ID]]` to reference other entries inline:

```markdown
This decision builds on [[DEC-023]] and supersedes [[DEC-019]] regarding scope.
See also [[B5]] for the bi-temporal pattern that motivates this.
```

**Status:**
- **At T0–T1:** YAML `related` / `supersedes` fields are CANONICAL. Inline `[[ID]]` is human-friendly supplemental form for readability; must be manually mirrored to the YAML field on save.
- **At T2+ (Node.js indexer):** Inline links auto-parsed into YAML on file save. Two-way sync. Wiki-links and YAML never drift.

**Rationale:** Wiki-link `[[]]` syntax is the universal PKM convention (Obsidian, Logseq, Roam, Khoj). Adopting it gives humans familiar ergonomics while keeping YAML as the machine-parseable canonical form. **Compatible with Obsidian vaults out of the box** — open the memory directory in Obsidian and wiki-links become clickable.

---

## 4.X — File-level frontmatter examples (v1.3)

### Example: MEMORY_INDEX.md (`scope: index`)

```markdown
---
id: MEMORY-INDEX
created_at: 2026-04-10
last_updated: 2026-05-27
source_agent: vault
source_session: 8
status: active
schema_version: "3.0"
scope: index
loaded_when: always
points_to:
  - memory/decisions/decisions.md
  - memory/sessions/session_state.md
  - memory/feedback/feedback.md
  - memory/projects/project_context.md
  - memory/security/vetting_log.md
  - memory/user/user_profile.md
  - memory/references/references.md
tags: [index, registry, master]
---

# Memory Index — Master Registry

[file body...]
```

### Example: session_state.md (`scope: session`)

```markdown
---
id: SESSION-STATE
created_at: 2026-04-09
last_updated: 2026-05-27
source_agent: orchestrator
source_session: 8
status: active
schema_version: "3.0"
scope: session
loaded_when: tier-1
tags: [session-state, heartbeat]
---

# Session State — Current

[heartbeat content...]
```

### Example: user_profile.md (`scope: user`)

```markdown
---
id: USER-PROFILE
created_at: 2026-04-09
last_updated: 2026-05-27
source_agent: user
source_session: 1
status: active
schema_version: "3.0"
scope: user
loaded_when: tier-1
tags: [identity, user-profile]
---

# User Profile — <your-name>

[profile content...]
```

### Example: decisions.md (`scope: entry-collection`, with per-entry frontmatter inside)

```markdown
---
id: DECISIONS-COLLECTION
created_at: 2026-04-10
last_updated: 2026-05-27
source_agent: vault
source_session: 8
status: active
schema_version: "3.0"
scope: entry-collection
loaded_when: tier-2
tags: [decisions, collection]
---

# Decisions Log — Per-Entry SCHEMA_A18 frontmatter follows

(Each DEC-NNN entry below has its own `scope: entry` frontmatter block.)

## DEC-001: ...

---
id: DEC-001
created_at: 2026-04-09
...
scope: entry              # implicit if omitted
---

[entry body]

## DEC-002: ...
[next entry...]
```

### Example: memory/2026-05-27.md (`scope: daily`, OpenClaw convention)

```markdown
---
id: DAILY-2026-05-27
created_at: 2026-05-27
last_updated: 2026-05-27
source_agent: orchestrator
source_session: 8
status: active
schema_version: "3.0"
scope: daily
loaded_when: session-start
tags: [daily-log, session-record]
---

# Daily Log — 2026-05-27

[session activity...]
```

### Backward compatibility note (v1.3)

**No migration required.** All existing v3.0 entries are implicitly `scope: entry`. Adding the `scope:` field to existing entries is OPTIONAL and additive.

**Runtime behavior:**
- Validation-on-read (MEMORY_PROTOCOL §4) accepts both old (no `scope`) and new (explicit `scope`) frontmatter
- Older parsers ignore unknown fields per YAML spec
- Schema version stays at `"3.0"` (this is the protocol version, not the document version)

---

## 5. Worked Example — A Decision Entry With Frontmatter

```markdown
---
id: DEC-024
created_at: 2026-05-13
last_updated: 2026-05-13
last_validated: 2026-05-13
expires_at: 2026-06-10              # 28 days from last_validated
valid_at: 2026-05-13                # B5 — same as created_at here (decision and fact-validity coincide)
source_agent: orchestrator
source_session: 7
status: active
schema_version: "3.0"
confidence: FINAL
related: [DEC-023, DEC-019]
tags: [memory, common-spec, tier-A]
---

## DEC-024: Example — Core Feature Set Approved as Definite Includes...

This decision builds on [[DEC-023]] (an earlier related decision) and complements [[DEC-019]].
Cross-references the [[B5]] bi-temporal model for forward audit traceability.

[remaining entry body in markdown as today]
```

The body remains exactly as the v2.0 format; only the frontmatter is added on top + optional inline `[[ID]]` wiki-links.

**Worked example — bi-temporal supersession:**

When DEC-024 is later superseded (hypothetically by DEC-040), TWO entries are touched:

```markdown
# Old entry — DEC-024 gets invalid_at set, status flipped to superseded:
---
id: DEC-024
created_at: 2026-05-13
last_updated: 2026-08-01            # Touched today by supersession
valid_at: 2026-05-13
invalid_at: 2026-08-01              # B5 — when the fact ended validity
status: superseded                  # Was: active
superseded_by: DEC-040              # Forward pointer
---

# New entry — DEC-040 references back:
---
id: DEC-040
created_at: 2026-08-01
valid_at: 2026-08-01
status: active
supersedes: DEC-024                 # Drives the auto-set of DEC-024's invalid_at
---
```

A point-in-time query "what did we believe about Tier A on 2026-06-15?" finds DEC-024 (valid window: 2026-05-13 → 2026-08-01). A query on 2026-09-15 finds DEC-040. **No history is lost.**

---

## 6. Scope — What This CAN and CANNOT Do

### CAN

- Track provenance of every memory entry (who created it, from what source)
- Enable validation-on-read by exposing `last_validated` + `expires_at`
- Support auto-promotion of recurring patterns (Pattern-Key + Recurrence-Count)
- Enable quarantine state for suspect entries
- Enable CAS-style concurrent writes (content_sha256)
- Support cryptographic signing (Wave 3) for tamper detection
- **Support bi-temporal point-in-time queries (B5)** — answer "what did we believe on date X?" without losing history
- **Support inline wiki-link cross-references (`[[ID]]`)** — Obsidian-compatible PKM ergonomics with YAML as canonical
- Be parsed by Obsidian, Jekyll, MkDocs, and any YAML-aware tool
- **Render in Obsidian as a graph view out of the box** (frontmatter + wiki-links both honored)
- Co-exist with the existing v2.0 narrative body format (no rewrite needed for body)

### CANNOT

- Prevent prompt-injection content from being WRITTEN into the body (frontmatter is metadata, not body sanitization)
- Replace the narrative body — every entry still needs human-readable prose
- Be retroactively applied to old entries without explicit migration (existing v2.0 entries lack frontmatter — see §7 Migration Strategy)
- Substitute for the audit log (the per-entry frontmatter records origin; the audit log records EVERY change)
- Encrypt content (signatures detect tampering; they do not hide content)

### Deployment tier

- **Core fields:** T0 (works anywhere)
- **Validation fields (last_validated, expires_at):** T0 (requires a periodic validator process — can be user-triggered or scheduled-tasks MCP)
- **Cryptographic fields (signature):** T3 (requires Code Execution to compute/verify)

### Edition fit

- **Compliance-profile deployments:** All core + validation fields mandatory. Cryptographic signature (HMAC) strongly recommended in Wave 3; Ed25519 offline-key signing is not implemented.
- **Default:** All core + validation fields default-on. Cryptographic signature NOT IMPLEMENTED — the `signature:` field is reserved; HMAC with a session-derived secret is the intended scheme.

---

## 7. Migration Strategy (existing v2.0 entries)

A one-time migration adds frontmatter to existing v2.0 entries:

1. For each entry in `decisions.md`, `feedback.md`, `vetting_log.md`, `project_context.md`:
   - Generate frontmatter from existing narrative metadata (parse "Date:", "Confidence:", "Tags:", etc.)
   - Set `last_validated = created_at` initially (will refresh on first read)
   - Set `expires_at = created_at + 28 days`
   - Insert frontmatter block before the entry's narrative body
2. Log the migration in `decisions.md` as DEC-NNN (next available number)
3. Run validation pass on all migrated entries — anything past expires_at gets revalidated or flagged stale

---

## 8. What Is to Come (and Why)

### Wave 1 (immediate)
- Schema documented (this file)
- Migration script `migrate_to_frontmatter.py` drafted (pseudocode at minimum; full Python if Code Execution allows)
- `decisions.md`, `feedback.md` schemas updated in `assets/` templates
- Memory Bank files (A3) adopt this schema natively

### Wave 2 (validation tooling)
- `validate_memory_entries.py` — scans all entries, checks `expires_at`, flags stale entries
- Quarantine workflow: suspect entries get `status: quarantined` + moved to `memory/quarantine/`

### Wave 3 (cryptographic)
- Signature generation + verification scripts
- High-assurance profile: Ed25519 with offline-generated keypair (user keeps private key in password manager)
- Intended scheme: HMAC-SHA256 with session-derived secret (NOT IMPLEMENTED)

### NOT in scope (and why)

- **Full git-style history of every metadata change** — Out of scope. The audit log (separate Wave 1 feature) captures changes; frontmatter records current state.
- **Real-time replication / sync across machines** — Out of scope. Manual file mirroring handles this for now; multi-machine sync is a designed-in future capability.
- **Encrypted memory body** — Out of scope. Defeats markdown-readability principle. Use external encryption at the filesystem level if needed.

---

## 9. Open Questions

1. **Date format:** ISO 8601 (`2026-05-13`) or with time (`2026-05-13T14:30:00Z`)? Trade-off: precision vs. readability. Lean: bare dates for daily-grain, full timestamps if we need finer.
2. **Schema migration trigger:** Run the v2.0 → v3.0 frontmatter migration all at once, or staged with each Wave 1 item?
3. **`expires_at` default:** TTL default configurable per compliance profile (e.g., 90 days, or 28 days matching Copilot). What should the shipped default be?
4. **Signature algorithm for high-assurance profile:** Ed25519 with offline-generated keypair (most secure; the operator must manage the private key) or HMAC with session-derived secret (simpler, slightly weaker)?
5. **What does WebFetch-sourced content quarantine look like by default?** Any entry with `source_agent: webfetch` should probably start in a "preliminary" state requiring orchestrator validation before promotion to `active`.

---

## 10. Cross-References

- **Citations:**
  - `[GitHubCopilot-MemoryDocs]` (TTL pattern)
  - `[arXiv-2503.03704]` (MINJA, motivates provenance)
  - `[Anthropic2026-ManagedAgentsMemory]` (content_sha256 CAS)
  - `[OWASP-ASI06]` (memory poisoning threat)
- **Sister schema:** `SCHEMA_A3_per_project_memory_bank.md` (Memory Bank files use this frontmatter)
- **Related specs:** `MODULARITY.md` (plug-in pattern), `MEMORY_PROTOCOL.md` §4–§5 (validation + write rules), `SCHEMA_audit_log.md` (the audit trail this schema's provenance fields feed)
