# PREFLIGHTQC — G-12 OWNER RISK ACCEPTANCE RECORD (V1)

| Field | Value |
| --- | --- |
| Date executed | **2026-08-09** |
| Release accepted | **PreflightQC 1.0.0 · Publisher ITISYOU · Windows x64 · Policy U — intentionally unsigned** |
| Accepted by | The Product Owner (leelaaravind), by explicit written instruction, reproduced verbatim in §2 |
| Gate | **G-12 (owner licensing & compliance risk acceptance, SPEC LOCK v1.1.0): COMPLETE for this release identity only** |
| Reopening | Any material change to dependencies, licences, distribution model, jurisdictions, or functionality **voids this acceptance** and reopens G-12 |
| **Never claimed** | No attorney review. No legal advice. No legal clearance. The residual risk is not claimed to be zero. |

## 1. WHAT WAS EXECUTED

The acceptance statement of `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md` §8,
for the release identity frozen on 2026-08-09
(`docs/reports/RELEASE-IDENTITY-FREEZE-V1.md`). The prerequisites of the amended gate
held at execution time:

| Condition (ADR §5) | State at execution |
| --- | --- |
| O-1 manifest complete | Mechanical gate PASS (verification build) |
| O-2 licence texts / notices present | Mechanical gate PASS |
| O-3 corresponding-source prepared | Bundle staged and verified; publication (H-1…H-3) remains a pre-distribution step |
| O-4 EULA present with carve-outs | PASS by test; draft banner removal remains a final-build step |
| O-5 unresolved questions documented | L-1…L-14 in `docs/licensing/LEGAL-REVIEW-PACK-V1.md`, unchanged |
| O-6 owner's written acceptance | **Executed — this record** |
| O-7 no attorney/clearance claim | Enforced by repository-wide guard test |
| O-8 reopening rule | Recorded here and in the ADR; mechanised in `generate_manifest.py`, which reports G-12 complete **only** for product version 1.0.0 |

## 2. THE PRODUCT OWNER'S INSTRUCTION — VERBATIM

> PRODUCT OWNER DECISION:
>
> I explicitly accept the documented residual licensing/compliance risks for:
>
> PreflightQC 1.0.0
> Publisher: ITISYOU
> Platform: Windows x64
> Release posture: Policy U — intentionally unsigned
>
> I understand:
>
> - no attorney has reviewed the product;
> - no legal clearance is claimed;
> - L-1 through L-14 remain unresolved professional-judgment questions;
> - R-1 through R-9 remain documented residual risks;
> - this acceptance applies only to this frozen release identity;
> - any material dependency, licensing, distribution, jurisdiction or functionality
>   change reopens G-12;
> - professional legal review remains recommended in the future.

## 3. WHAT THIS ACCEPTANCE DOES NOT DO

- It does **not** answer L-1…L-14 or close R-1…R-9 — they are accepted, unresolved.
- It does **not** constitute, replace, or claim attorney review, legal advice, or
  legal clearance of any kind.
- It does **not** authorise the final build or any distribution: `FINAL BUILD
  APPROVED` has not been issued, Policy U conditions U-1…U-6 are not yet all met,
  the corresponding-source page is not live, and clean-machine validation has not run.
- It does **not** extend to any other version, build, or identity. A changed identity
  requires a new acceptance.
