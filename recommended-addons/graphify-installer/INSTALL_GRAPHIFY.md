# Manual Install — Graphify Codebase Symbol Graph

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, or you want full manual control
> **Security status:** Passed Sentinel vetting (Tier C adjacent tool, C3)
> **CRITICAL:** Package name is `graphifyy` (DOUBLE-y); single-y `graphify` is an UNRELATED package

---

## Prerequisites

1. **Ultimate Memory Stack v3.6.0 (or later) is installed**
2. **Python environment** chosen (Conda env recommended on Windows; uv venv recommended on Linux)
3. **L1 bash-guard pattern decision:** are you willing to add the typosquat hook pattern, or skip with documented risk?

> **Note:** On Linux, `python3 -m venv <path>` may fail if `python3-venv` apt package is not installed. **`uv venv <path>` works as a drop-in replacement** without requiring the apt package — uv ships its own venv builder. Validated: graphify installs via `uv venv` + `uv pip install`.
4. **Read the typosquat warning** in `README.md` before proceeding

---

## Step-by-Step Manual Install

### Step 1 — L1 Defense: Add bash-guard pattern (RECOMMENDED)

Check current hook:

```bash
grep -n "pip install graphify[^y]" <working-dir>/.claude/hooks/bash-guard.sh
```

If no match, add:

```bash
# In <working-dir>/.claude/hooks/bash-guard.sh, add a new pattern block:

# Graphify typosquat defense
# Block single-y "graphify" (UNRELATED package); allow double-y "graphifyy"
if echo "$COMMAND" | grep -qE '\bpip install graphify(\s|$|=)'; then
  if ! echo "$COMMAND" | grep -qE '\bpip install graphifyy'; then
    echo "BLOCKED: 'pip install graphify' (single-y) — typosquat risk."
    echo "Use the install-graphify Skill or 'pip install -r requirements.txt'"
    echo "(installer pinned to graphifyy==0.8.21, double-y)."
    exit 1
  fi
fi
```

Verify by attempting a dry-run:
```bash
echo "pip install graphify" | bash -c 'COMMAND=$(cat); bash <working-dir>/.claude/hooks/bash-guard.sh'
```
Expected: BLOCKED message + exit 1.

### Step 2 — Activate target environment

```bash
conda activate <your-env>
# or: source /path/to/venv/bin/activate
```

### Step 3 — Verify installer manifest (L2 defense check)

```bash
cd <path-to>/recommended-addons/graphify-installer/
grep -E '^graphifyy==0\.8\.21$' requirements.txt
```

If grep returns no match: STOP. The manifest has been tampered with.

### Step 4 — Pre-install security audit

```bash
pip install pip-audit
pip-audit --requirement requirements.txt
```

**Outcomes:**
- **No vulnerabilities** → proceed
- **HIGH or CRITICAL CVE** → STOP. Capture DEC entry before any override
- **LOW or MEDIUM CVE** → proceed with disclosure note

### Step 5 — Install with exact pin (L4 defense)

```bash
pip install -r requirements.txt
```

This installs:
- `graphifyy==0.8.21` (EXACT)
- `tree-sitter>=0.20.0,<0.22.0`

**Do NOT use `pip install graphify`** — installs UNRELATED package.
**Do NOT use `pip install graphifyy`** (no pin) — installs latest, uncalibrated.

### Step 6 — Verify package identity (L2 defense check)

```bash
pip show graphifyy
```

Expected output should include:
```
Name: graphifyy
Version: 0.8.21
Summary: Codebase symbol graph via Tree-sitter
Home-page: https://github.com/safishamsi/graphify
Author: Safi Shamsi (captainturbo on PyPI; safishamsi on GitHub — same human, two account names)
License: MIT
```

**Red flags (STOP if you see any):**
- `Name: graphify` (single-y) — L2 bypass; uninstall immediately
- Maintainer is NOT captainturbo / Safi Shamsi
- License is NOT MIT

### Step 7 — Smoke test

```bash
python smoke_test.py
```

Expected output:
```
[smoke_test] Graphify module import:    OK (single-y module name; L2 defense in next step verifies distribution name)
[smoke_test] L2 identity check:            OK (Name=graphifyy, Version=0.8.21, License=MIT)
[smoke_test] Tree-sitter language pack:    OK
[smoke_test] Symbol extraction (parse): OK (extracted N symbols)
[smoke_test] All checks PASSED
```

Notes:
- The Python **module** is `graphify` (single-y) by upstream design; the typosquat defense is the L2 identity check, which verifies the installed **distribution** is `graphifyy` (double-y) via package metadata.
- In the Symbol extraction line, the entry-point name in parentheses may be `parse`, `extract_symbols`, or `Graphify` depending on the installed API surface, and `N` is the symbol count (must be non-zero).
- If no compatible extraction entry-point is found, that line is a `WARN` instead of `OK` — the install is likely valid but the smoke test couldn't auto-verify extraction.

### Step 8 — (Optional) Register with memory stack

Edit `<working-dir>/memory/user/USER_OVERRIDES.md` (the upgrade-safe config file — **not** `PROFILE.md`, which is regenerable):

```yaml
addons:
  graphify:
    enabled: true
    version: "0.8.21"
    package_name: "graphifyy"
    output_path: ./memory/references/graphify/
    language_packs:
      - python
      - javascript
      - typescript
```

### Step 9 — Subscribe to security advisories

**Via browser:** github.com/safishamsi/graphify → Watch → Custom → "Security advisories"

**Via gh CLI:**
```bash
gh api -X PUT /repos/safishamsi/graphify/subscription -f subscribed=true
```

### Step 10 — Log to vetting_log.md

Append VET-### entry per SKILL.md Step 11 template. Note defense_layers_active in frontmatter.

### Step 11 — Log to decisions.md

Append DEC-### entry per the documentation discipline (Purpose / Rationale / Sound reasoning / Scope CAN / Scope CANNOT).

---

## Periodic Maintenance

**Vetting condition: monthly review cadence.**

Calendar reminder for ~30 days from install:

```bash
# Re-audit installed env:
pip-audit

# Check for new graphifyy releases:
pip index versions graphifyy

# If new version released:
#   1. Run fresh Sentinel vetting on the new version (Mode 1)
#   2. If PASS, update requirements.txt to new exact pin
#   3. Capture VET-### + DEC-### entries
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `pip install` succeeds but `import graphifyy` fails | Conflicting package | `pip uninstall -y graphify graphifyy` then re-install from requirements.txt |
| `pip show graphifyy` shows wrong maintainer | L2 bypass; potentially malicious | Uninstall immediately; report to Sentinel via fresh VET- entry |
| Tree-sitter language pack missing | Default install doesn't include all packs | `graphifyy install <lang>` per upstream docs |
| `BLOCKED` from bash-guard but I want to install something else with "graphify" in the name | False positive on L1 pattern | Refine the pattern to be more specific, OR temporarily bypass with explicit approval logged to audit_log |

---

## Cross-References

- `SKILL.md`, `README.md`, `requirements.txt`, `smoke_test.py`
- Your deployment's `vetting_log.md` entry for this install (Sentinel verdict)
- C3 (Tier C adjacent tool)
- common-specs/TIER_C_ACTIVATION.md §C3 (Graphify activation guide)
