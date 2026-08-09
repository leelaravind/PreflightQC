# PREFLIGHTQC — G-12 SPEC LOCK AMENDMENT REPORT

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Amendment | Spec v1.0.0 → **v1.1.0** — §26.1 gate G-12, via the SPEC LOCK procedure (§29.2) |
| Authority | Explicit written Product Owner instruction (§29.2 step 1) |
| Decision record | `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md` |
| Tests | **1,309 passed, 3 skipped, 0 failed** (was 1,295 — 14 new amendment-guard tests) · mypy clean · ruff clean |
| Licensing gate re-run (§29.2 step 4) | G-1, G-2, G-5 mechanical checks **PASS**; `verify_source.py` **PASS**; G-12 reports **NOT COMPLETE** under its new name |
| **Status** | **G-12 SPEC LOCK AMENDMENT COMPLETE — OWNER RISK ACCEPTANCE REQUIRED** |
| **Never claimed** | No attorney reviewed anything. No legal clearance exists or is claimed. |

---

## 1. EXACT PREVIOUS REQUIREMENT (spec v1.0.0 §26.1, verbatim)

> | G-12 | **Final commercial licence and EULA review by a qualified software-IP attorney is complete.** |
>
> **No legal clearance is claimed by this specification or by any document in this
> repository.** G-12 is a hard release prerequisite.

## 2. EXACT NEW REQUIREMENT (spec v1.1.0 §26.1, verbatim)

> | G-12 | **Owner licensing & compliance risk acceptance is complete** *(amended 2026-08-09 by SPEC LOCK, v1.1.0 — previously: attorney review; see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`)*: the dependency manifest is complete; all required licence texts and notices are present; corresponding-source obligations are prepared and published as applicable; the EULA is present with its required carve-outs; every known unresolved legal question is documented (currently L-1…L-14 in `docs/licensing/LEGAL-REVIEW-PACK-V1.md`); the **Product Owner has explicitly accepted the residual legal/licensing risk in writing for the specific release**; no claim of attorney review or legal clearance appears anywhere; and any material change to dependencies, licences, distribution, jurisdictions or functionality reopens the gate. |

The gate was **not deleted**; it remains blocking and human. The closing paragraph now
also states, in the spec itself: *"No attorney has reviewed this product."*

## 3. RATIONALE (recorded permanently in the ADR §3)

£0 mandatory-spend constraint; conflict of mandatory paid review with that constraint;
extensive mechanical evidence and a structured review pack already exist; the owner
understands engineering evidence is not legal advice; the owner accepts residual
legal/licensing risk; professional review remains recommended, with reopening triggers;
and this is a deliberate risk-acceptance decision, **not** a finding that legal review is
unnecessary.

## 4. FILES CHANGED

| Category | Files |
| --- | --- |
| Decision record (new) | `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md` |
| Specification | `PREFLIGHTQC-V1-SPEC.md` — version 1.1.0, new Changelog section, §26.1 G-12 row + closing paragraph |
| Gate documents | `LICENSING-GATE-V1.md` (header, §2.0, §4.4, Q-2, §8 table, §8.1 ordering note, §10 closing); `IMPLEMENTATION-PLAN-V1.md` (G-12 row, GATE-5/6, risk line); `RELEASE-VALIDATION-V1.md` (sign-off cond. 4) |
| Living licensing docs | `EULA.txt` (draft banner + §9 retitled "OPEN LEGAL QUESTIONS"); `EULA-DRAFT.md`; `G13-QT-LICENCE-POSTURE.md`; `CORRESPONDING-SOURCE-PLAN.md` (H-4/H-6); `UNSIGNED-RELEASE-POLICY-V1.md`; `MS-VC-Redistributable.txt` §3; `LEGAL-REVIEW-PACK-V1.md` (status note only — content preserved) |
| Other living docs | `README.md`, `packaging/README.md`, `MARKETPLACE-LISTING-V1.md` (D-1, §10), `ADR-001-TECH-STACK.md` (Q-1/Q-2, §4, §7) |
| Tooling | `packaging/generate_manifest.py` — gate key `G-12_attorney_review` → `G-12_owner_risk_acceptance`, honest NOT COMPLETE message |
| Historical reports | 8 dated reports annotated with a uniform **AMENDMENT NOTE** and otherwise preserved verbatim: RELEASE-AUDIT, G12-AUDIT, FINAL-PREBUILD-AUDIT, CORRESPONDING-SOURCE-READINESS, RELEASE-PREP-SOURCE-MSVC, IMPLEMENTATION-COMPLETION, LGPLV3-SPEC-LOCK-REPORT, INSPECTOR-GATE-1-REPORT |
| Tests (new) | `tests/packaging/test_g12_amendment.py` — 14 tests |
| Verification build | Updated `EULA.txt` + `MS-VC-Redistributable.txt` copied into `dist/PreflightQC/licenses/`; manifest + notices regenerated |

## 5. L-1…L-14 DISPOSITION

**All fourteen remain UNRESOLVED.** None was answered, none was removed. Their
disposition changed from *"awaiting mandatory professional review"* to *"documented,
owner-accepted residual risk under the amended G-12; agenda for professional review if
later performed"* (ADR §6). `LEGAL-REVIEW-PACK-V1.md` is preserved unchanged apart from
a status note, and continues to state it has not been reviewed by counsel.

## 6. RESIDUAL RISKS

Everything in ADR §6: L-1…L-14 (LGPLv3 frozen-bundle route, bootloader exception,
Installation Information, patent provisions, mere aggregation, source-offer and EULA
sufficiency, governing/consumer law, Microsoft pass-through, trademark including the
uncleared product name, inspection patent scope) plus the licensing gate's R-1…R-9.
Accepted knowingly, without professional advice, and reopened by the ADR §7 triggers —
including **urgently** on any legal contact.

## 7. TESTS AND CHECKS PERFORMED (§29.2 steps 3–4)

| Check | Result |
| --- | --- |
| Full regression | **1,309 passed, 3 skipped, 0 failed** (exit 0) |
| New amendment guards | 14 tests: ADR completeness (reasons, £0, unresolved questions, reopening conditions, unsigned acceptance block), spec version/changelog/gate wording, manifest gate renamed and NOT COMPLETE, EULA questions survived the retitle, and a repo-wide scan proving **no document affirmatively claims attorney approval or legal clearance** (with a self-test that the scan can fire) |
| Mechanical licensing tests | Unweakened — all prior EULA-clause, notice, claim-guard, MS-runtime and Policy U tests pass unchanged |
| Licensing gate re-run | `generate_manifest.py` exit 0 (G-1/G-2/G-5 PASS; G-12 NOT COMPLETE, reported not enforced); `verify_source.py` exit 0 |
| mypy / ruff | Clean (55 files / all checks) |
| Third-party obligations | **Untouched** — no binary, dependency, licence text or notice obligation was altered to make anything pass |

## 8. REPOSITORY-WIDE CONTRADICTION SCAN

Terms swept: `G-12`, `attorney`, `counsel`, `legal clearance`, `hard release
prerequisite`, `legal review` — across all tracked files. After the amendment, every
remaining occurrence is one of:

1. the **amended wording** itself or an amendment marker pointing at the ADR;
2. an **honest negation** ("No attorney has reviewed…", "not attorney reviewed");
3. a **verbatim historical citation inside a dated report**, now behind that report's
   AMENDMENT NOTE banner;
4. `Temp/` phase-instruction archives (historical inputs, deliberately untouched).

No document still asserts that attorney review is an absolute release prerequisite. The
`test_no_affirmative_review_or_clearance_claim_anywhere` scan enforces the claims side
of this permanently.

## 9. `git status --short`

```
 M README.md
 M docs/architecture/ADR-001-TECH-STACK.md
 M docs/licensing/CORRESPONDING-SOURCE-PLAN.md
 M docs/licensing/EULA-DRAFT.md
 M docs/licensing/G13-QT-LICENCE-POSTURE.md
 M docs/licensing/LEGAL-REVIEW-PACK-V1.md
 M docs/licensing/LICENSING-GATE-V1.md
 M docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md
 M docs/marketing/MARKETPLACE-LISTING-V1.md
 M docs/planning/IMPLEMENTATION-PLAN-V1.md
 M docs/planning/RELEASE-VALIDATION-V1.md
 M docs/reports/CORRESPONDING-SOURCE-READINESS.md
 M docs/reports/FINAL-PREBUILD-AUDIT-V1.md
 M docs/reports/G12-AUDIT-V1.md
 M docs/reports/IMPLEMENTATION-COMPLETION-V1.md
 M docs/reports/INSPECTOR-GATE-1-REPORT.md
 M docs/reports/LGPLV3-SPEC-LOCK-REPORT.md
 M docs/reports/RELEASE-AUDIT-V1.md
 M docs/reports/RELEASE-PREP-SOURCE-MSVC.md
 M docs/specification/PREFLIGHTQC-V1-SPEC.md
 M packaging/EULA.txt
 M packaging/README.md
 M packaging/generate_manifest.py
 M third-party/licenses/MS-VC-Redistributable.txt
?? docs/decisions/
?? docs/reports/G12-SPEC-LOCK-AMENDMENT-REPORT.md
?? tests/packaging/test_g12_amendment.py
```

Nothing committed, nothing pushed, nothing built, signed, published or released.

---

## G-12 SPEC LOCK AMENDMENT COMPLETE — OWNER RISK ACCEPTANCE REQUIRED

The gate is amended, not passed. Before any release, the Product Owner must execute the
acceptance statement in ADR-G12 §8 for the specific release version. **No attorney
approval and no legal clearance is claimed, here or anywhere.**
