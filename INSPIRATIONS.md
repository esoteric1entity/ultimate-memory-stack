---
file: INSPIRATIONS
purpose: Credit upstream projects AND our internal collective work that informed the Agent Architect Stack design
status: active
license: Apache 2.0
---

# Inspirations

The Agent Architect Stack is built on the shoulders of giants — *and* on
the collective work of our own team of agents and machines. This file
gives credit where credit is due, in three categories:

1. **Upstream open-source projects** that influenced the design.
2. **Concepts / patterns** borrowed from research papers, blog posts, and
   prior art in the broader AI/agent ecosystem.
3. **Our own collective work** — concepts, decisions, designs, and
   implementations that originated across our various agents, machines,
   and prior-iteration bases, then were integrated into the first public
   release, v3.6.0 (often with hybrid-inclusion of upstream repo work
   toward the end of development).

**Following the project's standing principle** ("borrow ideas, not
numbers"): architectural patterns and design choices are transferable;
specific performance claims and benchmarks are situational and not borrowed.

---

## 1. Upstream open-source projects (with full citations)

### [Obsidian](https://obsidian.md/) — vault-as-folder knowledge management

- **Repo / website:** https://obsidian.md/ ; community plugins at https://obsidian.md/plugins
- **License:** Obsidian itself is free for personal use; community plugins vary
- **What we borrowed:** the idea that a memory vault should be a directory
  of plain Markdown files that any tool (GUI, CLI, or agent) can read, edit,
  and search. The "vault as folder" pattern is what makes UMS portable
  across agent harnesses, runnable in headless mode, and inspectable in
  a GUI without a database round-trip.
- **What we did NOT borrow:** Obsidian's closed-source rendering, sync,
  and publishing features. UMS uses a vault layout that is
  Obsidian-compatible (so users can opt into Obsidian as a viewer) but
  does not require Obsidian.
- **Recommended-addon:** `recommended-addons/obsidian-vault-config/`
  ships pre-configured community plugins + hotkeys for the UMS vault layout.

### [Graphiti](https://github.com/getzep/graphiti) — bi-temporal knowledge graph

- **Repo:** https://github.com/getzep/graphiti
- **License:** Apache 2.0
- **Citation:** Zep AI, Inc. and Graphiti contributors.
- **What we borrowed:** the idea that an agent's memory should be a
  bi-temporal knowledge graph — entities and relationships with both
  "event time" (when it happened in the world) and "ingestion time" (when
  the agent learned about it). This solves the "agent remembers what it
  thought at the time, not just what it thinks now" problem that simple
  RAG can't handle.
- **What we did NOT borrow:** Graphiti's specific graph-backend defaults,
  telemetry behavior (we disable PostHog by default), and
  LLM-prompt templates. The Memory branch's
  `recommended-addons/graphiti-installer/` is a separate install from the
  UMS core.
- **Documented in:** our internal vetting log (security review, PASS).

### [Graphify](https://github.com/safishamsi/graphify) — codebase symbol graph

- **Repo:** https://github.com/safishamsi/graphify
- **License:** MIT
- **Citation:** Safi Shamsi (`@safishamsi`) and Graphify contributors.
- **What we borrowed:** the idea of indexing a codebase as a graph of
  symbols (functions, classes, modules) and edges (calls, imports,
  inheritance) so an agent can navigate the codebase structurally rather
  than by grep. The 4-layer typosquat defense (L1-L4) is also adopted
  verbatim in the Security branch.
- **What we did NOT borrow:** Graphify's tree-sitter language bindings
  (we maintain our own lighter `codebase_indexer.py`). The 4-layer typosquat
  defense is reused because it is a clear security improvement with no
  innovation cost on our part.
- **Documented in:** our internal vetting log (security review, PASS).

### [Cline Memory Bank](https://github.com/cline/cline) — 6-file memory-bank convention

- **Repo:** https://github.com/cline/cline
- **License:** Apache 2.0
- **Citation:** Cline contributors.
- **What we borrowed:** the 6-file memory-bank convention — a small,
  fixed set of Markdown files the agent reads at session start — which
  our memory templates adopt as their baseline layout.
- **What we did NOT borrow:** Cline's editor extension or runtime; only
  the file convention is adopted.

### [LLMLingua / LLMLingua-2](https://github.com/microsoft/LLMLingua) — prompt compression

- **Repo:** https://github.com/microsoft/LLMLingua
- **License:** MIT
- **Citation:** Microsoft Research and LLMLingua contributors.
- **What we borrowed:** the prompt-compression idea — that long context
  can be distilled to its task-relevant core with little quality loss —
  which informs how UMS keeps memory loads compact.
- **What we did NOT borrow:** the LLMLingua models or library; UMS does
  not depend on them at runtime.

### [PostgreSQL](https://www.postgresql.org/) / [SQLite](https://www.sqlite.org/) / [DuckDB](https://duckdb.org/) — "data lives in a file you own"

- **Repos / websites:** https://www.postgresql.org/ ; https://www.sqlite.org/ ; https://duckdb.org/
- **Licenses:** PostgreSQL License (BSD-style); SQLite is in the public domain; MIT for DuckDB
- **What we borrowed:** the principle that user data should be in a file
  the user owns (not a proprietary service database). UMS stores memory
  in plain Markdown + JSON, not a proprietary database.
- **What we did NOT borrow:** the specific SQL/relational model. Our
  schemas are YAML-based and validated by lint rules, not by a SQL engine.

### [Apache Kafka](https://kafka.apache.org/) / Event Sourcing patterns

- **Repo / website:** https://kafka.apache.org/
- **License:** Apache 2.0
- **What we borrowed:** the append-only event log pattern. The Security
  branch's audit log (`agent_shield/audit.py` in the agent-shield repo)
  uses SHA-256-chained append-only JSONL — same conceptual model as
  Kafka topics + Kafka Connect sinks.
- **What we did NOT borrow:** Kafka's distributed-streaming runtime. Our
  audit log is a single-host file, not a distributed log.

### [Kubernetes](https://kubernetes.io/) / [Terraform](https://www.terraform.io/) / [Homebrew](https://brew.sh/) — modular pick-and-choose

- **Repos / websites:** https://kubernetes.io/ ; https://www.terraform.io/ ; https://brew.sh/
- **Licenses:** Apache 2.0 (Kubernetes); Business Source License / MPL (Terraform); BSD-2 (Homebrew)
- **What we borrowed:** the modular-composable ethos. Branches in this
  umbrella are peer siblings, installable independently. The user picks
  what they need, when they need it.
- **What we did NOT borrow:** the *mechanism* (kubectl apply, HCL, brew
  formulas). Our install model is `git clone` + per-branch install
  script — simpler, no orchestration runtime required.

### [Anthropic Claude](https://www.anthropic.com/) / Claude Code — supported harness (not a design source)

- **Documentation:** https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview
- **Role here:** Claude Code is one of the LLM harnesses the stack *runs on*
  (alongside OpenClaw and any 9-root-file harness) — a runtime, not a source
  we borrowed design from.
- **Provenance, to be unambiguous:** the agent architecture — the four-peer
  **Warden / Sentinel / Vault / Clerk** role model, the modular branch
  topology, and the spawn protocol — was conceived, designed, and specified
  **independently by esoteric1entity on private hardware**, and is original to
  this project (see §4). It does not derive from, and does not use, Anthropic's
  tool-use API contracts or function-calling schemas; it is
  implementation-agnostic and runs on Claude, OpenClaw, or any harness.

---

## 2. Concepts / patterns from prior art and research

These are not "code reuse" but "idea reuse." Each is a design pattern we
discovered independently and then validated against the published
literature.

- **Convergence is signal** — when multiple independent
  implementations arrive at the same architectural pattern, that's the
  strongest validation. Codify the convergence.
  - *Originating thought:* the "design patterns" tradition (Gang of Four,
    1994) and the "many eyes make all bugs shallow" principle applied to
    design rather than code.
- **Surface-only lint** — memory hygiene scanners surface
  problems for human review, they never auto-mutate content.
  - *Originating thought:* Andrej Karpathy's "Hygiene-pass" tweet and
    the broader "LLM-as-auditor" pattern; also inspired by the
    `pre-commit` and `eslint --fix` debate (auto-fix vs. surface).
- **5-element documentation discipline** — every decision
  carries Purpose, Rationale, Sound reasoning, Scope CAN, Scope CANNOT.
  - *Originating thought:* the AWS Well-Architected Framework's "design
    principles" and the "architecture decision record" (ADR) tradition
    ([Michael Nygard, 2011](https://cognitect.com/blog/2011/11/15/document-architecture-decisions)).
- **3-deep heartbeat window** — "current state" rolls in a 3-deep
  heartbeat window while "full history" stays in dated daily logs.
  - *Originating thought:* the `git log --oneline` + `git reflog`
    pattern; the operating-system "ring buffer" concept applied to
    persistent state.
- **Vault-as-folder with indexable metadata** — the idea that a vault
  can be searchable without a database by combining (a) plain-text
  content for grep, (b) YAML frontmatter for structured metadata, and
  (c) an optional knowledge-graph overlay for relational queries.
  - *Originating thought:* the [SilverBullet](https://silverbullet.md/)
    and [Tana](https://tana.inc/) approaches; also the classic
    "notebook + index" pattern from [Zettelkasten](https://en.wikipedia.org/wiki/Zettelkasten)
    (Niklas Luhmann, ~1950s).
- **LLM-as-wiki** — the concept of using an LLM to keep a structured
  wiki in sync with its source of truth, with human review on changes,
  comes from the broader LLM-wiki tooling ecosystem; UMS extends it so
  the LLM proposes schema entries, the human reviews, and the schema
  enforces the format.

---

## 3. Our collective work (the hybrid-inclusion model)

This stack is the product of work that originated across **our team's
various agents and machines**, and was integrated over the course of
multiple iterations. We are explicit about this: **the first public
release (v3.6.0) includes a substantial base of prior internal
iterations, with hybrid-inclusion of upstream repo work integrated
toward the end of development**.

In keeping with open-source norms, we credit this as **our collective
work** — the result of multiple agent sessions on multiple machines, with
each contributor's role acknowledged in `AUTHORS.md` and `NOTICE`.

### Where the original base came from

The design ideas for the Memory and Security branches — and for the
umbrella topology that hosts them — came from **prior internal iterations
on multiple machines and agent sessions**, before the first public
release (v3.6.0).
The following were part of that original base:

- The "agents need persistent memory" problem statement and the
  "memory as files in a vault" solution shape.
- The "modular umbrella, not monolith" architectural choice.
- The Warden / Sentinel / Vault / Clerk peer-agent role model.
- The 5-element decision discipline.
- The heartbeat + daily log + compactor pattern.
- The Tier 1 (HOT) / Tier 2 (WARM) / Tier 3 (COLD) load-priority model.
- The 4-pass scrub procedure for v3.6.0 pre-push hygiene.

These were developed using multiple AI agents across multiple machines,
working alongside — and under the direction of — the human designer.
Individual agent sessions contributed architecture, builds, reviews, and
documentation; every contribution passed through the project's cross-agent
peer-review cycle before adoption. One convergence deserves note: an
independent deployment arrived at the same cron-rotation design on its
own — that convergent implementation is what the convergence-is-signal
principle codifies.

Individual acknowledgements live in `AUTHORS.md` and `NOTICE`.

### What was hybrid-included (upstream repos integrated toward the end)

Toward the end of the v3.6.0 development cycle, we **integrated** (not merely
"cited") upstream work from the following repos. The hybrid inclusion
was deliberate — we kept our own structure as the backbone and used
upstream code where it filled a clear gap.

- **Graphiti** — the bi-temporal knowledge graph engine (Memory
  branch's `recommended-addons/graphiti-installer/`). This is a full
  install dependency, not a paraphrase. The hybrid is: our vault +
  schemas + lint pipeline on top, Graphiti's graph engine underneath.
- **Graphify** — the 4-layer typosquat defense (L1-L4) was adopted
  verbatim in the Security branch. The hybrid is: our broader 8-layer
  defensive model + Graphify's specific typosquat detection at Layer 3.
- **Obsidian vault config** — the community-plugins.json + hotkeys.json
  patterns for Obsidian vault automation were adopted from the Obsidian
  community plugin ecosystem.
- **PostgreSQL / SQLite / DuckDB** — not code-reused, but the design
  principle ("data lives in a file you own") is hybrid-included in the
  Memory branch's data model.

This hybrid-inclusion model means: **the first public release (v3.6.0)
is not 100% original code**, and we don't claim it is. The umbrella
architecture, the schemas, the documentation discipline, and the
integration pattern are original
contributions from our team. The graph engine, the typosquat defense,
and the vault config are upstream contributions integrated with our
work. Both are real, both are credited.

### Why we use the "hybrid inclusion" framing

We chose this framing over two alternatives:
1. **"100% original"** — would be inaccurate. We use Graphiti, Graphify,
   and Obsidian community plugins. Saying we didn't would be a lie.
2. **"100% a fork of X"** — would be inaccurate and would undersell our
   own substantial work. The umbrella topology, the 5-element
   discipline, the 4-pass scrub, and the agent topology spec are
   genuinely our own contributions.

The hybrid-inclusion framing is honest about what came from where, and
it treats upstream work with the same respect that the Apache 2.0
license treats attribution: cite the source, retain the copyright, and
be clear about what you contributed.

---

## 4. What is original to this project

The following are *not* borrowed from anywhere; they are original
contributions from esoteric1entity (sole project owner) and the broader
team's collective work:

- **The agentic-AI architecture itself — original to esoteric1entity.** This is
  the root contribution: the Stack grew out of a sustained personal design effort
  begun in **early 2026**, drawing on prior studies, practices, and influences (2025). It started as
  an original OpenClaw architecture developed across a series of design
  notebooks plus a multi-agent topology spec, then was **first deployed as the
  founder's own OpenClaw stack in March 2026** — the earliest and longest-running
  deployment in the lineage. The Memory and Security branches that make up this
  public release were **built afterward, by the founder's own directed agents on
  his own machines, on top of that original design** — they are its descendants,
  not its source. Concepts that carried over **directly** from that design into the
  public branches:
  - the **tiered (HOT/WARM/COLD) memory model** and the **9-root-file interface**;
  - **journaling-as-governance** with traceable provenance → the append-only **audit log** (JSONL; hash-chaining is designed but not implemented);
  - the **approval-gate / human-in-the-loop** workflow → the **Tribunal** cross-review pattern;
  - **tiered local-vs-paid routing**, **local-first autonomy**, and **component separation** (agent ≠ runtime ≠ UI);
  - the **sandbox / least-privilege** model and **skill-vetting** → agent-shield Layers 1–4;
  - **immutable provenance logging** → agent-shield Layer 7 (audit);
  - the **modular, install-what-you-need** branch philosophy → the umbrella topology below.
- The **modular umbrella topology**: the idea that
  Memory, Security, PM, and Orchestration are *peer sibling branches*
  with no hard runtime dependencies.
- The **5-element documentation discipline**: every decision
  carries Purpose, Rationale, Sound reasoning, Scope CAN, Scope
  CANNOT.
- The **agent topology spec**: the Warden / Sentinel / Vault / Clerk
  peer-agent role model, including the spawning protocol and
  parallel/serial spawn matrix.
- The **heartbeat + daily log + compactor** pattern: the idea that
  "current state" rolls in a 3-deep window while "full history" stays
  in dated daily logs.
- The **pick-and-choose install model** with **role hierarchy for
  contributors** (quorum principle).
- The **Karpathy Lint surface-only** principle: memory
  hygiene scanners surface problems; they never auto-mutate.
- The **convergence-is-signal** principle: when two
  independent implementations arrive at the same pattern, codify the
  convergence.
- The **borrowing ideas, not numbers** principle.
- The **4-pass v3.6.0 pre-push scrub procedure**: author scrub,
  content scrub, path scrub, mirror-line normalization.
- The **per-branch `release/<name>/` layout**: the idea that the first
  public release (v3.6.0) should consist of install-ready package
  directories, one per branch, kept separate from the rest of the R&D tree.

---

## 5. How to add to this list

If you submit a PR that introduces a new architectural idea borrowed
from an upstream project, or that adds new collective-work credit, add
it to this file. Be specific about what was borrowed and what wasn't —
the goal is honesty, not exhaustive attribution.

If your contribution is a hybrid-inclusion (upstream code integrated
with our own structure), add it to section 3 with a clear description
of the hybrid boundary.

## Cross-references

- [`README.md`](./README.md) — project overview (also has a short Inspirations section)
- [`LICENSE`](./LICENSE) — Apache 2.0
- [`AUTHORS.md`](./AUTHORS.md) — author + acknowledgements
- [`NOTICE`](./NOTICE) — copyright + acknowledgements
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to contribute
- [`common-specs/MEMORY_PROTOCOL.md`](./common-specs/MEMORY_PROTOCOL.md) — the operational memory protocol
