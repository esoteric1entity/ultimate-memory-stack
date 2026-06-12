# INSTALL_AGENT.md — Agent-Executed Install

> **Audience:** the AI agent your user pointed at this package ("install this").
> Works with Claude Code, OpenClaw, Hermes, or any agent harness with file access.
> **For humans:** you can read this top to bottom — it is the entire specification of
> what your agent will do. **Review before you run.** Agent-executed installs are a
> trust decision: nothing here requires network access, elevated permissions, or
> writes outside the install target you approve in Step 2.

---

You are an agent installing the **Ultimate Memory Stack v3.6.0** — a file-based
persistent-memory scaffold (markdown specs + a `memory/` directory + optional skills)
that your harness reads. Execute the steps below **in order**. Be honest in every
report: never claim a step succeeded without checking its result.

## Step 0 — Consent

Tell the user, in 3–4 lines, what this install will do:
copy `common-specs/` + `general-edition/` into a target directory, initialize a
`memory/` structure, register the memory protocol with the harness, run a setup
wizard, and verify. **Wait for explicit confirmation before touching anything.**

## Step 1 — Detect

Probe (read-only) and report what you find:

1. **Harness:** does the likely target contain `.claude/` → Claude Code project?
   Does `~/.openclaw/workspace/` exist, or does the target carry `AGENTS.md` + `SOUL.md`
   → OpenClaw workspace? Neither → `generic` (any 9-root-file-convention harness).
2. **Existing install:** `.ums-manifest.json` or `memory/` at the target → this is a
   re-install/upgrade, not a fresh install. Read the manifest and say so.
3. **Tools:** can you run bash? PowerShell? python3? (Decides Step 3's mechanism.)

## Step 2 — Confirm the target

Propose a default install target and let the user override:

- Default: the directory the user is working in — **unless it is this package itself.**
- If an OpenClaw workspace was detected, offer it as an option.
- **Never install into the package directory** (mixes user memory into the package
  tree and its git history) unless the user explicitly insists after a warning.

## Step 3 — Scaffold

Pick the strongest available mechanism:

- **bash available:** run the canonical installer — it handles guards, re-install
  refresh, addon registration, and the manifest:
  ```bash
  bash <package>/setup-memory-stack.sh --target <target> --yes --skip-wizard --compliance=none
  ```
  (Adjust flags to the user's wishes: `--minimal`, `--addon <name>`, `--compliance=<preset>`.
  Keep `--skip-wizard` — you will run the wizard conversationally in Step 5.)
- **PowerShell only (Windows):** same flags, PowerShell form:
  `& "<package>\setup-memory-stack.ps1" -Target <target> -Yes -SkipWizard -Compliance none`
  (requires Python 3.8+ on PATH).
- **No shell tools:** copy by hand, following `skills/install-ultimate-memory-stack/SKILL.md`
  Steps 7a–7f (copy `common-specs/` + `general-edition/` into `<target>/ultimate-memory-stack/`,
  create the 9 `memory/` subdirectories, initialize per-preset logs).

## Step 4 — Register with the harness

Wire the install into the harness so it loads every session. Ask before editing any
user-owned file:

| Harness | Registration |
|---|---|
| **Claude Code** | Ensure `<target>/.claude/rules/memory_protocol.md` exists (copy of `common-specs/MEMORY_PROTOCOL.md` — the script already did this). Offer to add `@ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md` as an import note in `CLAUDE.md`. |
| **OpenClaw** | The workspace itself is the memory home. For deep integration (9 root files), run the adapter in `core/openclaw-adapter/`. At minimum, offer to add a pointer in `TOOLS.md`/`AGENTS.md`: where `memory/` lives and that `MEMORY_PROTOCOL.md` governs it. |
| **Generic / Hermes / other** | Offer to add a short section to the harness's instruction file (`AGENTS.md` or equivalent): load `memory/MEMORY_INDEX.md` + `memory/sessions/session_state.md` at session start; follow `ultimate-memory-stack/common-specs/MEMORY_PROTOCOL.md` for all memory operations. |

## Step 5 — Setup wizard (conversational)

Ask the 6 wizard questions and write the answers — identity, active projects,
compliance preset, pet peeves, consumer agent topology, deployment tier. The full
playbook (questions, file destinations, SCHEMA_A18 frontmatter shapes) is
`skills/install-ultimate-memory-stack/SKILL.md` **Step 8** — follow it exactly,
instantiating from `common-specs/templates/`.

## Step 6 — Verify

- bash available: run `<package>/verify.sh <target>` — success ends with
  `✅ All checks passed`.
- Otherwise: run the T1–T9 self-test manually per `common-specs/MEMORY_PROTOCOL.md`
  §1.3 and report each check.

**If verification fails, say so plainly and stop — do not report a successful install.**

## Step 7 — Record

Confirm `<target>/.ums-manifest.json` exists (the script writes it). If you installed
by hand, write it yourself:

```json
{
  "package": "ultimate-memory-stack",
  "version": "3.6.0",
  "edition": "general",
  "installed_at": "<ISO-8601 UTC>",
  "install_door": "agent",
  "harness_detected": "<claude-code|openclaw|generic>",
  "minimal": false,
  "addons": [],
  "source_package": "<package path>",
  "registered": "<what you registered in Step 4>"
}
```

## Step 8 — Report

Summarize honestly: target, edition, preset, addons, harness registration performed,
verification result, manifest location. Then orient the user: memory operations now
follow `MEMORY_PROTOCOL.md` (auto-loaded where the harness supports it); at session
end they can say "update session state"; `verify.sh` re-validates any time.

---

*Cross-references: `INSTALL.md` (human quickstart) · `INSTALLATION_GUIDE.md` (full
multi-method guide) · `skills/install-ultimate-memory-stack/SKILL.md` (the Claude Code
native skill — the richest version of this flow) · `common-specs/BOOTSTRAP_PROMPT.md`
(the activation-prompt alternative).*
