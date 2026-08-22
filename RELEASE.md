# Release Checklist — Ultimate Memory Stack

Every item here exists because **this project actually shipped that defect**. Nothing is included
on general principle. If you cannot trace a line to a real failure, it does not belong.

Work top to bottom. A box you cannot tick is a release you do not cut.

---

## 0. Before anything — read this

The recurring failure in this codebase is not broken code. It is **a claim with nothing behind it**:
documentation describing a capability no code provides, a guard nothing invokes, a statistic with no
source. Every green suite in this project's history was green while at least one of those was true.

So the question at each step is not *"did the tests pass?"* It is **"what would have to be true for
this claim to be false, and did I check that?"**

---

## 1. Claims and citations

- [ ] **`pytest tests/test_citations.py` passes.** Every cited arXiv ID is registered in
      `common-specs/CITATIONS.md` with a verification date.
      <sub>*Shipped 2026-08-20: `arXiv:2501.13956` attributed to "Chalef et al." — he is the last of
      five authors; and `arXiv:2503.03704`, an arXiv preprint, called "peer-reviewed" in **two**
      evidence tables.*</sub>
- [ ] **Every NEW factual claim in this release has been checked against a primary source** — not
      recalled, not inherited from an earlier doc. Read the paper, the LICENSE file, the API
      response. Quote it.
      <sub>*Four of four load-bearing roadmap justifications audited on 2026-08-20 were wrong or
      unsourced. Three of them had been copied forward, unchecked, by later documents.*</sub>
- [ ] **No capability is described that no code performs.** For each capability claim, name the
      file and function. If you cannot, delete the claim or ship the code.
      <sub>*v4.0.1 withdrew ~20 HMAC-signing claims — including in SOC2 and PCI-DSS compliance
      profiles and an installer runtime banner — with no `import hmac` anywhere in the package.*</sub>
- [ ] **Dependency licences read from the upstream LICENSE file**, never a badge, a summary, or a
      previous version of our own docs.
      <sub>*Shipped: Graphify's licence stated as MIT in three places. It is Apache-2.0 — and our
      doc recorded the wrong value as a "correction" of the right one.*</sub>
- [ ] **Volatile figures carry an as-of date, or are removed.** Star counts, version numbers,
      "latest release" claims.
      <sub>*Shipped: "49.6k stars" when the real count was ~109k; "v0.8.13" when latest was 0.9.48.*</sub>

## 2. Every gate is actually wired

- [ ] **For each guard added this release, name the thing that INVOKES it** — a CI step, a test, a
      hook. "It has unit tests" is not an answer; a unit test proves the function works, not that
      anything calls it.
      <sub>*Shipped in a commit: a backend-integrity probe, unit-tested, documented in
      `requirements.txt` as "gated by CI" — and invoked by nothing. Caught by review, not by tests.*</sub>
- [ ] **The full CI matrix is green — not just `unit-tests`.** Check `addon-manifests` across all
      Python versions and all three OSes.
- [ ] **Each newly-gating lint check meets `SCHEMA_lint.md` §14's test obligation**, including a
      negative control.
- [ ] **Every fix in this release was negative-controlled**: revert it, watch its test fail, restore.
      <sub>*Multiple "fixes" in this project were themselves the bug. A test that has never failed
      has never been shown to work.*</sub>

## 3. The installers, on both doors

- [ ] **Run `setup-memory-stack.sh` AND `setup-memory-stack.ps1`** into fresh directories. The doors
      diverge silently — they are two hand-written implementations of one contract.
      <sub>*Shipped: the PowerShell door BOM'd `.ums-manifest.json` so `json.loads()` failed
      outright, while the bash door's parsed fine.*</sub>
- [ ] **Run the verify command the installer PRINTS, exactly as printed**, by copy-paste.
      <sub>*Shipped: `bash C:\pkg\verify.sh C:\vault` — bash eats the backslashes. Every Windows
      user hit it; nothing tested the one command we tell them to run.*</sub>
- [ ] **Parse `.ums-manifest.json` with a real JSON parser** after each door, and diff the two.
- [ ] **Open an installed add-on skill and follow its own instructions literally.** Every file it
      cites must exist where it says.
      <sub>*v4.0.0 shipped every add-on with its documented procedure impossible to follow — the
      installers copied only `SKILL.md`, so the `requirements.txt` and `smoke_test.py` those skills
      told users to run were never placed.*</sub>

## 4. Dependencies

- [ ] **`python recommended-addons/regenerate-locks.py --check --probe-upstream`** passes.
- [ ] **Actually `pip install` each add-on from its lock and run its `smoke_test.py`.** Resolution
      is not installation, and installation is not working.
      <sub>*v4.0.0 shipped two of three manifests literally unresolvable — `graphify` pinned
      `tree-sitter<0.22.0` against a `graphifyy` requiring `>=0.23.0`. Nothing in the repo had ever
      executed a `requirements.txt`.*</sub>
- [ ] **`python recommended-addons/preflight.py`** reviewed — a stale dependency is a decision to
      make, not a number to skim past.
- [ ] **Any new pin is a security-vetting decision**, recorded in the manifest header with its
      reasoning.

## 5. Version and documentation coherence

- [ ] `VERSION`, `CHANGELOG.md`, and every in-doc version string agree.
- [ ] **`CHANGELOG.md` is additions-only against `origin/main`** — released sections are history.
      Verify: `git diff --numstat origin/main -- CHANGELOG.md` shows `N 0`.
- [ ] **Nothing in the shipped docs contradicts anything else in the shipped docs.** Grep the topic
      exhaustively; do not phrase-match.
      <sub>*Twice in one session a fix left a contradicting statement elsewhere in the same file,
      because the sweep matched a keyword rather than enumerating.*</sub>
- [ ] Cross-surface: the landing page's version claim matches this release.

## 6. Before an EXTERNAL user (R2 gate — not required for an internal release)

⚠️ **The roadmap's stated gate is "no external user before this clears." None of it is done.**

- [ ] Weak-model red-team (Test E) — can a small model be talked past the protocol?
- [ ] Compliance-content liability review — we ship SOC2/GDPR/PCI-DSS preset language.
- [ ] External cold-install validation — someone who has never seen this repo installs from scratch.
- [ ] Add-on smoke tests running in CI, not just present in the tree.

## 7. Cutting the release

- [ ] Suite green; record the exact count in the commit message context.
- [ ] Commit is **staged by Claude, committed and pushed by the maintainer.**
- [ ] Plain one-line commit message. **No trailers.**
- [ ] Tag only after `origin/main` carries the commit.
- [ ] GitHub Release notes match `CHANGELOG.md`; mark "latest" deliberately.
- [ ] **Post-push: re-verify from the remote**, not from local state.
      <sub>*A prior release published notes against the wrong tag and showed the previous version as
      "latest".*</sub>

---

## When something ships broken anyway

Add a line here, with the defect in a `<sub>` note. A checklist that does not grow after an
incident is decoration — and this file's whole claim to authority is that every line was paid for.
