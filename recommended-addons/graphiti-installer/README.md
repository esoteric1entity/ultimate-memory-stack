# Graphiti Installer — v3.5 Ultimate Recommended Addon

> **Status:** ✅ v3.5 Ultimate ready (Sentinel vetting: PASS)
> **Tier:** C2 (biotech-first designed-in; general-edition opt-in)
> **Last updated:** 2026-05-28

---

## What This Addon Does

**Graphiti** is a bi-temporal knowledge-graph framework (Apache 2.0, maintained by Zep AI) for storing memory entries as temporal facts. Per ARCHITECTURE.md §9, it is the **Layer 5 storage upgrade** in the Ultimate Memory Stack — biotech-first designed-in for clinical/regulatory provenance.

**Why install it on the Ultimate Memory Stack:**
- Bi-temporal queries (valid_at + recorded_at) match MEMORY_PROTOCOL §3 B5 conflict resolution
- Knowledge graph enables relationship-aware retrieval (entries linked by `[[ID]]` materialize as graph edges)
- Provenance + recall for clinical/regulatory contexts (biotech-first per ARCHITECTURE.md §9)
- MCP server option lets Claude Code query the graph natively

**Why it's Tier C in general-edition (designed-in for biotech):**
- Biotech-edition: designed-in (Tier C2)
- General-edition: opt-in (Tier C2)
- Backend storage adds operational footprint
- LLM ingestion has cost/latency (mitigated by the Ollama path)

---

## CVE History — READ BEFORE INSTALLING

| CVE | Affected | Patched | Notes |
|---|---|---|---|
| **CVE-2026-32247** (Cypher Injection) | `graphiti-core` < 0.28.2 | 0.28.2 (2026-03-11) | **Kuzu backend was UNAFFECTED** — parameterized labels prevent the attack class |

**This installer enforces `graphiti-core>=0.29.1`** (one minor above the CVE patch) to guarantee the patch is in place AND that any subsequent patches flow in via standard pip upgrade.

**Upstream track record (cited by Sentinel as strength):**
- Coordinated CVE disclosure (responsible)
- Trusted Publishing with Sigstore attestations
- Active maintenance (last release 2026-05-21 v0.29.1)
- Commercial backing (Zep AI)

---

## Telemetry — DISABLED BY DEFAULT (Sentinel Vetting Condition #2)

Graphiti's upstream default is `PostHog telemetry ON`. This installer:

1. Sets `GRAPHITI_TELEMETRY_ENABLED=false` before first import (Step 5)
2. Persists the env var to your shell rc / Conda activate.d / Windows PowerShell `$PROFILE` (Step 6)
3. Documents the override in your `<edition>/PROFILE.md` if you wire Graphiti into the memory stack (Step 8)

**This is the security baseline.** Re-enabling telemetry is a deliberate user decision and should be logged as a DEC entry per the documentation discipline.

---

## Sentinel Vetting Summary

**Verdict:** PASS with conditions
**Confidence:** HIGH (Sentinel)

**Strengths cited:**
- Trusted Publishing with Sigstore attestations
- Coordinated CVE disclosure track record (responsible upstream)
- Apache 2.0 license — permissive, compatible
- Active maintenance + commercial backing (Zep AI)
- Kuzu backend immune to Cypher injection (parameterized labels)

**Risks cited:**
- PostHog telemetry default-ON (must disable) ← #1 concern
- Past Cypher injection CVE (CVE-2026-32247) — patched; only Neo4j path affected

**Required actions enforced by this installer:**
1. ✅ Pin `graphiti-core>=0.29.1` (security floor — `requirements.txt`)
2. ✅ Default `GRAPHITI_TELEMETRY_ENABLED=false` (SKILL.md Step 5 + Step 6 persistence)
3. ✅ Recommend Kuzu backend (avoids Cypher injection class — SKILL.md Step 1)
4. ✅ Pin `mcp>=1.0.2` if MCP server used (SKILL.md Step 3 + `requirements.txt`)
5. ✅ Subscribe to repo security advisories (SKILL.md Step 9)

---

## Installation

### Recommended: via Skill

```
/install-graphiti
```

The Skill walks through the 11-step workflow defined in `SKILL.md`:
backend selection → LLM provider → MCP option → pip-audit → install → telemetry persistence → smoke test → optional memory-stack integration → security subscription → activation logging → operational briefing

### Fallback: manual install

Per `INSTALL_GRAPHITI.md`:

```bash
# In your conda env or venv:
export GRAPHITI_TELEMETRY_ENABLED=false   # Linux/Mac
# or on Windows PowerShell:
# $env:GRAPHITI_TELEMETRY_ENABLED = "false"

pip install pip-audit
pip-audit --requirement requirements.txt   # MUST PASS

pip install -r requirements.txt
python smoke_test.py                       # Verify install + telemetry-off
```

---

## Documentation Discipline

### Purpose

Provide bi-temporal knowledge-graph storage to the Ultimate Memory Stack as the Layer 5 storage upgrade, enabling clinical/regulatory provenance (biotech-first) and relationship-aware recall (general-edition opt-in).

### Rationale

- Per ARCHITECTURE.md §9 Graphiti is the designed-in Layer 5 backend
- Sentinel vetting confirmed PASS with conditions; all conditions enforced by this installer
- A research refresh found Graphiti gained MCP server + Ollama paths — installer offers both
- This addon is one of 3 PASS-verdict addons proceeding in v3.5
- Telemetry-off-by-default is a security baseline, not a per-deployment toggle — codified in installer

### Sound reasoning

1. Per the security-first standing rule: Graphiti PASSED Sentinel vetting; installer enforces all 5 conditions
2. Per the ideal-first design principle: Kuzu backend is the cleanest topology (no server, no Cypher injection class)
3. Per the documentation discipline: this README + SKILL.md capture purpose/rationale/scope
4. As Tier C2: Graphiti is the Layer 5 storage upgrade — biotech-first designed-in (mandatory there), general-edition opt-in
5. MCP + Ollama paths reduce T3→T1 friction for cost-conscious deployments
6. Graphiti proceeds with its Sentinel-specified guardrails

### Scope — CAN

- Install Graphiti at floor pin `>=0.29.1` (CVE patch baseline)
- Choose backend (Kuzu recommended / Neo4j / FalkorDB)
- Choose LLM provider (Ollama local / Anthropic / OpenAI / defer)
- Optionally install MCP server (`mcp>=1.0.2`) for Claude Code integration
- Run `pip-audit` pre-install and block on HIGH/CRITICAL CVEs
- Persist `GRAPHITI_TELEMETRY_ENABLED=false` to environment
- Smoke-test bi-temporal round-trip via `smoke_test.py`
- Optionally wire into `<edition>/PROFILE.md` as Layer 5 backend
- Subscribe to upstream security advisories
- Log activation to vetting_log.md + decisions.md

### Scope — CANNOT

- Install Neo4j server (only the Python client if user picks Neo4j backend)
- Configure Ollama (must be pre-installed if user picks Ollama)
- Re-enable telemetry without explicit user action + DEC log entry
- Prevent Cypher injection on Neo4j backend (Kuzu's parameterized labels are an architectural protection; Neo4j requires app-code parameterization discipline)
- Manage graph storage growth indefinitely (user must periodically maintain)
- Auto-subscribe to security advisories without browser or `gh` CLI access

---

## Files in This Folder

| File | Purpose |
|---|---|
| `SKILL.md` | Claude-executable installer manifest (11-step workflow) |
| `README.md` | This file — addon README with CVE history + vetting summary |
| `requirements.txt` | Pinned dependency manifest |
| `INSTALL_GRAPHITI.md` | Companion manual install guide |
| `smoke_test.py` | Post-install verification (bi-temporal round-trip + telemetry check) |

---

## Cross-References

- `common-specs/TIER_C_ACTIVATION.md` §C2 (Graphiti activation guide)
- `common-specs/ARCHITECTURE.md` §9 (Layer 5 storage architecture)
