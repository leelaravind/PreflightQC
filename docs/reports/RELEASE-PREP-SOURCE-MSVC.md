# PREFLIGHTQC — RELEASE PREPARATION: CORRESPONDING SOURCE + MICROSOFT VC RUNTIME

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Covers | Release-preparation items #1 (FFmpeg corresponding-source hosting) and #2 (Microsoft VC runtime licence/notice) |
| Spend | **£0** — existing domain, static files, no purchases |
| Built / signed / published / uploaded / committed | **None of these.** |
| Tests | **1,279 passed, 3 skipped, 0 failed** (was 1,266 — 13 new MS-runtime tests) · mypy clean · ruff clean |
| **Status** | **RELEASE PREP #1+#2 COMPLETE** |

---

## 1. ITEM A — CORRESPONDING SOURCE: **SOURCE HOSTING READY**

Full detail: `docs/reports/CORRESPONDING-SOURCE-READINESS.md`; normative file list:
`docs/licensing/CORRESPONDING-SOURCE-PLAN.md` §5A.

### 1.1 The exact bundle prepared

`packaging/source-release/` — seven files, staged, nothing uploaded:

| File | SHA-256 |
| --- | --- |
| `ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz` (17,014,473 B) | `39002bfe54d48326b69c36a0b72231125bb5b408fadc29e14481b5ac2583a224` |
| `ffmpeg-builds-recipe-2437e7b868da.tar.gz` (103,117 B) | `b23920469c23615c539b4965c0bd18b3758c8dc9416b6bef343a83fcf4f310c7` |
| `README.txt` | source↔binary explanation, verification chain, three-year offer |
| `SHA256SUMS` | covers the other five files |
| `COPYING.LGPLv3.txt` | `ea7d049c…363432c9` |
| `COPYING.GPLv3.txt` | `0b383d5a…ac1171e6b` |
| `ffmpeg-build-configuration.txt` | `ffd89a45…481866e45` |

The two archives are byte-identical copies of the G-5/G-6 artefacts; upstream source was
not altered. They stay out of Git per existing repo policy
(`packaging/source-release/.gitignore`), and are reproducible byte-for-byte via
`tools/fetch_corresponding_source.py`.

### 1.2 Source/binary match evidence — re-verified today, not inherited

- `packaging/verify_source.py`: **PASS**, exit 0 — re-derives release tag, commit,
  commits-ahead, and all seven library version triplets from the artefacts themselves.
- Both archive hashes re-computed and equal to `binaries.lock.json`
  (`corresponding_source.archive_sha256`, `build_recipe_source.archive_sha256`).
- Binary self-reports `n8.1.2-34-g9b6c8969e0-20260809`; archive `RELEASE` reads `8.1.2`;
  libavutil 60.26.102 through libswresample 6.3.102 all match.
- Known caveat, unchanged and documented (plan §3.3): the *recipe* commit is a
  CI-run attribution, not a publisher declaration.

### 1.3 Intended public URL

```
https://itisyou.app/products/preflightqc/source
```

Already named in `binaries.lock.json` (`hosting_url`) and shown in the product's About
dialog. `hosting_status` remains **`NOT LIVE`** — correctly, because nothing is served yet.

### 1.4 Files still needing public upload (human action H-1)

All seven files in §1.1, byte-for-byte, then: re-hash the hosted copies over HTTPS
against `SHA256SUMS`, flip `hosting_status`, re-run the audit (H-2), and stand behind the
three-year offer (H-3).

---

## 2. ITEM B — MICROSOFT VC RUNTIME: NOTICE RESOLVED

### 2.1 Microsoft runtime files found (verification build `dist/PreflightQC`, 268 files)

**50 files, three locations, two provenances:**

| Location | Files | Arrived via |
| --- | --- | --- |
| `_internal/` | `VCRUNTIME140.dll` (`052ad6a2…`), `VCRUNTIME140_1.dll` (`6a99bc01…`), `ucrtbase.dll` (`c04daeba…`), 39 × `api-ms-win-*.dll` forwarders | python.org CPython 3.12 Windows build |
| `_internal/PySide6/` | `MSVCP140.dll` (`fd5be125…`), `MSVCP140_1.dll` (`a3334166…`), `MSVCP140_2.dll` (`e14d0194…`), `VCRUNTIME140.dll` (`f85a40b7…`), `VCRUNTIME140_1.dll` (`38b1fcd6…`) | PySide6 6.8.1.1 wheel |
| `_internal/shiboken6/` | `MSVCP140.dll` (`117509b2…`), `VCRUNTIME140.dll` (`c14afac1…`), `VCRUNTIME140_1.dll` (`cefef11e…`) | shiboken6 6.8.1.1 wheel |

No `MSVCR*`, `CONCRT*`, `VCOMP*`, `MFC*`, `VCAMP*` or `VCCORLIB*` file is shipped, and
the product does not require the standalone VC++ Redistributable installer. A test now
enforces this exact inventory.

### 2.2 Notice/licence status

**Resolved from authoritative material already present locally — nothing invented,
nothing fetched.** The runtime files arrive with the python.org CPython distribution,
whose own `LICENSE.txt` (shipped verbatim as `licenses/CPython-LICENSE.txt`) contains
the **"Additional Conditions for this Windows binary build"** section stating the
redistribution conditions for the Microsoft Distributable Code. That section is the
authoritative statement accompanying the distribution that supplied the DLLs.

`third-party/licenses/MS-VC-Redistributable.txt` is no longer a placeholder. It now:

- identifies all 50 files and both provenances;
- quotes the redistribution conditions **verbatim** from the CPython licence (a test
  fails if the quotes drift from the cited text);
- records how PreflightQC observes each condition;
- states plainly that the copies arriving via the Qt wheels carry no Microsoft-specific
  licence text in the wheels, and that the same protective conditions are applied to them;
- claims **no legal clearance** — confirming the EULA's pass-through wording (and the
  Qt-wheel treatment) is folded into **G-12**, which remains OPEN. The EULA's attorney
  checklist item 6 ("whether the Microsoft VC++ runtime redistribution terms are
  satisfied as shipped") is unchanged and still correct.

The standalone "Microsoft Software License Terms — Visual C++ Redistributable" document
is **deliberately not reproduced**: no authoritative copy exists locally and retyping it
from memory would be inventing terms. It is referenced by pointer only. If the attorney
wants that document in the package, obtaining it is a G-12 action.

The manifest gate now reports honestly resolved:
`G-2_licence_texts_present: PASS` (previously `PASS WITH OPEN ACTION`); the placeholder
detection stays in `generate_manifest.py`, and `collect_licences.py` will regenerate a
fail-visible placeholder if the authored notice ever goes missing.

### 2.3 Manifest / notices / package agreement

- `generate_manifest.py` MSVC component notice rewritten to state the true basis;
  regenerated `DEPENDENCY-MANIFEST.json` and `THIRD-PARTY-NOTICES.txt` in the
  verification build (static check only — no build performed). All gates:
  G-1 PASS, G-2 PASS, G-5 PASS, G-12 NOT COMPLETE (human).
- The authored notice was copied into `dist/PreflightQC/licenses/` so the verification
  artefact agrees with the repository; a test asserts byte equality.

---

## 3. TESTS

| Suite | Result |
| --- | --- |
| New `tests/packaging/test_ms_runtime.py` | **13 tests**: notice is genuine and complete; quoted conditions match the CPython licence verbatim; citation is not dangling; fallback stays fail-visible; manifest patterns claim every runtime path; package inventory is exactly the declared 50 files; forbidden runtime families absent; manifest and package reconcile; packaged notice equals the repo notice; licence gate reports clean PASS |
| Packaging suite | 91 passed |
| **Full regression** | **1,279 passed, 3 skipped, 0 failed** (exit 0) |
| mypy | Success, 55 files |
| ruff | All checks passed |

No existing test was weakened; the placeholder-detection mechanism was kept, not removed.

---

## 4. FILES CHANGED (this session)

| File | Change |
| --- | --- |
| `packaging/source-release/` (new) | Staged hosting bundle: 2 archives, README.txt, SHA256SUMS, 2 licence texts, configure line, .gitignore |
| `docs/licensing/CORRESPONDING-SOURCE-PLAN.md` | New §5A: exact hosted file list + three-layer integrity verification; header and H-1 updated |
| `docs/reports/CORRESPONDING-SOURCE-READINESS.md` (new) | Status report: **SOURCE HOSTING READY** |
| `third-party/licenses/MS-VC-Redistributable.txt` | Placeholder → genuine Microsoft Distributable Code notice |
| `packaging/generate_manifest.py` | MSVC component notice text corrected to the true basis |
| `tools/collect_licences.py` | Docstring + fallback updated; fallback remains fail-visible |
| `tests/packaging/test_ms_runtime.py` (new) | 13 tests, §3 above |
| `dist/PreflightQC/licenses/` | Notice copied in; manifest + notices regenerated (verification artefact, not tracked) |
| `docs/reports/FINAL-PREBUILD-AUDIT-V1.md` | Open-gates header and §10 MS-runtime row updated to the resolved state |
| `docs/reports/RELEASE-PREP-SOURCE-MSVC.md` (new) | This report |

`docs/reports/RELEASE-AUDIT-V1.md` (H-5) is left as written: it is a dated audit record
of the state at audit time, and rewriting history would make the trail less trustworthy.

## 5. REMAINING BLOCKERS — ALL HUMAN, NONE ENGINEERING

| Blocker | Gate |
| --- | --- |
| Upload the staged bundle; flip `hosting_status`; three-year commitment | H-1, H-2, H-3 |
| Attorney review, incl. EULA MS pass-through wording and Qt-wheel treatment | **G-12 OPEN** |
| Code-signing certificate | **G-11 OPEN** |
| Clean-machine validation | Phase 13 |

## 6. `git status --short`

```
 M README.md
 M docs/FUTURE.md
 M docs/licensing/CORRESPONDING-SOURCE-PLAN.md
 M packaging/binaries.lock.json
 M packaging/generate_manifest.py
 M src/preflightqc/__init__.py
 M src/preflightqc/reporting/claims.py
 M src/preflightqc/ui/about.py
 M src/preflightqc/ui/app.py
 M src/preflightqc/ui/main_window.py
 M src/preflightqc/ui/severity_style.py
 M src/preflightqc/ui/viewmodels.py
 M tests/packaging/test_corresponding_source.py
 M tests/reporting/test_reporting.py
 M third-party/licenses/MS-VC-Redistributable.txt
 M tools/collect_licences.py
?? Temp/
?? docs/design/
?? docs/licensing/CODE-SIGNING-READINESS.md
?? docs/marketing/
?? docs/reports/CORRESPONDING-SOURCE-READINESS.md
?? docs/reports/FINAL-PREBUILD-AUDIT-V1.md
?? packaging/source-release/
?? src/preflightqc/ui/design.py
?? src/preflightqc/ui/theme.py
?? src/preflightqc/ui/widgets.py
?? tests/packaging/test_ms_runtime.py
?? tests/ui/
?? tools/capture_screens.py
```

Nothing committed or pushed, per the standing constraint.

---

## RELEASE PREP #1+#2 COMPLETE

Not proceeded to: code signing, legal review, clean-machine validation, final build, or
publication. Those remain human-gated.
