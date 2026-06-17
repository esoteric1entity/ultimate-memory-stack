# User Profile — Template

> **Purpose:** Scaffolding for `memory/user/user_profile.md`. Populated during bootstrap setup wizard. Loaded every session (Tier 1).
> **Schema:** v3.0 (per SCHEMA_A18)
> **Companion:** BOOTSTRAP_PROMPT.md §Step-7 (setup wizard), MEMORY_PROTOCOL.md §1.2 Tier 1

---

```markdown
# User Profile

> **Schema Version:** 3.0

---
id: USER-PROFILE
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: user
source_session: 1
status: active
schema_version: "3.0"
---

## Identity

- **Name:** <Your name>
- **Role:** <Job title / role>
- **Organization:** <Company / institution>
- **Domain:** <Primary work domain — e.g., biotech R&D, web dev, data science, research, education>

## Communication preferences

- **Response style:** <brief vs detailed>
- **Technical level:** <novice / intermediate / expert in primary domain>
- **Formatting:** <markdown tables ok, code blocks for snippets, etc.>
- **Tone:** <formal / casual / direct>

## Tech stack

- **Languages:** <e.g., Python, TypeScript, Go>
- **Frameworks:** <e.g., React, FastAPI>
- **Tools:** <e.g., uv, conda, Git, VS Code>
- **Package managers:** <e.g., uv preferred over pip>

## Active projects (high-level — details in projects/<slug>/memory-bank/)

- **<Project 1 slug>:** <1-line description + status>
- **<Project 2 slug>:** <1-line description + status>

## Compliance posture

- **Edition deployed:** <biotech | general>
- **Compliance preset:** <none | healthcare | enterprise | custom>
- **Regulatory exposure:** <HIPAA / GDPR / SOC2 / none / other — be specific>

## Behavioral preferences

Pet peeves ("never do") and "always do" behaviors live in `feedback/feedback.md` as FB-NNN entries — per BOOTSTRAP_PROMPT.md Step 7 #4. They auto-promote to standing rules upon recurrence_count threshold (per SCHEMA_A18 B6 — biotech ≥3, general ≥5).

Do NOT duplicate them in this file. `feedback/feedback.md` is the single canonical location.

## Deployment tier

- **Code Execution:** <enabled | blocked>
- **Skills:** <enabled | blocked>
- **Web Search:** <enabled | blocked>
- **Node.js:** <available | not-installed>
- **Anthropic beta access:** <enabled | none>
- **Current effective tier:** <T0 | T1 | T2 | T3 | T4>

(See ARCHITECTURE.md §11.3 for tier definitions. Some Tier C features auto-activate based on these.)
```

---

## Worked example

```markdown
## Identity
- **Name:** <your-name>
- **Role:** Research Scientist
- **Organization:** <your-organization> (R&D Department)
- **Domain:** Biotech R&D — molecular NGS-based assay development, liquid handling automation, bioinformatics

## Communication preferences
- **Response style:** Brief, direct
- **Technical level:** Expert in domain (molecular diagnostics, ML, AI agents)
- **Formatting:** Markdown tables ok; prefer concise summaries

## Tech stack
- **Languages:** Python (primary), some TypeScript
- **Frameworks:** Pandas, scikit-learn, custom NGS pipelines
- **Tools:** uv (primary), Conda (project-specific envs), VS Code, Git
- **Package managers:** uv preferred over pip for personal use

## Active projects
- **NGS analysis workflows:** sequencing data processing + biomarker linkage. Active.
- **[Example project]:** Schema package design (phase 1 in progress). Active.

## Compliance posture
- **Edition deployed:** general
- **Compliance preset:** none (work projects use <your-organization> infrastructure separately)
- **Regulatory exposure:** Work touches HIPAA in production but memory stack here is for development/R&D notes; PHI never enters this memory system

## Behavioral preferences
(See `feedback/feedback.md` — pet peeves and "always do" items live there as FB-001 through FB-NNN entries.)

## Deployment tier
- **Code Execution:** blocked (pending admin)
- **Skills:** blocked
- **Web Search:** blocked
- **Node.js:** not installed
- **Anthropic beta:** none
- **Current effective tier:** T0
```

## Usage notes

- **Loaded every session (Tier 1):** Keep this file accurate; it shapes every interaction
- **Size cap:** 80 lines per MEMORY_PROTOCOL.md §11. Should rarely grow — consolidate if it does.
- **Update on change:** When role, tech stack, or projects change materially, update this file
- **Sensitive info:** OK to include role and projects; NEVER include personal info beyond what's professionally relevant

## Cross-references

- `MEMORY_PROTOCOL.md` §1.2 (Tier 1 load), §7 (standing rules incl. no-PII/PHI), §11 (size limits)
- `BOOTSTRAP_PROMPT.md` §Step-7 (setup wizard populates this file)
- `ARCHITECTURE.md` §11.3 (tier definitions)
