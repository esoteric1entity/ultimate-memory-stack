---
name: install-llmlingua
description: Optional installer for LLMLingua prompt compression addon (Tier C C6, opt-in). Wraps the Ultimate Memory Stack with token-level perplexity-based prompt compression (Microsoft Research, MIT licensed). Pins llmlingua==0.2.2 exactly (upstream stale ~2 years); runs pip-audit pre-install; installs to user-chosen conda or venv environment; verifies via smoke test. Use when the user asks to install, deploy, activate, or enable LLMLingua / prompt compression for their memory stack deployment.
version: "1.0"
authors: ["esoteric1entity"]
decision_authority: ["security-first vetting", "ideal-first design", "documentation discipline", "Tier C designed-in", "PASS-verdict addon batch"]
vetting_reference: security pre-vetted 2026-05-27 (verdict PASS with conditions)
edition: any (general-edition + biotech-edition both supported)
tier: C (opt-in; not loaded by default)
license: "MIT (LLMLingua); installer under Apache-2.0"
upstream_status: stale (last release 2024-04-09 v0.2.2); Microsoft Research moved to SecurityLingua arXiv 2506.12707
migration_path: v3.6+ — evaluate SecurityLingua as successor
---

# Install LLMLingua Prompt Compression — Skill Workflow

When this Skill is invoked (typically via `/install-llmlingua` slash command or when the user asks Claude to install/deploy/activate LLMLingua), execute the workflow below **IN ORDER**. Treat each step as required unless the user explicitly opts to skip.

This Skill is one of the recommended addons. It is **opt-in** per its Tier C designation — never auto-installed; user must invoke deliberately.

---

## Step 0 — Confirm Install Intent + Disclose Upstream Status

Greet the user briefly and disclose the upstream status before doing anything:

```
👋 You're about to install LLMLingua (prompt compression addon).

What LLMLingua does:
  - Token-level prompt compression using small-model perplexity scoring
  - Coarse-to-fine compression workflow (LLMLingua + LongLLMLingua)
  - Typical compression: 5-20× on long prompts with minimal quality loss
  - Designed for token-budget-constrained workflows (cost savings, context-budget pressure)

⚠️  UPSTREAM STATUS — READ BEFORE PROCEEDING:
  - Last upstream release: 2024-04-09 (v0.2.2) — STALE ~2 years
  - Microsoft Research moved on to SecurityLingua (arXiv:2506.12707, June 2025)
  - This installer pins llmlingua==0.2.2 EXACTLY (any drift would be a supply-chain anomaly)
  - Pinned transformers + torch versions accumulate CVEs over time
  - Plan a v3.6+ migration to SecurityLingua or successor

Vetting status: security pre-vetted (verdict PASS with conditions)
License: MIT (permissive)
Tier: C (opt-in, not loaded by default)

Continue with install? [Y/n]:
```

If user says no, stop gracefully. If user says yes, proceed.

---

## Step 1 — Detect Deployment Environment

Determine where LLMLingua should be installed:

1. **Read `<working-dir>/<edition>/PROFILE.md`** to confirm an Ultimate Memory Stack deployment exists
2. **If no deployment found:** error gracefully — LLMLingua is a memory-stack addon and assumes the base stack is installed
3. **Ask the user which Python environment to install into:**
   ```
   Which Python environment should LLMLingua install into?
     (a) Conda env (recommend: a dedicated env for ML libraries)
     (b) uv-managed venv (path: <path-to-venv>)
     (c) System Python (not recommended; CVE accumulation risk)
     (d) Other (specify path)
   ```
4. **Save as `INSTALL_ENV`** — used for all subsequent pip operations

---

## Step 2 — Pre-Install Security Check (pip-audit on Transitive Tree)

Per the security vetting's required conditions, run `pip-audit` against the pinned manifest BEFORE install:

```bash
# In INSTALL_ENV:
pip install pip-audit  # if not already present
pip-audit --requirement <path-to-this-skill>/requirements.txt
```

**Outcomes:**
- **No vulnerabilities found** → proceed to Step 3
- **HIGH or CRITICAL CVE found** → STOP. Surface the CVE to user. Do NOT proceed without explicit user override + DEC entry logging the override.
- **LOW or MEDIUM CVE found** → surface to user; user decides whether to proceed (default: proceed with disclosure note)

Log the pip-audit result to `<working-dir>/memory/security/audit_log.jsonl`:
```jsonl
{"ts":"<UTC>","actor":"orchestrator","session":<N>,"action":"pre-install-audit","entry_id":"<llmlingua-install>","subject":"llmlingua==0.2.2","outcome":"<pass|warn|block>","cve_count":<N>}
```

---

## Step 3 — Install LLMLingua with Exact Pin

In the chosen INSTALL_ENV, install from the bundled requirements.txt:

```bash
# In INSTALL_ENV (Conda or venv activated):
pip install -r <path-to-this-skill>/requirements.txt
```

This installs:
- `llmlingua==0.2.2` (exact pin)
- `transformers>=4.30.0,<4.40.0` (compatible range; tighter than upstream)
- `torch>=2.0.0,<2.3.0` (compatible range)
- `sentencepiece>=0.1.99` (tokenizer dependency)

**Do NOT use `pip install llmlingua` without the requirements.txt** — that allows transitive drift.

---

## Step 4 — Smoke Test

Run the bundled smoke test to verify the install works:

```bash
python <path-to-this-skill>/smoke_test.py
```

The smoke test:
1. Imports `llmlingua` (verifies install succeeded)
2. Loads the small compression model (verifies dependencies resolve)
3. Compresses a sample prompt and verifies output is non-empty + non-identical to input
4. Reports compression ratio and round-trip time

**On failure:** roll back by uninstalling (`pip uninstall -y llmlingua transformers torch sentencepiece`) and surface error details. Do NOT leave a half-installed environment.

---

## Step 5 — Register with Memory Stack (Optional Integration)

If the user wants LLMLingua wired into the memory stack's outbound prompt path:

1. **Ask:**
   ```
   Wire LLMLingua into the memory stack outbound path?
     (a) Yes — Tier C opt-in flag set in <edition>/PROFILE.md; compression triggers when prompt budget exceeded
     (b) No — install only; user invokes LLMLingua manually via Python API
   ```

2. **If yes:** add to `<working-dir>/<edition>/PROFILE.md`:
   ```yaml
   addons:
     llmlingua:
       enabled: true
       version: "0.2.2"
       trigger: budget_exceeded
       compression_ratio_target: 5
   ```

3. **If no:** user can invoke directly:
   ```python
   from llmlingua import PromptCompressor
   compressor = PromptCompressor()
   result = compressor.compress_prompt("<long prompt>", target_token=200)
   ```

---

## Step 6 — Log Activation to Vetting Log

Per the Tier C (C6) activation logging requirement, log to `<working-dir>/memory/security/vetting_log.md`:

```markdown
### VET-### : LLMLingua activated (`pip install llmlingua==0.2.2`)
- **Date:** <today>
- **Session:** <N>
- **Verdict:** ACTIVATED (Tier C opt-in)
- **Subject:** LLMLingua prompt compression (Tier C C6 / pre-vetted PASS)
- **Activation method:** install-llmlingua Skill v1.0
- **Pinned version:** llmlingua==0.2.2 (upstream stale, MS Research → SecurityLingua)
- **Tags:** tier-c, activation, llmlingua, addon
```

---

## Step 7 — Document Activation in Decision Log

Per the documentation discipline standing rule, append a brief DEC entry to `<working-dir>/memory/decisions/decisions.md`:

```markdown
## DEC-### : LLMLingua Activated for Compression Addon

- **Status:** FINAL
- **Confidence:** 1.0
- **Session:** <N>
- **Date:** <today>
- **Decision:** Activated LLMLingua (Tier C C6) via install-llmlingua Skill v1.0
- **Rationale:** [user-supplied; typically token-budget pressure or cost optimization]
- **Cross-references:** Tier C C6 designation, this activation's VET-### entry
- **Migration plan:** Evaluate SecurityLingua (arXiv:2506.12707) for v3.6+ before this pinning becomes unsupported
- **Tags:** addon-activated, tier-c, llmlingua
```

---

## Step 8 — Brief User on Operational Notes

Final hand-off message to user:

```
✅ LLMLingua installed (llmlingua==0.2.2 in <INSTALL_ENV>)

Operational notes:
  - Compression model downloads on first use (~500 MB; cached after)
  - First compression has higher latency (~5-10 sec) than subsequent (~1-3 sec)
  - Compression ratio depends on prompt structure; target 5-20× for typical prompts
  - Pinned versions accumulate CVEs — re-run pip-audit every 30-90 days
  - Plan v3.6+ migration to SecurityLingua (arXiv:2506.12707)

You can invoke compression now:
  python -c "from llmlingua import PromptCompressor; c = PromptCompressor(); print(c.compress_prompt('your long prompt here', target_token=200))"
```

---

## Workflow Summary (Compliance Cross-References)

| Step | Action | Design principle |
|---|---|---|
| 0 | Confirm intent + disclose upstream status | documentation discipline |
| 1 | Detect deployment environment | ideal-first design |
| 2 | pip-audit pre-install | security-first + vetting condition |
| 3 | Install with exact pin | vetting conditions (exact pin, bundled manifest) |
| 4 | Smoke test | validate before declaring done |
| 5 | Register with memory stack (optional) | Tier C C6 (opt-in flag) |
| 6 | Log to vetting log | auditability |
| 7 | Log activation as DEC entry | documentation discipline |
| 8 | Hand-off briefing | user-facing transparency |

---

## What This Skill CANNOT Do

- **Cannot auto-enable LLMLingua** without user opt-in (Tier C designation enforced)
- **Cannot install across multiple environments** in one invocation (one env per run)
- **Cannot upgrade beyond v0.2.2** (exact pin enforced; user override requires fresh DEC entry)
- **Cannot mitigate transitive CVE accumulation** beyond installer time (user must periodically re-audit)
- **Cannot integrate with memory protocol if base stack isn't installed** (Step 1 enforces precondition)
- **Cannot run on systems lacking the small compression model** (downloaded on first use; offline systems must pre-cache)
