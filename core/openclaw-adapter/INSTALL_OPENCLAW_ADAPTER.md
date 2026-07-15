# Manual Install — OpenClaw General Edition Adapter

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, or you want full manual control

---

## Prerequisites

1. **OpenClaw harness installed** at your chosen working directory (per https://openclaw.dev or equivalent)
2. **Python 3.10+** available (for `setup-openclaw.py`, `heartbeat_compactor.py`, `lint_runner.py`, `self_test.py`)
3. **Bash 4+** available (for `setup-openclaw.sh`)
4. **Adapter source** at `<this-folder>/` — verify presence of `templates/` (9 files) + `scripts/` (5 files)
5. **(Optional)** cron for heartbeat compactor
6. **(Optional)** USB or network share for cross-machine sync (Phase 4+ scope)

---

## Quickest path: one-liner via Bash

```bash
cd <path-to>/core/openclaw-adapter/scripts/
./setup-openclaw.sh <openclaw-root> --compliance none
```

This runs all 11 steps automatically. Equivalent Python entry point:

```bash
python setup-openclaw.py <openclaw-root> --compliance none
```

Either script will:
1. Detect OpenClaw installation
2. Back up existing root files (idempotent re-runs safe)
3. Verify adapter templates available
4. Generate 9 root files from templates
5. Generate memory/ subdirectory tree
6. Initialize audit + quarantine logs with adapter-install event
7. Write edition profile (PROFILE.md)
8. Install Option C Lint runner
9. Install heartbeat compactor + present cron entry
10. Run T1-T9 self-test
11. Log installation as DEC entry

---

## Step-by-Step Manual Install (if not using setup scripts)

### Step 1 — Verify OpenClaw

```bash
test -d <openclaw-root>/.openclaw && echo "OK" || mkdir -p <openclaw-root>/.openclaw
```

### Step 2 — Back up existing root files

```bash
BACKUP_DIR=<openclaw-root>/.openclaw/backup/pre-adapter-install-$(date +%Y-%m-%d)
mkdir -p "$BACKUP_DIR"
for f in MEMORY.md AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md BOOTSTRAP.md DREAMS.md; do
    [ -f "<openclaw-root>/$f" ] && cp "<openclaw-root>/$f" "$BACKUP_DIR/$f"
done
```

### Step 3 — Generate 9 root files from templates

```bash
ADAPTER=<path-to>/core/openclaw-adapter
for f in MEMORY AGENTS SOUL TOOLS IDENTITY USER HEARTBEAT BOOTSTRAP DREAMS; do
    cp "$ADAPTER/templates/${f}.md.template" "<openclaw-root>/${f}.md"
done
```

### Step 4 — Create memory/ subdirectory tree

```bash
cd <openclaw-root>
mkdir -p memory/{decisions,sessions,feedback/archive,security,references,user,projects,archive/{heartbeats,daily_logs},quarantine}
```

### Step 5 — Initialize logs

```bash
touch memory/security/audit_log.jsonl
touch memory/quarantine/quarantine_log.jsonl
touch memory/archive/daily_logs/DAILY_LOG_$(date +%Y-%m-%d).md

# Append adapter-install event to audit_log
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","actor":"orchestrator","session":0,"action":"adapter-install","entry_id":"<bootstrap>","subject":"openclaw-general-edition-adapter-v1.0","outcome":"success","compliance":"none"}' >> memory/security/audit_log.jsonl
```

### Step 6 — Write edition profile

Create `<openclaw-root>/ultimate-memory-stack/general-edition/PROFILE.md`:

```markdown
# General Edition Profile

---
edition: general
compliance: none
audit_log: false
quarantine_ux: toast
pattern_key_recurrence_threshold: 5
signature_scheme: none
adapter_version: "1.0"
---

(See setup-openclaw.sh Step 7 for the full template body if needed.)
```

### Step 7 — Install Lint runner + heartbeat compactor

```bash
mkdir -p <openclaw-root>/.openclaw/lint
# lint_runner.py moved to core/shared-tools/ in v4.0.0 (shared cross-harness
# tooling, not adapter-specific) — copy from there, not $ADAPTER/scripts/.
cp $ADAPTER/../shared-tools/lint_runner.py <openclaw-root>/.openclaw/lint/lint_runner.py
cp $ADAPTER/scripts/heartbeat_compactor.py <openclaw-root>/.openclaw/heartbeat_compactor.py
```

### Step 8 — (Optional) Wire heartbeat cron

Open crontab:

```bash
crontab -e
```

Paste:

```cron
# Ultimate Memory Stack — heartbeat compactor
*/30 8-22 * * * cd <openclaw-root> && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
0 0,6 * * * cd <openclaw-root> && python3 .openclaw/heartbeat_compactor.py >> .openclaw/lint/compactor.log 2>&1
```

### Step 9 — Run T1-T9 self-test

```bash
python $ADAPTER/scripts/self_test.py <openclaw-root>
```

Expected: all 9 tests PASS.

### Step 10 — Log DEC entry

Append to `<openclaw-root>/memory/decisions/decisions.md`:

```markdown
## DEC-INSTALL: OpenClaw General Edition Adapter Installed

(Use DEC-INSTALL template from setup-openclaw.sh Step 11 body)
```

### Step 11 — Optionally install addons

After adapter install validates, install Sentinel-vetted addons:

```bash
# Via Skills (if available):
/install-llmlingua
/install-graphiti
/install-graphify
/config-obsidian-vault

# Or manually per each addon's INSTALL_<NAME>.md
```

---

## Verification (Manual Checks)

```bash
cd <openclaw-root>

# Check 9 root files
ls -la MEMORY.md AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md BOOTSTRAP.md DREAMS.md

# Check memory tree
ls -la memory/

# Check audit log
cat memory/security/audit_log.jsonl

# Check profile
cat ultimate-memory-stack/general-edition/PROFILE.md

# Re-run self-test
python <path-to-adapter>/scripts/self_test.py .
```

---

## Periodic Maintenance

- **Re-run heartbeat_compactor.py manually** if cron isn't wired
- **Re-run lint_runner.py monthly** to catch documentation drift
- **Check `<openclaw-root>/memory/archive/daily_logs/`** for compactor findings
- **Re-audit transitive Python deps** (pip-audit) if addons installed

---

## Rollback

If adapter install causes issues:

```bash
BACKUP=<openclaw-root>/.openclaw/backup/pre-adapter-install-<YYYY-MM-DD>
for f in MEMORY.md AGENTS.md SOUL.md TOOLS.md IDENTITY.md USER.md HEARTBEAT.md BOOTSTRAP.md DREAMS.md; do
    [ -f "$BACKUP/$f" ] && cp "$BACKUP/$f" "<openclaw-root>/$f"
done
```

(memory/ subdirectory tree + edition profile are SAFE to keep even if root files reverted.)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `self_test.py` T1 FAIL | HEARTBEAT.md missing | Re-run Step 3 |
| `self_test.py` T7 FAIL | PII pattern in IDENTITY.md | Replace with REDACTED placeholders |
| Bootstrap exceeds 60K | Root files grew | Run heartbeat_compactor.py to archive oldest content |
| Compactor cron not firing | Crontab not loaded | Verify `crontab -l` shows the entry; check compactor.log |
| Lint runner false positives | Default thresholds too strict | Adjust `LINT_THRESHOLDS` in heartbeat_compactor.py |

---

## Cross-References

- `SKILL.md` (Claude-executable workflow source)
- `MAPPING.md` (v3.0/v3.5 ↔ OpenClaw convention mapping)
- `README.md` (addon-level documentation + 5-element documentation discipline)
- MEMORY_PROTOCOL §1.3 (T1-T9 self-test)
- MEMORY_PROTOCOL §11 (file size limits)
