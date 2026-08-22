# Tier C Activation Guide — Ultimate Memory Stack v4.0.1

> **File:** `common-specs/TIER_C_ACTIVATION.md`
> **Version:** 1.0 — 2026-05-19
> **Author:** esoteric1entity, AI-Assisted
> **Design basis:** ideal-first design principle; Tier C designed-in feature set; 2026-05-19 research refresh

---

## Purpose

The v3.0 spec **designs in** 9 Tier C features (C1–C10, minus C5 which is deferred to a future evolution layer). The installer (`setup.sh` / `setup.py` / `setup.ps1`) does NOT auto-install them — that's a deliberate design choice ("ideal-first design, gated by tier"). This doc walks you through manual activation of each Tier C tool when its deployment tier is unblocked.

**Worked example (two deployments of the same stack):**
- A locked-down workstation: T0 effective (Code Execution blocked, Skills blocked, no Node.js)
- A developer laptop: T3 effective (Python + cryptography + Node.js, Skills enabled)
- Most Tier C tools below CAN activate on the laptop today; the workstation runs the same stack at T0

---

## Activation overview by tier

| Tool | What it is | Activates at | Install effort | Status |
|---|---|---|---|---|
| **C1 Auto-Dream** | Anthropic `dreaming-2026-04-21` beta — offline async consolidation | T4 (Code Exec + Anthropic beta) | High — requires beta access | Dormant; design spec only |
| **C2 Graphiti + Kuzu** | Bi-temporal knowledge graph (Layer 5) | **T1 (Ollama) or T3 (Anthropic API)** | Medium — install from the add-on's hash-pinned lock (§C2), + MCP wiring | Refreshed 2026-08-20 |
| **C3 Graphify** | Codebase structural knowledge graph (adjacent tool, §11.5) | **T3 (Python) or T4 (Skill install)** | Low — `uv tool install graphifyy && graphify install` | Refreshed 2026-05-19 |
| **C4 Cryptographic signatures** | HMAC memory-entry signing (Ed25519 offline-key variant planned) | T3 (Code Execution) | Low — `cryptography` package + key gen via setup.py | Designed-in; signing pipeline not yet implemented |
| **C6 LLMLingua / LongLLMLingua** | Prompt compression on cached prefixes (~40× compound discount) | T3 (Code Exec + Python ML libs) | Medium | Designed-in; further research needed |
| **C7 Aider repo-map** | Tree-sitter + PageRank code-structure primitive (adjacent tool, §11.5) | T3 (Code Execution + Aider integration) | Medium | Designed-in; further research needed |
| **C8 LLM-as-judge evals** | Extends the manual eval harness with auto-grading | T3+ (LLM-callable infrastructure) | Medium-High | Designed-in; further research needed |
| **C9 Transformers.js embeddings** | Alternative semantic-search backend (if Ollama path B9 isn't viable) | T2 (Node.js 18+) | Medium | Designed-in; future research |
| **C10 Skill / template extraction pipeline** | Closes inline → decisions → standing rule → reusable Skill promotion ladder | T3 (Code Exec) + T4 (Skills) | High | Designed-in; future research |

**Out of scope:** C5 self-improvement loop — deferred to a future evolution layer.

---

## C2 — Graphiti + Kuzu (Layer 5 Knowledge Graph)  ✅ INSTALLER READY (v3.5)

> **Installer Skill:** `recommended-addons/graphiti-installer/`
> **Vetting:** passed security vetting with conditions (2026-05-27); CVE-2026-32247 patched at v0.28.2 (this installer floor pin `>=0.29.1` covers it)
> **Telemetry:** DISABLED by default (env var persisted as a standing vetting condition)
> **Recommended backend:** Kuzu (immune to Cypher injection class — parameterized labels).
> ⚠️ **Kuzu upstream is ARCHIVED, not merely quiet.** `github.com/kuzudb/kuzu` was archived
> read-only on **2025-10-10**, the same day it shipped its final release (0.11.3); Kùzu Inc.
> was acquired by Apple, disclosed via an EU DMA filing in February 2026. It is finished, not
> abandoned mid-flight — 0.11.3 installs everywhere we support and still publishes Windows wheels.
> MIT, so a fork is permitted; an active community successor exists (**LadybugDB**), but
> graphiti-core has no LadybugDB driver.
>
> ⚠️ **Windows users, read this before building a graph.** graphiti-core issue **#1469** (OPEN,
> filed 2026-05-06, last activity 2026-08-14) reports `add_episode` crashing the host process with
> an access violation inside Kuzu's C extension on Windows 11, at ~50 episodes. Reads are fine;
> only writes crash. It is a single report with a faulthandler trace, **no maintainer response, and
> we have not reproduced it** — credible, not confirmed. But an archived upstream means an engine
> bug would never be fixed, so plan for a server backend (Neo4j / FalkorDB) as your fallback.
>
> See `recommended-addons/graphiti-installer/requirements.txt` for the full disclosure and the
> maintenance position. *(Verified against PyPI + the GitHub API, 2026-08-20.)*
> **Activation:** invoke `/install-graphiti` (Skill) OR follow `INSTALL_GRAPHITI.md` manually

### What it is

Temporal-fact knowledge graph of memory entries. Apache 2.0. v0.29.3 (July 27, 2026). ~30.1k stars *(as of 2026-08-20 — a star count with no as-of date is a claim that rots silently)*. Architecture paper: `arXiv:2501.13956` — see `CITATIONS.md` for what that paper actually is and which of its numbers we refuse to cite. Per ARCHITECTURE.md §9, this is the **designed-in storage upgrade** for temporal provenance / point-in-time audit.

### When to activate

- **T1+ path (RECOMMENDED for cost-conscious activation):** Ollama installed locally. Graphiti uses Ollama as the LLM for ingestion. No cloud API dependency.
- **T3 path:** Anthropic API (or OpenAI/Gemini) for ingestion. Faster + higher quality, but cloud costs.

In the worked example above:
- The locked-down workstation (T0): cannot activate (no Code Execution, no Ollama)
- The developer laptop (T3): can activate today via Anthropic API path
- Either machine + Ollama install: T1 activation possible

### Install commands

**Use the add-on's hash-pinned lockfile. This is the only supported path:**
```bash
pip install --require-hashes -r <path-to-install-graphiti-skill>/locks/requirements-py3.12.lock
```
Match the lock to your Python (3.10 / 3.11 / 3.12 / 3.13). This is what `/install-graphiti`
runs, and it pins `graphiti-core==0.29.3` + `kuzu==0.11.3` by hash.

> ⚠️ **Do NOT `pip install graphiti-core[kuzu]`.** This document previously recommended it. Two
> problems: it is unpinned (you get whatever is latest, unverified against this stack), and
> graphiti-core has **deprecated the `[kuzu]` extra**. The second one fails *silently*: pip does
> not error on an extra a distribution no longer provides — it exits `0` and installs the package
> without it. On pip 25.3 there is not even a warning (measured 2026-08-20:
> `pip install --dry-run --no-deps "requests[does-not-exist]"` → `Would install requests-2.34.2`,
> exit 0, no diagnostic). So once upstream removes the extra, that command installs graphiti-core
> **with no graph backend** and reports success. The hash-pinned lock is immune to both: it names
> `kuzu` directly, not via the extra.
>
> The deprecation is on the EXTRA only. `graphiti_core/driver/kuzu_driver.py` still ships on the
> default branch and in 0.29.3, and no removal is scheduled — no target version, no milestone, no
> merged removal PR. *(Verified 2026-08-20.)*

**Choosing an LLM provider for ingestion** — do this by editing the add-on's `requirements.txt`
and regenerating the lock, never by installing ad-hoc:

> ⚠️ **Changing the dependency set needs the SOURCE PACKAGE, not just an installed skill.**
> `regenerate-locks.py` is a maintainer tool and is deliberately not copied into an installed
> skill — an installed skill has `requirements.txt` and `locks/`, but nothing to rebuild them
> with. To make any change below, clone the package
> (`git clone https://github.com/esoteric1entity/ultimate-memory-stack`), edit and regenerate
> there, then re-run the add-on install against the new lock. You also need
> [`uv`](https://docs.astral.sh/uv/) and network access. Paths below are relative to the
> package root.

- **Anthropic API:** uncomment the `anthropic>=0.49.0` line in
  `recommended-addons/graphiti-installer/requirements.txt`, then run
  `python recommended-addons/regenerate-locks.py graphiti`.
  ⚠️ Do **not** write `graphiti-core[anthropic]` instead. The dependency is named directly for the
  same reason `kuzu` is — an extra can be withdrawn upstream and pip will install without it,
  silently and successfully. Uncommenting alone does nothing: the install reads the **lock**, so
  you must regenerate.
- **Ollama:** nothing to install — it speaks the OpenAI-compatible API. Point Graphiti at it with
  `OPENAI_BASE_URL=http://localhost:11434/v1` and `OPENAI_API_KEY=ollama` (any non-empty string).

### Verification

```python
from graphiti_core import Graphiti
from graphiti_core.driver.kuzu_driver import KuzuDriver

driver = KuzuDriver(db="/tmp/graphiti.kuzu")
# If this constructs without error, Kuzu embedded backend is working.
print("Kuzu driver OK")
```

### Integration with the memory stack

Two paths:

**(a) Python bridge** — ingest `memory/` markdown into Graphiti:
- Walk `memory/decisions/`, `memory/feedback/`, `memory/projects/`
- Parse SCHEMA_A18 YAML frontmatter
- For each entry, call `graphiti.add_episode(...)` with the entry's content + `valid_at` timestamp from frontmatter
- Graphiti builds the bi-temporal knowledge graph automatically
- Re-run on demand; graph rebuilds from markdown source-of-truth

**(b) MCP server (NEW — refresh 2026-05-19)** — wire Graphiti directly into Claude Code:
```bash
# Start Graphiti MCP server (refer to graphiti/mcp_server/ in the repo)
# Then add to your Claude Code MCP config (.claude/settings.local.json):
# {
#   "mcpServers": {
#     "graphiti": { "command": "...", "args": [...] }
#   }
# }
```
This makes Graphiti queries available as `mcp__graphiti__*` tools in your Claude Code session — same pattern as your existing `mcp__ccd_session__*` and `mcp__Claude_Preview__*` namespaces.

### Caveats

- **Vendor benchmark numbers** (94.8% / +18.5% on LongMemEval / DMR) are not treated as authoritative — adopt the design, not the numbers.
- **First ingestion** is LLM-intensive (graph extraction). Subsequent updates are incremental.
- **Bi-temporal model** is the load-bearing value — point-in-time queries ("what did we believe on date X?") for audit/forensic reconstruction.

### Deactivation

```bash
pip uninstall graphiti-core
# Then remove the Kuzu DB file:
rm /tmp/graphiti.kuzu  # or wherever you put it
```

Memory stack at Layer 1 is unchanged — graph is a derived index, markdown is the source of truth.

---

## C3 — Graphify (Codebase Structural Graph, §11.5 Adjacent Tool)  ✅ INSTALLER READY (v3.5)

> ⚠️ **PACKAGE NAME IS `graphifyy` (DOUBLE-Y).** Single-y `graphify` on PyPI is an UNRELATED package — typosquat risk.
> **Installer Skill:** `recommended-addons/graphify-installer/`
> **Vetting:** passed security vetting with conditions (2026-05-27); active upstream (116 releases in ~8 weeks at vetting)
> **Defense layers active:** L1 bash-guard typosquat pattern + L2 manifest verification + L3 README warning + L4 exact pin `graphifyy==0.8.21` + L5 hash-pinned install (`--require-hashes` against `locks/`)
> **Activation:** invoke `/install-graphify` (Skill) OR follow `INSTALL_GRAPHIFY.md` manually
> **Status:** Skill registration validated — this Skill formalizes that pattern

### What it is

Tree-sitter (31 languages) AST + NetworkX + Leiden community detection (via graspologic) + vis.js. **Apache-2.0** license. Multi-modal: code + SQL + R + shell + docs + papers + images + videos.

> ⚠️ **Corrected 2026-08-20 — the previous "correction" here was the error.** This line read
> *"MIT license (refresh 2026-05-19 — prior spec said Apache 2.0; corrected)"*. The **original
> spec was right**: `Graphify-Labs/graphify` ships an **Apache License 2.0** — confirmed three
> ways (the repo's `LICENSE` file read directly, the GitHub API, and PyPI's `license_expression`).
> Per the project rule, a licence is read from the LICENSE file, never from a badge or a summary.
> The same wrong "MIT" had also propagated into the add-on's `SKILL.md` frontmatter and into
> `smoke_test.py`, which printed it as verified fact.
>
> Version and star figures were also stale and are deliberately **not restated here** — they rot.
> As of 2026-08-20: latest release **0.9.48**, ~**109k** stars; this add-on pins **0.8.21**, which
> is a security-vetting decision, not a staleness bug. Check the current numbers at the source.

**Important:** Graphify operates on **codebase files**, NOT memory entries. Its output is ingested by Layer 1 as a source artifact (`memory/references/codebase_graph_*.md`), but Graphify is not a memory backend.

### When to activate

- **T3 (Python on local machine):** Manual install path
- **T4 (Skills enabled):** Skill install path (one-line; cleanest)

In the worked example above:
- The locked-down workstation: Skills BLOCKED — manual install via uv possible if Code Execution unblocks
- With Skills ENABLED, a **one-line Skill install is possible today** (validated 2026-05-21)

### Prerequisites

**Tooling:**
- Python 3.10+
- `uv` — if not present, install via: `curl -LsSf https://astral.sh/uv/install.sh | sh` (adds `uv` + `uvx` to `~/.local/bin/`)
- Alternatives: `pipx install graphifyy` or `pip install graphifyy` work too

**LLM backend (required for full pipeline; NOT required for `--version` / `--help` / `install` / `update --no-cluster`):**

Graphify's full pipeline runs an AST pass (local, no LLM) + a semantic-extraction pass over docs/papers/images/videos (LLM required). Pick ONE backend:

| Backend | Env var to set | Cost posture |
|---------|----------------|--------------|
| Gemini (default) | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Free tier available |
| Claude | `ANTHROPIC_API_KEY` | Cost-controlled |
| OpenAI | `OPENAI_API_KEY` | Cost-controlled |
| Moonshot (Kimi) | `MOONSHOT_API_KEY` | Cost-controlled |
| DeepSeek | `DEEPSEEK_API_KEY` | Cost-controlled |
| Ollama (LOCAL — privacy preferred) | `--backend ollama` flag (requires Ollama running locally) | FREE; no API key |

Privacy posture: prefer Ollama for sensitive codebases (code-pass is already local via Tree-sitter AST; choosing Ollama for the semantic pass keeps docs/papers content local too).

### Install commands

**Recommended (Skill install at T4):**
```bash
uv tool install graphifyy   # note: PyPI package is "graphifyy" with double-y
graphify install            # registers ~/.claude/skills/graphify/SKILL.md + creates/updates ~/.claude/CLAUDE.md
```

**⚠️ Side-effect note (observed during validation):** `graphify install` creates/updates `~/.claude/CLAUDE.md` at the **USER level** (applies to ALL Claude Code sessions on this machine, not just one project's working directory). On a machine with no prior `~/.claude/CLAUDE.md`, this is a NEW file. If you already have `~/.claude/CLAUDE.md`, verify append vs overwrite behavior before installing (Graphify upstream concern; check your machine).

This makes `/graphify` a slash command in Claude Code. Same pattern across 14+ assistants (Codex, OpenCode, Cursor, Gemini CLI, etc.).

**Alternative (pipx or pip):**
```bash
pipx install graphifyy && graphify install
# OR
pip install graphifyy && graphify install
```

**Optional extras:**
```bash
pip install 'graphifyy[sql]'      # SQL schema graph support
pip install 'graphifyy[office]'   # docx / pptx / xlsx support
pip install 'graphifyy[video]'    # video transcription (uses faster-whisper)
pip install 'graphifyy[mcp]'      # MCP server mode
pip install 'graphifyy[leiden]'   # explicit Leiden via graspologic (Python < 3.13)
```

### Verification

```bash
# LLM-free smoke tests (no API key needed):
graphify --version                       # version sanity (e.g., "graphify 0.8.14")
graphify --help                          # see all subcommands
graphify install                         # idempotent Skill re-registration
graphify update ./my-project --no-cluster   # AST-only pass, no LLM

# Full pipeline (REQUIRES LLM backend — see Prerequisites above):
# Correct syntax for v0.8.14+ (older v0.8.13-era docs incorrectly said `graphify build`):
graphify ./my-project                    # default = full pipeline; outputs to ./graphify-out/
ls ./graphify-out/                       # expect: graph.html, GRAPH_REPORT.md, graph.json, cache/
```

### Integration with the memory stack

```
your codebase
     │
     ▼
[graphify ./codebase]  → ./graphify-out/
     │
     ▼
graphify-out/{graph.html, GRAPH_REPORT.md, graph.json}
     │
     ▼ (copy/symlink)
memory/references/codebase_graph_<YYYY-MM-DD>.md  ← Layer 1 ingestion
     │
     ▼ (then Layer 3 + Layer 5 index normally)
```

Place the Graphify output in `memory/references/` and the rest of the memory stack treats it as an ordinary source artifact. No special integration required.

### Multi-modal usage

Graphify can ingest more than just code:
- SQL schemas → graph nodes
- Docs / papers / PDFs → concept extraction (sent to LLM)
- Images → vision LLM extraction
- Videos / audio → faster-whisper transcription (audio never leaves machine) + LLM extraction

**Privacy posture:** Code files never leave the machine (Tree-sitter AST pass is local). Docs/papers/images go to whatever LLM you configured. Audio/video transcribed locally.

### Caveats

- **Vendor benchmark claim** ("71.5× / 499× fewer tokens" from LucasRosati's ClaudeCodeMemorySetup + PyShine/GoPenAI articles) is not treated as authoritative (strawman baseline). Adopt the tool, not the inflated number.
- **First-time graph build** on a large codebase can take minutes; cached afterward.
- **Optional MCP server mode:** `python -m graphify.serve graphify-out/graph.json` runs as MCP stdio server. Wire into Claude Code MCP config if you want query-time graph access.

### Deactivation

```bash
uv tool uninstall graphifyy
rm -rf ~/.claude/skills/graphify/   # removes the Skill registration
rm -rf ./graphify-out/              # remove generated graphs
```

---

## C4 — Cryptographic Memory Signatures (Ed25519 / HMAC)

### What it is

Per-entry cryptographic signatures for tamper detection.

⚠️ **NOT IMPLEMENTED.** No signing or verification code exists in this package — there is no `hmac` import, no signing function, and nothing that validates a signature on read. What ships is HMAC **secret generation** only (`--generate-hmac-secret`), which writes a key that nothing currently consumes. The schema reserves a `signature:` frontmatter field; populating and checking it is future work. Ed25519 offline-key signing is likewise unimplemented.

Do not describe this layer as active in any deployment.

### When to activate

- **T3 (Code Execution + cryptography package available)**
- Recommended for high-integrity deployments; optional otherwise

### Install + key generation

The command below generates an HMAC secret. It does **not** enable signing — nothing in this package reads that secret yet. It is useful only to pre-provision a key for future use.

**HMAC secret generation (the only part that ships):**
```bash
python3 <package>/general-edition/setup.py --generate-hmac-secret
# Output: ~/.config/ultimate-memory-stack/keys/general-edition.hmac.secret (256-bit, file mode 0o600)
```

### Verification

```bash
ls -la ~/.config/ultimate-memory-stack/keys/
# Expect: general-edition.hmac.secret (mode 600)
```

Add the secret reference to `<edition>/PROFILE.md`:
```yaml
hmac_secret_path: ~/.config/ultimate-memory-stack/keys/general-edition.hmac.secret
```

### Integration with memory stack

Memory entries with frontmatter can include a `signature` field:
```yaml
---
id: DEC-NNN
content_sha256: <hash>
signature: <Ed25519 sig or HMAC>
signed_at: <timestamp>
---
```

The signing pipeline is designed-in but not yet implemented in the protocol. Future versions will add `memory.sign(entry)` and `memory.verify(entry)` operations.

### Deactivation

⛔ **There is nothing to deactivate, because nothing signs.** This section previously read
*"Existing signatures become unverifiable"* — a leftover from the withdrawn signing claims. No
signing or verification code exists anywhere in this package; **there are no existing signatures**,
so nothing becomes unverifiable and no key rotation invalidates anything.

`setup.py --generate-hmac-secret` does exist and does generate a secret. That is *all* it does —
the secret is written and never used, because no code consumes it. Re-running it replaces the
secret with no effect on any stored entry. If a future version implements `memory.sign()` /
`memory.verify()`, rotation semantics get written **then**, against code that exists.

---

## C1, C6, C7, C8, C9, C10 — Brief notes

For the remaining Tier C tools, the design is in spec but activation steps need further research before this doc can give precise install commands. Quick orientation:

### C1 — Auto-Dream (Anthropic Dreaming beta)
- Requires Anthropic beta access
- When granted, Claude Code session will surface the beta in its capabilities
- Integration: offline async consolidation between sessions (memory entries get auto-clustered + summarized)
- Activation: TBD when beta access available

### C6 — LLMLingua / LongLLMLingua compression  ✅ INSTALLER READY (v3.5)
- Microsoft Research tool for prompt compression (MIT license)
- **Sentinel vetting:** passed with conditions (2026-05-27); upstream stale (v0.2.2 from 2024-04-09); MS moved to SecurityLingua (arXiv:2506.12707)
- **Installer Skill:** `recommended-addons/llmlingua-installer/`
  - `SKILL.md` — 8-step Claude-executable workflow
  - `INSTALL_LLMLINGUA.md` — manual fallback
  - `requirements.txt` — exact pin `llmlingua==0.2.2` + bounded transformers/torch
  - `smoke_test.py` — post-install verification
- **Activation:** invoke `/install-llmlingua` (Skill) OR follow `INSTALL_LLMLINGUA.md` manually
- **Tier C opt-in enforced:** never auto-installed; user must invoke deliberately
- **Pre-install gate:** `pip-audit` run on transitive tree (HIGH/CRITICAL CVEs block install)
- **Integration:** wraps memory entries before send → ~5-20× compression on typical prompts; compounds with prompt caching for cumulative cost reduction
- **v3.6+ migration:** evaluate SecurityLingua as successor (planned; not implemented)

### C7 — Aider repo-map primitive
- Aider is an open-source CLI; repo-map is its codebase ranking subsystem
- Activates with `pip install aider-chat` (provides the CLI; repo-map is a primitive within)
- Integration: similar to Graphify (output ingested as Layer 1 reference artifact)
- Activation: see Aider's docs at https://aider.chat/ for current install

### C8 — LLM-as-judge evals
- Pattern, not a specific tool — uses LLM to auto-grade memory operations
- Activation: wraps the existing manual eval harness with Claude API calls
- Integration: scheduled runs (or Karpathy Lint-style on-demand)
- Activation: needs design pass for our specific eval suite

### C9 — Transformers.js embeddings
- Alternative semantic-search backend if Ollama (B9) isn't available
- Activates with Node.js 18+: `npm install @xenova/transformers`
- Integration: replace B9 Ollama embedder with Transformers.js
- Activation: only relevant if the deployment can't install Ollama (Ollama is simpler)

### C10 — Skill / template extraction pipeline
- `extract_skill.py`-style automation
- Activates with Code Execution + Skills
- Integration: closes the promotion ladder (inline → decisions → standing rule → reusable Skill)
- Activation: needs custom build per our specific workflow

---

## Future evaluation candidates

These are NOT in v3.0 spec yet; reserved for future evaluation:

- ~~**CodeGraph** (`github.com/Abhishek-Aditya-bs/CodeGraph`)~~ — **EVALUATED 2026-05-19, REJECTED.** Tool offers GraphRAG hybrid retrieval pattern but requires Neo4j + Docker + OpenAI infrastructure (conflicts with our Kuzu embedded zero-infra + Ollama-first posture). 13 stars + 14 commits (very early); no AI assistant integration. GraphRAG pattern itself already captured via C2 Graphiti (with Kuzu zero-infra) + the community-summary pattern. NOTHING borrowed.
  - **RE-CHECKED 2026-08-19 — rejection STANDS.** 22 stars / 17 commits. The three commits added since the first evaluation are documentation and marketing only (`docs: rewrite README and add diagrams, LICENSE, demo queries`; a badges commit; `Add marketing website`). **Last functional change: 2025-06-08** — the codebase has not moved in over a year. The blockers are unchanged and remain in the project's own description (Neo4j + OpenAI embeddings + Docker); its README has zero mentions of Ollama, embedded, local-model, or offline operation. Maturity was never the deciding factor here — the infrastructure requirement is the architecture, not an early-stage shortcut. Do not re-evaluate on star count alone; re-open only if an embedded/local-embeddings path appears.
- Other code-graph entrants (2026 ecosystem may have evolved — periodic refresh recommended)
- Obsidian community plugins purpose-built for AI-memory workflows (passive integration; Layer 1 enrichment)

---

## General activation pattern

For every Tier C tool:

1. **Verify tier:** Run `setup.py --verify` to confirm Code Execution / Skills / Node.js / cryptography are detected
2. **Install:** Follow per-tool commands above
3. **Verify install:** Run the per-tool verification step
4. **Integrate:** Connect tool output to memory stack (Layer 1 ingestion path, MCP wiring, or direct Python bridge — depends on tool)
5. **Document activation:** Log a DEC entry (DEC-NNN) capturing what was activated, why, when, with what configuration
6. **Update profile:** Add tool's status to `<edition>/PROFILE.md` if it's persistent (signatures, audit log, etc.)

---

## Privacy considerations

| Tool | Code stays local? | Docs/papers leave? | Audio/video leaves? |
|---|---|---|---|
| Graphiti | N/A (memory not code) | Memory entries → LLM API (Anthropic/OpenAI/Ollama) | N/A |
| Graphify | YES (Tree-sitter AST local) | Sent to LLM API | Transcribed locally with faster-whisper, transcript sent to LLM |
| Aider repo-map | YES (similar pattern) | N/A | N/A |
| Auto-Dream | Memory → Anthropic Dreaming beta | N/A | N/A |

For sensitive or private data: prefer Ollama-based ingestion for both Graphiti + Graphify to keep all data local. Cloud LLM is faster but exfiltrates content.

---

## Cross-references

- Ideal-first design philosophy (design principle)
- Documentation discipline (design principle)
- Tier C designed-in features (all 10 items, with C5 deferred to a future evolution layer)
- Tier D exclusions (D3 Graphiti benchmark, D5 Graphify "71.5×" claim — both debunked)
- Research refresh 2026-05-19 surfacing Graphify + Graphiti updates
- **ARCHITECTURE.md §9** — Layer 5 Graphiti + Kuzu design
- **ARCHITECTURE.md §11.5** — Adjacent Tools (C3 Graphify, C7 Aider) — outside the 7-layer architecture proper
- **ARCHITECTURE.md §12** — Tier C full inventory
- **Sources (refresh 2026-05-19):**
  - https://github.com/getzep/graphiti (Graphiti)
  - https://github.com/safishamsi/graphify (Graphify canonical)
  - https://github.com/krshna-ai/graphify-codebase (Graphify fork)
  - https://github.com/safishamsi/graphify (Graphify source)

---

## Status

**Ready to use.** You can activate any Tier C tool listed above by following its per-tool section. Tools without precise install commands (C1, C6, C8, C9, C10) need further research before activation; design intent is captured in ARCHITECTURE.md §9–§12.

When activating any Tier C tool, please log the activation as a DEC entry in your decision log (full documentation discipline: purpose / rationale / reasoning / scope).
