# Tech Context — Template (Memory Bank, Cline 6-file convention)

> **Purpose:** The environment file. Lists technologies used, development setup, technical constraints, dependencies, and tool usage patterns.
> **Schema:** v3.0
> **Deploys to:** `memory/projects/<slug>/memory-bank/techContext.md`

---

```markdown
# Tech Context — <Project Name>

---
id: TECHCONTEXT-<slug>
created_at: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
source_agent: <user | orchestrator>
source_session: <N>
status: active
schema_version: "3.0"
project_slug: <slug>
---

## Tech Stack

### Languages
- **Primary:** [Language + version]
- **Secondary:** [Language + version, if applicable]

### Frameworks
- [Framework 1 + version + role]
- [Framework 2 + version + role]

### Libraries / Packages (key)
- `<package>` (vN.N.N) — [Role]
- `<package>` (vN.N.N) — [Role]
- (Reference `requirements.txt` / `package.json` / `pyproject.toml` etc. for full list)

### Tools
- [Build tool + version]
- [Test framework + version]
- [Linter / formatter + version]
- [Package manager + version]

## Development Setup

### Prerequisites
- [Software 1]
- [Software 2]

### Setup steps
1. `<command>` — [what this does]
2. `<command>` — [what this does]
3. ...

### Verification
- Run `<command>` to verify setup is correct. Expected output: `<output>`

## Technical Constraints

- **Performance:** [e.g., must respond in <200ms; must handle 10K req/s]
- **Memory:** [e.g., max 4GB; must run on N CPU cores]
- **Compatibility:** [Browser / OS / version requirements]
- **Security:** [e.g., must satisfy HIPAA §164.312 if handling regulated data]
- **Regulatory:** [Compliance requirements specific to this project]

## Dependencies

### External services
- [Service 1] — [What it provides + endpoint]
- [Service 2] — [What it provides + endpoint]

### Internal dependencies (other projects / shared code)
- [Project 1] — [What we use from it]
- [Project 2] — [What we use from it]

## Tool Usage Patterns

- **<Tool 1>:** [Specific patterns of use — e.g., "always pass `--strict`, never use interactive mode"]
- **<Tool 2>:** [Patterns]

## Environment Variables / Config

- `<VAR_NAME>` — [Purpose, where to find value, NOT the value itself]
- (NEVER store secret values here per MEMORY_PROTOCOL.md §7 standing rules)

## Known Issues + Workarounds

- **Issue 1:** [Description] — **Workaround:** [How to avoid / mitigate]
- **Issue 2:** [Description] — **Workaround:** [Approach]

---

> **Reminder:** This file is for HOW the project is built (tech, setup, constraints). WHAT the project does is in productContext.md. WHO the components are is systemPatterns.md.
```

---

## Usage notes

- **Versions matter:** Pin specific versions where they affect compatibility. Update when upgrading.
- **NEVER store secrets:** Per MEMORY_PROTOCOL.md §7 standing rule. Reference `<VAR_NAME>` and where to find it, never the value.
- **Workarounds are valuable:** Capture known issues + their workarounds — saves future-you from re-discovering them.
- **Update on stack change:** New library, new tool, new environment requirement → edit this file

## Cross-references

- `SCHEMA_A3_per_project_memory_bank.md`
- `projectbrief.md` (THIS tech stack serves THAT scope)
- `systemPatterns.md` (architecture this stack implements)
- `MEMORY_PROTOCOL.md` §7 (no secrets in memory files)
