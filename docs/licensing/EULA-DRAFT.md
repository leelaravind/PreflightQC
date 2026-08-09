# PREFLIGHTQC — EULA DRAFT NOTES (GATE G-8)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Operative text | **`packaging/EULA.txt`** — that file is the single source, shipped verbatim as `licenses/EULA.txt` and shown on the installer's licence page |
| Status | **DRAFT. Not reviewed. Not cleared.** |
| Blocking gate | **G-12 — attorney review. Not started.** |

This file is not a second copy of the agreement. Keeping the operative text in one place
means the shipped licence and the reviewed licence cannot drift apart, which is the whole
failure mode worth engineering against here. What follows is *why* the draft says what it
says, and what a reviewer needs to look at.

---

## 1. THE CARVE-OUTS, AND WHY EACH ONE IS THERE

FFmpeg's own compliance checklist names three EULA obligations. All three are met by
§3 of the draft.

| Obligation | Where | Why it matters |
| --- | --- | --- |
| Mention FFmpeg and the LGPL **in the EULA** | §3, first bullet — names FFmpeg, the URL, and **LGPLv3** explicitly | Naming "LGPL" without the version would be wrong: this build carries `--enable-version3` |
| **Disclaim ownership** of FFmpeg | §3.1 | The EULA asserts rights over the Software; without this, that assertion reads as covering FFmpeg too |
| **Remove any reverse-engineering prohibition** | §3.2 — an express grant, not merely an absent prohibition | This is the single most common LGPL failure in commercial software |

Two additions beyond the checklist, both load-bearing:

- **§3 precedence clause.** Any conflict between this agreement and an open source licence
  resolves in favour of the open source licence. A carve-out that only addresses reverse
  engineering leaves every *other* clause free to collide with the LGPL. The precedence
  clause closes the class of problem rather than one instance of it.
- **§3.3 replaceability.** LGPLv3 §4(d)(0) requires the user to be able to relink or
  substitute the covered libraries. The product's one-dir layout makes that physically
  true; §3.3 states it and confirms we do not restrict it. This is the EULA half of gate
  **G-13**.

### 1.1 The reverse-engineering clause is a grant, not a silence

Boilerplate EULAs prohibit reverse engineering by default. The draft does not merely omit
the prohibition — it affirmatively grants the right for the LGPL components and states
that nothing in the agreement shall be read as restricting LGPLv3 rights. Silence would
leave a court to infer intent from an industry norm that points the wrong way.

---

## 2. THE TRANSLATION OBLIGATION

FFmpeg's checklist requires the reverse-engineering fix in **all translations**, not just
the English text. §8 of the draft records this inside the agreement itself, so a
translator sees the constraint rather than having to be told about it out of band.

**Standing rule.** No translation ships until §3.1, §3.2 and the §3 precedence clause have
been carried into it and re-checked. A translated EULA that quietly reinstates a
reverse-engineering prohibition breaches the LGPL in the only language that reader relies
on — and it will not be caught by any test we can write.

---

## 3. WHAT THE DRAFT DELIBERATELY DOES NOT DO

| Omission | Reason |
| --- | --- |
| No governing law or jurisdiction | Depends on where the publishing entity is established and where it sells. Guessing produces a clause that looks finished and is wrong. |
| No pricing, subscription or refund terms | Not a licensing question; commercial terms are a separate decision. |
| No claim that the product guarantees platform acceptance | §2 states the opposite, deliberately. Platforms change requirements without notice, and a PASS is a statement about the file, not a promise about a third party. |
| No assertion that any gate is legally cleared | Nothing in this repository claims that, and this file must not become the first place it appears. |

---

## 4. WHAT A REVIEWER MUST DECIDE (G-12)

Carried in §9 of the draft so they travel with the document:

1. **LGPLv3 "Installation Information" for User Products** (LGPLv3 §4 / GPLv3 §6) — what,
   if anything, it requires of a desktop application delivered as an installer. This is a
   v3-specific obligation with no v2.1 equivalent, and it arrived with the SPEC LOCK
   amendment.
2. **LGPLv3 patent provisions** and their interaction with commercial distribution.
3. Whether **§3.2 is drafted broadly enough** for every jurisdiction of sale.
4. **Governing law and jurisdiction.**
5. **Consumer-law limits** on the warranty and liability sections in each target market.
6. Whether the **Microsoft Visual C++ runtime** redistribution terms are satisfied as
   shipped — see the open action in the release audit.

---

## 5. STATUS

| Item | State |
| --- | --- |
| Required carve-outs present | **Yes** — §3, §3.1, §3.2, §3.3 |
| Translation requirement recorded | **Yes** — §8 |
| Shipped in the package | **Yes** — `licenses/EULA.txt`, and shown by the installer |
| Verified by test | **Yes** — `tests/packaging/test_release_artefacts.py` asserts each required clause is present |
| **Attorney reviewed** | **NO — G-12 open. This is a hard release gate.** |
