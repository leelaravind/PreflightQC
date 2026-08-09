# PREFLIGHTQC — RELEASE IDENTITY FREEZE (V1)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Decision | Product Owner: freeze the V1 commercial release identity |
| **Canonical identity** | **PreflightQC 1.0.0 · Publisher ITISYOU · Windows x64 · Policy U — intentionally unsigned · commercial desktop software · £0 new mandatory spend** |
| **Status** | **RELEASE IDENTITY 1.0.0 FROZEN — G-12 OWNER ACCEPTANCE REQUIRED** |
| Not done, by instruction | No build, no signing, no publishing, no push, no commit, no G-12 execution, no `FINAL BUILD APPROVED` |

---

## 1. AUTHORITATIVE VERSION SOURCE

`src/preflightqc/__init__.py` → `__version__ = "1.0.0"` — the **single** authoritative
source, now annotated as such in the file. Everything derives from it:

| Surface | How it derives |
| --- | --- |
| Python package metadata | `pyproject.toml` `dynamic` → `{ attr = "preflightqc.__version__" }` (already so; verified) |
| Window title, About dialog, CLI banner, `QApplication` version | Import `__version__` (already so; verified) |
| Exported reports (HTML/CSV) | `product_version=__version__` at the call sites (already so; verified) |
| Installer (`AppVersion`, filename, **`VersionInfoVersion`**) | `build.py` passes `__version__` → `/DMyAppVersion`; `VersionInfoVersion` now `{#MyAppVersion}` instead of a drifting hardcoded `0.1.0` |
| Dependency manifest / notices | `generate_manifest.py` default now imports `__version__` instead of hardcoding `"0.1.0-dev"` |

## 2. SURFACES UPDATED IN THIS FREEZE

| File | Change |
| --- | --- |
| `src/preflightqc/__init__.py` | `0.1.0-dev` → **`1.0.0`**, with the authority comment |
| `packaging/installer.iss` | `VersionInfoVersion={#MyAppVersion}`; standalone fallback `0.0.0` (numeric, visibly non-release); **publisher corrected `PreflightQC` → `ITISYOU`** — an identity defect found during the audit |
| `packaging/generate_manifest.py` | `--product-version` default derives from the package |
| `docs/marketing/MARKETPLACE-LISTING-V1.md` | Header version row → 1.0.0 frozen; D-6 → RESOLVED; readiness "Version number" → Ready |
| `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md` | §8 acceptance now **release-specific**: pre-filled *"PreflightQC 1.0.0 (Windows x64, Policy U unsigned)"*; visibly **OPEN / OWNER ACCEPTANCE REQUIRED**; date/signature deliberately blank; identity change voids any prior acceptance |
| `docs/planning/RELEASE-VALIDATION-V1.md` | Package-under-test rows annotated: release run must use a 1.0.0 build / `PreflightQC-1.0.0-setup.exe` |
| `CHANGELOG.md` (new) | Records 1.0.0 (frozen, **NOT YET RELEASED**) and the 0.1.0-dev development identity honestly |
| `docs/design/screens/after/` | Primary review set re-captured with the frozen identity — only the version-bearing artefacts changed (`12-export-report.html` now prints `1.0.0`; `13-about.png`); all other renders byte-identical |
| `tests/packaging/test_release_identity.py` (new) | 13 guard tests — §5 |

## 3. HISTORICAL REFERENCES DELIBERATELY RETAINED (classified, not rewritten)

| Occurrence | Classification |
| --- | --- |
| `RELEASE-AUDIT-V1.md`, `IMPLEMENTATION-COMPLETION-V1.md`, `FINAL-PREBUILD-AUDIT-V1.md` (`0.1.0-dev` rows) | Dated audit records of the pre-freeze verification build |
| `IMPLEMENTATION-PLAN-V1.md` §97 ("CHANGELOG seeded at 0.1.0-dev") | Historical plan text; the CHANGELOG now exists and records both identities |
| `docs/design/screens/before/`, `scale-*/` sets | Pre-refinement and DPI-verification captures — comparative evidence |
| `tests/reporting/*`, `tests/integration/*` (`product_version="0.1.0-dev"`) | Test **fixture inputs** proving version round-trip through reports — arbitrary data, not product identity; unweakened |
| `dist/PreflightQC` verification build | Built as 0.1.0-dev, untracked, superseded — the 1.0.0 build regenerates everything from the frozen source |
| `Temp/` phase instructions | Historical inputs |

Repository-wide sweeps for development-build wording and for affirmative
review/clearance claims are clean: the only hits are the guard tests' own detector
lists and honest negations (enforced continuously by `test_g12_amendment.py`).

## 4. POLICY U AND G-12 STATUS

| Item | Status |
| --- | --- |
| Policy U | **Selected £0 V1 posture**, stated consistently: listing disclosure ("not digitally signed"), limitations, D-5, ADR §8 identity line, CHANGELOG. `sign.py verify` default (signed expectation) untouched and still fails on unsigned artefacts — **G-11 remains OPEN under the signed path** |
| G-12 | **OPEN / OWNER ACCEPTANCE REQUIRED** — the §8 statement now names PreflightQC 1.0.0 but carries no date and no signature. Nothing was executed on the owner's behalf. All **L-1…L-14** and **R-1…R-9** residual risks preserved verbatim. No attorney review, no legal clearance, no legal advice is claimed; the risk is not claimed to be zero |

## 5. TESTS AND CHECKS

| Check | Result |
| --- | --- |
| New identity guards (`test_release_identity.py`, 13 tests) | Authoritative version is 1.0.0 with no `-dev`; pyproject derives, never repeats; installer derives `VersionInfoVersion`, fallback non-release, publisher ITISYOU; no release script hardcodes a dev version; listing carries 1.0.0 and Policy U wording; CHANGELOG honest; ADR names the frozen release, stays unsigned/OPEN, and voids acceptance on identity change |
| Packaging + UI/copy suites | **All pass** (includes licensing guards, claim scans, Policy U guards, G-12 amendment guards) |
| Full regression | **1,322 passed, 3 skipped, 0 failed** |
| mypy | Clean, 55 files |
| ruff | Clean |
| Nothing weakened | No existing test modified except none; all changes additive |

## 6. REMAINING BLOCKERS BEFORE RELEASE — ALL HUMAN

1. **G-12 owner acceptance** for PreflightQC 1.0.0 (ADR §8) — deliberately not executed here.
2. Build the 1.0.0 package + installer and re-run all gates against it (needs `FINAL BUILD APPROVED`).
3. Policy U conditions U-1…U-6 at release time (hashes published, disclosure live, A2-U/A8-U run).
4. Corresponding-source page live (H-1…H-3).
5. Clean-machine validation (Phase 13) against the 1.0.0 build.
6. Marketplace business items: support pages, refund policy, price (D-2, D-7).

## 7. `git status --short`

```
 M docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md
 M docs/design/screens/after/12-export-report.html
 M docs/design/screens/after/13-about.png
 M docs/marketing/MARKETPLACE-LISTING-V1.md
 M docs/planning/RELEASE-VALIDATION-V1.md
 M packaging/generate_manifest.py
 M packaging/installer.iss
 M src/preflightqc/__init__.py
?? CHANGELOG.md
?? docs/reports/RELEASE-IDENTITY-FREEZE-V1.md
?? tests/packaging/test_release_identity.py
```

Uncommitted, per instruction. Nothing built, signed, published, or pushed.

---

## RELEASE IDENTITY 1.0.0 FROZEN — G-12 OWNER ACCEPTANCE REQUIRED
