# Manual Install + Manual Use — Audit Quarantine Skill

> **Companion to:** `SKILL.md` (Claude-executable workflow) — same logic, runnable by hand
> **Use this when:** Claude Code Skills unavailable, scripting from CI, or you want full manual control
> **Authority:** MEMORY_PROTOCOL_EXTENDED.md §E3.3 (Quarantine Routing)
> **Companion script:** `scripts/review_quarantined.py`

---

## Prerequisites

1. **Ultimate Memory Stack v3.6.0 (or later) installed** at your working directory
2. **`memory/quarantine/` directory exists** — adapter or the edition setup creates this
3. **Python 3.10+** for the standalone script
4. **Optional:** biotech-edition or general-edition profile loaded (Skill detects via PROFILE.md)

---

## Quickest path: via Skill

```
/audit-quarantine
```

Skill walks through the 9-step workflow defined in SKILL.md. Each entry presented interactively with full provenance.

---

## Standalone Python: via review_quarantined.py

```bash
cd <path-to>/core/audit-quarantine-skill/scripts/

# Interactive mode (default):
python review_quarantined.py <working-dir>

# Batch mode (read decisions from stdin):
echo "APPROVE entry-id-1
REJECT entry-id-2
DEFER entry-id-3" | python review_quarantined.py <working-dir> --mode batch
```

Output is appended to `audit_log.jsonl` + `quarantine_log.jsonl`.

---

## Step-by-Step Manual Process (if not using Skill or script)

### Step 1 — List quarantined entries

```bash
find <working-dir>/memory/quarantine -name "*.md" -type f
```

Expected output: zero or more `.md` files. If empty, nothing to review; exit.

### Step 2 — Read quarantine log

```bash
cat <working-dir>/memory/quarantine/quarantine_log.jsonl
```

For each entry from Step 1, find matching log line by `entry_id`. Surface context to yourself.

### Step 3 — Inspect each entry

For each `<entry-id>.md`:

```bash
ENTRY_FILE=<working-dir>/memory/quarantine/<category>/<entry-id>.md
head -30 "$ENTRY_FILE"      # Show frontmatter + first 25 lines of content
cat "$ENTRY_FILE" | wc -l   # Total lines
```

Decision: APPROVE / REJECT / DEFER.

### Step 4 — Apply APPROVE decision

```bash
# Parse original category from quarantine subdirectory:
ORIGINAL_CATEGORY="decisions"  # or feedback / sessions / security / etc.

# Move entry back
mv "$ENTRY_FILE" "<working-dir>/memory/$ORIGINAL_CATEGORY/<entry-id>.md"

# Update frontmatter (manual edit) — change:
#   status: quarantined → active
# Add:
#   quarantine_resolved_at: <YYYY-MM-DD>
#   quarantine_resolution: approved-after-review
```

### Step 5 — Apply REJECT decision

```bash
rm "$ENTRY_FILE"
```

### Step 6 — Apply DEFER decision

(No file action — leave entry in quarantine.)

### Step 7 — Append to quarantine_log.jsonl

For each decision:

```bash
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SESSION=<your-session-number>

# APPROVE
echo '{"ts":"'$TIMESTAMP'","actor":"orchestrator","session":'$SESSION',"action":"approve","entry_id":"<id>","entry_category":"'$ORIGINAL_CATEGORY'","resolution":"approved-after-review","prior_quarantine_reason":"<reason>"}' >> <working-dir>/memory/quarantine/quarantine_log.jsonl

# REJECT
echo '{"ts":"'$TIMESTAMP'","actor":"orchestrator","session":'$SESSION',"action":"reject","entry_id":"<id>","entry_category":"<category>","resolution":"rejected-after-review","prior_quarantine_reason":"<reason>"}' >> <working-dir>/memory/quarantine/quarantine_log.jsonl

# DEFER
echo '{"ts":"'$TIMESTAMP'","actor":"orchestrator","session":'$SESSION',"action":"defer","entry_id":"<id>","entry_category":"<category>","resolution":"deferred","prior_quarantine_reason":"<reason>"}' >> <working-dir>/memory/quarantine/quarantine_log.jsonl
```

### Step 8 — Append to audit_log.jsonl

```bash
echo '{"ts":"'$TIMESTAMP'","actor":"orchestrator","session":'$SESSION',"action":"audit-quarantine-review","entry_id":"<id>","outcome":"<approve|reject|defer>","decision_basis":"<your-reason>"}' >> <working-dir>/memory/security/audit_log.jsonl
```

### Step 9 — Verify logs

```bash
tail -10 <working-dir>/memory/quarantine/quarantine_log.jsonl
tail -10 <working-dir>/memory/security/audit_log.jsonl
```

---

## Common Patterns + Edge Cases

### "I have 50 quarantined entries; full review will take forever"

Use batch mode in `review_quarantined.py`:

```bash
# Generate a decisions file from a CSV/spreadsheet review:
echo "DEFER all entries with reason=pii-detected" | python review_quarantined.py <working-dir> --mode batch-by-reason --reason pii-detected --action DEFER
```

Or use the Skill's "SKIP TO END" option to defer all remaining.

### "Biotech edition won't let me DEFER without a reason"

Per B2 — biotech-edition forensic completeness requires explicit reason. Supply one:

```bash
python review_quarantined.py <working-dir> --action DEFER --reason "Pending Sentinel re-vetting after CVE-2026-XXXX patch"
```

### "I approved an entry but want to revoke it"

Approval is reversible per MEMORY_PROTOCOL_EXTENDED.md §E3.4 bi-temporal supersession:

1. Re-quarantine the entry (write `status: quarantined` to frontmatter; move file back)
2. Log the action in audit_log.jsonl with action: `re-quarantine`
3. Re-run this Skill / script

### "I rejected an entry but need it back"

REJECT is permanent by design. The `quarantine_log.jsonl` line preserves the FACT of the entry's existence + reason + timestamp; if you need the content recreated, you must author a fresh entry.

This is a security feature, not a bug — accidental approvals are recoverable; intentional rejections are not.

---

## Verification

After completing review:

```bash
# Confirm quarantine directory state
ls -la <working-dir>/memory/quarantine/

# Confirm logs updated
wc -l <working-dir>/memory/quarantine/quarantine_log.jsonl
wc -l <working-dir>/memory/security/audit_log.jsonl

# Re-run /lint-memory to surface any NEW quarantine candidates
/lint-memory
```

---

## Cross-References

- `SKILL.md` — Claude-executable workflow source
- `README.md` — addon-level overview + documentation discipline
- `scripts/review_quarantined.py` — standalone Python entry point
- MEMORY_PROTOCOL_EXTENDED.md §E3.3 (Quarantine Routing — write-side)
- MEMORY_PROTOCOL_EXTENDED.md §E3.4 (bi-temporal supersession on resolution)
- `audit_log.jsonl` canonical format
