# ADR — G-12: OWNER LICENSING & COMPLIANCE RISK ACCEPTANCE (V1)

| Field | Value |
| --- | --- |
| Decision ID | ADR-G12-V1-OWNER-RISK-ACCEPTANCE |
| Date | 2026-08-09 |
| Decided by | **Product Owner** — explicit written instruction, per SPEC LOCK §29.2(1) |
| Status | **ADOPTED.** Amends spec §26.1 via the SPEC LOCK procedure (spec v1.0.0 → v1.1.0) |
| Supersedes | The mandatory-attorney-review form of gate G-12 (below), and every statement in this repository that attorney review is an absolute V1 release prerequisite |
| **What this is not** | **No attorney has reviewed anything. No legal advice has been received. No legal clearance exists or is claimed, here or anywhere in this repository.** |

---

## 1. WHAT G-12 WAS

Spec §26.1 (v1.0.0), verbatim:

> | G-12 | **Final commercial licence and EULA review by a qualified software-IP attorney is complete.** |
>
> **No legal clearance is claimed by this specification or by any document in this
> repository.** G-12 is a hard release prerequisite.

**Why it was originally introduced.** PreflightQC is a closed-source commercial product
bundling copyleft-licensed components (LGPLv3 FFmpeg, LGPLv3 Qt/PySide6). The licensing
gate identified real interpretive questions — the frozen-bundle §4(d)(1) route, the
bootloader exception, patent provisions, consumer-law limits — that engineering can
frame but cannot answer. G-12 existed so those questions would reach someone qualified
to answer them before money changed hands. That reasoning was sound and is not being
repudiated; see §7.

`docs/reports/G12-AUDIT-V1.md` (2026-08-09) confirmed the requirement was explicitly
mandatory in four independent places, and that attorney engagement had not started.

## 2. THE DECISION

The Product Owner supersedes mandatory attorney review for V1 and replaces G-12 with:

> **G-12 — OWNER LICENSING & COMPLIANCE RISK ACCEPTANCE**

The new gate's conditions are in §5. It remains **blocking** — release without closing
it is still prohibited — but it closes on the owner's explicit, informed, written
acceptance of residual risk rather than on professional review.

## 3. REASONS — RECORDED PERMANENTLY

1. PreflightQC V1 is developed under a strict **£0 mandatory upfront-spend constraint**.
2. Mandatory paid external legal review conflicts with that V1 constraint.
3. Engineering has produced extensive **mechanical licensing/compliance evidence** and a
   structured legal-review pack (`docs/licensing/LEGAL-REVIEW-PACK-V1.md`: facts
   F-1…F-14, each enforced by failing-closed automation).
4. The owner understands that **engineering evidence is not legal advice**.
5. The owner **accepts that releasing without professional legal review leaves residual
   legal and licensing risk** — including the possibility that a compliance
   interpretation relied on here is wrong.
6. **Professional legal review remains recommended** and may be performed later,
   particularly if dependencies, distribution model, jurisdictions, functionality, or
   the revenue/risk profile materially change.
7. This is a **deliberate risk-acceptance and specification decision, not a finding
   that legal review is unnecessary.**

## 4. EVIDENCE AVAILABLE AT DECISION TIME

- `docs/licensing/LEGAL-REVIEW-PACK-V1.md` — 14 mechanically established facts, each
  backed by a script or test that fails the release if it stops being true; a
  13-document inventory; 14 framed legal questions. **Preserved unchanged as the
  evidence base. It has not been reviewed by counsel.**
- `docs/reports/G12-AUDIT-V1.md` — the pre-amendment audit of the gate.
- 1,295 passing tests, including the licensing-gate suite; mypy and ruff clean.
- The licensing gate's mechanical results: G-1…G-10 and G-13 automated checks passing;
  corresponding-source bundle staged and verified.

## 5. THE NEW GATE — CONDITIONS REQUIRED BEFORE RELEASE

G-12 (owner form) closes only when **all** of the following hold:

| # | Condition | Verified how |
| --- | --- | --- |
| O-1 | Dependency manifest complete and matching the shipped package | Mechanical (G-1 tooling) |
| O-2 | All required licence texts and third-party notices present and accurate | Mechanical (G-2 tooling) |
| O-3 | Corresponding-source obligations prepared, and published as applicable, per `CORRESPONDING-SOURCE-PLAN.md` | Mechanical + human (H-1…H-3) |
| O-4 | EULA present, shipped verbatim, carrying its required carve-outs | Mechanical (G-8 clause tests) |
| O-5 | Known unresolved legal questions **documented** — currently L-1…L-14 in the legal-review pack — with no pretence they are answered | This ADR + the pack |
| O-6 | The Product Owner has **explicitly accepted the residual risk in writing** for the specific release (the §8 statement, or equivalent, dated and identifying the release version) | Human — the owner, nobody else |
| O-7 | **No claim of attorney review or legal clearance** appears anywhere in the product, its documents, or its listings | Mechanical scan + review |
| O-8 | Any material change to dependencies, licences, distribution model, jurisdictions, or functionality since the last acceptance **reopens this gate** | Standing rule; the same triggers reopen professional-review consideration (§7) |

## 6. RISKS ACCEPTED

By closing this gate, the owner accepts — knowingly and without professional advice —
the unresolved questions **L-1 through L-14** of the legal-review pack, including:

- the LGPLv3 §4(d)(1) interpretation for Qt in a frozen bundle (L-1) and the
  PyInstaller bootloader exception scope (L-2);
- LGPLv3 Installation Information and patent provisions in commercial distribution
  (L-3, L-4);
- the subprocess / mere-aggregation line for ffprobe (L-5);
- sufficiency of the written source offer, EULA carve-outs, governing-law and
  consumer-law posture (L-6…L-10);
- the Microsoft Distributable Code pass-through treatment (L-11);
- trademark exposure, including the uncleared product name (L-13); and
- the residual risk register R-1…R-9 of `LICENSING-GATE-V1.md`, which that document
  correctly says it does not close.

The owner also accepts that the mechanical evidence, however thorough, verifies facts
about the artefact — not legal conclusions.

## 7. CONDITIONS THAT REOPEN PROFESSIONAL-REVIEW CONSIDERATION

Professional legal review must be actively reconsidered — not merely permitted — when
any of the following occurs:

1. Any change to bundled third-party components, their versions, or their licences.
2. A change of distribution model (new marketplace, reseller, bundle, enterprise sales).
3. Sales into a jurisdiction with materially different consumer or IP law.
4. New functionality touching decode, encode, upload, or platform APIs.
5. Material revenue, or any legal contact: a licence-compliance inquiry, trademark
   objection, patent assertion, or consumer-law complaint — in which case review is
   **urgent**, not optional.
6. Any acquisition, investment, or due-diligence event.

## 8. OWNER ACCEPTANCE STATEMENT (TO BE EXECUTED PER RELEASE)

> I, the Product Owner of PreflightQC, have read this decision record, the legal-review
> pack, and the unresolved questions L-1…L-14. I understand that no attorney has
> reviewed this product, that nothing in the repository is legal advice, and that
> releasing carries residual legal and licensing risk. I accept that risk for release
> version: ______ Date: ______ Signature: ______

**This block is intentionally unsigned in this document.** Signing happens per release,
at release time. Its absence means G-12 is OPEN.

## 9. DOCUMENTS SUPERSEDED OR AMENDED

| Document | Disposition |
| --- | --- |
| Spec §26.1 G-12 row and closing paragraph | Amended (v1.1.0, changelog entry) |
| `LICENSING-GATE-V1.md` header box, §8 table, §8.1 ordering, §10 closing | Amended to the owner-gate form |
| `IMPLEMENTATION-PLAN-V1.md` G-12 row, GATE-5/GATE-6 | Amended |
| `RELEASE-VALIDATION-V1.md` sign-off condition 4 | Amended |
| Every other living document naming attorney review as an absolute prerequisite | Updated to reference this ADR |
| Dated reports (release audit, gate reports, G-12 audit, etc.) | **Preserved verbatim** with a dated amendment note — history is not rewritten |
| `LEGAL-REVIEW-PACK-V1.md` | **Preserved** as the evidence base and as the input for any future professional review. Not reviewed by counsel, and its text continues to say so |

## 10. FINAL STATEMENTS

- **No legal advice has been sought or received for this decision.**
- **No legal clearance is claimed by this document or any other in this repository.**
- This ADR records a risk-acceptance decision by the Product Owner under the SPEC LOCK
  procedure. It does not make the underlying legal questions go away, and it says so.
