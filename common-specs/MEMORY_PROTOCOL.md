# Memory Protocol

> **Status:** stable (ships with UMS v3.6.0) · **Authors:** see /AUTHORS.md
> **In one sentence:** the runtime contract — HOW the agent loads, prioritizes, validates, writes, audits, and conflict-resolves memory.
> **Auto-load target:** this file gets COPIED to `.claude/rules/memory_protocol.md` during bootstrap (per BOOTSTRAP_PROMPT §Step-3); Claude Code auto-loads it every session. It replaces any v2.0-era protocol file.
>
> Version history lives in [`CHANGELOG.md`](../CHANGELOG.md).

---

## What This File Is (and Isn't)

**Purpose:** Operational rules. This file tells Claude HOW to load, prioritize, validate, write, audit, and resolve conflicts in memory. It is the runtime contract.

**Not in this file:**
- Content (Layer 1 markdown vault holds content)
- Schema definitions (see SCHEMA_A3, SCHEMA_A18, SCHEMA_audit_log, SCHEMA_quarantine, SCHEMA_compliance_profile)
- Architecture (see ARCHITECTURE.md)
- The deployment activation prompt (see BOOTSTRAP_PROMPT.md)
- Edition-specific overrides (see `<edition>/PROFILE.md` + `overrides/`)

**Auto-load mechanism:** Claude Code reads `.claude/rules/*.md` at session start. This file is one of those rules. Place a copy at `.claude/rules/memory_protocol.md` during bootstrap.

---

## 1. Session Start Protocol

### Step 1.1 — Edition Detection

Read `<working-dir>/<edition>/PROFILE.md` to determine:
- Active edition (`biotech` or `general`)
- Compliance preset (`none` / `healthcare` / `enterprise` / `custom`) per B7
- Audit log policy (REQUIRED for biotech / OPT-IN for general) per B1
- Quarantine UX (workflow vs toast) per B2
- Pattern-key recurrence threshold (≥3 biotech, ≥5 general) per B6
- Cryptographic signature scheme (Ed25519 / HMAC / none) per C4
- Override-file map per B4

If PROFILE.md not found, the deployment is incomplete. Halt and warn the user.

### Step 1.2 — Adaptive Context Loading (Tiered)

Load memory files in tiers based on session needs. **Do NOT load everything blindly.**

#### Tier 1 — ALWAYS load (every session)
- `memory/sessions/session_state.md` — where we left off (lifeline)
- `memory/user/user_profile.md` — who you're working with

#### Tier 2 — Load if resuming work or making decisions
- `memory/decisions/decisions.md` — don't re-ask settled questions
- `memory/projects/<active-project-slug>/memory-bank/activeContext.md` — current project state (per SCHEMA_A3)
- `memory/projects/<active-project-slug>/memory-bank/progress.md` — current project progress

#### Tier 3 — Load on demand (only when relevant)
- `memory/feedback/feedback.md` — when doing something with prior corrections
- `memory/security/vetting_log.md` — when installing tools or reviewing code
- `memory/references/references.md` — when needing a specific file pointer
- `memory/projects/<slug>/memory-bank/{projectbrief,productContext,systemPatterns,techContext}.md` — when working on project foundation/architecture
- Any other memory files referenced by session_state.md

### Step 1.3 — Self-Test Suite (run silently — only report failures)

| Test | What it checks | Failure severity |
|------|----------------|-------------------|
| **T1** | `memory/sessions/session_state.md` exists, has Schema Version header | CRITICAL — stop |
| **T2** | `memory/MEMORY_INDEX.md` exists; entry counts non-negative | CRITICAL — stop |
| **T3** | Session number in session_state.md is ≥ previous session number (no regression) | WARNING — ask user |
| **T4** | No memory file exceeds its size limit (see §11 File Size Limits) | INFO — consolidate |
| **T5** | All files referenced in MEMORY_INDEX.md actually exist on disk | WARNING — update index |
| **T6** | Schema Version in memory files ≤ protocol version (no future versions) | INFO — proceed with caution |
| **T7** | No PII/PHI patterns detected in memory files (SSN format, MRN format, emails outside user_profile) | CRITICAL — do not load affected file |
| **T8** | All entries have valid SCHEMA_A18 frontmatter (id, created_at, source_agent, status, schema_version) | WARNING — flag entries; quarantine if biotech |
| **T9** | Active edition profile (`<edition>/PROFILE.md`) is loaded and override-file map resolves | WARNING — proceed with common-spec only if overrides missing |

**Run silently.** Only report to user if failures occur. All-pass = no message.

### Step 1.4 — Greet and Orient

Brief greeting:
- "Last session we [X]. Ready to continue with [Y], or would you like to work on something else?"
- Mention active edition + compliance preset if first-time session in this deployment
- Mention any T1–T9 failures requiring user attention

Skip greeting if session_state.md indicates a mid-task continuation; just resume.

---

## 2. Context Budget (Tiered)

Manage context window like a resource. Budget varies by session complexity:

| Tier | Memory Budget | Typical Session |
|------|--------------|-----------------|
| **Tier 1** (simple tasks) | ≤15% of context | Quick fixes, single-file edits |
| **Tier 2** (standard work) | ≤30% of context | Feature development, multi-file changes |
| **Tier 3** (complex sessions) | ≤45% of context | Architecture changes, major refactors, reviews |

**Hard limits (always enforced):**
- **Reserved for work:** ≥25% of context must ALWAYS remain free for code, conversation, tool output
- **Absolute ceiling:** Memory files NEVER exceed 40% of context, regardless of tier
- **Escalation rule:** If Tier 1 budget insufficient, escalate to Tier 2. If Tier 2 insufficient, escalate to Tier 3. NEVER jump straight to Tier 3.
- **Emergency override:** If context critically low (<15% free), drop to Tier 1 only and warn user
- **Position-pinning (NEW v3.5):** Tier 1 entries injected at BOTH start AND end of bootstrap; mitigates U-shape attention rot. See §2.5 below.

### 2.5 — Context Rot Mitigation

**The problem.** Three independent studies (Redis, Chroma, Morph — 2025-2026) found that long context degrades non-linearly even BELOW the model's stated context limit. The attention pattern is **U-shaped**:

```
Attention strength
   ▲
   │ ██                                        ██
   │ ██                                        ██
   │ ██                                        ██
   │ ██░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░ ░░  ██
   │ ██                                        ██
   └─────────────────────────────────────────────► Position in context
     START      ← weak middle attention →      END
     ✓                                          ✓
```

Critical entries placed in the MIDDLE of a long context get less reliable recall, even when total context fits within the budget.

**The mitigation (per the context-rot research):**

Pin Tier 1 entries at **BOTH the start AND end** of the bootstrap injection. So instead of loading session_state.md + user_profile.md once at session start, the loading sequence becomes:

```
[BOOTSTRAP START]
  → Tier 1 entries (anti-rot start pin):
      • session_state.md (latest heartbeat)
      • user_profile.md (machine inventory + identity)
  → Tier 2 entries (loaded if relevant):
      • decisions.md, activeContext.md, etc.
  → Tier 3 entries (loaded on demand):
      • per-project memory-bank files
  → Tier 1 entries (anti-rot end pin) — RE-INJECTED:
      • session_state.md heartbeat (just the top-most slice)
      • user_profile.md identity section
[BOOTSTRAP END / USER TURN BEGINS]
```

**Why this works:** The end pin re-establishes recency. The model attends to it strongly even after long middle content. The start pin maintains the original semantic anchor. Together, they create a "context sandwich" that preserves critical state across positions.

**What gets pinned (default):**

| Tier | Pinned at start | Pinned at end | Rationale |
|---|---|---|---|
| **Tier 1** | ✓ | ✓ (NEW) | session_state heartbeat + user_profile identity — these MUST survive context rot |
| **Tier 2** | ✓ | ✗ | One-position injection acceptable; less critical for moment-to-moment recall |
| **Tier 3** | ✗ (on-demand) | ✗ | Loaded only when explicitly referenced; position-agnostic |

**End-pin content (compressed):** The end-pin can be a CONDENSED version (e.g., session_state heartbeat top section only, not the full file). Goal is recency anchoring, not full re-injection. Reduces budget impact while preserving rot mitigation.

**Edition behavior:**
- **Both editions:** Position-pinning applied. No edition-specific override (universal best practice).
- **Per-harness:** Implementation differs (see below).

**Implementation per harness:**

| Harness | Mechanism | v3.5 status |
|---|---|---|
| **Claude Code** | Memory Protocol auto-load behavior — bootstrap currently loads files once; v3.5 documents the pinning pattern. Mechanism for actual end-injection arrives in v3.6+ (requires hook into auto-load or system prompt restructure). | DOCUMENTED |
| **OpenClaw General Edition Adapter** | Adapter Skill controls injection sequence; end-pin via duplicate include in MEMORY.md tail OR HEARTBEAT.md regeneration at session-mid checkpoint | SHIPS in v3.5 via adapter |
| **Multi-Machine Sync (v4.0)** | Sync state can carry end-pin signature for cross-machine consistency | Future |

**Source citations (borrow ideas, not numbers):**
- [Redis context rot blog](https://redis.io/blog/context-rot/) — independent measurement
- [Morph context rot analysis](https://www.morphllm.com/context-rot) — independent measurement
- Chroma findings (context-rot research synthesis)

**What this does NOT mitigate:**
- Middle-position entries STILL get weak attention. Position-pinning only protects the entries that get pinned (Tier 1). Entries that need strong recall but lack tier-1 status should either be promoted (DEC promotion logic §12) or referenced via wikilink which prompts re-load.
- Doesn't reduce TOTAL context usage. End-pin adds budget cost (~1-3% of total). Trade-off: ~1-3% budget for substantially better recall on critical state.

**Validation strategy:** validation included exercising position-pinning behavior — confirm Tier 1 content survives 60K+ char middle content reliably.

---

## 3. Conflict Resolution Hierarchy

When memory files contradict each other, resolve in this order (highest authority wins):

1. **Compliance rules** (HIPAA, PII/PHI, regulatory — NEVER overridden)
2. **User's live instruction** (what the user just told you this session)
3. **Security decisions** (vetting verdicts, access restrictions)
4. **`feedback.md`** (explicit corrections override older decisions)
5. **`decisions.md` — FINAL** (settled decisions, confidence: FINAL)
6. **`session_state.md`** (most recent state)
7. **`decisions.md` — TENTATIVE** (provisional decisions, subject to revision)
8. **`project_context.md` / project memory-bank** (background context)
9. **`user_profile.md`** (general preferences, lowest specificity)

### Bi-temporal precedence (B5 — applies within levels 5–8)

When two entries at the same hierarchy level both apply, **bi-temporal validity wins**:
- If entry A has `invalid_at` set AND entry B (its successor via `supersedes`) is active → use entry B
- If user queries with explicit point-in-time → return entry valid at that timestamp:
  `valid_at ≤ query_time AND (invalid_at IS NULL OR invalid_at > query_time)`
- If both entries are simultaneously valid (overlap, no `invalid_at`) → escalate to user; do not guess

**Cross-machine bi-temporal (per `SCHEMA_sync_log.md`):** When entries with overlapping validity windows exist on multiple machines, `sync_log.jsonl` events capture `valid_at` + `content_sha256_before/after` + `parent_event_id` for full provenance chain. Conflict resolution still follows this hierarchy (§3 levels 1-9), but sync_log provides the cross-machine evidence base for resolution decisions.

**If a conflict cannot be resolved by this hierarchy, ASK the user. Do not guess.**

---

## 4. During-Session Protocols

### 4.1 Validation-on-Read (B8)

Every time a memory entry is loaded into context, validate before use:

1. **Frontmatter integrity** — parse YAML; require core fields (id, created_at, source_agent, status, schema_version)
2. **Schema version compatibility** — entry's schema_version ≤ protocol version (you)
3. **Status check** — refuse to load `status: quarantined` entries silently; flag them
4. **Expiry check** — if `expires_at < today` and entry is `status: active`, flag for revalidation (do not refuse to load; warn)
5. **Signature verification** (if C4 active at T3) — verify Ed25519/HMAC signature; quarantine on failure
6. **Provenance sanity check** — if `source_agent: webfetch` AND `last_validated < created_at + 1 day`, treat as PRELIMINARY; require orchestrator confirmation before promoting beyond initial use

**On validation failure:**
- Biotech edition: route entry to `memory/quarantine/`, log to audit, refuse to load
- General edition: log warning, prompt user with one-line toast, refuse to load unless user approves

### 4.2 Pattern-Key Promotion (B6)

For feedback and recurring observations:
- Each entry has `pattern_key` (stable dotted identifier) + `recurrence_count` (integer)
- When the same pattern_key is observed again, increment `recurrence_count`, update `last_seen`
- **Promotion threshold:**
  - **Biotech edition:** recurrence_count ≥ 3 → auto-promote to a standing rule in `.claude/rules/`
  - **General edition:** recurrence_count ≥ 5 → suggest promotion to the user
- Promoted patterns get a DEC entry capturing the source feedback chain

### 4.3 Wiki-Link Sync (T2+ when Node.js parser available; manual at T0–T1)

Within entry bodies, contributors may use `[[ID]]` wiki-links (Obsidian convention) to reference other entries inline.

- **At T0–T1:** YAML `related` / `supersedes` are CANONICAL. Inline `[[ID]]` is supplemental human-friendly form. Manual sync — both should be present.
- **At T2+ (Node.js indexer):** Auto-parse `[[ID]]` from body, populate YAML `related` field. Two-way sync.

When generating a new entry, populate BOTH the YAML field and (if mentioning in prose) the inline wiki-link form. Do not generate orphan inline links without a YAML counterpart.

### 4.4 Heartbeat Checkpoint (every ~30 minutes of active work)

Update `memory/sessions/session_state.md` → "Current Work" section with a brief status note. Prevents context loss if session ends unexpectedly (laptop lid close, browser crash, /compact mid-task).

Heartbeat content should include:
- Current task name + sub-step (if any)
- File(s) being modified with line numbers
- Specific blocker if any
- Updated timestamp

---

## 5. Write Operations

### 5.1 CAS-Style Concurrency (B3)

For **replace-class** operations (str_replace, insert into existing entry):
1. Read current entry; compute `content_sha256` of body **using canonical normalization** (see SCHEMA_A18 §"`content_sha256` normalization")
2. Compare to `content_sha256` field in entry's frontmatter
3. If mismatch → another writer modified the entry; refuse write, ask user
4. If match → proceed; update body; recompute `content_sha256` using canonical normalization; update frontmatter

**Canonical normalization (one-liner — must match across all agents):**
```python
body = file_text.split('---', 2)[2].lstrip('\n')
content_sha256 = hashlib.sha256(body.encode('utf-8')).hexdigest()
```

- `lstrip('\n')` is REQUIRED — without it, cross-agent hashes diverge for byte-identical files (Stage 3 verification 2026-06-02 found this empirically)
- UTF-8 encoding, no BOM
- LF line endings preserved; do NOT normalize CRLF↔LF
- Trailing whitespace preserved; do NOT rstrip

See SCHEMA_A18 §"`content_sha256` normalization" for full spec + backwards-compat notes.

**Append-only writes don't need CAS** (new entries, new audit log lines, new quarantine records). The CAS check applies only when overwriting existing content.

### 5.2 Audit Log Writes (B1)

Every memory write produces an entry in `memory/security/audit_log.jsonl`:

```jsonl
{"ts":"2026-05-14T15:30:00Z","actor":"orchestrator","session":7,"action":"write","entry_id":"DEC-024","entry_summary":"<first-200-chars>","content_sha256_before":"...","content_sha256_after":"...","outcome":"success"}
```

**Biotech edition:** REQUIRED on every write (including reads-for-validation if SCHEMA_audit_log.md so configures). Non-overridable.

**General edition:** OPT-IN; default OFF. User enables via `audit_log: true` in compliance profile.

**Do NOT log entry content** — only summaries (first 200 chars) to keep log size manageable and PHI-free.

### 5.3 Quarantine Routing (B2)

If validation-on-read (§4.1) fails for an entry:
1. Move entry to `memory/quarantine/<original-category>/<entry-id>.md` (preserve provenance)
2. Append quarantine record to `memory/quarantine/quarantine_log.jsonl`
3. Set entry's `status: quarantined` in frontmatter
4. Log to audit log per §5.2

**Biotech edition UX:** Surface quarantine via `/audit-quarantine` — review workflow with batch approve/reject. Entries cannot be released without explicit user approval.

> **Implementation note:** `/audit-quarantine` ships as a **packaged Skill artifact** at `core/audit-quarantine-skill/`.
>
> The Skill includes:
> - `SKILL.md` — 9-step Claude-executable workflow (load entries → review → apply decisions → log)
> - `README.md` — full documentation discipline
> - `INSTALL_AUDIT_QUARANTINE_SKILL.md` — manual fallback for non-Skill environments
> - `scripts/review_quarantined.py` — standalone Python CLI equivalent
>
> Both biotech and general-edition UX (full workflow vs toast notification) are supported.

**General edition UX:** One-line toast at session start: "X entries quarantined since last session — review?" with quick approve/reject inline.

### 5.4 Bi-Temporal Supersession (B5)

When a new entry supersedes an older one:
1. New entry has `supersedes: <old-entry-id>` in frontmatter
2. Old entry gets `invalid_at: <today>` set automatically; `status` flipped to `superseded`
3. Old entry's body remains untouched — history preserved
4. Forward pointer: old entry gets `superseded_by: <new-entry-id>`

**This is the Graphiti pattern**: contradictions don't delete history; they mark validity boundaries. Enables point-in-time queries (§3 bi-temporal precedence).

**Cross-machine extension (per `SCHEMA_sync_log.md`):** Supersession events that cross machine boundaries are captured in `memory/security/sync_log.jsonl` with `parent_event_id` linking the original `supersedes` event to its sync-related propagation. See `SCHEMA_sync_log.md` §6.4 for full cross-machine bi-temporal semantics. (Implementation is a future deliverable; the schema ships now.)

---

## 6. Edition Profile Application (B4 + B7)

### 6.1 Override-File Precedence

For every common-spec file `common-specs/X.md`, check for an override at `<edition>/overrides/X.override.md`:
- If override file exists, parse its sections
- For each section header in the override, REPLACE the same-named section in the common-spec
- Other sections inherit from common-spec unchanged

**Example:**
- `common-specs/MEMORY_PROTOCOL.md` (this file) defines `§5.3 Quarantine Routing`
- `biotech-edition/overrides/MEMORY_PROTOCOL.override.md` overrides `§5.3 Quarantine Routing` with biotech-specific workflow details
- Other sections of MEMORY_PROTOCOL.md inherit unchanged

### 6.2 Compliance Preset (B7)

Active compliance preset (from PROFILE.md) selects detection patterns + redaction rules + audit defaults:

| Preset | What activates |
|--------|----------------|
| `none` | No regulatory detection. Standard hygiene only (secrets, credentials). Lowest friction. |
| `healthcare` | Full PHI detection (MRN, specimen IDs, accession numbers, genomic identifiers). Redact-on-sight. Audit log default ON. Biotech: non-overridable. |
| `enterprise` | GDPR + SOC2 baseline — provenance + audit + consent tracking. Hard delete with recovery window. |
| `custom` | Compliance is fully configured via `<edition>/overrides/compliance.override.md` — fine-grained for power users. |

Active preset is **always logged** to session_state.md at session start.

---

## 7. Standing Rules (Always Active, Cannot Be Overridden by Session Instructions)

- **NEVER** store passwords, API keys, tokens, secrets in memory files
- **NEVER** store sensitive personal information (SSN, credit cards, financial account numbers)
- **NEVER** store PII/PHI in memory files (patient data, MRNs, specimen IDs, genomic identifiers) — regardless of edition or compliance preset
- **When in doubt about whether to remember something, remember it** — user can always tell you to forget
- **Be specific in `session_state.md`** — vague notes are useless. Say exactly what file, function, line, issue.
- **If memory files seem stale or contradictory**, use the §3 Conflict Resolution Hierarchy. If still unresolved, ASK.
- **Every memory write produces a frontmatter-compliant entry** per SCHEMA_A18 — no orphan entries lacking metadata
- **Every memory file declares its Schema Version** — never silently upgrade. Migration is explicit (§13).

---

## 8. Risk Scoring (for high-impact tasks)

Before executing high-impact tasks (deleting files, modifying configs, restructuring code, bulk operations), assess risk using this 6-factor rubric:

| Factor | LOW (1) | MEDIUM (2) | HIGH (3) | CRITICAL (4) |
|--------|---------|------------|----------|---------------|
| **Blast Radius** | 1 file | 2-5 files | 6-20 files | 20+ files / system-wide |
| **Reversibility** | Easy undo (git) | Moderate (manual rollback) | Hard (data loss possible) | Irreversible |
| **Protected Files** | None affected | Config files | Credentials/env files | Production data |
| **Test Coverage** | Fully tested | Partially tested | Untested | No tests exist |
| **Novelty** | Done this before | Similar to past work | First time, understood | First time, uncertain |
| **User Data Impact** | No user data | Read-only access | Modifies user data | Deletes user data |

**Scoring rule:** Take the MAX score across all 6 factors (not the average).
- **LOW (1):** Proceed normally
- **MEDIUM (2):** Mention the risk to user, proceed if acknowledged
- **HIGH (3):** Explain the risk, get explicit approval before proceeding
- **CRITICAL (4):** STOP. Present the risk assessment. Do NOT proceed without explicit user instruction.

---

## 9. Cascade Failure Detection

If you encounter **3 or more unrelated errors within 5 minutes**, STOP all work immediately.

**Do NOT attempt to self-repair.** Instead:
1. Stop executing tasks
2. Report to user: "I've hit multiple unrelated errors in a short window. This may indicate an environmental issue rather than a code problem."
3. List the errors with timestamps
4. Suggest environment diagnostics (disk space, network, running processes, mounted drives, etc.)
5. Wait for user instruction before continuing

**Rationale:** Prevents cascading damage from environmental failures (out of disk space, network blips, corrupted tools, mounted drive unmount mid-write).

---

## 10. Self-Trimming Protocol (Every 10 Sessions)

Run during consolidation. **Suggestions only — never auto-delete or auto-archive.**

| Condition | Suggestion |
|-----------|------------|
| File not accessed in 15+ sessions | Suggest archiving |
| Low-value TENTATIVE decisions not referenced in 10+ sessions | Suggest cleanup |
| File at 80%+ of size limit | Suggest split or archive |
| Quarantined entries older than 90 days | Suggest user review |
| Pattern-keys with `recurrence_count` 1 unchanged for 30+ days | Suggest cleanup (likely one-offs) |

**Exempt from trimming (never suggest):**
- Security entries in `vetting_log.md` (audit trail must be preserved)
- FINAL decisions (settled — they stay until user says otherwise)
- User profile (always relevant)
- Standing rules in this protocol
- Audit log entries (`memory/security/audit_log.jsonl`) — append-only, archive by date only

**Bi-temporal note (B5):** Self-trimming does NOT delete superseded entries — those have `invalid_at` set but body preserved. Archiving moves them to `memory/archive/`; the bi-temporal record is intact.

---

## 10.5 Lint Operation (Karpathy LLM Wiki Pattern)

Periodic memory integrity scanner. **Complementary to §10 Self-Trimming** — Self-Trimming is usage-based (last-accessed); Lint is integrity-based (cross-entry checks). Both run during consolidation passes.

**Full spec:** See `SCHEMA_lint.md` for complete schema, workflow, and configuration details.

### Lint Checks (6 original + 5 NEW v3.5 self-improvement extension = 11 total)

#### 6 original Lint checks

| Check | Tier | What it finds |
|-------|------|---------------|
| Orphan entries | T0 | Entries with no incoming `[[ID]]` or `related:` references |
| Broken references | T0 | `[[ID]]` or `supersedes:` pointing to non-existent entries |
| Stale TENTATIVE/EXPLORATORY | T0 | Non-FINAL decisions not revisited in N sessions |
| Stale webfetch citations | T0 | `source_agent: webfetch` entries with `last_validated > Y days ago` |
| Cross-entry contradictions | T3 | Semantically conflicting active entries without supersession chain |
| Missing concept entries | T3 | Concepts repeatedly mentioned without dedicated reference entries |

#### 5 self-improvement Lint checks

These five checks extend the lint pass toward *self-improvement detection* —
surfacing where the memory base could be tidied, merged, or promoted. They are
deliberately **detection-only**: like the original six checks, lint NEVER
auto-fixes — it surfaces findings for the user to decide on. (A self-modifying
"auto-apply" loop was considered and rejected for its reward-hacking risk; the
value worth keeping is the *detection*, not automatic rewriting.)

| # | Check | Tier | What it finds | Detection logic |
|---|---|---|---|---|
| 7 | **Promotion candidates approaching threshold** | T0 | Entries near §12 PageRank trigger but not yet qualifying | `access_count ≥ 4` AND `len(recent_sessions) ≥ 2` (one short of `≥5` AND `≥3` thresholds). Surfaces "next promotion candidates" for proactive review. |
| 8 | **Pattern condensation opportunities** | T3 | Multiple decisions on same topic across entries — supersession/merge candidates | Cluster entries by shared tags + cross-references; if cluster size ≥3 entries with overlapping topic + all `status: active`, suggest merge candidate. LLM-assisted for semantic similarity. |
| 9 | **Naming inconsistencies** | T3 | Same concept referred to differently across entries — canonical-naming candidates | Tokenize entry bodies; flag candidate-pairs with high textual overlap but different surface terms (e.g., "decision log" vs "decisions.md" vs "DEC log"). LLM-assisted for synonym detection. |
| 10 | **Documentation completeness gaps** | T0 | Entries missing documentation-discipline elements (Purpose / Rationale / Sound Reasoning / Scope CAN / Scope CANNOT) | For each entry with `scope: entry`: grep for the 5 required headers. Flag entries missing any. Severity scales with missing-count. |
| 11 | **Standing-rule candidates** | T3 | Patterns observed in multiple sessions that could become standing rules per §7 | Cluster feedback (FB-NNN) entries + observation logs by topic; if cluster ≥3 feedback events across ≥3 sessions, suggest promotion to standing rule. LLM-assisted for pattern detection. |

**Design principle:** these checks expand WHAT lint detects, not HOW it acts.
Every finding is read-only and recorded as an entry in `lint_runs.jsonl`; the
user reviews it and decides whether to act. No file is modified by the lint
pass itself.

#### Edition behavior (5 new checks)

| Check | biotech-edition | general-edition |
|---|---|---|
| 7 Promotion candidates | ✅ Enabled (cadence: weekly) | ✅ Enabled (cadence: monthly) |
| 8 Pattern condensation | ✅ Enabled (T3 — needs LLM) | ⚠️ Opt-in (Tier C) |
| 9 Naming inconsistencies | ✅ Enabled (T3 — needs LLM) | ⚠️ Opt-in (Tier C) |
| 10 Doc completeness gaps | ✅ Enabled — CRITICAL severity (HIPAA forensics demand documentation-discipline compliance) | ✅ Enabled — MEDIUM severity |
| 11 Standing-rule candidates | ✅ Enabled | ⚠️ Opt-in (Tier C) |

#### Maturity

- The **surfacing layer** ships now: the memory subagent (per the §10.5
  Execution Model) runs all five checks alongside the original six.
- Checks 8, 9, and 11 use LLM-assisted semantic detection; lightweight
  pattern-match versions ship today, with fuller semantic versions planned.
- A findings-triage flow (navigate findings, approve/reject promotion
  candidates one at a time) is planned.

### Trigger Mechanisms

- **Manual:** `/lint-memory` slash command (runs immediately; outputs to chat + logs to `memory/security/lint_runs.jsonl`)
- **Auto biotech:** Weekly cadence; if last run >7 days ago, runs at session start; HIGH/CRITICAL findings block new writes until reviewed (matches the biotech quarantine pattern)
- **Auto general:** Monthly cadence; surfaces as toast at session start; non-blocking; user opts in to review or defers

### Surface-Only Design

Lint NEVER auto-fixes findings. It surfaces problems and suggests remediations. The user decides whether to act.

This matches `eslint --no-fix` philosophy — Lint is a checker, not an editor.

### Execution Model — Memory Subagent

**Lint runs in a memory subagent, NOT in the orchestrator's inline context.** This pattern is borrowed from Subagent Context Isolation (LangChain subagents, AgentSys, Claude Code's flat sub-agent hierarchy) and applies the consuming architecture's modular agent topology.

**Why subagent execution:**
- **Parent context savings** — Lint's intermediate analysis (parsing 6 checks across entries, scoring findings) does NOT pollute the orchestrator's working memory. Vault returns only the structured findings.
- **Audit log clarity** — Vault's full analysis log lives separately at `memory/security/lint_runs.jsonl`; orchestrator's audit_log gets a single `lint-run` action entry.
- **Tier-aware execution** — Vault can run Lint at lower context priority without competing with orchestrator's Tier 1 session work.
- **Mirrors OpenClaw equivalent** — OpenClaw's `sessionTarget: "isolated"` for cron-driven memory ops provides the same isolation; v3.5 lint matches that pattern for cross-stack consistency.

**Execution flow:**

```
1. Orchestrator receives trigger (manual /lint-memory, auto-cadence, or consolidation pass)
   ↓
2. Orchestrator spawns Vault subagent:
     - subagent_type: "general-purpose"
     - allowed tools: Read, Write, Edit, Glob, Grep (per agent_orchestration.md)
     - explicit instructions: "Run 6 Lint checks against memory/; return structured findings JSON"
   ↓
3. Vault subagent executes:
     - Loads memory/ files into ITS OWN context (not parent's)
     - Runs the 6 checks (4 deterministic + 2 LLM-assisted at T3)
     - Writes detailed analysis to memory/security/lint_runs.jsonl (Vault has Write tool)
     - Returns to orchestrator: { findings: [...], summary: "...", severity_counts: {...} }
   ↓
4. Orchestrator receives findings:
     - Surfaces to user per edition mode (chat output / toast / blocking on biotech CRITICAL)
     - Appends single "lint-run" entry to audit_log.jsonl per B1
     - Does NOT see Vault's intermediate analysis (Vault context discarded)
```

**Backward compatibility (v3.0 → v3.5):**

Both modes work. v3.0 deployments that ran Lint inline continue to work; v3.5 deployments default to Vault subagent execution. The protocol does not REQUIRE subagent execution — it RECOMMENDS it. Lint output format is identical either way.

**Constraints (per agent_orchestration.md):**
- **Vault + Clerk parallel** — NOT allowed (both write to logs). When Lint runs, no parallel Clerk task work.
- **Vault + Sentinel parallel** — Allowed (Sentinel reads only; no log write contention).
- **Vault read-only mode** — Vault has Write/Edit tools BY NECESSITY for `lint_runs.jsonl` writes. Lint findings ARE written by Vault directly; orchestrator only writes the audit_log summary entry.

**OpenClaw equivalent (Adapter compatibility):**

In the OpenClaw General Edition Adapter, Lint runs as a Skill with `metadata.openclaw.sessionTarget: "isolated"`. OpenClaw's existing cron infrastructure handles scheduling. The findings JSON format is identical to Claude Code's Vault subagent output, enabling cross-stack tooling.

**Implementation roadmap:**
- **v3.5 ships the PROTOCOL** (this update) — execution model documented; orchestrator behavior specified
- **v3.5 ships the agent template update** — `agents/memory_stack_agent.md` Vault prompt gains explicit Lint workflow section
- **v3.6+ ships the SLASH COMMAND wiring** — `/lint-memory` invocation auto-spawns Vault subagent; OpenClaw adapter ships ClawHub Skill

### Output Log

`memory/security/lint_runs.jsonl` — append-only JSONL log of each lint run + findings. Format per SCHEMA_lint.md §4.1.

Retention:
- **Biotech:** 365 days minimum (HIPAA forensic completeness)
- **General:** 90 days default; configurable

### Edition Configuration

Per-edition PROFILE.md gains a `lint:` config block:

```yaml
# Biotech (non-overridable cadence/mode)
lint:
  cadence: weekly
  mode: auto
  blocking_on_critical: true
  retention_runs_days: 365
  thresholds:
    stale_tentative_sessions: 10
    stale_webfetch_days: 30
    orphan_minimum_age_sessions: 5
  checks_enabled:
    orphan: true
    broken_ref: true
    stale_tentative: true
    stale_webfetch: true
    contradiction: true            # T3 required
    missing_concept: true          # T3 required

# General (configurable; defaults shown)
lint:
  cadence: monthly
  mode: suggested
  blocking_on_critical: false
  retention_runs_days: 90
  thresholds:
    stale_tentative_sessions: 20
    stale_webfetch_days: 90
    orphan_minimum_age_sessions: 10
  checks_enabled:
    orphan: true
    broken_ref: true
    stale_tentative: true
    stale_webfetch: true
    contradiction: false           # opt-in for general
    missing_concept: false         # opt-in for general
```

### Integration with Existing Workflows

- **Audit log integration (B1):** Every lint run logs a `lint-run` action to audit_log.jsonl
- **Quarantine integration (B2):** HIGH-severity contradictions may route to quarantine for biotech-edition (per `SCHEMA_quarantine.md` §6 reason codes — `lint-contradiction` is a valid reason)
- **Self-trimming (§10) complementarity:** Findings overlap (e.g., orphan + low-value TENTATIVE) — surface once across both, not twice
- **Bi-temporal (B5) handling:** Contradictions in explicit `supersedes:` chains are NOT flagged by Lint (the chain itself resolves them); Lint catches contradictions that lack explicit chains

### When To Run Lint

- Whenever the user invokes `/lint-memory`
- Per-edition auto-cadence at session start (biotech weekly; general monthly)
- During consolidation pass (every 10 sessions per §10) — run alongside self-trimming

### What Lint CANNOT Do

- Auto-fix any finding (surface-only by design)
- Delete entries (only suggest archiving)
- Replace user judgment
- Operate without `memory/` directory existing
- Pre-emptively prevent rot at write-time (that's Layer 2 quarantine's job)

---

## 11. File Size Limits

> **Caps reflect realistic SCHEMA_A18 frontmatter overhead** (~12 lines per entry). Cap raises are documented in the calibration history (see CHANGELOG.md). Archive content to `memory/archive/` when caps approached; archival preserves history while keeping operational files responsive.
>
> **Enforcement upgrade:** Caps below were ADVISORY in v3.0; they are now **enforced hard errors** at write-time. See §11.5 for enforcement model + remediation + override semantics + legacy file handling.

| File | Max Size | Action When Exceeded |
|------|----------|---------------------|
| `sessions/session_state.md` | 1500 lines | Archive old session summaries to `memory/archive/sessions/` (cap raised from 150 → 1500; realistic 7-session active state with heartbeats + decisions accumulates 1000+ lines) |
| `decisions/decisions.md` | 1500 lines | Move FINAL decisions older than 20 sessions to `memory/archive/decisions/` (cap raised from 200 → 1500; SCHEMA_A18 frontmatter adds ~12 lines per entry × 38 entries = ~456 lines pure overhead before content) |
| `feedback/feedback.md` | 300 lines | Consolidate repeated feedback into standing rules (wizard initialization with 12 FB entries is ~293 lines) |
| `projects/project_context.md` | 400 lines | Split paused projects to archive; promote active projects to per-slug memory-banks per SCHEMA_A3 (newer cap; SCHEMA_A18 + 11 entries = ~220 lines minimum) |
| `projects/<slug>/memory-bank/*.md` | 300 lines each | Split if a single file grows; activeContext.md should rotate to progress.md frequently (cap raised from 200 → 300; SCHEMA_A3 6-file structure with frontmatter benefits from extra room) |
| `user/user_profile.md` | 100 lines | Should rarely grow — consolidate if it does (realistic populated content is ~82 lines) |
| `security/vetting_log.md` | 400 lines | Archive entries older than 1 year (cap raised from 200 → 400; SCHEMA_A18 + 13 vetting/CR entries = ~260 lines minimum) |
| `security/audit_log.jsonl` | 50,000 lines | Rotate to `security/audit_log_<YYYY-MM>.jsonl`, gzip old months |
| `references/references.md` | 100 lines | Split by domain (per-project, per-tool) |
| `MEMORY_INDEX.md` | 150 lines | Should stay small — it's just pointers (cap raised 80 → 100 → 150; Recent Entries sections accumulate over time, ~138 lines for 7 sessions tracked is realistic) |

### 11.5 — Enforcement Model

**v3.0 behavior:** Caps were **advisory** — the protocol documented them but no mechanism enforced them. Files could grow indefinitely; the "Action When Exceeded" column was a suggestion, not a gate.

**Documented real-world failure:** In one observed deployment, a heartbeat file grew to 16K+ characters violating its own "keep tiny" rule. The advisory model didn't prevent this — manual discipline failed.

**v3.5 behavior:** Caps become **enforced hard errors** at write-time. Pre-write check blocks writes that would cause overflow. Remediation required before write completes.

#### Pre-write enforcement

Before any write operation (`write_file`, `Edit`, `Edit replace_all`, append) to a memory file with a §11 cap:

```
1. Read current file line count (or byte count for .jsonl files)
2. Estimate post-write size: current_size + delta_from_write
3. If post-write size > cap:
   → HARD ERROR — block the write
   → Surface error message with remediation path
   → Do NOT silently truncate (anti-pattern; defeats audit)
   → Do NOT silently allow (defeats enforcement)
4. If post-write size > 90% of cap:
   → WARNING (allow write, but advise consolidation)
5. If post-write size ≤ 90% of cap:
   → Allow write normally
```

#### Error message format

When a write is blocked:

```
✗ HARD CAP EXCEEDED — Write blocked
  File: memory/sessions/session_state.md
  Current size: 1487 lines
  Attempted write: +24 lines
  Post-write would be: 1511 lines
  Cap: 1500 lines (§11)

  Required action before retry:
  1. Archive old session summaries to memory/archive/sessions/
     (action specified in §11 table for this file type)
  2. Reduce current file to ≤ 1450 lines (leave 50-line buffer)
  3. Retry the write

  Override (use sparingly):
  • Set MEMORY_PROTOCOL_OVERRIDE=cap-bypass in environment
  • OR: invoke /override-cap slash command
  • Override is logged to audit_log.jsonl as compliance_handling: cap-override
```

The error gives the user actionable remediation (archive instructions per the §11 table's "Action When Exceeded" column) AND an explicit override path for emergencies.

#### Edition behavior

| Edition | Default mode | Override mechanism | Audit |
|---|---|---|---|
| **biotech-edition** | Hard error (non-overridable in healthcare preset) | Requires admin token via `compliance.healthcare.cap_override_admin_token` config | Override logged to audit_log; HIPAA forensic complete |
| **general-edition** | Hard error (user-overridable) | `/override-cap` slash command OR env var | Override logged to audit_log if audit_log enabled per B1 opt-in |

#### Backward compatibility (legacy over-cap files)

**Problem:** Existing v3.0 deployments may have files already over cap (e.g., a migration test surfaced 5 files over cap).

**Solution:** Grace period via Lint surfacing.

- At v3.5 deployment: file size scanner runs once; files already over cap get marked `legacy_overflow: true` in their file-level frontmatter (per SCHEMA_A18 v1.3 `scope: file` field)
- Legacy over-cap files: read-allowed, write-allowed (no new content), append-allowed up to a freeze cap (1.25× normal cap), then HARD ERROR
- Lint operation (§10.5) surfaces legacy_overflow files in every weekly/monthly run as remediation candidates
- Once user manually archives the file below cap, `legacy_overflow` flag clears

This prevents v3.5 deployment from immediately blocking productive work on day 1 while still pushing toward enforcement.

#### Special case: append-only JSONL logs

Files like `audit_log.jsonl` and `quarantine_log.jsonl` have larger caps (e.g., 50,000 lines for audit_log) AND automatic rotation behavior (per §11 table "Action When Exceeded" column).

For these files:
- Cap is enforced (hard error if exceeded)
- BUT rotation happens AUTOMATICALLY when 80% threshold reached (not on hard-error-block)
- Rotation creates `<filename>_<YYYY-MM>.jsonl.gz` archive; current file resets to empty
- User never blocked by these caps in practice — rotation pre-empts overflow

#### Implementation roadmap

- **v3.5 ships the PROTOCOL** (this update) — enforcement behavior specified; error format documented
- **v3.5 ships the ENFORCEMENT in setup scripts** — `setup.sh` / `setup.py` / OpenClaw adapter Skill all do pre-write check
- **v3.5 ships the legacy-overflow flag** — file-level frontmatter `legacy_overflow: true` populated at deploy-time scan
- **v3.6+ ships hooks** — write-guard.sh hook checks caps for shell-driven writes; PreToolUse hook for Edit/Write tool invocations

#### Validation strategy

Cross-machine validation includes exercising:
- Hard error fires when expected
- Error message format correct + actionable
- Override mechanism works
- Audit log entry created on override
- Legacy over-cap files accept reads + minor appends but not bulk writes
- Auto-rotation triggers for JSONL logs at 80% threshold

---

## 12. Decision Promotion Pattern

### 12.1 — Inline → promoted (current rule, augmented v1.4)

- **New decisions** start inline in `memory/sessions/session_state.md` under "Active Decisions"
- Promote to `memory/decisions/decisions.md` with explicit DEC-### IDs when **ANY** of the following triggers fire:

| # | Trigger | Source | Notes |
|---|---|---|---|
| **A** | Topic accumulates **>5 related decisions** in session_state.md | Original v3.0 rule | "Heavily discussed" signal — qualitative |
| **B** | Pattern-Key `recurrence_count` ≥ **3** (biotech) or ≥ **5** (general) | §4.2 Pattern-Key Promotion | Biotech is stricter |
| **C** | Single entry's `access_count` ≥ **5** AND `len(recent_sessions)` ≥ **3** | NEW v1.4 — SCHEMA_A18 access tracking fields | **PageRank-style "heavily referenced" signal** |
| **D** | User explicitly marks via `/promote-entry` slash command | User override | Manual escape hatch |

**Either signal A, B, C, or D qualifies — OR logic.** This is by design: heavily-discussed AND heavily-referenced are independent indicators of durability; either alone is sufficient grounds for promotion.

### 12.2 — When promoting

  - Merge duplicates (keep most recent confidence)
  - Keep only the latest FINAL per topic
  - Remove superseded TENTATIVE entries (or set their `invalid_at` if you want bi-temporal history)
- Promoted decisions get full SCHEMA_A18 frontmatter at promotion time (not inherited from session_state — fresh assignment)
- **NEW v1.4:** If promoting via trigger C (PageRank signal), the entry's existing `access_count`, `last_accessed`, and `recent_sessions` carry over (they represent its access history; don't reset).

### 12.3 — PageRank signal sourcing (NEW v1.4)

The PageRank signal (trigger C) depends on SCHEMA_A18 v1.4+ access tracking fields. Operationally:

- **`access_count` and `recent_sessions`** are populated by runtime hooks at Tier 1/2/3 load + memory_search query result events. The schema ships now; the auto-incrementer is a future deliverable (or arrives via OpenClaw heartbeat-driven compaction).
- **Baseline:** counters are populated manually (the user edits the field) OR retroactively computed from `audit_log.jsonl` if available OR initialized to defaults and accrued from this point forward.
- **Lint operation (§10.5)** surfaces entries near the PageRank threshold (`access_count` ≥ 4 AND `len(recent_sessions)` ≥ 2) as "candidates approaching promotion" — gives the user visibility into emerging promotion candidates before they auto-qualify.

### 12.4 — Rationale

The PageRank signal addresses a documented gap: in one observed OpenClaw deployment, heavy-reference entries should have promoted earlier but didn't because:
- They weren't part of a topic cluster (Trigger A didn't fire)
- They didn't have a Pattern-Key (Trigger B didn't fire)
- They lacked a manual promotion trigger (Trigger D didn't fire)

But they WERE heavily-referenced (e.g., cron architecture details stayed inline at 2K chars instead of promoting to a detail file). Adding Trigger C catches this case.

Borrowed pattern from Aider's repo-map PageRank algorithm — files heavily-referenced in code get boosted weight (borrow ideas, not numbers). Here applied to memory entries.

### 12.5 — Edition behavior

Both editions accept Triggers A/B/C/D identically. The only edition difference is Trigger B's threshold (3 for biotech vs 5 for general per §4.2). PageRank signal (Trigger C) uses same thresholds in both editions for now; may be tuned per-edition in future revisions if data warrants.

---

## 13. Schema Migration

If a memory file's `schema_version` is older than this protocol's version:
1. **Do NOT silently upgrade** — schema migration must be explicit
2. **Inform the user** before migrating: "File X is at schema_version Y; protocol is at Z. Migrate now?"
3. **Migration is additive** — preserve all existing content; add new frontmatter fields with sane defaults
4. **Log the migration** as a DEC entry in `decisions.md` with the migration script reference
5. **Backup before migrating** — copy old file to `memory/archive/migrations/<file>.v<old-version>.md`

**v2.0 → v3.0 specific:** Adds YAML frontmatter to entries lacking it; treats them as legacy with `confidence: FINAL`, `status: active`, `created_at: <file-mtime>`, `schema_version: "2.0"`. The migration procedure lives in the edition's `MIGRATION_v2_to_v3.md`.

---

## 14. Session End Protocol

Triggered when user says: "wrap up", "end session", "save state", "session end", or similar.

1. **Update `memory/sessions/session_state.md`** with:
   - What we accomplished this session (specific — file names, line numbers, decisions made)
   - What's still in progress (BE SPECIFIC — exact file, function, line, status)
   - What should happen next session
   - Any decisions made (with confidence levels + DEC-### IDs if promoted)
   - Carry-overs that did not complete

2. **Update other changed memory files**:
   - `decisions.md` (new decisions promoted from session_state inline section)
   - `feedback/feedback.md` (any new corrections)
   - `projects/<slug>/memory-bank/activeContext.md` (if project work done)
   - `projects/<slug>/memory-bank/progress.md` (if status changed)
   - `security/vetting_log.md` (if vetting performed)
   - `security/audit_log.jsonl` (closing summary entry)
   - `MEMORY_INDEX.md` (entry counts, last-updated dates)

3. **Run consolidation pass** if it's been 10+ sessions since last:
   - Check file size limits (§11)
   - Run self-trimming suggestions (§10)
   - Update `Last Accessed` columns in MEMORY_INDEX.md
   - Present suggestions to user; await approval

4. **Mirror parity check**: if the deployment mirrors its files, verify canonical and mirror sizes match for all common-specs files. Report any drift.

5. **Brief summary to user**: 1-2 sentences on what was saved + any pending items for next session.

---

## 15. Compaction-Safe Handoff

If `/compact` is invoked mid-session (or auto-compaction triggers near context limit):

**Before compaction:**
- Heartbeat session_state.md (§4.4) — capture current task, file, line, blocker
- Ensure all in-flight DEC entries are persisted
- Mirror parity check

**After compaction:**
- Re-read Tier 1 + Tier 2 files (auto-restoration)
- Verify session_state.md heartbeat is current
- Smoke-test recall: can you answer "what were we just working on?" from the heartbeat
- Resume from heartbeat's "Current Work" section

**This protocol IS the auto-restoration mechanism.** Memory Protocol auto-loads at session start; reads session_state.md (Tier 1 always); restores you to the post-heartbeat state. No manual relay needed.

---

## 16. Documentation Discipline (Standing Rule)

Every memory entry that captures a decision, feature, schema, or pattern MUST carry:

- **Purpose** — what's the user-facing goal?
- **Rationale** — why this approach over alternatives?
- **Sound reasoning** — what evidence/research/decisions back this?
- **Scope (CAN)** — what it does
- **Scope (CANNOT)** — explicit boundaries

This applies to:
- DEC entries (already so structured in v2.0)
- New schemas (SCHEMA_*.md files)
- New protocol sections (this file)
- Feature additions in BOOTSTRAP_PROMPT.md
- Standing rules (in this file)

Undocumented features do NOT ship. If a feature lacks any of the 5 elements, flag it; either document or remove.

---

## 17. Healthcare Compliance Profile (Active When `compliance: healthcare`)

**Activated by:**
- Biotech edition (mandatory, non-overridable per B7)
- General edition with `compliance: healthcare` preset

### Detection triggers (activate this profile when encountering)
- Patient identifiers (MRN, specimen IDs, accession numbers, hospital IDs)
- Genomic data (variant calls, gene names linked to patients, sequencing results, FASTQ headers)
- Clinical data (diagnosis codes, treatment records, lab results, pathology reports)
- File paths containing `PHI`, `patient`, `clinical`, `HIPAA`, `MRN`, or similar keywords

### When activated
- **NEVER** store detected identifiers in memory files — not even as examples or in comments
- **NEVER** include patient data in session summaries, decision logs, feedback, or audit log entry summaries
- **Redact on sight:** If patient data appears in tool output, note `[REDACTED — PHI detected]` in any memory entry
- **Warn the user:** "I've detected what may be protected health information. I will not store this in memory files. Please confirm if this data requires HIPAA handling."
- **Log the event (NOT the data)** to `memory/security/vetting_log.md`: date, type of data detected, action taken
- **Set `compliance_handling: phi-redacted`** in the frontmatter of any entry that encountered (and redacted) PHI

### Standing compliance rules (active regardless of profile)
- No PII/PHI in memory files — ever
- No specimen IDs, MRNs, or genomic identifiers in session state
- If unsure whether data is PHI, treat it as PHI

---

## 18. Cross-References

- **Schemas:** `SCHEMA_A3_per_project_memory_bank.md`, `SCHEMA_A18_per_entry_metadata.md`, `SCHEMA_audit_log.md`, `SCHEMA_quarantine.md`, `SCHEMA_compliance_profile.md`, `SCHEMA_lint.md`, `SCHEMA_sync_log.md`
- **Architecture:** `ARCHITECTURE.md` (Layer 0-6 + adjacent tools, deployment tier markers)
- **Bootstrap:** `BOOTSTRAP_PROMPT.md` (one-time activation, copy this file to `.claude/rules/`)
- **Edition profiles:** `<edition>/PROFILE.md` (PROFILE selects active features + overrides)
- **Core Skills:**
  - `core/openclaw-adapter/` — first Other-harness adapter (validates the modular consumer architecture)
  - `core/audit-quarantine-skill/` — `/audit-quarantine` Skill artifact (supersedes the behavioral-protocol-only note in §5.3)
- **Recommended addons** (all security-vetted):
  - `recommended-addons/llmlingua-installer/` (Tier C C6)
  - `recommended-addons/graphiti-installer/` (Tier C C2)
  - `recommended-addons/graphify-installer/` (Tier C C3 — L1-L4 typosquat defense)
  - `recommended-addons/obsidian-vault-config/` (Tier B recommended; 16 files including 6 SCHEMA_A3 memory_bank templates)

---

## 19. Status + Open Questions

**This protocol is stable.** The companion schemas (`SCHEMA_audit_log.md`, `SCHEMA_quarantine.md`, `SCHEMA_compliance_profile.md`) and templates all ship alongside it. Remaining open questions are tracked here for future versions:

1. ~~**CAS hash function** — should `content_sha256` be normalized before hashing?~~ **CLOSED: yes — canonical normalization is locked in SCHEMA_A18 §"`content_sha256` normalization".**
2. **Quarantine release escalation** — the `/audit-quarantine` workflow ships; escalation paths beyond approve/reject/defer may grow in a future version.
3. **Audit log retention defaults** — biotech (1 year minimum for HIPAA forensics?), general (90 days?). Per-edition PROFILE.md decides; this protocol defines the rotation mechanism (§11).
4. **Pattern-key promotion target** — auto-promote where? `.claude/rules/auto_rules.md`? Or DEC entries? Lean toward DEC entries with `source_agent: auto-promoted-from-pattern` and full provenance.
5. **Compaction trigger threshold** — protocol says "near context limit"; should it be deterministic (e.g., ~85%)? Community-derived guidance suggests ~95%.
6. **Edition mixing** — what if a user wants `general` edition + `compliance: healthcare` (general-edition with HIPAA preset, no biotech-specific UX)? Currently supported via PROFILE.md customization.
