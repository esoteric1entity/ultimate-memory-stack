# Ultimate Memory Stack — End-User Cheat Sheet (Core)

> **Version:** 1.2 — stable
> **Audience:** Anyone deploying the Ultimate Memory Stack for the first time
> **Approximate read time:** 8 minutes (skim) · 12 minutes (with the quickstart section)
> **Companion files:** `general-edition/USER_CHEAT_SHEET_general_addendum.md` (general/public-context) | **`INSTALL.md`** (addon install reference — see "Recommended addons and core skills")

---

## Quickstart

**If you're deploying fresh:** Start with `INSTALL.md` — pick an install method, then follow the "Recommended addons and core skills" section for the addons.

**If you've already got the base stack and want the add-on components:** Read `INSTALL.md` → "Recommended addons and core skills".

**The 6 add-on components (originally delivered with v3.5):**

| Component | Skill | When to install |
|---|---|---|
| Obsidian vault config | `/config-obsidian-vault` | Use Obsidian for memory editing |
| LLMLingua installer | `/install-llmlingua` | Token-budget pressure / cost optimization |
| Graphiti installer | `/install-graphiti` | Bi-temporal knowledge graph queries |
| Graphify installer | `/install-graphify` | Codebase symbol-graph (31 langs) |
| Audit Quarantine | `/audit-quarantine` | Auto-available — use when quarantine has entries |
| OpenClaw adapter | `/install-openclaw-adapter` | Deploying to OpenClaw harness |

**v3.5 retrofits to MEMORY_PROTOCOL.md are AUTOMATIC** — included in base stack v3.5:
- Context Rot mitigation (EXTENDED §E1 — Tier 1 pinned start AND end)
- Option C self-improvement Lint checks (EXTENDED §E7 — 5 new checks)
- Hard-cap enforcement (§11 / EXTENDED §E8 — file size limits now enforced)
- PageRank promotion (§12 / EXTENDED §E9 — 4-trigger logic)

---

## 30-Second TL;DR

The Ultimate Memory Stack gives Claude persistent memory across sessions. Without it: every session starts blank. With it: Claude remembers your decisions, projects, preferences, and history.

**The 3 things you absolutely must know:**

1. **`session_state.md` is your lifeline.** It tells Claude where you left off. Keep it specific (file names, line numbers, exact status). Update at session end.
2. **`/compact` is your friend, used right.** Run it before context hits ~85%. Before compacting, write a heartbeat (file:line + current task) so Claude can resume cleanly after.
3. **Don't fight the protocol.** It's designed to load smart, write structured, and protect you from memory poisoning. Trust it.

That's it. Everything below is depth.

---

## Top 10 Habits

What separates effective users from confused ones:

1. **Be specific in everything.** "Fixed the bug" is useless. "Fixed race condition in auth.py:47, changed to await refresh_token() with 3s retry" is useful. Apply to session state, decisions, feedback.
2. **End every session with "update session state."** Even a 5-second update saves 5 minutes next session.
3. **Promote recurring feedback to standing rules.** If Claude makes the same mistake 3+ times, that pattern should become a permanent rule (it auto-promotes per pattern-key threshold).
4. **Use confidence levels (FINAL/TENTATIVE/EXPLORATORY) honestly.** FINAL = settled forever. TENTATIVE = subject to revision. EXPLORATORY = testing. Marking everything FINAL erases nuance.
5. **Heartbeat during long sessions.** ~30 min checkpoints in session_state.md prevent context loss if anything crashes. Don't skip this.
6. **Run `/compact` proactively, not reactively.** Once context exceeds ~85%, your responses degrade. Compact before you feel pressure.
7. **Review the quarantine queue regularly.** Suspicious entries land there. Review = release-or-discard with brief justification.
8. **Don't manually edit memory files unless you understand the consequences.** YAML frontmatter is precise; broken frontmatter quarantines the entry on next read.
9. **Document the WHY, not the WHAT.** "Used Pandas" tells future-you nothing. "Used Pandas because we may add categorical ops later; SQLite was rejected because mixed dtypes get painful" tells future-you everything.
10. **Trust the architecture; don't customize prematurely.** The defaults are research-backed and battle-tested. Customize only when you have a specific friction.

---

## When to `/compact` — Decision Tree

```
Are you currently working on a multi-step task?
├── YES → Don't compact mid-task. Finish current step first.
│         Heartbeat session_state.md, then compact at task boundary.
│
└── NO → How full is your context?
         ├── <50% → Don't compact. Wastes work.
         ├── 50-75% → Compact ONLY if you're starting a fresh sub-task.
         ├── 75-85% → SHOULD compact. You'll feel the squeeze soon.
         ├── 85-95% → MUST compact NOW. Heartbeat first.
         └── >95% → Already too late. Heartbeat MAX detail, then /compact.
                    Resume from heartbeat after compaction.
```

### Pre-compact checklist (run before `/compact`)

Before invoking `/compact`, take 1 minute to:

1. **Update session_state.md heartbeat** with:
   - Current task name + specific sub-step
   - File(s) being modified + line numbers
   - Specific blocker (if any)
   - "Resume by re-reading [file]:[line] and continuing [step]" instruction
2. **Verify mirror parity** (if you mirror your memory dir to a second location) — `setup.sh --verify` or equivalent
3. **Stage any pending DEC entries** — promote inline decisions to `decisions.md` if they're settled
4. **Note any pending agent spawns or tool calls** that should resume after compaction

After `/compact`, your first action should be reading session_state.md to pick up exactly where the heartbeat left you.

---

## Slash Commands Reference (the 13 that matter)

Claude Code has ~60 slash commands. Realistically, you'll use these 13:

| Command | When to use |
|---------|-------------|
| `/compact` | Compact context (see decision tree above) |
| `/clear` | Wipe conversation but keep memory files |
| `/help` | List available commands |
| `/cost` | Check token usage this session |
| `/model` | Switch Claude model (Sonnet, Haiku, Opus) |
| `/init` | Initialize CLAUDE.md for a new project |
| `/agents` | List/manage sub-agents |
| `/permissions` | Adjust tool permissions |
| `/review` | Run code review on current changes |
| `/memory` | View/edit memory files |
| `/audit-quarantine` | Review quarantine queue (review workflow — surfaced as a toast at session start) |
| `/lint-memory` | Run memory integrity check — surfaces orphans, broken refs, stale TENTATIVE, stale citations, contradictions (T3+) |
| `/graphify` | Build codebase knowledge graph (Tier C adjacent tool — see TIER_C_ACTIVATION.md). Available after `uv tool install graphifyy && graphify install`. Multi-modal: code + SQL + docs + papers + images + videos. Runs locally for code (Tree-sitter AST); LLM for docs. |

If a command isn't in this list, you probably don't need it.

## Interpreting Lint Findings

Lint is your memory's periodic check-up. It runs automatically (monthly by default) and on-demand via `/lint-memory`. Here's what each finding type means + how to act:

| Finding | What it means | Common remediation |
|---------|---------------|---------------------|
| **Orphan** | Entry with no incoming references | Either: add link from a related entry, archive, or `lint_orphan_ignore: true` in frontmatter |
| **Broken reference** | `[[ID]]` or `supersedes:` points to non-existent entry | Fix the reference (often a typo); fuzzy match suggests likely correct ID |
| **Stale TENTATIVE** | Non-FINAL decision sat in limbo for N+ sessions | Promote to FINAL (you've committed), demote to archive (you've abandoned), or update with current thinking |
| **Stale webfetch** | External-source entry not re-validated recently | Re-validate source URL; update `last_validated` field; or archive if no longer needed |
| **Contradiction** *(T3+)* | Two active entries assert conflicting facts without explicit supersession | Either supersede one with the other, clarify they apply to different contexts, or unify to a single position |
| **Missing concept** *(T3+)* | Term mentioned many times without dedicated reference entry | Create a reference entry anchoring the concept's definition; or ignore if term is well-known |

**Severity guide:**
- 🔴 HIGH/CRITICAL — needs attention; may block new writes until resolved under strict compliance presets
- ⚠️ MEDIUM — recommended fix
- ℹ️ LOW — informational; user judgment

Lint **never auto-fixes**. You always decide what to do. To dismiss a finding: tell Claude "ignore for now" (will resurface next lint run unless resolved).

**Tiering checks** (mostly ℹ️ LOW; two are 🔴 HIGH and, as of v4.0.1, make `lint_runner.py` exit non-zero — `eager-set-over-budget` and `archive-pointer-dangling`): as `sessions/`, `decisions/`, and `feedback/` grow and rotate old content into `memory/archive/<category>/` (see "Rotation" in the Glossary), lint watches for drift — an archive entry not listed in its `ARCHIVE_INDEX.md`, a hot-side entry count out of sync, a missing index file, an oversized index one-liner, a file nearing its §11 cap, or the live always-loaded set exceeding `eager_set_budget_bytes`. Full check list: `SCHEMA_lint.md` §13.

---

## 12 Anti-Patterns to Avoid

Common mistakes that erode value:

1. **Storing every detail.** Memory is for what's important to RECALL, not what's ephemeral. Don't store this hour's TODO list.
2. **Vague session_state entries.** "Worked on the bug" — useless. Be specific.
3. **Never compacting.** Context bloat slows everything down; compact regularly.
4. **Compacting mid-task.** Loses work-in-flight. Heartbeat first or wait for task boundary.
5. **Manually editing decisions to mark TENTATIVE as FINAL.** Confidence levels are honest signals; don't game them.
6. **Skipping the setup wizard.** The 5-minute wizard prevents 5 hours of confusion later.
7. **Disabling audit log when you shouldn't.** If your context is regulated, the audit log is your forensic evidence. Keep it on.
8. **Storing secrets in memory files.** NEVER. Use a password manager. Memory files are plain markdown.
9. **Storing PII/PHI when your preset doesn't allow it.** Detection will quarantine. Don't fight the system.
10. **Ignoring the quarantine queue.** Suspicious entries are surfaced for a reason. Review them.
11. **Modifying common-specs files.** Use override files (`*.override.md`) per your edition. Modifying common-specs breaks brand-protection.
12. **Treating the memory stack as a one-time install.** It's a system. It needs occasional consolidation passes (every 10 sessions).

---

## Memory Poisoning — User-Side Defenses

The memory stack has defenses (provenance tracking, validation-on-read, quarantine, optional cryptographic signatures). YOUR contribution:

### Spot-check WebFetch-sourced entries

If an entry has `source_agent: webfetch`, treat it as PROVISIONAL until you've personally verified:
- The URL is what you intended
- The content matches what you remember
- No suspicious prompt-injection patterns (e.g., text that looks like instructions to Claude)

**Real incident:** On 2026-05-12, a WebFetch-sourced entry contained a hidden prompt injection. The memory stack's validation caught it. Don't rely on detection alone — review.

### Don't manually paste large unverified blobs

If you copy content from an external source into a memory entry, scan it briefly. Prompt injections often hide as "system instructions" disguised as content.

### Trust source_agent attribution

Each entry has `source_agent` (who wrote it). If you see entries written by an agent you didn't expect, investigate. The memory stack records provenance for exactly this reason.

### Verify before promoting

Before promoting an inline decision to `decisions.md`, ask: am I confident enough to mark this FINAL? If not, keep it TENTATIVE.

---

## Bi-Temporal Memory — Quick Intro

The memory stack supports two date axes for memory facts:

- **`created_at`:** when you recorded the fact
- **`valid_at`:** when the fact became true in the world
- **`invalid_at`:** when the fact was superseded by a newer fact

This lets you ask: *"What did we believe about X on date Y?"* — and get the right answer even if you've since changed your mind.

**Practical example:**
- In April, you decide to use PostgreSQL (`valid_at: 2026-04-15`)
- In August, you supersede with SQLite for embedded use (`valid_at: 2026-08-01`)
- PostgreSQL entry gets `invalid_at: 2026-08-01` set automatically
- Query "what was our DB choice in June 2026?" returns PostgreSQL (still valid then)
- Query "what was our DB choice in September 2026?" returns SQLite

Most users won't think about bi-temporal explicitly — but it's useful for forensic/regulated audit (knowing what was believed at any historical date).

---

## Wiki-Links — Cross-Reference Syntax

Within memory entry bodies, you can write inline references using `[[ID]]` syntax (like Obsidian, Logseq, Roam):

```markdown
This decision builds on [[DEC-023]] and supersedes [[DEC-019]].
See [[B5]] for the bi-temporal pattern that enables this.
```

These are equivalent to YAML `related: [DEC-023, DEC-019]` fields but more readable inline. At T2+, an indexer auto-syncs both forms.

If you open your `memory/` directory in Obsidian, wiki-links become clickable + graph view renders the connections.

---

## Glossary

- **Bi-temporal model:** Facts have both "when recorded" + "when true in the world" dates. Lets you query state at any historical date.
- **Common-spec:** The universal 95% of the memory stack (schemas, protocol, architecture) shared across every edition and deployment.
- **Compaction:** Reducing context window usage by summarizing earlier conversation. Triggered by `/compact`.
- **DEC-NNN:** Decision entry ID. Every architectural choice has a DEC entry with purpose/rationale/scope.
- **Edition:** A packaging variant of the memory stack, selected at install time, that sets which layers and presets are mandatory vs optional. The general edition (user-configurable presets) ships in this package.
- **Frontmatter:** YAML block at top of each memory entry with metadata (id, dates, source_agent, status, etc.).
- **Heartbeat:** Brief update to session_state.md every ~30 minutes documenting current task state.
- **MEMORY_INDEX.md:** Master registry of memory file counts + categories.
- **Override file:** Per-edition customization that REPLACES sections of common-spec files (`*.override.md`).
- **Pattern-key:** Stable dotted identifier (e.g., `output.formatting.tables`) for recurring patterns. Auto-promotes at threshold.
- **Quarantine:** Isolation zone for suspicious entries. Reviewed by user; can release or discard.
- **Rotation (tiering, v4.0.0):** When `sessions/`, `decisions/`, or `feedback/` hits its §11 line cap, the oldest entries move — full content to `memory/archive/<category>/<category>-archive.md`, a one-line pointer to that category's `ARCHIVE_INDEX.md`. Nothing is deleted; every rotated entry stays findable by ID. Bringing a rotated entry back is "rehydration."
- **Source_agent:** Attribution field — who wrote this entry? `user`, `orchestrator`, or consumer-defined sub-agent names (registered at the setup wizard).
- **Tier (T0-T4):** Deployment tier based on available infrastructure. T0 = base; T4 = ideal state (all features active).
- **YAML frontmatter:** Machine-readable metadata header on every memory entry. Critical to keep valid.

---

## Where to Go Next

- **Setting up?** Read your edition's `DEPLOYMENT.md`.
- **Upgrading from v2.0?** Read your edition's `MIGRATION_v2_to_v3.md`.
- **Upgrading from v3.6.x?** Read your edition's `MIGRATION_v3.6_to_v4.0.md`.
- **Want HIPAA-grade behavior?** HIPAA/PHI is out of scope for this edition.
- **Tweaking presets?** Read `overrides/compliance-presets.override.md` (general-edition) or your edition's overrides.
- **Curious about architecture?** Read `ARCHITECTURE.md` in common-specs (deeper, ~30 KB).

## Cross-references

- `ARCHITECTURE.md` (full layer architecture)
- `MEMORY_PROTOCOL.md` (operational rules)
- `BOOTSTRAP_PROMPT.md` (deployment activation prompt)
- `MODULARITY.md` (brand-protection + consumer architecture pluggability)
- End-user best-practices research (primary source for this document)
