# PREFLIGHTQC — FINAL BINDING AUDIT (V1)

| Field | Value |
| --- | --- |
| Date | 2026-08-10 |
| Plan | `docs/planning/PREFLIGHTQC-V1-FINAL-BINDING-IMPLEMENTATION-PLAN.md` — found **empty** at execution time; populated verbatim from the Product Owner's Final Binding instruction and executed |
| Identity | **PreflightQC 1.0.0 · ITISYOU · Windows x64 · £19.99 GBP one-time · Policy U intentionally unsigned · £0 new spend** |
| **Status** | **FINAL BINDING COMPLETE — READY FOR FINAL BUILD APPROVAL** |
| Not done, by instruction | No final build, no signing, no upload, no publish, no push, no dependency change, no identity change, no `FINAL BUILD APPROVED` |

---

## 1. BRANDING INTEGRATION

**Approved asset:** `assets/logo/logo.png` — Product Owner-provided and approved
artwork, pinned by SHA-256 (`54372b3e…880cfda3`) in `assets/logo/PROVENANCE.md` and in
a guard test, so a silent replacement fails the suite. **Not redesigned, not
reinterpreted:** every derivative is a pure geometric resize (Qt smooth scaling, fixed
settings, deterministic for the pinned Qt version) via `tools/generate_icons.py`.

| Derivative | Purpose | SHA-256 |
| --- | --- | --- |
| `assets/logo/preflightqc.ico` | Executable + installer icon. Proper multi-size Windows ICO: 16/24/32/48 as 32-bit BMP entries, 64/128/256 as PNG entries — structure and Qt-readability verified | `dbda9406…681f3fc2` |
| `src/preflightqc/ui/assets/preflightqc.png` | 256 px window/taskbar icon, shipped in `_internal/` | `b2074635…397fc7f75` |
| `assets/logo/logo-512.png` | Marketplace/listing artwork | `80cc324e…79a9153f` |

**Bindings:** PyInstaller spec `icon=` + `datas` entry for the shipped PNG; Inno Setup
`SetupIconFile` + `UninstallDisplayIcon`; `QApplication`/`MainWindow` window icon via
the new `preflightqc/ui/branding.py` (tolerant loader — a missing asset degrades to
unbranded, never a crash); About dialog shows the logo as a **document resource** (no
URL, offline posture intact). No splash screen, no UI redesign.

## 2. COMMERCIAL LOCK

`docs/marketing/COMMERCIAL-TERMS-V1.md` is the canonical record: **£19.99 GBP,
one-time, no subscription, no automatic renewal.** Refunds: request within **7
calendar days**; eligible refunds normally receive the **full purchase price**;
processed through the MoR/platform; statutory rights and platform rules take
precedence; **no 15% deduction, no prorated/day-based refunds** — and a guard test
forbids deduction/proration/recurring-billing language on every other marketing
surface, forbids any price other than £19.99, and requires the one-time/no-subscription
statement on every sales surface. Master listing rows D-2 (refunds) and D-7 (price) are
RESOLVED.

## 3. CUSTOMER-PAGE READINESS

Publication-ready content exists for all five URLs — **nothing published, nothing
uploaded**: `docs/marketing/pages/{PRODUCT,SUPPORT,REFUNDS,LEGAL,SOURCE}-PAGE.md`.

The product page states, before any purchase action, every required fact — Windows
x64, £19.99 one-time, offline, no login/account, no telemetry/analytics, the refund
policy, **intentionally unsigned + SmartScreen/Unknown Publisher warning**, SHA-256
checksum availability, system requirements and support — each asserted by test.
Placeholders remaining for publication time: `{{SHA256_INSTALLER}}` (exists only after
the final build), `{{SUPPORT_CONTACT}}` (must be connected to a real mailbox), and the
merchant link. The source page fronts the staged seven-file bundle byte-for-byte.

## 4. MARKETPLACE READINESS

`LEMON-SQUEEZY-LISTING-V1.md` and `GUMROAD-LISTING-V1.md` — consistent by
construction: shared copy comes from the master listing, both carry the identical
"Before you buy" disclosure block (verified by test), both specify single-payment
£19.99, licence-key features **off** (no activation exists), `logo-512.png` artwork,
and release-time checklists. No products created, no files uploaded, nothing
published.

## 5. LICENSING / EULA / POLICY U / G-12

| Item | Verified state |
| --- | --- |
| Licensing gates | Re-run this session: G-1, G-2, G-5 **PASS**; `verify_source.py` **PASS** |
| G-12 | **PASS — scoped**: owner acceptance recorded 2026-08-09 for PreflightQC 1.0.0 only; L-1…L-14 and R-1…R-9 remain unresolved and accepted; **no attorney review, no legal clearance claimed** — unchanged by this binding |
| Policy U | Selected posture, stated on every sales surface; `sign.py verify` default untouched (G-11 stays OPEN under the signed path) |
| EULA | Present with required carve-outs, verified by test. **Draft banner deliberately retained**: the binding plan does not authorize its removal, so it is documented as the **first FINAL BUILD action** in `RELEASE-OUTPUTS-V1.md` §4.1, including the planned, justified guard-assertion move |
| Notices / manifest / MS runtime / corresponding source | Consistent; nothing altered to obtain any pass |

## 6. RELEASE-OUTPUT SPECIFICATION

`docs/planning/RELEASE-OUTPUTS-V1.md`: final filenames
(`PreflightQC-1.0.0-setup.exe`), package layout, installer identity fields,
`RELEASE-HASHES.txt` format, source-bundle relationship chain, and the exact
post-authorization sequence (banner removal → build with gates → Policy U
verification both ways → full suite → hashes → screenshots → clean-machine run-book →
ordered publication steps). **The final customer build was not created.**

## 7. TESTS AND CHECKS

| Check | Result |
| --- | --- |
| New guards | `tests/packaging/test_final_binding.py` (13: pinned logo hash, ICO ladder, PNG dimensions, provenance, spec/installer wiring, price/subscription/refund/disclosure locks) + `tests/ui/test_branding.py` (3: icon loads, main window carries it, pixmap scaling) |
| Packaging + UI suites | All pass |
| **Full regression** | **1,344 passed, 3 skipped, 0 failed** (the new branding module is also swept by the parameterized forbidden-claims scan) |
| mypy | Clean (57 files — branding module added) |
| ruff | Clean |
| Consistency scans | No stale price/refund/version contradictions; forbidden-claim and identity guards all green; nothing weakened (the three failures during development were fixed in the *documents*, or were flattening artifacts fixed in the new tests themselves) |

## 8. FILES CHANGED

New: `assets/` (logo + ico + 512 + PROVENANCE), `src/preflightqc/ui/branding.py`,
`src/preflightqc/ui/assets/preflightqc.png`, `tools/generate_icons.py`,
`docs/marketing/{COMMERCIAL-TERMS-V1,LEMON-SQUEEZY-LISTING-V1,GUMROAD-LISTING-V1}.md`,
`docs/marketing/pages/` (5), `docs/planning/{PREFLIGHTQC-V1-FINAL-BINDING-IMPLEMENTATION-PLAN,RELEASE-OUTPUTS-V1}.md`,
`tests/packaging/test_final_binding.py`, `tests/ui/test_branding.py`, this audit.
Modified: `packaging/preflightqc.spec`, `packaging/installer.iss`,
`src/preflightqc/ui/{app,about,main_window}.py`, `docs/marketing/MARKETPLACE-LISTING-V1.md`.

## 9. REMAINING POST-AUTHORIZATION ACTIONS

Everything in `RELEASE-OUTPUTS-V1.md` §4, gated on the Product Owner's explicit
**`FINAL BUILD APPROVED`**: EULA banner removal, the 1.0.0 build + gates, Policy U
U-1…U-6, `RELEASE-HASHES.txt`, screenshot re-shoot, clean-machine validation, then the
ordered publication steps (source page + H-2/H-3, customer pages with support contact
connected, both marketplace products).

## 10. `git status --short`

```
 M docs/marketing/MARKETPLACE-LISTING-V1.md
 M packaging/installer.iss
 M packaging/preflightqc.spec
 M src/preflightqc/ui/about.py
 M src/preflightqc/ui/app.py
 M src/preflightqc/ui/main_window.py
?? assets/
?? docs/marketing/COMMERCIAL-TERMS-V1.md
?? docs/marketing/GUMROAD-LISTING-V1.md
?? docs/marketing/LEMON-SQUEEZY-LISTING-V1.md
?? docs/marketing/pages/
?? docs/planning/PREFLIGHTQC-V1-FINAL-BINDING-IMPLEMENTATION-PLAN.md
?? docs/planning/RELEASE-OUTPUTS-V1.md
?? docs/reports/FINAL-BINDING-AUDIT-V1.md
?? src/preflightqc/ui/assets/
?? src/preflightqc/ui/branding.py
?? tests/packaging/test_final_binding.py
?? tests/ui/test_branding.py
?? tools/generate_icons.py
```

Uncommitted; nothing built, signed, uploaded, published, or pushed.

---

## FINAL BINDING COMPLETE — READY FOR FINAL BUILD APPROVAL
