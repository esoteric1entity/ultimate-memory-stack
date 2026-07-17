# Security Policy — Ultimate Memory Stack

## Supported versions

| Version | Supported |
|---|---|
| 4.0.x | ✅ current release line |
| 3.6.x | ⚠️ security fixes only (previous release line) |
| < 3.6 | ❌ pre-release R&D versions (never published) |

## Reporting a vulnerability

**Please do NOT open a public issue for security vulnerabilities.**

1. **GitHub Security Advisory** — open a private vulnerability report through
   the repository's "Security" tab → "Report a vulnerability." This is the
   preferred (and currently the only) confidential channel; a direct
   maintainer contact with PGP fingerprint will be published in a future
   release.

Please include: a description, reproduction steps, the affected
files/components, and your assessment of impact. You'll receive an
acknowledgement within 7 days.

## What counts as a security issue here

UMS is a **memory layer for AI agents** — its security surface is mostly
*data handling*, not network services:

- **In scope:** the installers writing outside the confirmed target;
  re-install touching user `memory/` data; the lint/quarantine pipeline
  mutating content it should only surface; PII/credential content escaping
  quarantine routing; template or skill content that induces an agent to
  exfiltrate vault contents; path-traversal in any shipped script.
- **Out of scope:** vulnerabilities in your agent harness (report to the
  harness), in optional addons' upstream projects (Graphiti, Graphify,
  LLMLingua, Obsidian — report upstream), or in Python itself.

## What UMS does NOT provide

UMS stores what your agent writes. It does **not** encrypt the vault at rest,
authenticate readers, or sandbox the agent — file-system permissions and your
harness's controls are the protection layer. For runtime guardrails, see the
sibling Security branch, `agent-shield` (in development).

## Disclosure

We won't publicly disclose a reported vulnerability before a fix is
available, unless it is already being exploited or the reporter requests
immediate disclosure and we agree it's appropriate.
