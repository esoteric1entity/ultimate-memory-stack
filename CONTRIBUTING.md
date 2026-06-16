---
file: CONTRIBUTING
title: "Contributing to Agent Architect Stack"
audience: contributors (human + AI agents)
license: Apache 2.0
---

# Contributing to Agent Architect Stack

Thank you for your interest in contributing. This document covers the **how** of contributing. The **why** is captured in the project's [README](./README.md) and the per-branch documentation.

## Quick links

- [Code of Conduct](#code-of-conduct)
- [Contributor License Agreement (CLA)](#contributor-license-agreement-cla)
- [How to submit a pull request](#how-to-submit-a-pull-request)
- [Coding style](#coding-style)
- [Commit message convention](#commit-message-convention)
- [Testing requirements](#testing-requirements)
- [Documentation requirements](#documentation-requirements)
- [Review process](#review-process)

## Code of Conduct

Be respectful, be constructive, assume good faith. We're all here to make AI agents more reliable. Disagreement on technical approach is welcome; personal attacks are not.

## Contributor License Agreement (CLA)

**All contributors must sign a CLA** before their first pull request can be merged. The CLA is short (~1 page) and protects BOTH you and the project:

- **For you:** it confirms that you retain copyright on your contributions AND that you grant the project a license to use them.
- **For the project:** it provides a clear, documented grant of rights for every contribution, so the project can distribute your work under its Apache 2.0 license without later disputes over what was granted.

The CLA is at [`CLA.md`](./CLA.md) (a separate document). A maintainer will ask you to confirm the CLA on your first PR.

## How to submit a pull request

1. **Fork** the repository.
2. **Create a branch** from `main` (or the relevant branch's default):
   ```bash
   git checkout -b your-name/short-description
   ```
3. **Make your changes** in the fork.
4. **Sign your commits** with the DCO (Developer Certificate of Origin):
   ```bash
   git commit -s -m "Your commit message"
   # The -s flag adds:
   # Signed-off-by: Your Name <your.email@example.com>
   ```
5. **Run the tests** (see [Testing requirements](#testing-requirements) below).
6. **Push** to your fork and open a Pull Request against the upstream `main` (or relevant branch's default).
7. **Fill out the PR template** (auto-loaded by GitHub).
8. **Wait for review.** Reviewer may request changes; iterate.
9. **Merge** happens after 1 approving review + green CI.

## Coding style

| Language | Style | Tool |
|---|---|---|
| Python | PEP 8 + type hints | `ruff` or `black` + `mypy` |
| Bash | shellcheck-clean | `shellcheck` |
| Markdown | line length 120, ATX headers | `markdownlint` (optional) |
| YAML | 2-space indent | (no specific linter enforced) |
| TOML | (any) | (no specific linter enforced) |

Per-file style is consistent within each branch. Match the existing style when adding to a file.

## Commit message convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated changelog generation:

```
<type>(<scope>): <short summary>

<body — explain the WHY, not the WHAT>

<footer — reference issues, breaking changes, etc.>
```

**Types:**
- `feat` — new feature
- `fix` — bug fix
- `docs` — documentation only
- `style` — formatting, no code change
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or fixing tests
- `chore` — maintenance (deps, CI, etc.)

**Scope:** which branch / component is affected (e.g., `memory`, `security`, `umbrella`, `docs`)

**Examples:**
```
feat(memory): add Graphiti backfill for Episodic nodes

Adds backfill utility for ingesting existing decisions/learnings
into the Graphiti graph when upgrading from v0.x to v1.0.

Ref: LEARN-005 (deferred episodes)
```

```
fix(security): close write-guard self-protection gap

Adds RED pattern for agent_shield/*.py to write_guard.py
to prevent Edit attacks on the canonical guard module.
```

## Testing requirements

- **All new code must include tests** (unit + integration where applicable).
- **No PR can reduce test coverage.** If you add code without tests, the PR will be rejected.
- **Tests must pass locally before PR submission.** Each branch has its own test runner:
  ```bash
  # Memory: see ultimate-memory-stack README for test invocation
  # Security: pytest tests/ && bash tests/run_sh_tests.sh (in the agent-shield repo)
  ```
- **For new public functions, add a docstring** explaining inputs, outputs, and at least one example.

## Documentation requirements

Per the project's documentation discipline (defined in the Memory branch specs), all new features, decisions, or standing rules must carry 5 elements:

1. **Purpose** — what this thing is for
2. **Rationale** — why we chose this approach
3. **Sound reasoning** — what the tradeoffs were
4. **Scope CAN** — what this thing does
5. **Scope CANNOT** — what this thing does NOT do

These can be in code comments, README sections, or a short "Design rationale" note in the PR description — the maintainers will promote durable rationale into the project's decision log.

## Review process

1. **Automated checks** (the pytest unit suite + cross-OS install CI) run on every PR; the maintainer reviews all changes.
2. **One approving review** from a maintainer is required for merge.
3. **Reviewer may request changes** — address each comment, then re-request review.
4. **After approval**, the maintainer (or you, if you have write access) merges the PR using "Squash and merge" to keep the main branch history clean.

## Recognition

Contributors are listed in [`AUTHORS.md`](./AUTHORS.md) in alphabetical order. Your GitHub profile picture + contribution count auto-appear in the repo's "Insights → Contributors" tab.

## What NOT to do

- **Don't commit secrets.** Even if your PR is private at first, git history is permanent. If you accidentally commit a secret, follow `git filter-repo` + rotate the secret + LEARN entry.
- **Don't include employer names** in the public code (the biotech-edition is the exception, kept private for that reason).
- **Don't rewrite the LICENSE** in a PR. The project is Apache 2.0; relicensing is governed by the contributor-vote safeguard in CLA.md (and is not on the roadmap).
- **Don't merge your own PR** without an approving review.

## Institutional adoption (biotech edition)

This public repository ships the **general edition**. A HIPAA/PHI-focused institutional edition is planned for a future release (not yet available); it will layer non-overridable healthcare compliance (mandatory audit + quarantine workflows, HIPAA-aligned technical safeguards) on the same architecture you see here. It is not selectable in the general-edition installer today.

Interested in institutional adoption? Open a GitHub Issue describing your use case (or use GitHub Security Advisories for private/sensitive inquiries) so we can gauge demand. Licensing terms for any future institutional deployments will be defined when that edition becomes available.

## Questions?

Open a GitHub Issue. For private or sensitive questions, use GitHub Security Advisories.

## Cross-references

- [`README.md`](./README.md) — project overview
- [`INSTALL.md`](./INSTALL.md) — install guide
- [`LICENSE`](./LICENSE) — Apache 2.0
- [`CLA.md`](./CLA.md) — Contributor License Agreement
- [`AUTHORS.md`](./AUTHORS.md) — contributor list
