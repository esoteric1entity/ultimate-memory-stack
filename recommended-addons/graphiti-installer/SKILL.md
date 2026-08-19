---
name: install-graphiti
description: Installer for Graphiti bi-temporal knowledge graph addon (Tier C C2, Layer 5 storage upgrade). Installs graphiti-core>=0.29.1 with Kuzu backend (recommended; avoids Cypher injection CVE class) and PostHog telemetry disabled by default. Optionally configures MCP server (>=v1.0.2) for Claude Code integration. Validates via smoke test. Use when the user asks to install, deploy, activate, or enable Graphiti / knowledge-graph backend for their memory stack deployment.
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["security-first vetting", "ideal-first design", "documentation discipline", "Tier C Layer 5 storage upgrade", "PASS-verdict addon batch"]
vetting_reference: pre-release security vetting (verdict PASS with conditions)
edition: any
tier: C (opt-in)
license: Apache 2.0 (Graphiti); installer license: Apache-2.0
upstream_status: active (last release 2026-05-21 v0.29.1; coordinated CVE disclosure track record)
known_cve_history: CVE-2026-32247 (Cypher Injection) — patched at v0.28.2; Kuzu backend was UNAFFECTED
maintainers: paulzep + sunnysideup (Zep AI commercial backing)
---

# Install Graphiti Bi-Temporal Knowledge Graph — Skill Workflow

When this Skill is invoked (typically via `/install-graphiti` slash command or when the user asks Claude to install/deploy/activate Graphiti), execute the workflow below **IN ORDER**.

Graphiti is the Layer 5 storage upgrade in the Ultimate Memory Stack architecture (per ARCHITECTURE.md §9). It is an opt-in Tier C Layer 5 storage upgrade.

---

## Step 0 — Confirm Install Intent + Disclose CVE History

```
👋 You're about to install Graphiti (bi-temporal knowledge graph addon).

What Graphiti does:
  - Stores memory entries as temporal facts in a knowledge graph
  - Supports bi-temporal queries (valid_at + recorded_at) — matches MEMORY_PROTOCOL §3 B5 model
  - Backends: Kuzu (embedded, RECOMMENDED) / Neo4j (server-based) / FalkorDB
  - Optional MCP server for Claude Code integration

⚠️  CVE HISTORY — READ BEFORE PROCEEDING:
  - CVE-2026-32247 (Cypher Injection) — affected versions <0.28.2; PATCHED 2026-03-11
  - Kuzu backend was UNAFFECTED (parameterized labels prevent the attack class)
  - Coordinated CVE disclosure track record (responsible upstream)
  - This installer pins graphiti-core>=0.29.1 to ensure CVE-2026-32247 patch is in place

⚠️  TELEMETRY — DISABLED BY DEFAULT:
  - Graphiti's default behavior is PostHog telemetry ON
  - This installer sets GRAPHITI_TELEMETRY_ENABLED=false in the environment
  - User can opt-in to telemetry post-install if desired

Vetting reference: pre-release security vetting (verdict PASS with conditions)
License: Apache 2.0 (permissive)
Tier: C — opt-in addon

Continue with install? [Y/n]:
```

---

## Step 1 — Backend Selection (Critical Security Decision)

```
Which Graphiti backend?
  (a) Kuzu (RECOMMENDED) — embedded, no server, immune to CVE-2026-32247 class
  (b) Neo4j — server-based; requires running Neo4j separately; bigger attack surface
  (c) FalkorDB — Redis-based alternative; advanced users only
```

**Strongly recommend (a) Kuzu.** Save as `BACKEND` for subsequent steps.

If user picks (b) Neo4j, surface additional warning:
```
⚠️  Neo4j backend exposes the Cypher injection class.
    This installer enforces graphiti-core>=0.29.1 (CVE patch in place),
    but parameterized queries are your responsibility in application code.
    Consider Kuzu unless you have a specific reason to need Neo4j.
```

---

## Step 2 — LLM Provider Selection

```
Which LLM provider for Graphiti ingestion?
  (a) Ollama (LOCAL) — no cloud cost; uses local model; requires Ollama install
  (b) Anthropic API — faster + higher quality; cloud cost
  (c) OpenAI API — alternate cloud option
  (d) Skip — install only, configure provider later
```

A research refresh reduced this from T3 to T1 via the Ollama path. Save as `LLM_PROVIDER`.

---

## Step 3 — MCP Server Decision (Optional)

```
Install Graphiti's MCP server for Claude Code integration?
  (a) Yes — Claude Code can query Graphiti directly via MCP (requires mcp-v1.0.2+)
  (b) No — Graphiti available via Python API only
```

If yes, the `mcp` package will be pinned `>=1.0.2`. Save as `INSTALL_MCP`.

---

## Step 4 — Pre-Install Security Audit

```bash
# In INSTALL_ENV:
pip install pip-audit
pip-audit --requirement <path-to-this-skill>/requirements.txt
```

### Dependency freshness check (informational)

Before installing, see what upstream looks like today versus what this add-on pins:

```bash
python <path-to-this-skill>/preflight.py
```

It prints, per dependency, the constraint this package ships against the latest
version on PyPI and when that version was published — so an abandoned
dependency is visible BEFORE you install rather than months later. It never
blocks the install and never edits anything; being offline is not a finding.
Advancing a pin is a security-vetting decision, not a mechanical refresh.


**Outcomes:**
- **No vulnerabilities** → proceed to Step 5
- **HIGH or CRITICAL CVE** → STOP. Surface CVE. Capture DEC entry before any override.
- **LOW or MEDIUM CVE** → proceed with disclosure in activation log

Log to `<working-dir>/memory/security/audit_log.jsonl` per Step 2 of LLMLingua installer pattern.

---

## Step 5 — Install Graphiti

In the INSTALL_ENV (Conda or venv):

```bash
# Set telemetry off BEFORE install (so first import respects setting):
export GRAPHITI_TELEMETRY_ENABLED=false   # Linux/Mac
# OR on Windows PowerShell:
# $env:GRAPHITI_TELEMETRY_ENABLED = "false"

# Check your Python version, then install from the matching lock:
python --version
pip install --require-hashes -r <path-to-this-skill>/locks/requirements-py3.12.lock
```

`requirements.txt` states what versions are ACCEPTABLE; the lock states exactly
what you GET, verified by hash. `--require-hashes` makes pip refuse any artifact
whose hash is not listed. The locks are universal — one file per Python version
covers every platform.

This installs:
- `graphiti-core>=0.29.1` (floor pin — security floor for CVE-2026-32247)
- `kuzu>=0.11.3` — the embedded backend, in-process, no server
- `mcp>=1.0.2` (only if INSTALL_MCP = yes — uncomment it in `requirements.txt`)
- `posthog` arrives as a transitive dependency, gated behind the telemetry env var

⚠️ **Kuzu's last release was 0.11.3 on 2025-10-10, and it is on a removal clock.**
Upstream has been cold for roughly ten months, and `graphiti-core`'s own
`pyproject.toml` marks its `[kuzu]` extra *"Deprecated: the upstream Kuzu project
is unmaintained; this extra will be removed in a future release."*

It still installs and runs — this add-on depends on `kuzu` directly rather than
through the extra, and the hash-pinned lock fixes the resolution — but you are
adopting a backend that is not receiving security patches and that the library
above it intends to drop. It remains the default only because it is the sole
embedded backend covering every platform this package supports.

On **macOS or Linux with Python 3.12+**, prefer the maintained embedded
alternative — edit `requirements.txt` to swap `kuzu` for
`falkordblite>=0.5.0; python_version >= "3.12"`, then regenerate the locks
(`python recommended-addons/regenerate-locks.py graphiti`). FalkorDB Lite
publishes no Windows wheels, which is why it is not the default.

Server-based backends (`neo4j`, plain `falkordb`) are commented out in
`requirements.txt` — uncomment one only if you already operate that server.
Note that plain `falkordb` is a **client**, not an embedded engine.

Backends are not interchangeable at rest: graph data written by one engine is
not readable by another. Choose once, at install time.

---

## Step 6 — Persist Telemetry-Off Setting

Add to deployment environment file (so telemetry stays off across sessions):

**Linux/Mac (`~/.bashrc` or shell rc):**
```bash
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.bashrc
```

**Windows PowerShell (`$PROFILE`):**
```powershell
Add-Content -Path $PROFILE -Value '$env:GRAPHITI_TELEMETRY_ENABLED = "false"'
```

**Conda env (`<conda-env>/etc/conda/activate.d/`):**
```bash
mkdir -p <conda-env>/etc/conda/activate.d
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' > <conda-env>/etc/conda/activate.d/graphiti-telemetry-off.sh
```

Ask user which scope, then write the appropriate file.

---

## Step 7 — Smoke Test

```bash
python <path-to-this-skill>/smoke_test.py
```

Verifies:
1. `graphiti` imports
2. Kuzu backend constructs (creates ephemeral graph in tmp dir)
3. Telemetry env var is set to false
4. A test fact ingests + queries successfully (bi-temporal round-trip)
5. Cleanup tmp dir

**On failure:** uninstall and surface error. No half-installed state.

---

## Step 8 — Register with Memory Stack (Optional Integration)

```
Wire Graphiti into the memory stack as Layer 5 storage?
  (a) Yes — `memory/user/USER_OVERRIDES.md` gets graphiti config block; memory entries promote to graph at threshold
  (b) No — install only; user invokes Graphiti via Python API for ad-hoc queries
```

If yes, add to `<working-dir>/memory/user/USER_OVERRIDES.md`:
```yaml
addons:
  graphiti:
    enabled: true
    version_floor: "0.29.1"
    backend: kuzu              # or neo4j / falkordb
    llm_provider: ollama       # or anthropic / openai
    mcp_server: false          # or true
    telemetry_enabled: false   # NEVER override — security baseline
    graph_db_path: ./memory/graph/
```

---

## Step 9 — Subscribe to Security Advisories

**Required vetting action:** subscribe to upstream security advisories.

```
Open https://github.com/getzep/graphiti/security/advisories in browser
Click "Watch" → "Custom" → check "Security advisories"
```

OR via GitHub CLI:
```bash
gh repo set-default getzep/graphiti
gh api -X PUT /repos/getzep/graphiti/subscription -f subscribed=true
```

Document the subscription in vetting log entry.

---

## Step 10 — Log Activation

Append to `<working-dir>/memory/security/vetting_log.md`:

```markdown
### VET-###: Graphiti activated (`pip install graphiti-core>=0.29.1`)

---
id: VET-###
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
subject: graphiti-core>=0.29.1 (Kuzu backend)
verdict: ACTIVATED
pipeline: install-graphiti Skill v1.0
---

- **Date:** <today>
- **Verdict:** ACTIVATED (Tier C — opt-in)
- **Backend:** Kuzu (parameterized labels prevent Cypher injection class)
- **Telemetry:** DISABLED (env var set)
- **MCP server:** [installed | not installed]
- **CVE patch status:** CVE-2026-32247 covered (>=0.29.1 floor)
- **Security subscription:** ENABLED (github.com/getzep/graphiti/security/advisories)
- **Tags:** tier-c, activation, graphiti, addon, layer-5
```

Append corresponding DEC-### entry to `<working-dir>/memory/decisions/decisions.md` per the documentation discipline standing rule.

---

## Step 11 — Brief User on Operational Notes

```
✅ Graphiti installed (graphiti-core>=0.29.1 in <INSTALL_ENV>)
✅ Backend: <BACKEND>  ·  LLM: <LLM_PROVIDER>  ·  MCP: <INSTALL_MCP>
✅ Telemetry: DISABLED (GRAPHITI_TELEMETRY_ENABLED=false persisted)
✅ Security advisories: subscribed

Operational notes:
  - Ingestion latency depends on LLM_PROVIDER (Ollama: ~3-5s; API: ~1-2s)
  - Kuzu backend stores graph at: ./memory/graph/
  - Bi-temporal queries: use valid_at + recorded_at filters per MEMORY_PROTOCOL §3
  - Re-run pip-audit every 30-90 days for transitive CVEs
  - Monitor https://github.com/getzep/graphiti/security/advisories
```

---

## Compliance Cross-References

| Step | Action | Decision authority |
|---|---|---|
| 0 | Intent + CVE disclosure | documentation discipline |
| 1 | Backend selection (Kuzu recommended) | vetting condition #3 |
| 2 | LLM provider | research refresh (T3→T1 reduction) |
| 3 | MCP server option | vetting condition #4 |
| 4 | pip-audit | security-first vetting |
| 5 | Install with floor pin | vetting condition #1 |
| 6 | Persist telemetry-off | vetting condition #2 |
| 7 | Smoke test | ideal-first design |
| 8 | Register with stack (opt) | Tier C opt-in (C2) |
| 9 | Security subscription | vetting condition #5 |
| 10 | Log activation | security-first vetting + documentation discipline |
| 11 | Hand-off | ideal-first design |

---

## What This Skill CANNOT Do

- **Cannot install Neo4j server** — only the Python client (`neo4j` package) if user picks Neo4j backend
- **Cannot configure Ollama** — installer assumes Ollama is already installed if user picks Ollama
- **Cannot disable telemetry retroactively** if user installs from a different path and the env var isn't set first
- **Cannot prevent CVE class on Neo4j backend** — Kuzu's parameterized labels are an architectural protection; Neo4j requires user discipline in app code
- **Cannot manage Graphiti's storage indefinitely** — graph file grows with ingestion; user must periodically maintain
- **Cannot subscribe to security advisories** if user lacks GitHub CLI or browser access
