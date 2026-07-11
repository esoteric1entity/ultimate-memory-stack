# Memory Protocol — Extended Reference

> **Status:** stable (ships with UMS v4.0.0) · **Authors:** see /AUTHORS.md
> **What this is:** on-demand reference material for the [Memory Protocol](MEMORY_PROTOCOL.md) core. **This file is NEVER auto-loaded** — it is not copied into `.claude/rules/`, and nothing in the bootstrap sequence reads it at session start. The core protocol points here explicitly ("read `memory/MEMORY_PROTOCOL_EXTENDED.md` §N before proceeding") when a specific operation needs this detail.
> **Repo location:** `common-specs/MEMORY_PROTOCOL_EXTENDED.md` · **Installed location:** `memory/MEMORY_PROTOCOL_EXTENDED.md` (vault root — never under `.claude/rules/`; see §E-killer-edge below).
>
> Version history lives in [`CHANGELOG.md`](../CHANGELOG.md).

## Table of Contents

- [E1. Context Rot Mitigation](#e1-context-rot-mitigation) — full detail behind core §2's position-pinning rule
- [E2. Wiki-Link Sync Detail](#e2-wiki-link-sync-detail) — full detail behind core §4's inline `[[ID]]` mention
- [E3. Write Operation Mechanics](#e3-write-operation-mechanics) — CAS concurrency, audit log format, quarantine skill detail, bi-temporal supersession
- [E4. Edition Override & Compliance Preset Mechanics](#e4-edition-override--compliance-preset-mechanics) — override-file precedence + full compliance preset activation table
- [E5. Risk Scoring Rubric](#e5-risk-scoring-rubric) — full 6-factor table for high-impact tasks
- [E6. Self-Trimming Protocol](#e6-self-trimming-protocol) — full every-10-session consolidation detail
- [E7. Lint Operation — Full Spec](#e7-lint-operation--full-spec) — 11 checks, edition config, execution model
- [E8. File Size Cap Enforcement Model](#e8-file-size-cap-enforcement-model) — error format, override mechanism, legacy handling
- [E9. Decision Promotion — Rationale & Signal Sourcing](#e9-decision-promotion--rationale--signal-sourcing)
- [E10. Status + Open Questions (historical)](#e10-status--open-questions-historical)

---

## E1. Context Rot Mitigation

*(Full detail behind core §2's position-pinning rule.)*

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

| Harness | Mechanism | Status |
|---|---|---|
| **Claude Code** | Memory Protocol auto-load behavior — bootstrap currently loads files once; the pinning pattern is documented. Mechanism for actual end-injection requires a hook into auto-load or system prompt restructure. | DOCUMENTED |
| **OpenClaw General Edition Adapter** | Adapter Skill controls injection sequence; end-pin via duplicate include in MEMORY.md tail OR HEARTBEAT.md regeneration at session-mid checkpoint | SHIPS via adapter |
| **Multi-Machine Sync (v4.0)** | Sync state can carry end-pin signature for cross-machine consistency | Future |

**Source citations (borrow ideas, not numbers):**
- [Redis context rot blog](https://redis.io/blog/context-rot/) — independent measurement
- [Morph context rot analysis](https://www.morphllm.com/context-rot) — independent measurement
- Chroma findings (context-rot research synthesis)

**What this does NOT mitigate:**
- Middle-position entries STILL get weak attention. Position-pinning only protects the entries that get pinned (Tier 1). Entries that need strong recall but lack tier-1 status should either be promoted (core §12 promotion logic) or referenced via wikilink which prompts re-load.
- Doesn't reduce TOTAL context usage. End-pin adds budget cost (~1-3% of total). Trade-off: ~1-3% budget for substantially better recall on critical state.

**Validation strategy:** validation included exercising position-pinning behavior — confirm Tier 1 content survives 60K+ char middle content reliably.

---

## E2. Wiki-Link Sync Detail

*(Full detail behind core §4's inline `[[ID]]` mention.)*

### Wiki-Link Sync (T2+ when Node.js parser available; manual at T0–T1)

Within entry bodies, contributors may use `[[ID]]` wiki-links (Obsidian convention) to reference other entries inline.

- **At T0–T1:** YAML `related` / `supersedes` are CANONICAL. Inline `[[ID]]` is supplemental human-friendly form. Manual sync — both should be present.
- **At T2+ (Node.js indexer):** Auto-parse `[[ID]]` from body, populate YAML `related` field. Two-way sync.

When generating a new entry, populate BOTH the YAML field and (if mentioning in prose) the inline wiki-link form. Do not generate orphan inline links without a YAML counterpart.

---

## E3. Write Operation Mechanics

*(Full detail behind core §5's write-rule summary.)*

### E3.1 CAS-Style Concurrency (B3)

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

### E3.2 Audit Log Writes (B1)

Every memory write produces an entry in `memory/security/audit_log.jsonl`:

```jsonl
{"ts":"2026-05-14T15:30:00Z","actor":"orchestrator","session":7,"action":"write","entry_id":"DEC-024","entry_summary":"<first-200-chars>","content_sha256_before":"...","content_sha256_after":"...","outcome":"success"}
```

**Biotech edition:** REQUIRED on every write (including reads-for-validation if SCHEMA_audit_log.md so configures). Non-overridable.

**General edition:** OPT-IN; default OFF. User enables via `audit_log: true` in compliance profile.

**Do NOT log entry content** — only summaries (first 200 chars) to keep log size manageable and PHI-free.

### E3.3 Quarantine Routing Detail (B2)

If validation-on-read (core §4) fails for an entry:
1. Move entry to `memory/quarantine/<original-category>/<entry-id>.md` (preserve provenance)
2. Append quarantine record to `memory/quarantine/quarantine_log.jsonl`
3. Set entry's `status: quarantined` in frontmatter
4. Log to audit log per E3.2

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

### E3.4 Bi-Temporal Supersession (B5)

When a new entry supersedes an older one:
1. New entry has `supersedes: <old-entry-id>` in frontmatter
2. Old entry gets `invalid_at: <today>` set automatically; `status` flipped to `superseded`
3. Old entry's body remains untouched — history preserved
4. Forward pointer: old entry gets `superseded_by: <new-entry-id>`

**This is the Graphiti pattern**: contradictions don't delete history; they mark validity boundaries. Enables point-in-time queries (core §3 bi-temporal precedence).

**Cross-machine extension (per `SCHEMA_sync_log.md`):** Supersession events that cross machine boundaries are captured in `memory/security/sync_log.jsonl` with `parent_event_id` linking the original `supersedes` event to its sync-related propagation. See `SCHEMA_sync_log.md` §6.4 for full cross-machine bi-temporal semantics. (Implementation is a future deliverable; the schema ships now.)

---

## E4. Edition Override & Compliance Preset Mechanics

*(Full detail behind core §6's override/preset one-liner.)*

### E4.1 Override-File Precedence (B4 + B7)

For every common-spec file `common-specs/X.md`, check for an override at `<edition>/overrides/X.override.md`:
- If override file exists, parse its sections
- For each section header in the override, REPLACE the same-named section in the common-spec
- Other sections inherit from common-spec unchanged

**Example:**
- `common-specs/MEMORY_PROTOCOL.md` defines `§5 Write Operations`
- `biotech-edition/overrides/MEMORY_PROTOCOL.override.md` overrides its quarantine-routing subsection with biotech-specific workflow details
- Other sections of MEMORY_PROTOCOL.md inherit unchanged

### E4.2 Compliance Preset (B7)

Active compliance preset (from PROFILE.md) selects detection patterns + redaction rules + audit defaults:

| Preset | What activates |
|--------|----------------|
| `none` | No regulatory detection. Standard hygiene only (secrets, credentials). Lowest friction. |
| `healthcare` | Full PHI detection (MRN, specimen IDs, accession numbers, genomic identifiers). Redact-on-sight. Audit log default ON. Biotech: non-overridable. |
| `enterprise` | GDPR + SOC2 baseline — provenance + audit + consent tracking. Hard delete with recovery window. |
| `custom` | Compliance is fully configured via `<edition>/overrides/compliance-presets.override.md` — fine-grained for power users. |

Active preset is **always logged** to session_state.md at session start.

---

## E5. Risk Scoring Rubric

*(Full 6-factor table behind core §8's trigger pointer.)*

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

## E6. Self-Trimming Protocol

*(Full detail behind core §10's pointer. Runs during consolidation, every 10 sessions.)*

**Suggestions only — never auto-delete or auto-archive.**

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
- Standing rules in the core protocol
- Audit log entries (`memory/security/audit_log.jsonl`) — append-only, archive by date only

**Bi-temporal note (B5):** Self-trimming does NOT delete superseded entries — those have `invalid_at` set but body preserved. Archiving moves them to `memory/archive/`; the bi-temporal record is intact.

---

## E7. Lint Operation — Full Spec

*(Full detail behind core §10's summary. Karpathy LLM Wiki Pattern — periodic memory integrity scanner. Complementary to E6 Self-Trimming — Self-Trimming is usage-based (last-accessed); Lint is integrity-based (cross-entry checks). Both run during consolidation passes.)*

**Full spec:** See `SCHEMA_lint.md` for complete schema, workflow, and configuration details.

### Lint Checks (6 original + 5 self-improvement extension = 11 total)

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
| 7 | **Promotion candidates approaching threshold** | T0 | Entries near core §12 PageRank trigger but not yet qualifying | `access_count ≥ 4` AND `len(recent_sessions) ≥ 2` (one short of `≥5` AND `≥3` thresholds). Surfaces "next promotion candidates" for proactive review. |
| 8 | **Pattern condensation opportunities** | T3 | Multiple decisions on same topic across entries — supersession/merge candidates | Cluster entries by shared tags + cross-references; if cluster size ≥3 entries with overlapping topic + all `status: active`, suggest merge candidate. LLM-assisted for semantic similarity. |
| 9 | **Naming inconsistencies** | T3 | Same concept referred to differently across entries — canonical-naming candidates | Tokenize entry bodies; flag candidate-pairs with high textual overlap but different surface terms (e.g., "decision log" vs "decisions.md" vs "DEC log"). LLM-assisted for synonym detection. |
| 10 | **Documentation completeness gaps** | T0 | Entries missing documentation-discipline elements (Purpose / Rationale / Sound Reasoning / Scope CAN / Scope CANNOT) | For each entry with `scope: entry`: grep for the 5 required headers. Flag entries missing any. Severity scales with missing-count. |
| 11 | **Standing-rule candidates** | T3 | Patterns observed in multiple sessions that could become standing rules per core §7 | Cluster feedback (FB-NNN) entries + observation logs by topic; if cluster ≥3 feedback events across ≥3 sessions, suggest promotion to standing rule. LLM-assisted for pattern detection. |

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

- The **surfacing layer** ships now: the memory subagent (per the Execution Model below) runs all eleven checks.
- Checks 8, 9, and 11 use LLM-assisted semantic detection; lightweight pattern-match versions ship today, with fuller semantic versions planned.
- A findings-triage flow (navigate findings, approve/reject promotion candidates one at a time) is planned.

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
- **Parent context savings** — Lint's intermediate analysis (parsing 11 checks across entries, scoring findings) does NOT pollute the orchestrator's working memory. Vault returns only the structured findings.
- **Audit log clarity** — Vault's full analysis log lives separately at `memory/security/lint_runs.jsonl`; orchestrator's audit_log gets a single `lint-run` action entry.
- **Tier-aware execution** — Vault can run Lint at lower context priority without competing with orchestrator's Tier 1 session work.
- **Mirrors OpenClaw equivalent** — OpenClaw's `sessionTarget: "isolated"` for cron-driven memory ops provides the same isolation; lint matches that pattern for cross-stack consistency.

**Execution flow:**

```
1. Orchestrator receives trigger (manual /lint-memory, auto-cadence, or consolidation pass)
   ↓
2. Orchestrator spawns Vault subagent:
     - subagent_type: "general-purpose"
     - allowed tools: Read, Write, Edit, Glob, Grep (per agent_orchestration.md)
     - explicit instructions: "Run 11 Lint checks against memory/; return structured findings JSON"
   ↓
3. Vault subagent executes:
     - Loads memory/ files into ITS OWN context (not parent's)
     - Runs the checks (deterministic + LLM-assisted at T3)
     - Writes detailed analysis to memory/security/lint_runs.jsonl (Vault has Write tool)
     - Returns to orchestrator: { findings: [...], summary: "...", severity_counts: {...} }
   ↓
4. Orchestrator receives findings:
     - Surfaces to user per edition mode (chat output / toast / blocking on biotech CRITICAL)
     - Appends single "lint-run" entry to audit_log.jsonl per E3.2
     - Does NOT see Vault's intermediate analysis (Vault context discarded)
```

**Backward compatibility:** Both inline and subagent execution modes work. The protocol does not REQUIRE subagent execution — it RECOMMENDS it. Lint output format is identical either way.

**Constraints (per agent_orchestration.md):**
- **Vault + Clerk parallel** — NOT allowed (both write to logs). When Lint runs, no parallel Clerk task work.
- **Vault + Sentinel parallel** — Allowed (Sentinel reads only; no log write contention).
- **Vault read-only mode** — Vault has Write/Edit tools BY NECESSITY for `lint_runs.jsonl` writes. Lint findings ARE written by Vault directly; orchestrator only writes the audit_log summary entry.

**OpenClaw equivalent (Adapter compatibility):**

In the OpenClaw General Edition Adapter, Lint runs as a Skill with `metadata.openclaw.sessionTarget: "isolated"`. OpenClaw's existing cron infrastructure handles scheduling. The findings JSON format is identical to Claude Code's Vault subagent output, enabling cross-stack tooling.

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
- **Self-trimming (E6) complementarity:** Findings overlap (e.g., orphan + low-value TENTATIVE) — surface once across both, not twice
- **Bi-temporal (B5) handling:** Contradictions in explicit `supersedes:` chains are NOT flagged by Lint (the chain itself resolves them); Lint catches contradictions that lack explicit chains

### When To Run Lint

- Whenever the user invokes `/lint-memory`
- Per-edition auto-cadence at session start (biotech weekly; general monthly)
- During consolidation pass (every 10 sessions per E6) — run alongside self-trimming

### What Lint CANNOT Do

- Auto-fix any finding (surface-only by design)
- Delete entries (only suggest archiving)
- Replace user judgment
- Operate without `memory/` directory existing
- Pre-emptively prevent rot at write-time (that's Layer 2 quarantine's job)

---

## E8. File Size Cap Enforcement Model

*(Full detail behind core §11's cap table + one-line enforcement note.)*

**Historical note:** Caps were **advisory** in early versions — no mechanism enforced them, and files could grow indefinitely. **Documented real-world failure:** in one observed deployment, a heartbeat file grew to 16K+ characters violating its own "keep tiny" rule; the advisory model didn't prevent this. Caps became **enforced hard errors** at write-time from v3.5 onward. Pre-write check blocks writes that would cause overflow. Remediation required before write completes.

### Pre-write enforcement

Before any write operation (`write_file`, `Edit`, `Edit replace_all`, append) to a memory file with a core §11 cap:

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

### Error message format

When a write is blocked:

```
✗ HARD CAP EXCEEDED — Write blocked
  File: memory/sessions/session_state.md
  Current size: 1487 lines
  Attempted write: +24 lines
  Post-write would be: 1511 lines
  Cap: 1500 lines (core §11)

  Required action before retry:
  1. Archive old session summaries to memory/archive/sessions/
     (action specified in core §11 table for this file type)
  2. Reduce current file to ≤ 1450 lines (leave 50-line buffer)
  3. Retry the write

  Override (use sparingly):
  • Set MEMORY_PROTOCOL_OVERRIDE=cap-bypass in environment
  • OR: invoke /override-cap slash command
  • Override is logged to audit_log.jsonl as compliance_handling: cap-override
```

The error gives the user actionable remediation (archive instructions per the core §11 table's "Action When Exceeded" column) AND an explicit override path for emergencies.

### Edition behavior

| Edition | Default mode | Override mechanism | Audit |
|---|---|---|---|
| **biotech-edition** | Hard error (non-overridable in healthcare preset) | Requires admin token via `compliance.healthcare.cap_override_admin_token` config | Override logged to audit_log; HIPAA forensic complete |
| **general-edition** | Hard error (user-overridable) | `/override-cap` slash command OR env var | Override logged to audit_log if audit_log enabled per B1 opt-in |

### Backward compatibility (legacy over-cap files)

**Problem:** Existing deployments may have files already over cap.

**Solution:** Grace period via Lint surfacing.

- At deployment: file size scanner runs once; files already over cap get marked `legacy_overflow: true` in their file-level frontmatter (per SCHEMA_A18 `scope: file` field)
- Legacy over-cap files: read-allowed, write-allowed (no new content), append-allowed up to a freeze cap (1.25× normal cap), then HARD ERROR
- Lint operation (E7) surfaces legacy_overflow files in every weekly/monthly run as remediation candidates
- Once user manually archives the file below cap, `legacy_overflow` flag clears

This prevents a new enforcement deployment from immediately blocking productive work on day 1 while still pushing toward enforcement.

### Special case: append-only JSONL logs

Files like `audit_log.jsonl` and `quarantine_log.jsonl` have larger caps (e.g., 50,000 lines for audit_log) AND automatic rotation behavior (per core §11 table "Action When Exceeded" column).

For these files:
- Cap is enforced (hard error if exceeded)
- BUT rotation happens AUTOMATICALLY when 80% threshold reached (not on hard-error-block)
- Rotation creates `<filename>_<YYYY-MM>.jsonl.gz` archive; current file resets to empty
- User never blocked by these caps in practice — rotation pre-empts overflow

### Validation strategy

Cross-machine validation includes exercising:
- Hard error fires when expected
- Error message format correct + actionable
- Override mechanism works
- Audit log entry created on override
- Legacy over-cap files accept reads + minor appends but not bulk writes
- Auto-rotation triggers for JSONL logs at 80% threshold

---

## E9. Decision Promotion — Rationale & Signal Sourcing

*(Full detail behind core §12's promotion-trigger table.)*

### E9.1 When promoting

  - Merge duplicates (keep most recent confidence)
  - Keep only the latest FINAL per topic
  - Remove superseded TENTATIVE entries (or set their `invalid_at` if you want bi-temporal history)
- Promoted decisions get full SCHEMA_A18 frontmatter at promotion time (not inherited from session_state — fresh assignment)
- If promoting via trigger C (PageRank signal), the entry's existing `access_count`, `last_accessed`, and `recent_sessions` carry over (they represent its access history; don't reset).

### E9.2 PageRank signal sourcing

The PageRank signal (trigger C) depends on SCHEMA_A18 access tracking fields. Operationally:

- **`access_count` and `recent_sessions`** are populated by runtime hooks at Tier 1/2/3 load + memory_search query result events. The schema ships now; the auto-incrementer is a future deliverable (or arrives via OpenClaw heartbeat-driven compaction).
- **Baseline:** counters are populated manually (the user edits the field) OR retroactively computed from `audit_log.jsonl` if available OR initialized to defaults and accrued from this point forward.
- **Lint operation (E7)** surfaces entries near the PageRank threshold (`access_count` ≥ 4 AND `len(recent_sessions)` ≥ 2) as "candidates approaching promotion" — gives the user visibility into emerging promotion candidates before they auto-qualify.

### E9.3 Rationale

The PageRank signal addresses a documented gap: in one observed OpenClaw deployment, heavy-reference entries should have promoted earlier but didn't because:
- They weren't part of a topic cluster (Trigger A didn't fire)
- They didn't have a Pattern-Key (Trigger B didn't fire)
- They lacked a manual promotion trigger (Trigger D didn't fire)

But they WERE heavily-referenced (e.g., cron architecture details stayed inline at 2K chars instead of promoting to a detail file). Adding Trigger C catches this case.

Borrowed pattern from Aider's repo-map PageRank algorithm — files heavily-referenced in code get boosted weight (borrow ideas, not numbers). Here applied to memory entries.

### E9.4 Edition behavior

Both editions accept Triggers A/B/C/D identically. The only edition difference is Trigger B's threshold (3 for biotech vs 5 for general per core §4). PageRank signal (Trigger C) uses same thresholds in both editions for now; may be tuned per-edition in future revisions if data warrants.

---

## E10. Status + Open Questions (historical)

**This protocol is stable.** The companion schemas (`SCHEMA_audit_log.md`, `SCHEMA_quarantine.md`, `SCHEMA_compliance_profile.md`) and templates all ship alongside it. Remaining open questions are tracked here for future versions:

1. ~~**CAS hash function** — should `content_sha256` be normalized before hashing?~~ **CLOSED: yes — canonical normalization is locked in SCHEMA_A18 §"`content_sha256` normalization".**
2. **Quarantine release escalation** — the `/audit-quarantine` workflow ships; escalation paths beyond approve/reject/defer may grow in a future version.
3. **Audit log retention defaults** — biotech (1 year minimum for HIPAA forensics?), general (90 days?). Per-edition PROFILE.md decides; the core protocol defines the rotation mechanism (§11).
4. **Pattern-key promotion target** — auto-promote where? `.claude/rules/auto_rules.md`? Or DEC entries? Lean toward DEC entries with `source_agent: auto-promoted-from-pattern` and full provenance.
5. **Compaction trigger threshold** — protocol says "near context limit"; should it be deterministic (e.g., ~85%)? Community-derived guidance suggests ~95%.
6. **Edition mixing** — the `healthcare` preset is **NOT supported in general-edition**: the installer refuses it (general-edition presets are `none` / `enterprise` / `custom` only; `healthcare` is biotech-edition-reserved). General-edition deployments with regulatory needs use the `enterprise` or `custom` preset. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available). See CONTRIBUTING.md.
