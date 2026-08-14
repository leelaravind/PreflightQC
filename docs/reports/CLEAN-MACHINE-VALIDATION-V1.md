# PREFLIGHTQC — PHASE 13 CLEAN-MACHINE VALIDATION (V1)

Three clean-machine validation runs have been performed. The first two failed on first
launch and those candidates are **WITHDRAWN**; the third run **PASSED on Windows 11 x64
and Windows 10 x64** and closes Phase 13. Each run, root cause and fix is recorded
below in full; nothing is erased.

| Run | Date | Candidate SHA-256 | Result |
| --- | --- | --- | --- |
| 1 | 2026-08-12 | `d9e6f9078906ec4ff5c84df69bd8c57d9d0fad64f57a45f9a4d2fdad7aadf05f` | **FAIL — WITHDRAWN** (missing stdlib module `urllib.request`) |
| 2 | 2026-08-14 | `0563117bf0d53f2108c11d17cf1e5197037703f0c6ba94061a4d9869d1d43386` | **FAIL — WITHDRAWN** (missing package data `preset.schema.json`) |
| 3 | 2026-08-14 | `5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504` | **PASS — Windows 11 observed by Product Owner; Windows 10 PRODUCT OWNER ATTESTED** |

Environment for the failed runs (and the Windows 11 pass): fresh Windows 11 x64
VirtualBox VM restored from `CLEAN-WIN11-BASELINE-BEFORE-PREFLIGHTQC` — no Python,
FFmpeg, MediaInfo, Git, VS Code, Claude Code or PreflightQC dev environment.

---

## RUN 1 — 2026-08-12 — candidate `d9e6f907…aadf05f`

### 1.1 What passed before the failure

The run-book was followed in order and these steps behaved exactly as specified:

- Installer SHA-256 verified against `RELEASE-HASHES.txt` before installation — match.
- SmartScreen showed **Unknown Publisher**, the disclosed Policy U behaviour (A2-U).
- The per-user installer completed without elevation.
- The EULA and third-party notices displayed correctly during installation.

### 1.2 The failure

First application launch failed before any window appeared:

```
Unhandled exception in script.
Failed to execute script 'app' due to unhandled exception:
No module named 'urllib.request'
```

Traceback path: `preflightqc/ui/app.py` → `preflightqc/ui/main_window.py` →
`preflightqc/profiles/compiler.py` → `preflightqc/rules/loader.py` → `jsonschema` →
missing `urllib.request`.

### 1.3 Root cause

The PyInstaller spec deliberately excluded `urllib.request`, `http`, `email`, `socket`
and `_socket` to make the no-network claim structural ("no socket implementation at
all"). But `jsonschema` 4.23.0 — which validates every preset document — executes
`from urllib.request import urlopen` at module scope (`jsonschema/validators.py`,
line 12). The import is unconditional even though PreflightQC never resolves a remote
`$ref`. The frozen application therefore could not import its own launch path.

**Why every gate passed anyway:** the only gate that ran the frozen executable was
`--self-check`, which imported the inspector/platform layer but not the GUI launch
closure — so the one import chain a customer exercises first was the one no gate
exercised.

### 1.4 The fix (applied same day)

1. **Exclusion policy moved to one importable module**, `packaging/frozen_excludes.py`,
   consumed by the spec and by tests. The minimum stdlib closure jsonschema forces —
   `urllib.request` → `http.client`/`email` and `socket` → `_socket`/`selectors` — now
   ships. `ssl`/`_ssl` remain excluded (both `urllib.request` and `http.client` degrade
   cleanly without them), so **no TLS stack ships**; `Qt6Network`, `libcurl`,
   `ftplib`, `smtplib`, `socketserver` and `xmlrpc` remain excluded. Full derivation
   and safety argument in that file's docstring.
2. **`--self-check` now imports the exact launch closure** (`main_window` →
   `profiles.compiler` → `rules.loader` → `jsonschema`) and reports
   `import closure : OK (…)`; any failure makes it exit non-zero, which fails the
   build gate on the build machine.
3. **Regression tests** (`tests/packaging/test_frozen_import_closure.py`): a fresh
   interpreter with every excluded module blocked imports the full launch closure and
   runs a real schema validation; built-package tests assert `_socket.pyd` shipped, no
   `_ssl`/`libssl` shipped, and the frozen self-check reports the closure OK. Run
   against the withdrawn candidate's package, the new tests **fail** — confirming they
   detect this defect.
4. The customer-facing claim was corrected from "no socket implementation" to the
   honest form — no network transport, no TLS stack, no networking code — in the
   marketplace listing, legal page, legal review pack (F-8), G-13 posture document and
   the A9 run-book entry. AC-12 (full cycle with outbound blocked) is unaffected.

---

## RUN 2 — 2026-08-14 — candidate `0563117b…d1d43386` (the run-1 rebuild)

### 2.1 What passed before the failure

- Installer SHA-256 verified against `RELEASE-HASHES.txt` before installation — match.
- SmartScreen displayed the expected Policy U **Unknown Publisher** warning (A2-U).
- The per-user installation succeeded without elevation.
- The EULA and third-party notices displayed correctly.
- The run-1 defect is confirmed fixed: no `urllib.request` crash.

### 2.2 The failure

First application launch again failed before any window appeared:

```
Unhandled exception in script.
Failed to execute script 'app' due to unhandled exception:
[Errno 2] No such file or directory:
C:\Users\test\AppData\Local\Programs\PreflightQC\_internal\...
```

Traceback path: `preflightqc/ui/app.py` → `preflightqc/ui/main_window.py`
(`_load_presets`) → `preflightqc/rules/loader.py` (`load_catalog` →
`load_preset_file` → `build_preset` → `_validator` → `_schema`).

The dialog truncated the path; the missing file was identified by inspecting the built
package, not guessed: `_internal\preflightqc\rules\schema\preset.schema.json` is absent
from the withdrawn candidate's package (its `_internal\preflightqc\` contains only
`ui\assets\preflightqc.png`).

### 2.3 Root cause

`rules/loader.py` reads the preset schema relative to its own module file
(`SCHEMA_PATH = Path(__file__).parent / "schema" / "preset.schema.json"`). In a one-dir
freeze that resolves under `_internal/preflightqc/rules/schema/`, and files land there
only if declared in the spec's `datas` — which declared **only the icon PNG**. The
schema is data, not a module, so neither the hidden-imports mechanism nor the run-1
import-closure fix could ship it. The same defect existed, latent, for the HTML report
template (`reporting/templates/report.html.j2`, read relative to `__file__` by
`html_renderer.py`): startup would now have succeeded and the first report export would
have crashed identically.

**Why every gate passed anyway:** the run-1 fix made the self-check *import* the launch
closure, but importing a module proves nothing about the files it reads lazily. No gate
performed the launch's *data reads* against the frozen package. On the dev machine the
source tree masks nothing — the file is genuinely absent from `dist/` there too — but
the packaged self-check never triggered the read (`_schema()` is called on the first
preset load, which `--self-check` did not perform).

### 2.4 The fix (applied same day)

1. **Package-data manifest moved to one importable module**,
   `packaging/frozen_datas.py` — the exact pattern that fixed run 1, applied to data:
   one list of every non-Python file the runtime reads relative to `__file__`
   (`rules/schema/preset.schema.json`, `reporting/templates/report.html.j2`,
   `ui/assets/preflightqc.png`), consumed by the spec's `datas` AND by tests. The
   root-staged payload (`presets/`, `licenses/`, `bin/`) is deliberately not in it —
   that is staged beside the executable by `build.py` per ADR-001 §5 and verified by
   `layout_check.py`, unchanged.
2. **`--self-check` now performs the launch's data reads**, not merely its imports: it
   loads the shipped preset catalogue through the real loader (schema + validator,
   reporting `preset catalogue : OK (12 presets, schema validated)`) and loads the HTML
   report template through the real renderer (`report template : OK`). Any missing
   resource, rejected shipped preset or empty catalogue exits non-zero. The build gate
   (`verify_frozen_self_check`) additionally requires the three affirmative lines
   (`import closure`, `preset catalogue`, `report template`) verbatim in the output, so
   a silently weakened self-check also fails the build.
3. **Regression tests** (`tests/packaging/test_frozen_data_resources.py`):
   - every non-Python file under `src/preflightqc` must be declared in the manifest
     (adding a resource without shipping it fails the suite the same day);
   - every runtime resource path the code actually uses (`loader.SCHEMA_PATH`, the
     renderer's template path, the icon path) must resolve to a declared entry;
   - a **frozen-shaped layout** — the declared data files and nothing else — is built
     in a temp directory and the real startup chain (`load_catalog` → `build_preset` →
     `_validator` → `_schema`) is run inside it over the real shipped presets, in a
     fresh interpreter; deleting the schema from that layout reproduces the crash,
     proving the test is not theatre;
   - built-package tests assert every declared file shipped under `_internal/`, the
     shipped schema is byte-equivalent to the reviewed one, and the packaged
     self-check reports the data reads OK.
   Run against the withdrawn `0563117b…` package, the built-package tests **fail**
   (schema and template absent, no data-read lines in the self-check output) —
   confirming they detect exactly this defect. Against the rebuilt package they pass.
4. No licensing gate, offline/no-telemetry property or test was touched. The fix ships
   two additional first-party data files inside `_internal/`; no third-party component,
   no network capability, no new dependency.

---

## RUN 3 — 2026-08-14 — candidate `5d71cec8…13517504` (the run-2 rebuild) — **PASS**

### 3.1 Candidate identity

| Field | Value |
| --- | --- |
| Installer | `PreflightQC-1.0.0-setup.exe`, 72,810,462 bytes |
| Installer SHA-256 | `5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504` |
| `PreflightQC.exe` SHA-256 | `deaed7c7bafddac802c6afbd86a5bf1220e25303dceb43de047c6855aac7aa9d` |
| Build state | Source commit `4ddfa98` plus the two Phase 13 packaging fixes; built 2026-08-14 with `packaging/build.py --clean`, all 12 gates PASS |
| `RELEASE-HASHES.txt` | This candidate is the sole current entry; both withdrawn hashes are named as never-publish |

### 3.2 Evidence classification — stated plainly, per the run-book's own rule

The run-book forbids marking any step PASS by anyone who did not run it. The clean
machine sessions were run by the **Product Owner**; the results below are the Product
Owner's reported observations (Windows 11) and the Product Owner's attestation of an
equivalent session (Windows 10), recorded 2026-08-14. **No screenshots or machine logs
from these sessions are stored in the repository** — evidence artefacts remain with
the Product Owner. Nothing below is invented or inferred by anyone who was not present.

### 3.3 Windows 11 x64 — observed by the Product Owner

Same clean VM baseline as runs 1 and 2. The full customer workflow, end to end:

- Installer transferred by a customer-like download route; SHA-256 verified against
  `RELEASE-HASHES.txt` **before** execution — match (A2-U step 4, Policy U condition U-3).
- SmartScreen showed the disclosed Policy U behaviour: **Unknown Publisher** warning
  with **More info → Run anyway** available and working (A2-U).
- Per-user installation succeeded without elevation (A1).
- EULA and third-party notices displayed during installation.
- **Application launched successfully** — the step both withdrawn candidates failed (A3).
- Presets/rules loaded (the run-2 defect confirmed fixed).
- A real MP4 was added; real media inspection completed; PASS/WARN/FAIL/UNKNOWN
  findings rendered (A6/A7 workflow, observed against real media).
- HTML report exported and opened; CSV exported (the run-2 latent template defect
  confirmed fixed in the export path a customer actually uses).
- Application closed and reopened successfully.
- Uninstall succeeded; the installed program directory was removed; user-generated
  reports intentionally remained in Local AppData; no unexpected roaming AppData
  residue (A12 — user data preserved, program removed).

### 3.4 Windows 10 x64 — PRODUCT OWNER ATTESTED

The Product Owner confirms an **equivalent clean-machine validation was completed on
Windows 10 x64** (P13-A14 requires both OS generations). This is recorded as an
owner attestation: no per-step observation list and no captured artefacts were
provided for the Windows 10 session, and this document does not pretend otherwise.

### 3.5 Mechanically pre-verified rows (AUTO), re-confirmed against this exact package

Independent of the clean-machine sessions, the rows the run-book marks **AUTO** were
re-proven on 2026-08-14 against the exact validated package by the automated suite:
A4 (packaged self-check reports both inspector versions, the launch import closure,
the preset catalogue and the report template), A5 (PATH-decoy ffprobe never used) and
A9's structural half (no network transport, TLS stack or networking code ships).

### 3.6 Phase 13 closure

**PHASE 13 PASS — declared by the Product Owner** on the basis of the sessions above:
Windows 11 observed, Windows 10 PRODUCT OWNER ATTESTED, evidence classification as in
§3.2. GATE-6 also requires G-12, which is complete and scoped to exactly 1.0.0 (see
the shipped `DEPENDENCY-MANIFEST.json` gate record).

---

## 4. DISPOSITION

| Artefact | Status |
| --- | --- |
| `PreflightQC-1.0.0-setup.exe` `d9e6f9078906ec4ff5c84df69bd8c57d9d0fad64f57a45f9a4d2fdad7aadf05f` | **WITHDRAWN — must never be published or uploaded** |
| `PreflightQC-1.0.0-setup.exe` `0563117bf0d53f2108c11d17cf1e5197037703f0c6ba94061a4d9869d1d43386` | **WITHDRAWN — must never be published or uploaded** |
| Their `RELEASE-HASHES.txt` entries | Superseded; the regenerated file names both withdrawn hashes |
| `PreflightQC-1.0.0-setup.exe` `5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504` | **VALIDATED — Phase 13 PASS (run 3). This exact artefact must be the one published; any rebuild voids this validation and restarts Phase 13** |

**Phase 13 status: CLOSED — PASS on the third candidate, with both failures recorded
above. The validated installer must be published byte-for-byte as tested; publication
steps remain (see `FINAL-BUILD-AUDIT-V1.md` §8).**
