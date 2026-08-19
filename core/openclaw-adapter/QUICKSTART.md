# Ultimate Memory Stack v4.0.1 — Quick-Start for OpenClaw (No-Claude Path)

---
file: QUICKSTART
project: ultimate-memory-stack
component: openclaw-adapter
created_at: 2026-05-29
last_updated: 2026-07-11
schema_version: "3.0"
schema: A18
scope: file
status: active
audience: public
purpose: "Single-page deployment runbook for any user installing Ultimate Memory Stack v4.0.1 onto an OpenClaw harness, with no dependency on Claude Code being present on the target machine"
related: [README.md, INSTALL_OPENCLAW_ADAPTER.md, MAPPING.md, SKILL.md]
---

## What this is

A condensed deployment runbook (~3-5 minutes of reading + 15-30 minutes of execution) for installing the **Ultimate Memory Stack v4.0.1** onto a machine running **OpenClaw** (or any compatible harness following the same 9-root-file convention) **without requiring Claude Code on the target machine**.

The memory stack is a metadata + protocol layer — harness-agnostic by design per the modular consumer architecture decision. Inference (LLM calls) is delegated to whatever model endpoint OpenClaw is configured to use (e.g., Ollama local, Ollama Turbo cloud, OpenAI-compatible API). The memory stack itself does not call Claude or any specific model.

## Who this is for

- **OpenClaw operators** deploying the stack onto a NAS, server, or workstation where OpenClaw is the resident agent runtime
- **Self-hosters** running an LLM on private hardware who want persistent memory + audit + quarantine
- **Public-repo users** evaluating the stack who don't have a Claude Code subscription
- **Cross-machine deployers** who plan to use this stack from multiple agent runtimes (Claude Code on one machine, OpenClaw on another, etc.)

For the full Claude-Code-resident path, see `INSTALL_OPENCLAW_ADAPTER.md` and the parent `INSTALL.md`.

## Prerequisites

| # | Requirement | How to check |
|---|---|---|
| 1 | **OpenClaw** harness installed at a known workspace path | Run `openclaw configure` (or inspect `~/.openclaw/openclaw.json`); default workspace is `~/.openclaw/workspace`. If `OPENCLAW_PROFILE` env var is set, it becomes `~/.openclaw/workspace-<profile>`. See [OpenClaw agent-workspace docs](https://docs.openclaw.ai/concepts/agent-workspace) for current canonical conventions. |
| 2 | **bash** (≥ 4.0) OR **python3** (≥ 3.10) | `bash --version` · `python3 --version` |
| 3 | **Disk space:** ≥ 50 MB for stack files + memory growth | `df -h <workspace-path>` |
| 4 | **LLM endpoint** reachable from the target machine | e.g., `curl http://localhost:11434/api/tags` for local Ollama; or test your provider's API |
| 5 | **(Optional) Obsidian** if you want a visual vault UI | Install from <https://obsidian.md> on a workstation that can read the memory directory |

### OpenClaw workspace path resolution

The adapter generates files INTO OpenClaw's workspace. To find your workspace path on the target machine:

```bash
# Quickest — read the OpenClaw config directly
cat ~/.openclaw/openclaw.json | grep -A1 workspace

# OR — use OpenClaw's own CLI (canonical)
openclaw configure --show     # exact subcommand may vary; check `openclaw --help`

# Fallback — the documented default
echo "${OPENCLAW_PROFILE:+~/.openclaw/workspace-$OPENCLAW_PROFILE}" 2>/dev/null || echo "~/.openclaw/workspace"
```

Pass that path as `<workspace>` in Step 2 below. The adapter's 9 root files (MEMORY/AGENTS/SOUL/TOOLS/IDENTITY/USER/HEARTBEAT/BOOTSTRAP/DREAMS) align with OpenClaw's documented workspace conventions; `DREAMS.md` is the only adapter-specific addition beyond the canonical OpenClaw root-file set.

## 5-Step Deployment

### Step 1 — Transport the stack to the target machine

Pick whichever transport suits your network posture:

```bash
# Option A — USB / removable media
# (plug in USB containing the ultimate-memory-stack/ folder)
cp -r /path/to/usb/ultimate-memory-stack ~/memory-stack

# Option B — rsync over LAN from another machine
rsync -av --progress source-machine:/path/to/ultimate-memory-stack/ ~/memory-stack/

# Option C — git clone (once published)
git clone <repo-url> ~/memory-stack
```

### Step 2 — Run the adapter setup

Either Bash or Python works (both are functionally equivalent — parity is enforced; pick whichever your environment supports more reliably). Substitute `<workspace>` with the path you resolved in the Prerequisites table above (default: `~/.openclaw/workspace`):

```bash
# Bash path (Linux / macOS / WSL)
bash ~/memory-stack/core/openclaw-adapter/scripts/setup-openclaw.sh <workspace>

# Python path (cross-platform)
python3 ~/memory-stack/core/openclaw-adapter/scripts/setup-openclaw.py <workspace>
```

The setup will:

- Generate the **9 root auto-load files** at `<openclaw-root>/`: `MEMORY.md`, `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, `DREAMS.md`
- Create the `<openclaw-root>/memory/` subtree (decisions / feedback / projects / sessions / security / references)
- Write the **edition profile** to `<openclaw-root>/ultimate-memory-stack/general-edition/PROFILE.md`
- Install supporting Python scripts at `<openclaw-root>/.openclaw/` (heartbeat compactor, lint runner, self-test)

When prompted, choose:

- **Edition** — `general-edition` (the only edition in this package): opt-in audit log, toast-style quarantine UX. HIPAA/PHI is out of scope for this edition.
- **Compliance preset** — `none` / `enterprise` / `custom`

### Step 3 — Wire the LLM endpoint

Configure OpenClaw to call your chosen LLM endpoint. The memory stack does NOT prescribe a specific model — any endpoint OpenClaw can hit will work.

```bash
# Example — local Ollama
export OLLAMA_HOST="http://localhost:11434"

# Example — remote Ollama (cloud, private network, or another machine on LAN)
export OLLAMA_HOST="http://<endpoint>:<port>"

# Example — OpenAI-compatible API
export OPENAI_API_BASE="https://<provider-endpoint>"
export OPENAI_API_KEY="<key>"
```

Refer to OpenClaw's own config docs for the canonical environment variables or config-file syntax. Add the appropriate exports to your shell profile or OpenClaw's startup config.

**Suggested starter models:**

| Role | Model | Size | Why |
|---|---|---|---|
| Orchestration | Llama 3.1 8B Instruct (Q5) | ~5 GB | Fits in 8 GB VRAM; strong instruction-following |
| Memory retrieval / embeddings | nomic-embed-text v1.5 | ~280 MB | Fast; Apache-2.0 licensed |
| Heavier reasoning (cloud) | Llama 3.3 70B or larger | (cloud) | Route via your cloud endpoint for complex tasks |

### Step 4 — Restart OpenClaw + observe bootstrap

```bash
# Whatever OpenClaw's restart command is for your setup
# Example (systemd-managed):
sudo systemctl restart openclaw

# Or (foreground for first-boot observation):
openclaw --bootstrap
```

Watch for:

- ✅ All 9 root files load (no parse errors on YAML frontmatter)
- ✅ Bootstrap budget stays under **60,000 characters** (per HEARTBEAT.md spec)
- ✅ A first heartbeat appears in `<openclaw-root>/memory/sessions/session_state.md`
- ✅ No T1-T9 self-test failures reported in startup log

### Step 5 — Run the smoke tests

```bash
# Self-test (T1-T9 + PII detection + provenance sanity)
python3 ~/memory-stack/core/openclaw-adapter/scripts/self_test.py <openclaw-root>

# Heartbeat compaction (validates session_state.md round-trip)
cd <openclaw-root> && python3 .openclaw/heartbeat_compactor.py

# Lint operation (multi-platform — works on Claude Code AND OpenClaw)
python3 <openclaw-root>/.openclaw/lint/lint_runner.py <openclaw-root>

# Optional — exercise the quarantine workflow with a deliberate malformed entry
# (see core/audit-quarantine-skill/README.md for the manual test scenario)
```

All four should exit with code `0` and a clean summary. Any non-zero exit is a hard fail — see Troubleshooting below.

**Multi-platform note:** `lint_runner.py` auto-detects whether the workspace is OpenClaw (via `.openclaw/`) or Claude Code (via `.claude/rules/`). Use `--harness openclaw|claude_code` or `--seed-file <path>` to override detection if needed.

## Verification — what success looks like

After Step 5:

```
<openclaw-root>/
├── MEMORY.md           ← 9 root auto-load files (Step 2 output)
├── AGENTS.md
├── SOUL.md
├── TOOLS.md
├── IDENTITY.md
├── USER.md
├── HEARTBEAT.md
├── BOOTSTRAP.md
├── DREAMS.md
├── memory/             ← Memory stack content (Step 2 output)
│   ├── decisions/      ← decisions.md grows as you accumulate DEC entries
│   ├── feedback/       ← feedback.md captures user corrections
│   ├── projects/       ← per-project memory_bank/ subdirectories
│   ├── sessions/       ← session_state.md heartbeat
│   ├── security/       ← audit_log.jsonl + vetting_log.md + quarantine/
│   └── references/     ← references.md pointer file
├── ultimate-memory-stack/
│   └── general-edition/
│       └── PROFILE.md  ← Active edition + compliance preset
└── .openclaw/          ← Adapter scripts + edition config
    ├── heartbeat_compactor.py
    ├── lint/
    │   └── lint_runner.py  ← multi-platform (Claude Code + OpenClaw)
    └── ...
```

Stage 2 PASS criteria:

- ✅ OpenClaw boots cleanly with the 9 root files
- ✅ Adapter Python scripts execute end-to-end without error
- ✅ A test write-read round-trip on `memory/decisions/decisions.md` validates SCHEMA_A18 frontmatter integrity

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `setup-openclaw.sh: command not found` | bash not on `PATH` or script not marked executable | `chmod +x scripts/setup-openclaw.sh` then re-run; or use the Python variant |
| `python3: No module named 'venv'` (Linux) | Distro doesn't ship `python3-venv` by default | `sudo apt install python3-venv` (Debian/Ubuntu) OR install `uv` (<https://docs.astral.sh/uv/>) and use `uv venv` instead |
| 9 root files generated but OpenClaw doesn't see them | OpenClaw configured for a different root path | Verify `<openclaw-root>` matches OpenClaw's actual config; re-run setup against the correct path |
| `T7 FAIL` in self_test output | A memory file accidentally contains PII/PHI-looking patterns | Review the flagged file; redact identifiers; re-run; if it's a false positive on an unusual format, tune the regex in `self_test.py` PII_PATTERNS |
| LLM calls return errors but stack files are fine | LLM endpoint misconfigured (Step 3 incomplete) | Verify the endpoint with `curl`; confirm OpenClaw's env vars or config file points to it |
| Bootstrap budget exceeds 60 K characters | A root file has bloated over time | Run `python3 .openclaw/heartbeat_compactor.py` to compact `HEARTBEAT.md`; review other root files for accumulated content |
| Audit log grows quickly | The opt-in audit log is enabled and writing entries on memory operations | Rotation triggers at 50,000 lines per `MEMORY_PROTOCOL.md §11`; rotated logs land at `audit_log_<YYYY-MM>.jsonl`. Disable the opt-in audit log in your edition profile if you don't need it |

For deeper issues, consult `INSTALL_OPENCLAW_ADAPTER.md` (full install guide) and `MAPPING.md` (architecture reference).

## Where to next

| Goal | Resource |
|---|---|
| Full install guide with all options | `INSTALL_OPENCLAW_ADAPTER.md` |
| Architecture reference (what each root file does) | `MAPPING.md` |
| Adding recommended Tier C addons (LLMLingua / Graphiti / Graphify / Obsidian) | `../../recommended-addons/{graphiti,graphify,llmlingua}-installer/INSTALL_*.md` + `obsidian-vault-config/INSTALL_OBSIDIAN_VAULT.md` |
| Quarantine review workflow | `../audit-quarantine-skill/README.md` |
| Edition-specific behavior (general-edition) | `../../general-edition/PROFILE.md` |
| Memory protocol behavior reference | `../../common-specs/MEMORY_PROTOCOL.md` |
| Multi-machine sync (future) | `../../common-specs/SCHEMA_sync_log.md` |

## Attribution

**Ultimate Memory Stack** is a PDuk Brainworks project. Authors: see /AUTHORS.md. The OpenClaw General Edition Adapter validates the modular consumer architecture by demonstrating that any agent harness — not just Claude Code — can host the stack.

See the repository root for license terms and contribution guidelines.

## Footnotes / Spec compatibility

- Schema version: **3.0** (per memory protocol)
- Stack version: **v4.0.1**
- This quick-start covers the **no-Claude-required path**; if Claude Code is present on the target machine, the slash-command Skills (`/install-openclaw-adapter`, `/audit-quarantine`, etc.) provide an alternative entry that wraps the same Python scripts shown here.
