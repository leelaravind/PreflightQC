# PREFLIGHTQC V1 — FINAL BINDING IMPLEMENTATION PLAN

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Provenance | This file was found **empty** at execution time. Its content below is the Product Owner's Final Binding instruction of 2026-08-10, recorded verbatim so the plan named by that instruction exists as a durable document. Nothing was added or reinterpreted. |
| Executed by | The Final Binding session; results in `docs/reports/FINAL-BINDING-AUDIT-V1.md` |

---

## AUTHORITATIVE RELEASE IDENTITY

- Product: PreflightQC
- Version: 1.0.0
- Publisher: ITISYOU
- Platform: Windows x64
- Price: £19.99 GBP one-time
- Subscription: none
- Automatic renewal: none
- Signing: Policy U — intentionally unsigned
- Mandatory new upfront spend: £0
- G-12: COMPLETE for PreflightQC 1.0.0 only
- Domain: itisyou.app

## APPROVED BRAND ASSET

`assets/logo/logo.png` — Product Owner approved. Do NOT redesign or stylistically
reinterpret it.

## 1. BRAND

Inspect and preserve the original logo. Generate production derivatives required by the
existing Windows/PySide6 packaging architecture, including a proper multi-size Windows
`.ico` where required. Use high-quality deterministic resizing.

Bind the approved branding consistently to: application/window icon; packaged
executable metadata/icon configuration; installer branding/icon where supported;
About/customer-facing application surfaces where appropriate.

Do not introduce unnecessary splash screens or redesign the UI. Document provenance:
the supplied logo is Product Owner-provided/approved project artwork.

## 2. COMMERCIAL DETAILS

Lock everywhere applicable: **£19.99 GBP one-time. No subscription. No automatic
renewal.**

Refund policy: request within 7 calendar days; eligible refunds normally receive the
full purchase price; processed through the Merchant of Record/platform; statutory
rights/platform requirements take precedence; no 15% deduction; no prorated/day-based
refund.

## 3. CUSTOMER/PUBLICATION MATERIAL

Finalize publication-ready content/specification for:
`itisyou.app/products/preflightqc` (+ `/support`, `/refunds`, `/legal`, `/source`).
Do NOT publish/upload.

Pre-purchase material must clearly state: Windows x64; £19.99 one-time; offline; no
login/account; no telemetry/analytics; refund policy; intentionally unsigned; possible
Windows SmartScreen/Unknown Publisher warning; checksum availability; system
requirements/support.

## 4. MARKETPLACE

Finalize consistent Lemon Squeezy and Gumroad listing material. Do NOT create
products, upload files or publish listings.

## 5. LEGAL/LICENSING BINDING

Verify consistency of: EULA; third-party notices; dependency manifest; FFmpeg
corresponding source; Microsoft runtime notice; Policy U; completed G-12 acceptance.
Do not alter licence obligations to obtain a pass. Do not claim attorney review/legal
clearance. Handle any EULA draft-banner action only if this plan explicitly authorizes
it before build; otherwise document it as the first FINAL BUILD action. *(This plan
does not authorize it: the banner removal is the first FINAL BUILD action.)*

## 6. RELEASE PREPARATION

Prepare exact: final filenames; package layout; installer identity; manifest
structure; RELEASE-HASHES structure; source-bundle relationship; post-build
verification commands. Do NOT create the final customer build.

## 7. VALIDATION

Run all relevant: logo/icon validation; identity/version guards; commercial-copy
guards; Policy U guards; G-12 guards; licensing gates; packaging tests; UI tests; full
regression; mypy; ruff; repository consistency scans. Do not weaken tests.

Produce `docs/reports/FINAL-BINDING-AUDIT-V1.md`.

## PROHIBITIONS

Do not: build final EXE/installer; sign; upload; publish; push; change dependencies;
change release identity; issue FINAL BUILD APPROVED.
