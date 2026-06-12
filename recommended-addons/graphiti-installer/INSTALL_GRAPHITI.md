# Manual Install — Graphiti Bi-Temporal Knowledge Graph

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, or you want full manual control
> **Authority:** Sentinel-vetted (PASS verdict) — Tier C C2 addon

---

## Prerequisites

> **Note:** On Linux, `python3 -m venv <path>` may fail if `python3-venv` apt package is not installed. **`uv venv <path>` works as a drop-in replacement** without requiring the apt package — uv ships its own venv builder. Recommended when sudo apt install is impractical.



1. **Ultimate Memory Stack v3.6.0 (or later) is installed**
2. **Python environment** chosen (a dedicated Conda env recommended)
3. **Backend choice made:**
   - **Kuzu (RECOMMENDED)** — no additional setup; embedded
   - **Neo4j** — Neo4j server must be running separately
   - **FalkorDB** — Redis with FalkorDB module must be running separately
4. **LLM provider chosen:** Ollama (local) / Anthropic / OpenAI / defer
5. **MCP decision:** install MCP server for Claude Code integration, or skip

---

## Step-by-Step Manual Install

### Step 1 — Activate environment

```bash
# Conda:
conda activate <your-env>

# uv venv:
source /path/to/venv/bin/activate
```

### Step 2 — Set telemetry-off BEFORE first import

This is **critical** — Graphiti's PostHog telemetry initializes on first import. Set env var first:

**Linux/Mac:**
```bash
export GRAPHITI_TELEMETRY_ENABLED=false
```

**Windows PowerShell:**
```powershell
$env:GRAPHITI_TELEMETRY_ENABLED = "false"
```

### Step 3 — Edit requirements.txt for backend choice

Uncomment ONE of the optional backend lines in `requirements.txt`:

| Backend | Line to uncomment |
|---|---|
| Kuzu (default — no edit needed) | (none — `kuzu>=0.4.0,<1.0.0` is already active) |
| Neo4j | `# neo4j>=5.0.0,<6.0.0` |
| FalkorDB | `# falkordb>=1.0.0,<2.0.0` |

If installing MCP server too, also uncomment `# mcp>=1.0.2,<2.0.0`.

### Step 4 — Pre-install security audit

```bash
pip install pip-audit
cd <path-to>/recommended-addons/graphiti-installer/
pip-audit --requirement requirements.txt
```

**Outcomes:**
- **No vulnerabilities** → proceed to Step 5
- **HIGH or CRITICAL CVE** → STOP. Surface CVE. Capture DEC entry before any override
- **LOW or MEDIUM CVE** → proceed with disclosure note

### Step 5 — Install

```bash
pip install -r requirements.txt
```

### Step 6 — Persist telemetry-off

**Linux/Mac (`~/.bashrc`):**
```bash
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' >> ~/.bashrc
source ~/.bashrc
```

**Windows PowerShell (`$PROFILE`):**
```powershell
Add-Content -Path $PROFILE -Value '$env:GRAPHITI_TELEMETRY_ENABLED = "false"'
```

**Conda env scope (recommended for project isolation):**
```bash
mkdir -p $CONDA_PREFIX/etc/conda/activate.d
echo 'export GRAPHITI_TELEMETRY_ENABLED=false' > $CONDA_PREFIX/etc/conda/activate.d/graphiti-telemetry-off.sh
conda deactivate && conda activate <your-env>   # re-activate to pick up
```

### Step 7 — Smoke test

```bash
python smoke_test.py
```

Expected output:
```
[smoke_test] Graphiti import:        OK
[smoke_test] Kuzu backend init:      OK
[smoke_test] Telemetry env var:      OK (set to false)
[smoke_test] Ingest test fact:       OK
[smoke_test] Bi-temporal query:      OK (1 fact retrieved)
[smoke_test] Cleanup:                OK
[smoke_test] All checks PASSED
```

### Step 8 — (Optional) Register with memory stack

Edit `<working-dir>/<edition>/PROFILE.md`:

```yaml
addons:
  graphiti:
    enabled: true
    version_floor: "0.29.1"
    backend: kuzu              # or neo4j / falkordb
    llm_provider: ollama       # or anthropic / openai
    mcp_server: false          # or true
    telemetry_enabled: false   # NEVER override
    graph_db_path: ./memory/graph/
```

### Step 9 — Subscribe to security advisories

**Via browser:** Visit https://github.com/getzep/graphiti/security/advisories → click Watch → Custom → check "Security advisories"

**Via gh CLI:**
```bash
gh api -X PUT /repos/getzep/graphiti/subscription -f subscribed=true
```

### Step 10 — Log to vetting_log.md

Append VET-### entry to `<working-dir>/memory/security/vetting_log.md` per SKILL.md Step 10 template.

### Step 11 — Log to decisions.md

Append DEC-### entry per the documentation discipline (Purpose / Rationale / Sound reasoning / Scope CAN / Scope CANNOT). Include backend choice, LLM provider, MCP decision.

---

## Periodic Maintenance (Every 30-90 days)

```bash
# Re-audit transitive deps:
pip-audit

# Check for security advisories at upstream:
# https://github.com/getzep/graphiti/security/advisories
```

If new HIGH/CRITICAL CVEs surface, decide:
1. Upgrade graphiti-core (security floor pin allows minor upgrades — usually safe)
2. If transitive (e.g., neo4j, kuzu), upgrade the specific transitive package
3. If unfixable, document as risk and consider migration

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `posthog` HTTP calls observed | Telemetry env var not set BEFORE first import | Restart Python process with env var set; verify with `echo $GRAPHITI_TELEMETRY_ENABLED` |
| `ImportError: kuzu` | Kuzu not in requirements (Backend mismatch) | Uncomment correct backend line in `requirements.txt`, reinstall |
| Cypher injection warning at runtime (Neo4j backend) | Backend not parameterizing | Switch to Kuzu, OR add `parameterized=True` to query calls |
| `mcp` import fails | MCP not installed | Uncomment `mcp>=1.0.2` in `requirements.txt`, reinstall |
| Smoke test fails on round-trip | LLM provider not configured | Run Step 8 to configure provider, or check Ollama is running |

---

## Cross-References

- `SKILL.md`, `README.md`, `requirements.txt`, `smoke_test.py`
- ARCHITECTURE.md §9 (Layer 5 storage)
- common-specs/TIER_C_ACTIVATION.md §C2 (Graphiti activation guide)
