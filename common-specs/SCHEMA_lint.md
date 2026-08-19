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

- **Weekly (high-compliance profiles):** regulated contexts benefit from frequent integrity checks; a stricter compliance posture warrants a tighter cadence
- **General (monthly):** Lower friction for non-regulated contexts; user can opt to run on-demand more frequently

---

## 3. Sound Reasoning (Sources + Evidence)

| Claim | Source | Evidence type |
|-------|--------|---------------|
| Three-operation model (Ingest / Query / Lint) is convergent | Karpathy LLM Wiki ecosystem research (~4,300 words) | Multi-system pattern observation |
| Lint prevents wiki rot | Karpathy 2026 gist + commentary | Source author's framing |
| Orphan / broken-ref checks are well-understood deterministic operations | Graph theory + standard linter design | First principles |
| Contradiction detection requires semantic analysis | Cross-entry reasoning is non-trivial without LLM | Established knowledge |
| Surface-only design preserves user trust | Security-first principle + quarantine design | Existing design pattern |

---

## 4. Schema Definition

### 4.1 Lint Run Log Format (`memory/security/lint_runs.jsonl`)

Each lint run produces a single JSONL line summarizing the run, followed by zero or more finding lines.

**Run header line:**
```jsonl
{"ts":"2026-05-15T15:30:00Z","run_id":"<uuid-or-ts>","trigger":"manual|scheduled","actor":"user|orchestrator|lint-skill","actor_session":<N>,"edition":"general","tier_active":<T0-T4>,"checks_run":["orphan","broken-ref","stale-tentative","stale-webfetch","contradiction","missing-concept"],"entries_scanned":<N>,"findings_count":<N>}
```

**Finding line (one per finding):**
```jsonl
{"ts":"<run-ts>","run_id":"<same-run-id>","finding_type":"<check-name>","severity":"info|low|medium|high|critical","entry_id":"<offending-entry>","entry_path":"<file:line>","description":"<human-readable>","suggested_remediation":"<actionable-text>","auto_actionable":false}
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
# General-edition (per PROFILE.md update)
lint:
  cadence: monthly
  mode: suggested                    # surface as toast, don't auto-run
  blocking_on_critical: false        # never block in general-edition
  retention_runs_days: 90
  thresholds:
    stale_tentative_sessions: 20    # TENTATIVE not revisited in N sessions
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
- "Term 'service-name' appears in 12 entries but has no dedicated reference entry. Consider creating one for clarity?"

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

**High-compliance profiles (weekly auto):**
- At session start, if last lint run was >7 days ago, run auto-lint
- Findings surface via blocking workflow (if HIGH/CRITICAL severity) or toast (LOW/MEDIUM)
- User must review HIGH/CRITICAL before continuing new writes (similar to the quarantine review workflow, feature B2)

**General-edition (monthly suggested):**
- At session start, if last lint run was >30 days ago, suggest run via toast
- User accepts toast → lint runs; user dismisses → defer
- Non-blocking (matches general-edition's overall UX posture)

### 6.3 Integration with Existing Workflows

**Audit log integration:**
- Every lint run logs a `lint-run` action to `memory/security/audit_log.jsonl` per SCHEMA_audit_log.md
- High/Critical findings additionally surface as security-relevant events

**Quarantine integration:**
- HIGH-severity contradictions may route to quarantine for review via `/audit-quarantine`
- Lower-severity findings surface in the lint findings UI; quarantine is not auto-triggered

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
- Surface findings via appropriate UX (toast; blocking workflow when configured for critical findings)
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

Memory Lint Report — 2026-11-15T15:30:00Z (weekly run, high-compliance profile)

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

1. **Threshold defaults:** Is `stale_tentative_sessions: 20` the right default? Operational data will inform tuning.
2. **Orphan tolerance:** Should orphan threshold be tunable per-category (e.g., references/ might naturally have many orphans)?
3. **Contradiction LLM cost:** At T3, semantic contradiction checks cost LLM tokens. Should there be a budget cap or sampling strategy?
4. **Auto-fix override:** Some users may want auto-fix for trivial cases (typo-fix for fuzzy-matched broken refs). Add as opt-in?
5. **Lint findings retention:** lint_runs.jsonl grows over time. Compress/archive after N months?

---

## 11. Cross-References

- `MEMORY_PROTOCOL_EXTENDED.md` §E7 (Lint Operation full spec)
- `MEMORY_PROTOCOL.md` §10 (Self-Trimming — complementary)
- `SCHEMA_audit_log.md` (every lint run produces audit log entry)
- `SCHEMA_quarantine.md` (HIGH-severity contradictions may route to quarantine)
- `SCHEMA_A18` (frontmatter fields drive 4 of 6 checks)
- `USER_CHEAT_SHEET_core.md` — `/lint-memory` slash command + how to interpret findings
- `general-edition/PROFILE.md` §lint (monthly suggested)
- Karpathy LLM Wiki ecosystem research

---

## 12. Status

**SHIPPED — stable.** Lint runs today via `core/shared-tools/lint_runner.py`; §13 below documents the 8 tiering checks (6 added in v4.0.0, 2 in v4.0.1) and §14 the exit-code contract. The phased plan below is retained as design history — Phase A deterministic checks are live; Phases B and C remain future enhancements.

Implementation phases (original plan):
- **Phase A (T0 deterministic checks):** Implement 4 checks (orphan, broken-ref, stale-tentative, stale-webfetch). Can ship immediately at T0.
- **Phase B (T3 LLM-assisted):** Implement contradiction + missing-concept checks when Code Execution available.
- **Phase C (UX polish):** Skill-wrapped `/lint-memory` at T4 via a future Skill extension.

Lint Phase A can be tested alongside the Skill installer.

---

## 13. Tiering Checks (v4.0.0 — Hot/Cold Backport)

8 checks supporting `MEMORY_PROTOCOL_EXTENDED.md` §Tiering (E12) — the `sessions/`/`decisions/`/`feedback/` rotation-and-archive-index mechanism. The runner's severity enum is `["info","low","medium","high","critical"]` — no `"warning"` level exists; using one crashes the `--severity` CLI filter.

**Most are advisory (`low`); two are gates (`high`).** The split is not arbitrary — it tracks whether the finding means *information can be silently lost*:

- **Advisory (`low`)** — drift, untidiness, and aging signals. An aged pre-4.0.0 vault with no `ARCHIVE_INDEX.md` files yet just gets advisories with a migration pointer, never a hard failure.
- **Gating (`high`)** — `eager-set-over-budget` and `archive-pointer-dangling`. Both mean memory the reader believes is available is not: one because content past a harness load limit is dropped without warning, the other because the cold index promises a rotated entry that is absent. See §14 for the exit-code contract and the standing test obligation.

⚠️ The two gates have **different** exposure on an un-migrated vault, and conflating them is a mistake worth naming:

- `archive-pointer-dangling` requires a **non-empty `ARCHIVE_INDEX.md`**, so it genuinely cannot fire on a vault that has never rotated anything.
- `eager-set-over-budget` measures the live always-loaded set and is **independent of rotation** — it can and will fire on a vault with no `memory/archive/` directories at all. That is intentional (the budget is about load cost, not tiering state), but it means **upgrading to v4.0.1 can newly fail a lint run on a vault that has never tiered**. §E12.5 notes that pre-split, the rules copy alone approaches the budget. Anyone who needs the old behaviour has `--fail-on none`.

**Ownership split:** `verify.sh` owns EXISTENCE-only checks post-fresh-install (the 3 tiered categories' `ARCHIVE_INDEX.md` files present at the standard `memory/archive/<category>/` locations). Lint owns all behavioral/aging checks below. No duplicated logic between the two.

| Check ID | Fires when | Severity |
|---|---|---|
| `eager-set-over-budget` | Summed bytes of the live always-loaded set (`.claude/rules/memory_protocol.md` + `sessions/session_state.md` + `user/user_profile.md` + `MEMORY_INDEX.md`) exceeds `eager_set_budget_bytes` (default 80,000 — reads `PROFILE.md`/`USER_OVERRIDES.md` frontmatter, defaulting on any parse failure) | **high** (gates) |
| `file-nearing-cap` | A §11-capped file (`sessions/`, `decisions/`, `feedback/`) exceeds ~80% of its line cap | low |
| `archive-unindexed` | `memory/archive/<category>/<category>-archive.md` contains an entry section not represented in that category's `ARCHIVE_INDEX.md` | low |
| `archive-count-drift` | A hot-side "Older entries: ... (N entries)" pointer, or a `MEMORY_INDEX.md` Archived column, doesn't match the actual `ARCHIVE_INDEX.md` entry count | low |
| `archive-index-missing` | `memory/archive/<category>/` (one of the 3 tiered categories) contains an archive file but no `ARCHIVE_INDEX.md` | low |
| `entry-over-cap` | An `ARCHIVE_INDEX.md` one-liner, or a `MEMORY_INDEX.md` row description, exceeds its R5 cap class (~300B) | low |
| `archive-pointer-dangling` | An `ARCHIVE_INDEX.md` one-liner names an entry that is **not present** in that category's `<category>-archive.md` (or the archive file is missing entirely) | **high** (gates) |
| `unreachable-memory-file` | A file under `memory/` has body content but is referenced **nowhere** in `MEMORY_INDEX.md` | low |

**Implementation notes (pre-decided, not open to Stage-2 improvisation):**
1. §11 caps are hardcoded as a dict in `lint_runner.py`, comment-cross-referenced to §11's table, pinned by a unit test — parsing §11's free-text markdown table would be more fragile than this documented drift risk. A future §11 cap change must touch both places.
2. `collect_all_entries()` deliberately skips any path containing `"archive"`/`"archived"` — correct for the 6 original checks, unusable for the 3 archive-inspecting checks above. Tiering uses a dedicated, separate archive walker; the existing walker's semantics are unchanged.
3. `eager-set-over-budget` needed net-new scope: the runner had zero PROFILE/overrides-reading infrastructure before v4.0.0 (CLI args only). A small, self-contained, defensive frontmatter loader (limited reads, defaults on any failure) was added for this one check.

**Not covered here:** the fresh-install release-gate eager-load budget (a template-snapshot check at install time, ~10K-token target) — that is a different quantity from `eager-set-over-budget`'s live-vault measurement; see `MEMORY_PROTOCOL_EXTENDED.md` §E12.5 for the distinction.

### 13.1 The two silent-recall-failure checks

Rotation has two sides, and each can fail without anything looking broken. Both checks below exist because the invariant they enforce was previously stated in prose only.

**`archive-pointer-dangling` (high, gates) — a pointer promising content that is gone.**

The exact inverse of `archive-unindexed`, and the severities are deliberately asymmetric:

| | Content | Pointer | Meaning | Severity |
|---|---|---|---|---|
| `archive-unindexed` | present | missing | bookkeeping lapse — nothing lost, just harder to find | low |
| `archive-pointer-dangling` | **missing** | present | the index says a rotated entry is one on-demand read away, and it is not | **high** |

The second case is the direct falsification of §E12.2's **"loss-proof by construction"** claim. Before this check, that claim was enforced only by the rotation procedure being followed correctly by hand — and `tests/test_tiering.py`'s round-trip fixture builds both sides with the same helper, so it could never have caught a real vault where they diverged.

Three deliberate design choices, which a future contributor should leave alone without new evidence:

1. **Anchors are NOT validated.** The one-liner's `→ <file>#<anchor>` tail is navigation; the entry's *presence* is the invariant that proves content survived. Heading-slug derivation is fragile enough to have produced a wrong "fix" in this project's own history, and a gate that mis-slugs would fail correct vaults. Do not upgrade this to anchor matching without a fixture proving the slug rule against real rotated headings.
2. **Presence is tested conservatively** — an ID counts as present if structured extraction finds it *or* it appears anywhere in the archive file as a literal string. This deliberately admits false negatives and excludes false positives. For something that fails builds, that is the correct direction: a gate that cries wolf gets switched off. The known false negatives, all of the same shape — the ID survives as text while the entry itself does not:
   - the ID mentioned inside another entry's prose (`"supersedes DEC-007"`);
   - a stale table-of-contents or rehydration note listing an entry whose section was later removed;
   - any header or summary block that enumerates IDs.

   `archive-unindexed` and `archive-count-drift` catch most of these from the other direction. Tightening to heading-only matching would trade these for false positives on a *gate*, which is the worse error.

3. **Unreadable input is a finding, not a pass.** If `<category>-archive.md` or the `ARCHIVE_INDEX.md` itself cannot be decoded, the check emits a `high` finding rather than skipping the category. Every other check treats an unreadable file as "nothing to report", which is right for an advisory and wrong for a gate: a single stray cp1252 byte from a Notepad save would otherwise silently switch off the check that exists to catch corruption, exactly when the vault is already damaged. **Unverifiable is not the same as clean.**

**`unreachable-memory-file` (low, advisory) — content no pointer reaches.**

The hot-tier complement: `archive-unindexed` covers the cold side, this covers the hot side. `MEMORY_INDEX.md` is the master registry (core §1.3); a file no row points at is effectively invisible at recall time even though nothing was deleted.

- **No-ops when `MEMORY_INDEX.md` is absent.** A fresh install ships no index — it is written by the agent on first use — and "unreachable" is meaningless without something to be reachable *from*. Inferring one would make every day-zero install fire.
- **Matching is a substring test** on the `memory/`-relative POSIX path, so it is insensitive to backticks: `MEMORY_INDEX.template.md` deliberately lists not-yet-created categories as plain text (so the T5 self-test ignores them) and active ones backticked. Both count as references.
- **Reachability includes ancestor directories.** SCHEMA_A3 per-project memory banks are registered in `MEMORY_INDEX.template.md` as directories (`projects/<slug>/memory-bank/`), and that template states the index summarizes while full state lives in the bank. Exact-path-only matching would flag all six Cline convention files for every project on every run — noise from day one on the most common real layout. An ancestor counts only when the index names the **directory itself**: the match must be followed by a character that cannot continue a path segment, so the Category Summary's `projects/project_context.md` row does not make the bare prefix `projects/` exempt everything beneath it.
- **Exempt:** `archive/` (owns its own index), `quarantine/` (excluded from tiering entirely per §E12.1), templates, hidden paths, `MEMORY_INDEX.md` itself, the vault-root `MEMORY_PROTOCOL_EXTENDED.md`, and `user/USER_OVERRIDES.md` (user configuration per §E4.3, not an entry).
- **Advisory, not gating** — an unindexed file is hard to find, not lost, and there are legitimate reasons to keep a file out of the index.

---

## 14. Exit-Code Contract (v4.0.1)

`lint_runner.py` returns:

| Code | Meaning |
|---|---|
| `0` | No finding at or above the `--fail-on` threshold. |
| `1` | At least one finding at or above `--fail-on`. The blocking findings are printed to **stderr** with severity, check-id, message, and path. |
| `2` | Usage/detection error (workspace not found, harness undetectable). Unchanged from earlier versions. |

**`--fail-on {none,info,low,medium,high,critical}` — default `high`.**

### Why this exists

Before v4.0.1 `main()` returned `0` unconditionally, so **no lint finding could ever fail a build**. Every check was advisory by construction, including `eager_set_over_budget` — the guard against an always-loaded set outgrowing its budget. That is a silent-data-loss risk, not a style nit: content past a harness's load limit is dropped **without warning** on the next session load, so the first symptom is an agent that has quietly forgotten something.

`eager_set_over_budget` is therefore severity **`high`** (raised from `low` in v4.0.1) and, at the default threshold, fails the run. `archive_pointer_dangling` (new in v4.0.1) gates for the same reason: both mean memory the reader believes is available is not. Every other check remains advisory.

### The `--severity` interaction (deliberate)

`--severity` is a **display** filter; `--fail-on` is the **gate**. The gate is evaluated against the *unfiltered* finding set, so `--severity critical` cannot silently switch off the high-severity gate. A gate that a display option can disable is not a gate.

### Compatibility

`--fail-on none` restores the pre-v4.0.1 advisory-only behavior for anyone whose pipeline depends on the old exit code.

### Test obligation

Any check promoted to a gating severity must ship with a test proving it **rejects bad input** — not merely that a compliant vault passes. Each gate therefore ships three things: a negative control on bad input, a sensitivity check that a compliant vault still exits `0`, and a guard that `--severity` cannot disable it.

| Gate | Tests |
|---|---|
| `eager_set_over_budget` | `tests/test_lint_runner.py::TestEagerSetGate` |
| `archive_pointer_dangling` | `tests/test_lint_runner.py::TestArchivePointerDangling` |

A negative control is only meaningful if it has been *observed failing*. Both classes above were verified by reverting the check (and, for `archive_pointer_dangling`, separately by downgrading its severity) and confirming the "must fire" tests fail while the "must not fire" tests keep passing. **A gate never observed failing is not a gate.**
