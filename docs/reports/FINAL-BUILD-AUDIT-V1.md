# PREFLIGHTQC — FINAL BUILD AUDIT (V1)

| Field | Value |
| --- | --- |
| Date | 2026-08-10 (first candidate) · 2026-08-12 (second) · **2026-08-14 (third — rebuild after the second Phase 13 failure; this is the current state)** |
| Authorization | **FINAL BUILD APPROVED** — explicit Product Owner instruction, executing `docs/planning/RELEASE-OUTPUTS-V1.md` §4; rebuilds executed under the Phase 13 defect-fix instructions |
| Source commit | `4ddfa98f8d24f20a5f874f86ee8e17f061f6565f` plus the two Phase 13 packaging fixes (uncommitted at rebuild time; see §9) |
| Final version | **PreflightQC 1.0.0** · Publisher ITISYOU · Windows x64 · £19.99 GBP one-time · **Policy U — intentionally unsigned** |
| **Status** | **PHASE 13 VALIDATED — Windows 11 (Product Owner observed) + Windows 10 (PRODUCT OWNER ATTESTED), 2026-08-14. Engineering complete; publication steps remain (§8)** |
| Never claimed | The installer is **not** digitally signed. No legal clearance. Windows 10 evidence is a Product Owner attestation, not repository-captured machine evidence (see `CLEAN-MACHINE-VALIDATION-V1.md` §3.2). |

---

## 0. PHASE 13 FAILURES OF THE FIRST TWO CANDIDATES — RECORDED, NOT ERASED

**First candidate** (2026-08-10,
`d9e6f9078906ec4ff5c84df69bd8c57d9d0fad64f57a45f9a4d2fdad7aadf05f`) **failed Phase 13
on 2026-08-12**: it installed correctly on a fresh Windows 11 x64 VM and crashed on
first launch with `No module named 'urllib.request'` — the freeze had excluded a stdlib
module that `jsonschema` imports at module scope, and no gate imported the GUI launch
closure frozen. **WITHDRAWN.**

**Second candidate** (2026-08-12,
`0563117bf0d53f2108c11d17cf1e5197037703f0c6ba94061a4d9869d1d43386`) **failed Phase 13
on 2026-08-14**: the first fix held (no import crash), but first launch died with
`[Errno 2] No such file or directory: …\_internal\preflightqc\rules\schema\preset.schema.json`.
The rules loader reads the preset schema relative to `__file__`; the spec's `datas`
declared only the icon, so the schema — data, not a module — never shipped, and the
strengthened self-check *imported* the launch closure without performing its data
reads. The same latent defect covered the HTML report template. **WITHDRAWN.**

Both gates were incomplete, not wrong, and both failure modes are now closed
mechanically. Full failure records, root causes and fixes:
`docs/reports/CLEAN-MACHINE-VALIDATION-V1.md`; policy rationales:
`packaging/frozen_excludes.py` (imports) and `packaging/frozen_datas.py` (data).
Neither withdrawn hash may ever be published. Sections 1, 3 and 5 below describe the
**third** candidate. Everything not restated (EULA finalization §2, Policy U §4,
screenshots §6, limitations §7) is unchanged and was re-verified by the same tests.

---

## 1. WHAT WAS BUILT

Rebuilt 2026-08-14 with `python packaging/build.py --clean` after the second Phase 13
fix. No prior installer or hash is reused; the withdrawn values are recorded in §0.

| Artefact | Size | SHA-256 |
| --- | --- | --- |
| `dist/installer/PreflightQC-1.0.0-setup.exe` — **the rebuilt release candidate** | 72,810,462 bytes (69.4 MB) | `5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504` |
| `dist/PreflightQC/` package | 272 files, 232.3 MB (was 270 — `rules/schema/preset.schema.json` and `reporting/templates/report.html.j2` now ship under `_internal/`; see §0) | per-file hashes in the shipped `DEPENDENCY-MANIFEST.json` |
| `dist/PreflightQC/PreflightQC.exe` (branded with the approved icon) | — | `deaed7c7bafddac802c6afbd86a5bf1220e25303dceb43de047c6855aac7aa9d` |
| `dist/installer/RELEASE-HASHES.txt` | regenerated **after** the artefacts were frozen; names **both** withdrawn hashes | contains the installer hash above |

Build commands, exactly as documented:

```
python packaging/build.py --clean    # freeze → stage → gates → installer (exit 0)
python packaging/sign.py verify --expect unsigned    # exit 0
python packaging/sign.py verify                      # exit 1 (recorded)
```

## 2. EULA FINALIZATION (first action, as pre-authorized)

The draft banner was removed from `packaging/EULA.txt` exactly per
`RELEASE-OUTPUTS-V1.md` §4.1. Preserved and verified by test: the LGPL carve-outs and
open-source-precedence clause, the FFmpeg ownership disclaimer, the reverse-engineering
grant, the three-year source offer, the translation obligation, the G-12 §9 history —
and the honesty block, now inside §9 of the shipped agreement itself: *it has not been
reviewed by a qualified software-IP attorney, no legal clearance is claimed for it,
and nothing in it is legal advice.* The guard assertions moved with the text — the
planned, pre-justified change, not a weakening.

## 3. BUILD GATES — ALL TWELVE STEPS PASS

`[PASS]` inspector binaries match `binaries.lock.json` · G-5 corresponding source
matches the shipped binary · PyInstaller one-dir build · staging (presets, licences,
inspectors) · Qt pruning (no Qt6Network) · no dangling DLL imports · **G-1/G-2
manifest + notices generated from the package** · G-3/G-4/G-7 prohibited-component
scan · P11-A3 layout · preset staleness/traceability · **packaged application
self-check** · Inno Setup installer.

Shipped manifest (`licenses/DEPENDENCY-MANIFEST.json`) gate status: G-1 complete +
checksums verified, G-2 closure + licence texts, G-5, and
**G-12_owner_risk_acceptance: PASS — scoped to exactly this version (1.0.0)**. No
gate was weakened; one genuine build-blocking defect was found and fixed — the Final
Binding icon change had duplicated the installer script's pre-existing
`UninstallDisplayIcon`/empty `SetupIconFile` directives; the stale pair was removed
(configuration fix only, no scope/identity/dependency change).

The rebuilds also **strengthened** the gates in response to §0, once per failure:

*After the first failure (imports):* the packaged self-check imports the exact GUI
launch closure and reports `import closure : OK (6 modules)`;
`tests/packaging/test_frozen_import_closure.py` proves on every machine that the
spec's exclusion list cannot break the launch import closure.

*After the second failure (data):* the spec's `datas` are built from one manifest,
`packaging/frozen_datas.py`; the packaged self-check now also **performs the launch's
data reads** — it loads the shipped preset catalogue through the real loader
(`preset catalogue : OK (12 presets, schema validated)`) and loads the HTML report
template (`report template : OK`) — and the build gate requires all three affirmative
lines verbatim, so a weakened self-check also fails the build.
`tests/packaging/test_frozen_data_resources.py` fails on any machine if a package-data
file is undeclared, if a runtime resource path leaves the manifest, or if the startup
chain cannot run in a frozen-shaped layout built from the manifest alone; deleting the
schema from that layout reproduces the crash, proving the guard fires.

Run against each withdrawn candidate's package, the corresponding tests fail; against
the rebuilt package they pass — each net catches exactly the defect that escaped.

## 4. POLICY U VERIFICATION — RECORDED HONESTLY, BOTH WAYS

| Command | Result |
| --- | --- |
| `sign.py verify --expect unsigned` | **exit 0** — `PreflightQC.exe` and `PreflightQC-1.0.0-setup.exe` both present and `UNSIGNED (as declared by Policy U)` |
| `sign.py verify` (default, G-11) | **exit 1** — `G-11 NOT SATISFIED: 2 artefact(s) are unsigned` — **the correct result: G-11 remains OPEN** |

The installer is **not digitally signed**, will trigger the disclosed SmartScreen
behaviour, and no material anywhere claims otherwise.

## 5. VALIDATION

| Check | Result |
| --- | --- |
| **Full regression, run against the rebuilt release build** (`TestTheBuiltPackage`, `test_frozen_import_closure.py` and the new `test_frozen_data_resources.py` exercised the actual rebuilt 1.0.0 package, including the packaged self-check with launch-closure imports, launch data reads and PATH-decoy subprocess tests) | **1,365 tests: 1,362 passed, 3 skipped, 0 failed** |
| UI + packaging + licensing/commercial/identity/Policy U/G-12 guards | All included above, all pass |
| Policy U re-verified against the rebuilt artefacts | `sign.py verify --expect unsigned` exit 0; `sign.py verify` exit 1 (G-11 correctly remains OPEN) |
| mypy | Clean, 57 files |
| ruff | Clean |
| Release consistency | Identity guards pin 1.0.0 across every surface; commercial guards pin £19.99/refund policy; claim guards pin no-signing/no-clearance language |

## 6. FINAL SCREENSHOTS

All 14 customer/marketplace states re-captured (`docs/design/screens/after/`) from
the same frozen code the package was built from, showing 1.0.0 and the bound logo in
About. Only the two brand/version-bearing artefacts changed against the previous
capture; the UI itself was not altered for screenshots.

## 7. KNOWN LIMITATIONS (unchanged, disclosed)

Metadata-only inspection (no loudness/GOP/edit-list measurement); one preset per
batch; first stream judged; Windows x64 only; custom profiles file-based (no in-app
editor); dark theme only; unsigned installer (Policy U) with per-release SmartScreen
reputation reset; L-1…L-14 and R-1…R-9 remain owner-accepted, unresolved residual
risks.

## 8. REMAINING HUMAN / PUBLICATION ACTIONS

| # | Action | Status |
| --- | --- | --- |
| 1 | **Phase 13 clean-machine validation** on real Windows 10 x64 and Windows 11 x64 (run-book with A2-U/A8-U) | **DONE 2026-08-14 — PASS on the third candidate** (`5d71cec8…`): Windows 11 observed by the Product Owner end-to-end (install → inspect → export → uninstall), Windows 10 PRODUCT OWNER ATTESTED. Two prior runs failed on the withdrawn candidates (§0). Record: `CLEAN-MACHINE-VALIDATION-V1.md` |
| 2 | Publish the corresponding-source bundle; H-2 HTTPS hash re-check; flip `hosting_status`; three-year commitment (H-3) | Pending |
| 3 | Publish the four customer pages + refunds page; connect the support contact; fill `{{SHA256_INSTALLER}}` = `5d71cec8…13517504` (the third candidate — **not** the withdrawn `d9e6f907…aadf05f` or `0563117b…d1d43386`) | Pending |
| 4 | Create the Lemon Squeezy and Gumroad products per their checklists; upload the installer; verify the uploaded file's hash equals `RELEASE-HASHES.txt` | Pending |
| 5 | Confirm Policy U conditions U-1…U-6 at publication (U-1 already verified against these artefacts) | Partially met |
| 6 | Commit this final-build state | **DONE 2026-08-14** — "Validate PreflightQC 1.0.0 release candidate on clean Windows" (not pushed) |

## 9. `git status --short`

As of the 2026-08-14 rebuild — all of the below (plus `CHANGELOG.md` and the Phase 13
closure edits to the two reports and the run-book) were subsequently committed in the
validation checkpoint (§8 row 6), leaving the tree clean:

```
 M docs/design/screens/after/12-export-report.html
 M docs/design/screens/after/13-about.png
 M docs/licensing/EULA-DRAFT.md
 M docs/licensing/G13-QT-LICENCE-POSTURE.md
 M docs/licensing/LEGAL-REVIEW-PACK-V1.md
 M docs/marketing/MARKETPLACE-LISTING-V1.md
 M docs/marketing/pages/LEGAL-PAGE.md
 M docs/planning/PREFLIGHTQC-V1-FINAL-BINDING-IMPLEMENTATION-PLAN.md
 M docs/planning/RELEASE-VALIDATION-V1.md
 M packaging/EULA.txt
 M packaging/build.py
 M packaging/installer.iss
 M packaging/preflightqc.spec
 M src/preflightqc/ui/app.py
 M tests/packaging/test_final_binding.py
 M tests/packaging/test_release_artefacts.py
?? docs/reports/CLEAN-MACHINE-VALIDATION-V1.md
?? docs/reports/FINAL-BUILD-AUDIT-V1.md
?? packaging/frozen_datas.py
?? packaging/frozen_excludes.py
?? tests/packaging/test_frozen_data_resources.py
?? tests/packaging/test_frozen_import_closure.py
```

(`dist/` and `build/` are build outputs, untracked by policy). Nothing pushed,
nothing uploaded, nothing published.

---

## PHASE 13 VALIDATED — PREFLIGHTQC 1.0.0 ENGINEERING COMPLETE; PUBLICATION STEPS REMAIN (§8)
