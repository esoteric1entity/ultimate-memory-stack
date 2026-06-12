# Manual Install — LLMLingua

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, or you want full manual control
> **Authority:** Security vetting PASS verdict (Tier C C6 addon)

---

## Prerequisites

1. **Ultimate Memory Stack v3.6.0 (or later) is installed** at your working directory
   - Verify by checking `<working-dir>/<edition>/PROFILE.md` exists
2. **Python environment** chosen for install (one of):
   - Conda env (recommended on Windows: a dedicated env for ML libraries)
   - uv-managed venv (recommended on Linux when `python3-venv` apt package not installed — see Note below)
   - System Python (not recommended due to CVE accumulation risk; also blocked by PEP 668 on modern Linux)

> **Note:** On Linux, `python3 -m venv <path>` may fail if `python3-venv` apt package is not installed. The fix is either:
> (a) `sudo apt install python3.X-venv` (X matches your Python minor version), OR
> (b) **`uv venv <path>` works as a drop-in replacement** without requiring the apt package — uv ships its own venv builder. Recommended when admin install is impractical.
>
> First-run note: `python smoke_test.py` downloads a ~500 MB model on first run; can exceed 5 minutes on moderate network. Use `python smoke_test.py --quick` to validate import without triggering the download. Run full smoke after model is cached.

---

## Step-by-Step Manual Install

### Step 1 — Activate target environment

```bash
# Option A: Conda env
conda activate <your-ml-env>

# Option B: uv venv
source /path/to/venv/bin/activate
# or on Windows:
# .\path\to\venv\Scripts\activate
```

### Step 2 — Install pip-audit (one-time)

```bash
pip install pip-audit
```

### Step 3 — Pre-install security audit

**Required by the security vetting conditions.** Run pip-audit against the pinned requirements.txt BEFORE installing:

```bash
# Navigate to the installer folder:
cd <path-to>/recommended-addons/llmlingua-installer/

# Run audit:
pip-audit --requirement requirements.txt
```

**Outcomes:**
- **No vulnerabilities** → proceed to Step 4
- **HIGH or CRITICAL CVE** → STOP. Surface CVE details. Capture DEC entry before any override.
- **LOW or MEDIUM CVE** → proceed with disclosure note in your activation log

### Step 4 — Install pinned packages

```bash
pip install -r requirements.txt
```

This installs (with vetted exact + bounded pins):
- `llmlingua==0.2.2`
- `transformers>=4.30.0,<4.40.0`
- `torch>=2.0.0,<2.3.0`
- `sentencepiece>=0.1.99,<0.3.0`

**Do NOT use `pip install llmlingua` (without `-r requirements.txt`)** — that allows transitive drift outside the vetted pin range.

### Step 5 — Smoke test

```bash
python smoke_test.py
```

Expected output (approximate):

```
[smoke_test] LLMLingua import:    OK
[smoke_test] PromptCompressor:    OK (model loading...)
[smoke_test] Compression test:    OK (ratio: 4.2×, latency: 6.3s first-call)
[smoke_test] Round-trip:          OK (output non-empty, distinct from input)
[smoke_test] All checks PASSED
```

**On failure:** uninstall and surface error:

```bash
pip uninstall -y llmlingua transformers torch sentencepiece
```

Do not proceed with half-installed state.

### Step 6 — (Optional) Register with memory stack

If you want LLMLingua wired into the memory stack's outbound prompt path, edit `<working-dir>/<edition>/PROFILE.md` and add:

```yaml
addons:
  llmlingua:
    enabled: true
    version: "0.2.2"
    trigger: budget_exceeded
    compression_ratio_target: 5
```

If you just want it available for ad-hoc Python invocation, skip this step.

### Step 7 — Log to vetting log

Append to `<working-dir>/memory/security/vetting_log.md`:

```markdown
### VET-### : LLMLingua activated (`pip install llmlingua==0.2.2`)

---
id: VET-###
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: orchestrator
source_session: <N>
status: active
schema_version: "3.0"
subject: llmlingua==0.2.2 (manual install)
verdict: ACTIVATED
pipeline: manual-install (per INSTALL_LLMLINGUA.md)
---

- **Date:** <today>
- **Session:** <N>
- **Verdict:** ACTIVATED (Tier C opt-in)
- **Subject:** LLMLingua prompt compression (Tier C C6 addon, vetting PASS)
- **Activation method:** Manual install via INSTALL_LLMLINGUA.md
- **Pinned version:** llmlingua==0.2.2 (upstream stale; MS Research → SecurityLingua)
- **pip-audit result:** [no CVE | LOW CVE in <pkg> — proceeded with disclosure | other]
- **Smoke test:** PASSED
- **Tags:** tier-c, activation, llmlingua, addon, manual-install
```

### Step 8 — Log activation to decisions.md

Append to `<working-dir>/memory/decisions/decisions.md`:

```markdown
## DEC-### : LLMLingua Activated

- **Status:** FINAL
- **Confidence:** 1.0
- **Session:** <N>
- **Date:** <today>
- **Decision:** Activated LLMLingua (Tier C C6) via manual install
- **Rationale:** [your reason — typically token-budget pressure or cost optimization]
- **Cross-references:** VET-### (this activation)
- **Migration plan:** Evaluate SecurityLingua (arXiv:2506.12707) for v3.6+ before pinning becomes unsupported
- **Tags:** addon-activated, tier-c, llmlingua, manual-install
```

---

## Periodic Maintenance (Every 30-90 days)

```bash
# Re-audit the installed environment for new transitive CVEs:
pip-audit
```

If new HIGH/CRITICAL CVEs surface, decide:
1. **Patch in place** if Sentinel vets a newer minor (requires fresh VET- entry)
2. **Migrate to SecurityLingua** if that's farther along (likely the right move long-term)
3. **Disable LLMLingua** if no good patch exists (toggle `addons.llmlingua.enabled: false` in PROFILE.md)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `pip install` fails with conflicting transformers | Existing env has newer transformers | Create fresh env or use `--force-reinstall` (after auditing) |
| Smoke test hangs on model download | Slow network, large model (~500 MB) | Wait; first download is one-time |
| `ImportError: No module named 'llmlingua'` | Wrong env activated | Confirm `pip list \| grep llmlingua` in the active env |
| `RuntimeError: CUDA out of memory` | GPU compression with too-large prompt | Use CPU mode (set `device='cpu'` in PromptCompressor init) |
| `pip-audit` reports new CVE post-install | Transitive CVE emerged | Run periodic maintenance flow above |

---

## Cross-References

- `SKILL.md` — Claude-executable equivalent of this manual flow
- `README.md` — addon-level README with upstream status + vetting summary
- `requirements.txt` — pinned manifest used by Step 3 + Step 4
- `smoke_test.py` — verification script used by Step 5
- Sentinel vetting verdict for LLMLingua (see `README.md` vetting summary)
