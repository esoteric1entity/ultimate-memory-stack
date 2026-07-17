# Schema — Lint Operation (Karpathy LLM Wiki Pattern)

> **File:** `common-specs/SCHEMA_lint.md`
> **Version:** 1.0 — 2026-05-15
> **Status:** APPROVED
> **Authors:** see /AUTHORS.md
> **Design principles:** Karpathy Lint operation formally included; documentation discipline; design philosophy: ideal-first with tier markers

---

## 1. Purpose

Detect and surface 6 classes of "memory rot" — silently accumulating problems that erode memory system quality over time. **Surface-only:** Lint reports findings to the user; the user decides remediation. No auto-fix, no auto-delete.

This is the **Lint** leg of the Karpathy LLM Wiki three-operation model:
- **Ingest** — covered by SCHEMA_A18 frontmatter writes ✓ (already in v3.0)
- **Query** — covered by Tier 1/2/3 context loading ✓ (already in v3.0)
- **Lint** — covered by THIS spec ✓

---

## 2. Rationale

### Why Lint?

Memory systems accumulate cruft over time:
- Decisions get made then forgotten (orphan entries)
- References break when entries are renamed/removed (broken refs)
- TENTATIVE decisions sit in limbo forever (stale tentative)
- External-source citations go stale (stale webfetch)
- Conflicting facts coexist without explicit supersession (contradictions)
- Concepts get mentioned repeatedly without dedicated entries (missing concepts)

Karpathy's framing: *"Lint is what keeps the wiki from rotting."*

Without periodic maintenance, a memory system after 6–12 months looks coherent at first glance but is actually full of stale state, broken links, forgotten threads, and silent contradictions.

### Why hybrid tier (T0 deterministic + T3 LLM-assisted)?

4 of 6 checks are deterministic (regex/parsing/date math) and run anywhere — these provide most of the value with zero infrastructure dependency. The remaining 2 (semantic contradiction detection, missing concept detection) genuinely need LLM-assisted analysis, so they're gated to T3.

This matches the project's design philosophy: build for ideal state, activate progressively as infrastructure unblocks.

### Why surface-only (no auto-fix)?

Trust boundary principle. Lint is a CHECKER, not an EDITOR. The user is the authority on:
- Whether a TENTATIVE decision should be promoted vs archived
- Whether a "contradiction" is genuine vs benign
- Whether an orphan is forgotten vs intentionally isolated
- Whether to act on stale citations or leave them

Same design philosophy as `eslint --no-fix` or `pylint` without auto-formatting.

### Why per-edition cadence?

- **Biotech (weekly):** HIPAA-regulated context benefits from frequent integrity checks; matches biotech-edition's higher compliance posture
- **General (monthly):** Lower friction for non-regulated contexts; user can opt to run on-demand more frequently

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| Three-operation model (Ingest / Query / Lint) is convergent | Karpathy LLM Wiki ecosystem research (~4,300 words) | Multi-system pattern observation |
| Lint prevents wiki rot | Karpathy 2026 gist + commentary | Source author's framing |
| Orphan / broken-ref checks are well-understood deterministic operations | Graph theory + standard linter design | First principles |
| Contradiction detection requires semantic analysis | Cross-entry reasoning is non-trivial without LLM | Established knowledge |
| Surface-only design preserves user trust | Security-first principle + biotech-edition quarantine design | Existing design pattern |

---

## 4. Schema Definition

### 4.1 Lint Run Log Format (`memory/security/lint_runs.jsonl`)

Each lint run produces a single JSONL line summarizing the run, followed by zero or more finding lines.

**Run header line:**
```jsonl
{"ts":"2026-05-15T15:30:00Z","run_id":"<uuid-or-ts>","trigger":"manual|scheduled","actor":"user|orchestrator|lint-skill","actor_session":<N>,"edition":"biotech|general","tier_active":<T0-T4>,"checks_run":["orphan","broken-ref","stale-tentative","stale-webfetch","contradiction","missing-concept"],"entries_scanned":<N>,"findings_count":<N>}
```

**Finding line (one per finding):**
```jsonl
{"ts":"<run-ts>","run_id":"<same-run-id>","finding_type":"<check-name>","severity":"LOW|MEDIUM|HIGH|CRITICAL","entry_id":"<offending-entry>","entry_path":"<file:line>","description":"<human-readable>","suggested_remediation":"<actionable-text>","auto_actionable":false}
```

### 4.2 Finding Severity Mapping

| Finding type | Default severity |
|--------------|-------------------|
| `orphan` | LOW (informational; not always a problem) |
| `broken-ref` | MEDIUM (likely a real issue) |
| `stale-tentative` | LOW (informational; user judgment) |
| `stale-webfetch` | MEDIUM (verification recommended) |
| `contradiction` | HIGH (needs resolution) |
| `missing-concept` | LOW (informational; user choice) |

Severity drives surface UX: HIGH/CRITICAL → review-required; MEDIUM → flagged; LOW → informational summary.

### 4.3 Configuration (in PROFILE.md per edition)

```yaml
# Biotech-edition (per PROFILE.md update)
lint:
  cadence: weekly                    # auto-run frequency
  mode: auto                         # auto OR suggested
  blocking_on_critical: true         # block new writes if HIGH findings unresolved
  retention_runs_days: 365           # keep lint_runs.jsonl history
  thresholds:
    stale_tentative_sessions: 10    # TENTATIVE not revisited in N sessions
    stale_webfetch_days: 30          # webfetch entries not re-validated in N days
    orphan_minimum_age_sessions: 5  # don't flag entries < N sessions old as orphans
  checks_enabled:
    orphan: true
    broken_ref: true
    stale_tentative: true
    stale_webfetch: true
    contradiction: true              # requires T3
    missing_concept: true            # requires T3

# General-edition (per PROFILE.md update)
lint:
  cadence: monthly
  mode: suggested                    # surface as toast, don't auto-run
  blocking_on_critical: false        # never block in general-edition
  retention_runs_days: 90
  thresholds:
    stale_tentative_sessions: 20    # more lenient than biotech
    stale_webfetch_days: 90
    orphan_minimum_age_sessions: 10
  checks_enabled:
    orphan: true
    broken_ref: true
    stale_tentative: true
    stale_webfetch: true
    contradiction: false             # opt-in for general
    missing_concept: false           # opt-in for general
```

---

## 5. The 6 Checks — Detail

### 5.1 Orphan Detection (T0 deterministic)

**What:** Find entries with no incoming references.

**Algorithm:**
1. Build a set of all entry IDs from frontmatter (`id:` field in YAML)
2. For each entry, scan body for `[[ID]]` wiki-link patterns and frontmatter `related:` / `supersedes:` fields
3. Build incoming-reference count per entry
4. Flag entries with `incoming_count == 0` AND `age_sessions >= orphan_minimum_age_sessions`

**Severity:** LOW (orphans aren't always problems; could be intentionally isolated entries)

**Exclusions:**
- `user_profile.md` (always referenced implicitly)
- Standing rules
- Entries with `lint_orphan_ignore: true` in frontmatter (user opt-out)

**Suggested remediation:**
- "Entry X is an orphan. Was this entry forgotten? Consider archiving OR adding a link from somewhere relevant."

### 5.2 Broken Reference Detection (T0 deterministic)

**What:** Find references pointing to non-existent IDs.

**Algorithm:**
1. Build entry-ID set
2. For each entry, extract every `[[ID]]` and `supersedes:` / `superseded_by:` / `related:` value
3. Flag references not in the entry-ID set

**Severity:** MEDIUM (likely a typo, deleted entry, or migration error)

**Suggested remediation:**
- Use fuzzy match to suggest correct ID (e.g., "DEC-099 doesn't exist; did you mean DEC-029?")
- If no fuzzy match: "Reference is dead. Remove or update."

### 5.3 Stale TENTATIVE / EXPLORATORY Detection (T0 deterministic)

**What:** Find decisions in non-FINAL confidence states that haven't been revisited.

**Algorithm:**
1. Filter entries where `confidence: TENTATIVE` or `confidence: EXPLORATORY`
2. Compute `sessions_since_last_updated`
3. Flag entries exceeding `stale_tentative_sessions` threshold

**Severity:** LOW (informational; user decides)

**Suggested remediation:**
- "DEC-X has been TENTATIVE for N sessions. Promote to FINAL, demote to archive, or update with current thinking?"

### 5.4 Stale Webfetch Detection (T0 deterministic)

**What:** Find entries sourced from external URLs that haven't been re-validated recently.

**Algorithm:**
1. Filter entries where `source_agent: webfetch`
2. Compute `days_since_last_validated`
3. Flag entries exceeding `stale_webfetch_days` threshold

**Severity:** MEDIUM (external sources can change/move/disappear)

**Suggested remediation:**
- "WEB-X cites a URL last validated N days ago. Re-validate before treating as authoritative."

### 5.5 Contradiction Detection (T3 LLM-assisted)

**What:** Find pairs of currently-active entries that assert semantically conflicting facts WITHOUT being part of a supersession chain.

**Algorithm:**
1. Group entries by topic (via tags, project_slug, semantic clustering)
2. For each topic group, identify pairs with potential conflict (T0: keyword overlap; T3: LLM semantic check)
3. Filter pairs where neither has `invalid_at` set AND neither references the other via `supersedes`
4. Flag pairs as potential contradictions

**Severity:** HIGH (genuine state inconsistencies need resolution)

**Performance note:** Pairwise check is O(N²). For N > 1000 entries, use clustering (group by tags/topic) to reduce to O(N log N) effective complexity.

**Suggested remediation:**
- "DEC-X says A; DEC-Y says B. Both active. Either: (a) supersede one with the other, (b) clarify they apply to different contexts, (c) update both to reflect a unified position."

### 5.6 Missing Concept Detection (T3 LLM-assisted)

**What:** Find concepts mentioned repeatedly across entries without dedicated reference entries.

**Algorithm:**
1. Extract entity mentions (capitalized terms, acronyms, domain-specific terms) across all entries
2. Count occurrences
3. For high-occurrence terms (configurable threshold), check whether a dedicated reference entry exists
4. Flag missing reference entries

**Severity:** LOW (user choice — sometimes terms don't need anchoring)

**Suggested remediation:**
- "Term 'NGS-assay-name' appears in 12 entries but has no dedicated reference entry. Consider creating one for clarity?"

---

## 6. Trigger Mechanisms

### 6.1 Manual: `/lint-memory` Slash Command

User invokes via Claude Code:
```
/lint-memory
```

Optional flags:
- `--checks=orphan,broken-ref` — run only specified checks
- `--severity=MEDIUM,HIGH` — show only findings at specified severities
- `--dry-run` — preview what would be checked without executing
- `--since=<date>` — only check entries modified since date

Output: lint run summary + findings written to lint_runs.jsonl; user-facing report rendered in chat.

### 6.2 Auto: Per-Edition Cadence

**Biotech-edition (weekly auto):**
- At session start, if last lint run was >7 days ago, run auto-lint
- Findings surface via blocking workflow (if HIGH/CRITICAL severity) or toast (LOW/MEDIUM)
- User must review HIGH/CRITICAL before continuing new writes (similar to the biotech quarantine workflow, feature B2)

**General-edition (monthly suggested):**
- At session start, if last lint run was >30 days ago, suggest run via toast
- User accepts toast → lint runs; user dismisses → defer
- Non-blocking (matches general-edition's overall UX posture)

### 6.3 Integration with Existing Workflows

**Audit log integration:**
- Every lint run logs a `lint-run` action to `memory/security/audit_log.jsonl` per SCHEMA_audit_log.md
- High/Critical findings additionally surface as security-relevant events

**Quarantine integration:**
- HIGH-severity contradictions may route to quarantine if biotech-edition (user reviews via /audit-quarantine)
- General-edition: surfaces in lint findings UI; quarantine not auto-triggered

**Self-trimming complementarity (§10):**
- Self-trimming = usage-based (last-accessed); Lint = integrity-based (cross-entry checks)
- Both run during consolidation passes
- Findings can overlap (e.g., orphan + low-value TENTATIVE) — surface once, not twice

---

## 7. Scope — CAN / CANNOT

### CAN
- Scan all entries in `memory/` for 6 problem classes
- Run at T0 with 4 deterministic checks
- Run at T3 with all 6 checks (deterministic + LLM-assisted)
- Write findings to `lint_runs.jsonl` (append-only)
- Surface findings via edition-appropriate UX (toast for general; blocking workflow for biotech if critical)
- Run on-demand via `/lint-memory`
- Run automatically per edition cadence
- Suggest specific remediations per finding
- Operate on `memory/` directory only (does not scan the package's spec files)

### CANNOT
- Auto-fix any finding (surface-only by design — trust boundary)
- Delete entries (only suggest archiving)
- Replace user judgment (findings are recommendations, not commands)
- Operate without `memory/` directory existing
- Catch contradictions where neither entry is obviously wrong (genuinely ambiguous state requires human resolution)
- Pre-emptively prevent rot at write-time (this is a periodic checker, not a real-time validator — that's Layer 2 quarantine's job per SCHEMA_quarantine.md)

### Deployment tier

| Tier | What's available |
|------|-------------------|
| **T0** (base) | 4 deterministic checks (orphan, broken-ref, stale-tentative, stale-webfetch) |
| **T1** (+ Ollama) | Same as T0 + optional embedding similarity for orphan/concept detection |
| **T2** (+ Node.js) | Same as T1 + file-watcher for real-time detection of certain finding types |
| **T3** (+ Code Execution) | All 6 checks active including semantic contradiction + missing concept |
| **T4** (+ Skills) | Skill-wrapped `/lint-memory` UX |

---

## 8. Worked Example — Lint Run Output

```
$ /lint-memory

Memory Lint Report — 2026-11-15T15:30:00Z (weekly run, biotech-edition)

Entries scanned: 234
Findings: 7 (3 actionable now; 4 informational)

ORPHANS (3 entries with no incoming references):
  ⚠️  DEC-008 (Warden as Security Domain Head) — last referenced session 12 (LOW)
       Suggested: archive OR add link from agent orchestration docs

  ⚠️  FB-014 (preferred markdown table style) — last referenced session 22 (LOW)
       Suggested: promote to standing rule OR archive

  ⚠️  REF-007 (internal financial PDF location) — last referenced session 9 (LOW)
       Suggested: archive (project complete)

BROKEN REFERENCES (1):
  🔴 DEC-024 references [[DEC-099]] — DEC-099 does not exist (MEDIUM)
       Suggested: Was this meant to be DEC-029? (typo)
       Action: Edit DEC-024 to fix reference

STALE TENTATIVE (2):
  ⚠️  DEC-042 (Future-feature gating) — TENTATIVE since 2026-05-12, 180 days unrevisited (LOW)
       Suggested: Promote to FINAL OR archive

  ⚠️  DEC-018 (Memory stack scope correction) — TENTATIVE since 2026-05-12 (LOW)
       Suggested: This was promoted to FINAL elsewhere; sync status here

STALE WEBFETCH (1):
  🔴 WEB-003 (article citation) — source URL last validated 95 days ago (MEDIUM)
       Suggested: Re-validate before treating as authoritative

CONTRADICTIONS (0 found at T3)
MISSING CONCEPTS (0 flagged at T3)

═══════════════════════════════
ACTIONS RECOMMENDED:
  - 2 entries need EDIT (broken reference, stale citation)
  - 5 entries need REVIEW (informational)

To act on a finding: just tell me which one (e.g., "fix DEC-024 typo to DEC-029")
To dismiss: "ignore for now" (will resurface next lint run unless resolved)
```

---

## 9. Migration + Compatibility

### From v3.0 without Lint → v3.0 with Lint

Lint is a NEW v3.0 feature (added 2026-05-15). Existing v3.0 deployments add Lint by:
1. Pull updated MEMORY_PROTOCOL.md to `.claude/rules/memory_protocol.md` (and MEMORY_PROTOCOL_EXTENDED.md to `memory/MEMORY_PROTOCOL_EXTENDED.md`, never `.claude/rules/`)
2. Update PROFILE.md with `lint:` config block
3. Create empty `memory/security/lint_runs.jsonl`
4. First lint run baselines current state

### From v2.0 → v3.0 (with Lint)

Same as standard v2.0 → v3.0 migration. Lint becomes active after edition PROFILE.md is in place.

---

## 10. Open Questions (for v3.x refinement)

1. **Threshold defaults:** Are `stale_tentative_sessions: 10` (biotech) and `20` (general) right? Operational data will inform tuning.
2. **Orphan tolerance:** Should orphan threshold be tunable per-category (e.g., references/ might naturally have many orphans)?
3. **Contradiction LLM cost:** At T3, semantic contradiction checks cost LLM tokens. Should there be a budget cap or sampling strategy?
4. **Auto-fix override:** Some users may want auto-fix for trivial cases (typo-fix for fuzzy-matched broken refs). Add as opt-in?
5. **Lint findings retention:** lint_runs.jsonl grows over time. Compress/archive after N months?

---

## 11. Cross-References

- `MEMORY_PROTOCOL_EXTENDED.md` §E7 (Lint Operation full spec)
- `MEMORY_PROTOCOL.md` §10 (Self-Trimming — complementary)
- `SCHEMA_audit_log.md` (every lint run produces audit log entry)
- `SCHEMA_quarantine.md` (HIGH-severity contradictions may route to biotech quarantine)
- `SCHEMA_A18` (frontmatter fields drive 4 of 6 checks)
- `USER_CHEAT_SHEET_core.md` — `/lint-memory` slash command + how to interpret findings
- `biotech-edition/PROFILE.md` §lint (weekly auto)
- `general-edition/PROFILE.md` §lint (monthly suggested)
- Karpathy LLM Wiki ecosystem research

---

## 12. Status

**SHIPPED — stable.** Lint runs today via `core/shared-tools/lint_runner.py`; §13 below documents the 6 tiering checks added in v4.0.0. The phased plan below is retained as design history — Phase A deterministic checks are live; Phases B and C remain future enhancements.

Implementation phases (original plan):
- **Phase A (T0 deterministic checks):** Implement 4 checks (orphan, broken-ref, stale-tentative, stale-webfetch). Can ship immediately at T0.
- **Phase B (T3 LLM-assisted):** Implement contradiction + missing-concept checks when Code Execution available.
- **Phase C (UX polish):** Skill-wrapped `/lint-memory` at T4 via a future Skill extension.

Lint Phase A can be tested alongside the Skill installer.

---

## 13. Tiering Checks (v4.0.0 — Hot/Cold Backport)

6 new checks supporting `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (E12) — the `sessions/`/`decisions/`/`feedback/` rotation-and-archive-index mechanism. All fire at severity **`low`** (the runner's actual enum is `["info","low","medium","high","critical"]` — no `"warning"` level exists; using one crashes the `--severity` CLI filter). Non-blocking by design: an aged pre-4.0.0 vault with no `ARCHIVE_INDEX.md` files yet just gets advisories with a migration pointer, never a hard failure.

**Ownership split:** `verify.sh` owns EXISTENCE-only checks post-fresh-install (the 3 tiered categories' `ARCHIVE_INDEX.md` files present at the standard `memory/archive/<category>/` locations). Lint owns all behavioral/aging checks below. No duplicated logic between the two.

| Check ID | Fires when | Severity |
|---|---|---|
| `eager-set-over-budget` | Summed bytes of the live always-loaded set (`.claude/rules/memory_protocol.md` + `sessions/session_state.md` + `user/user_profile.md` + `MEMORY_INDEX.md`) exceeds `eager_set_budget_bytes` (default 80,000 — reads `PROFILE.md`/`USER_OVERRIDES.md` frontmatter, defaulting on any parse failure) | low |
| `file-nearing-cap` | A §11-capped file (`sessions/`, `decisions/`, `feedback/`) exceeds ~80% of its line cap | low |
| `archive-unindexed` | `memory/archive/<category>/<category>-archive.md` contains an entry section not represented in that category's `ARCHIVE_INDEX.md` | low |
| `archive-count-drift` | A hot-side "Older entries: ... (N entries)" pointer, or a `MEMORY_INDEX.md` Archived column, doesn't match the actual `ARCHIVE_INDEX.md` entry count | low |
| `archive-index-missing` | `memory/archive/<category>/` (one of the 3 tiered categories) contains an archive file but no `ARCHIVE_INDEX.md` | low |
| `entry-over-cap` | An `ARCHIVE_INDEX.md` one-liner, or a `MEMORY_INDEX.md` row description, exceeds its R5 cap class (~300B) | low |

**Implementation notes (pre-decided, not open to Stage-2 improvisation):**
1. §11 caps are hardcoded as a dict in `lint_runner.py`, comment-cross-referenced to §11's table, pinned by a unit test — parsing §11's free-text markdown table would be more fragile than this documented drift risk. A future §11 cap change must touch both places.
2. `collect_all_entries()` deliberately skips any path containing `"archive"`/`"archived"` — correct for the 6 original checks, unusable for the 3 archive-inspecting checks above. Tiering uses a dedicated, separate archive walker; the existing walker's semantics are unchanged.
3. `eager-set-over-budget` needed net-new scope: the runner had zero PROFILE/overrides-reading infrastructure before v4.0.0 (CLI args only). A small, self-contained, defensive frontmatter loader (limited reads, defaults on any failure) was added for this one check.

**Not covered here:** the fresh-install release-gate eager-load budget (a template-snapshot check at install time, ~10K-token target) — that is a different quantity from `eager-set-over-budget`'s live-vault measurement; see `MEMORY_PROTOCOL_EXTENDED.md` §E12.5 for the distinction.
