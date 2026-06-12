# Vetting Log — Template

> **Purpose:** Scaffolding for `memory/security/vetting_log.md`. Holds security vetting reports (tool/skill/MCP installations) and code review records.
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** SCHEMA_A18 §Security-specific-additional-fields

---

```markdown
# Security Vetting Log

> **Schema Version:** 3.0
> **Entries:** 0 (initial)
> **Last Updated:** <YYYY-MM-DD>

---

## VET-001: <Tool/skill/MCP being vetted>

---
id: VET-001
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: sentinel                       # or warden / orchestrator
source_session: <N>
status: active
schema_version: "3.0"
subject: <tool-name OR repo-url OR PR-ID>
verdict: PASS | REVIEW_REQUIRED | FAIL       # for tool vetting
pipeline: warden-sentinel-mode1              # mode1 = tool vetting; mode2 = code review
findings_count: <N>
tags: [vetting, <tool-type>, <verdict>]
---

**Subject:** [Specific tool/skill/MCP being vetted — name, version, source URL]

**Pre-vetting context (Warden):**
- CVE history: <findings>
- Author reputation: <findings>
- Conflict analysis with existing installations: <findings>

**Vetting analysis (Sentinel):**
- Permissions requested: <list>
- Network access: <yes/no/limited>
- Filesystem access: <scope>
- External dependencies: <list>
- Prompt injection risks: <findings>
- Privilege escalation risks: <findings>
- Data exfiltration risks: <findings>
- Findings (specific): <list of N findings>

**Combined assessment (Warden):**
- Risk score: <LOW / MEDIUM / HIGH / CRITICAL per risk rubric>
- Recommendation: <APPROVE / APPROVE_WITH_NOTES / REJECT>
- Conditions: <any required mitigations if APPROVE_WITH_NOTES>

**User decision:** <APPROVE / REJECT — the user approves or rejects per the security-first policy>

**Installation result:** <successful / failed / pending>

**Post-installation observations:** <any issues during use>

---

## CR-001: <PR or code review>

---
id: CR-001
created_at: <YYYY-MM-DD>
source_agent: sentinel
pipeline: warden-sentinel-mode2              # mode2 = code review
subject: <PR-URL OR repo+commit>
verdict: APPROVE | APPROVE_WITH_NOTES | NEEDS_DISCUSSION | REQUEST_CHANGES
findings_count: <N>
tags: [code-review, <verdict>]
---

**Subject:** [PR URL, commit range, or repo+files being reviewed]

**Layer 1 — Correctness:**
- Findings: <list>

**Layer 2 — Quality:**
- Findings: <list>

**Layer 3 — Architecture:**
- Findings: <list>

**Layer 4 — Testing:**
- Findings: <list>

**Layer 5 — Security:**
- Findings: <list>

**Combined assessment (Warden):**
- Risk score: <LOW / MEDIUM / HIGH / CRITICAL>
- Verdict: <APPROVE / APPROVE_WITH_NOTES / NEEDS_DISCUSSION / REQUEST_CHANGES>
- Critical findings (if any): <list>

**Author response:** <if applicable>

**Final disposition:** <merged / blocked / iterating>
```

---

## Worked example — VET entry

```markdown
## VET-009: kanban-skill from mattjoyce/kanban-skill

---
id: VET-009
created_at: 2026-04-10
source_agent: sentinel
source_session: 3
status: active
schema_version: "3.0"
subject: https://github.com/mattjoyce/kanban-skill
verdict: PASS
pipeline: warden-sentinel-mode1
findings_count: 2
tags: [vetting, skill, kanban, pm-tool, user-approved]
---

**Subject:** kanban-skill — Markdown-based kanban board management skill

**Pre-vetting context (Warden):**
- CVE history: None found
- Author reputation: mattjoyce — 50+ public skills, active maintainer
- Conflict analysis: No conflicts with existing PM tools (Clerk agent extends, doesn't replace)

**Vetting analysis (Sentinel):**
- Permissions requested: Read, Write to `kanban/` directory only
- Network access: None
- Filesystem access: Scoped to working directory
- External dependencies: None
- Prompt injection risks: LOW — operates on user-written markdown only
- Findings: 2 minor (suggestions for improved error handling; not blocking)

**Combined assessment (Warden):**
- Risk score: LOW (1)
- Recommendation: APPROVE
- Conditions: None

**User decision:** APPROVE (user, 2026-04-10)
**Installation result:** successful
**Post-installation observations:** Working as expected; templates in regular use.
```

## Usage notes

- **Two modes:** VET- = tool/skill/MCP vetting (pipeline=mode1); CR- = code review (pipeline=mode2)
- **Verdict values differ by mode:** vetting uses PASS/REVIEW_REQUIRED/FAIL; code review uses APPROVE/APPROVE_WITH_NOTES/NEEDS_DISCUSSION/REQUEST_CHANGES
- **Warden + Sentinel pipeline:** Per agent_orchestration.md, Warden provides context and final assessment; Sentinel does the analysis
- **The user approves all:** no tool is installed without the user's explicit approval
- **Size cap:** 200 lines per MEMORY_PROTOCOL.md §11. Archive entries older than 1 year.

## Cross-references

- `MEMORY_PROTOCOL.md` §11 (size limits)
- `SCHEMA_A18` §Security-specific-additional-fields
- `DEC-001` (example: your security-first tool-installation decision)
- `agent_orchestration.md` (Warden + Sentinel pipeline definitions)
