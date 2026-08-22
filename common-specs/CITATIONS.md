# Citation Registry — Ultimate Memory Stack

Every external paper cited anywhere in this package, with what we checked and when.

## Why this file exists

On 2026-08-20 a single review pass found **two wrong citations in shipped documentation** and, in
our internal planning docs, a headline statistic that was wrong on five counts — including a figure
spliced in from a source we had ourselves labelled *debunked*. None of it was malicious and none of
it was careless in the moment. Each was written from memory of a paper rather than from the paper,
and then copied forward by later documents that had no way to tell a checked claim from an
unchecked one.

A prose rule ("verify citations") cannot fix that, because prose rules are invisible to the gates.
This registry can: `tests/test_citations.py` fails if any `arXiv:` ID appears in a tracked document
without an entry here. That does not prove a citation is *used* correctly — only a human reading
the paper can decide that — but it makes the act of registration mandatory and dates it, so the
next reader can tell what was checked and when.

**Scope: arXiv IDs only.** Deliberately narrow. It is the citation form that appears in these docs,
it is machine-extractable, and both defects were of exactly this kind. Standards bodies (OWASP,
MITRE) and vendor blog posts are out of scope — widening this to "all external claims" would make
it unenforceable, and an unenforceable gate is the thing we are trying to stop building.

## How to use it

**Adding a citation:** fetch it, read at least the abstract, add a row, then cite it.
```bash
curl -s "http://export.arxiv.org/api/query?id_list=<ID>" | grep -E "<title>|<name>|<published>|journal_ref"
```
**Never** describe a paper's numbers from memory. Quote the abstract or read the section.

⚠️ **`journal_ref`/DOI absent does not prove a paper was never peer-reviewed** — authors often do
not update arXiv metadata after acceptance. It proves only that arXiv records no venue. Say exactly
that. Do not upgrade a preprint to "peer-reviewed" without a venue you have seen, and do not
downgrade one to "rejected" because the metadata is bare.

---

## Registry

### `arXiv:2501.13956`
| | |
|---|---|
| **Title** | *Zep: A Temporal Knowledge Graph Architecture for Agent Memory* |
| **Authors** | Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, Daniel Chalef |
| **Published** | 2025-01-20 |
| **Venue** | No `journal_ref` or DOI in arXiv metadata (checked 2026-08-20) |
| **We cite it for** | The bi-temporal fact model (`valid_at` / `invalid_at`) that SCHEMA_A18 §B5 adopts, and as the architecture paper behind Graphiti |
| **Cited in** | `ARCHITECTURE.md` §9 · `SCHEMA_A18_per_entry_metadata.md` · `TIER_C_ACTIVATION.md` C2 |
| **Verified** | 2026-08-20 — title, authors, and date read from the arXiv API |

⚠️ **Two traps, both of which we fell into.**
1. The paper is titled ***Zep***, not Graphiti. Graphiti is the open-source engine underneath Zep.
   Citing it as "the Graphiti paper" without saying so invites a reviewer to think we cited the
   wrong work.
2. We wrote **"Chalef et al."** for over a year. Daniel Chalef is the **last of five** authors; the
   first author is **Rasmussen**. Corrected 2026-08-20.

⛔ **Do not cite this paper's benchmark numbers.** Its 94.8% / +18.5% LongMemEval and DMR figures
are vendor-published and unreplicated; `ARCHITECTURE.md` §13 lists them under debunked claims. The
standing rule is *"borrow ideas, not numbers."* This is not theoretical — that exact 94.8% was
later spliced into an unrelated statistic in our own roadmap.

### `arXiv:2503.03704`
| | |
|---|---|
| **Title** | *Memory Injection Attacks on LLM Agents via Query-Only Interaction* |
| **Authors** | Shen Dong, Shaochen Xu, Pengfei He, Yige Li, Jiliang Tang, Tianming Liu, Hui Liu, Zhen Xiang |
| **Published** | 2025-03-05 |
| **Venue** | No `journal_ref` or DOI in arXiv metadata (checked 2026-08-20) |
| **We cite it for** | Evidence that memory poisoning is a real, demonstrated attack class — the justification for the quarantine layer |
| **Cited in** | `SCHEMA_quarantine.md` §3 · `SCHEMA_A18_per_entry_metadata.md` |
| **Verified** | 2026-08-20 |

⚠️ Both citing tables called this a **"peer-reviewed paper"** until 2026-08-20. It is an arXiv
preprint with no venue recorded. That was the same overclaim we refuse to accept from vendor
preprints two files away — we were applying a stricter standard to others than to ourselves. The
paper's *existence and content* fully support the claim it is cited for; only the evidence-strength
label was wrong.

### `arXiv:2506.12707`
| | |
|---|---|
| **Title** | *SecurityLingua: Efficient Defense of LLM Jailbreak Attacks via Security-Aware Prompt Compression* |
| **Authors** | Yucheng Li, Surin Ahn, Huiqiang Jiang, et al. |
| **Published** | 2025-06-15 |
| **Venue** | No `journal_ref` or DOI in arXiv metadata (checked 2026-08-20) |
| **We cite it for** | The successor line of work to LLMLingua, as the migration target if the pinned `llmlingua==0.2.2` becomes unsupportable |
| **Cited in** | `TIER_C_ACTIVATION.md` · `llmlingua-installer/` (README, SKILL.md, INSTALL_LLMLINGUA.md) |
| **Verified** | 2026-08-20 — title and 2025-06 date confirmed; Huiqiang Jiang is a shared author with the LLMLingua line, which is the basis for calling it a successor |

⚠️ We describe it as "Microsoft's successor project". What is verified is the **shared authorship**
and the subject-matter continuity. We have **not** seen Microsoft designate it as a successor or
deprecate LLMLingua. Keep the wording at "the successor line of work"; do not harden it into an
official deprecation notice.

---

## Cross-references
- `ARCHITECTURE.md` §13 — the debunked / not-adopted claims inventory
- `SCHEMA_lint.md` §14 — the exit-code contract these gates run under
- `tests/test_citations.py` — the mechanism that makes this file load-bearing
