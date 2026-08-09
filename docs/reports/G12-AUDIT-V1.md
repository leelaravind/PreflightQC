# PREFLIGHTQC — GATE G-12 AUDIT

> **AMENDMENT NOTE (2026-08-09, added after this report was written).** Gate G-12 was
> amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing &
> compliance risk acceptance** — see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`.
> Statements below describing attorney review as an absolute release prerequisite record
> the gate as it stood when this report was written and are preserved unchanged.
> **No attorney review has occurred, and no legal clearance is claimed.**

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Question | What does the locked specification actually require of G-12, is it explicitly mandatory for a V1 release, and what state is it in? |
| Method | Citations from the locked specification and its subordinate gate documents — no recollection, no paraphrase where the wording is load-bearing |
| G-12 status | **OPEN. NOT STARTED.** This audit does not amend, waive, or pass it. |
| Deliverable alongside this audit | `docs/licensing/LEGAL-REVIEW-PACK-V1.md` — the complete pack for the reviewing attorney |

---

## 1. WHAT THE LOCKED SPECIFICATION REQUIRES — VERBATIM

**`docs/specification/PREFLIGHTQC-V1-SPEC.md` §26.1**, heading and rows:

> **26.1 Release gates (all blocking)**
>
> | G-12 | **Final commercial licence and EULA review by a qualified software-IP attorney is complete.** |

and immediately below the table (spec §26.1, closing paragraph):

> **No legal clearance is claimed by this specification or by any document in this
> repository.** G-12 is a hard release prerequisite.

**`docs/licensing/LICENSING-GATE-V1.md`** (subordinate to spec §21/§26, executed by
Phase 12) — header box:

> **Final commercial licence, EULA, and third-party notice review by a qualified
> software-IP attorney is a hard release prerequisite (gate G-12).** It cannot be
> satisfied by any engineering artefact, test, or automated scan in this repository.

and its gate table (§8):

> All gates are **blocking**. No release proceeds with any gate open.
>
> | **G-12** | **Attorney review of licence, EULA, notices and build manifest complete** | **No — blocking, human** |

**Gate ordering** (licensing gate §8.1):

> before P6 → GATE-3 GUI licence question resolved; **ATTORNEY ENGAGEMENT STARTS**
> Phase 12 → GATE-5 G-1…G-11, G-13 pass; **G-12 initiated**
> Phase 13 → GATE-6 clean-machine validation passes **AND G-12 complete**

**Clean-machine sign-off** (`docs/planning/RELEASE-VALIDATION-V1.md` §4, condition 4):

> **G-12** is complete — attorney review of the licence, EULA and notices.

## 2. DETERMINATION — IS G-12 EXPLICITLY MANDATORY FOR V1 RELEASE?

**Yes. Explicitly, in four independent places, with no conditional path around it.**

1. Spec §26.1 titles the gate table *"Release gates (all blocking)"* and calls G-12 a
   *"hard release prerequisite"* in the same section. The spec is the locked, authoritative
   document; every other document defers to it.
2. The licensing gate states *"No release proceeds with any gate open"* and marks G-12
   *"blocking, human"* — and separately states it **cannot** be satisfied by any
   engineering artefact.
3. GATE-6 — the final gate before release — conjoins clean-machine validation **and**
   G-12 completion. There is no branch, waiver clause, or alternative route anywhere in
   the gate ordering. (Contrast G-11, where the spec's own run-book wording *"or the
   observed behaviour is recorded and accepted"* left room that Policy U later
   formalized. G-12 has no such wording anywhere.)
4. Every downstream artefact repeats it rather than softening it: the EULA carries
   "NOT LEGAL ADVICE" and "has not been reviewed" (asserted by test), the manifest
   generator emits `G-12_attorney_review: NOT COMPLETE` on every run, and Policy U §
   header states G-12 attorney review "still applies to everything customer-facing".

**The only lawful way G-12 could cease to be mandatory** is the SPEC LOCK amendment
procedure (spec §29.2): an explicit written instruction from the product owner, a
specification update, and re-verification. That procedure has **not** been exercised for
G-12, this audit does not recommend exercising it, and nothing in this audit constitutes
such an instruction.

## 3. SCOPE OF G-12 — WHAT THE ATTORNEY MUST ACTUALLY REVIEW

The spec's wording is *"final commercial licence and EULA review"*; the licensing gate
expands the object list to *"licence, EULA, notices and build manifest"*. Union of both,
plus every item the repository itself has explicitly deferred to G-12:

| # | Review object | Deferred-to-G-12 by |
| --- | --- | --- |
| 1 | The EULA (`packaging/EULA.txt`) — including its own §9 list of six open questions | Spec §26.1, EULA-DRAFT header ("Not started") |
| 2 | Third-party notices and licence texts as shipped | Licensing gate header + §8 |
| 3 | The dependency manifest | Licensing gate §8 |
| 4 | LGPLv3 posture: Qt-in-frozen-bundle route (Q-1/R-5), FFmpeg `--enable-version3` cost analysis, patent provisions, Installation Information | Licensing gate §2.0, §4.3–4.4, R-5; G13 doc |
| 5 | PyInstaller bootloader exception scope (Q-2/R-6) | Licensing gate §4.4, R-6 |
| 6 | Subprocess / "mere aggregation" line (R-3) | Licensing gate §10 |
| 7 | Microsoft Distributable Code pass-through as shipped | EULA §9 item 6; `MS-VC-Redistributable.txt` §3 |
| 8 | Corresponding-source written-offer wording (H-4) | `CORRESPONDING-SOURCE-PLAN.md` §6 |
| 9 | Trademark posture: product name and descriptive platform-mark use (R-8) | Licensing gate §10 |
| 10 | Consumer-law and jurisdiction questions | EULA §9 items 3–5 |

## 4. CURRENT STATE, HONESTLY

| Item | State |
| --- | --- |
| G-12 | **OPEN — and per `EULA-DRAFT.md`, engagement is "Not started"** |
| Plan conformance | **Behind plan.** Gate ordering called for attorney engagement at GATE-3, *before* Phase 6. Implementation is past Phase 12. The licensing gate itself predicted this: *"G-12's turnaround is the most likely schedule risk in the whole plan, and it is the one that cannot be accelerated by engineering effort."* Engaging counsel is now the critical-path item for release. |
| Inputs for review | **Complete and assembled** — see `LEGAL-REVIEW-PACK-V1.md`. Everything the review needs exists in the repository; nothing blocks starting the engagement today except selecting and instructing counsel. |
| What engineering can still do | Nothing that advances G-12 itself. The pack separates what counsel may take as mechanically established fact from what requires their judgment, which shortens the engagement — that is the limit of engineering's contribution. |

## 5. WHAT THIS AUDIT DID NOT DO

- It did **not** amend, waive, reinterpret, or pass G-12.
- It did **not** claim, and must not be read as claiming, any legal clearance.
- It did **not** invoke or recommend the SPEC LOCK procedure against G-12.

**G-12 remains OPEN. It is explicitly mandatory for V1 release. The next action is the
product owner's: engage a qualified software-IP attorney and hand them the pack.**
