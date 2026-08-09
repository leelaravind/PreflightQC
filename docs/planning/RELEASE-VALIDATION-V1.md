# PREFLIGHTQC — CLEAN-MACHINE RELEASE VALIDATION RUN-BOOK (PHASE 13)

| Field | Value |
| --- | --- |
| Date issued | 2026-08-09 |
| Package under test | `PreflightQC 0.1.0-dev`, 268 files, 231.8 MB — the pre-freeze verification build. **The release run-book must be executed against a `PreflightQC 1.0.0` build** (version frozen 2026-08-09) |
| Installer | `PreflightQC-0.1.0-dev-setup.exe`, 68.8 MB — verification artefact; the release installer will be `PreflightQC-1.0.0-setup.exe` |
| **Execution status** | **NOT EXECUTED.** Requires clean Windows 10 and Windows 11 x64 machines that do not exist in this environment. |
| Gate | **GATE-6** — this run-book passing on both operating systems **and** G-12 complete |

---

## 0. HOW TO READ THIS DOCUMENT

Each criterion carries a **Pre-verified** column. That is not a substitute for running the
step; it records what has already been proven mechanically on the build machine, so the
operator knows which failures would be surprising and which would not.

| Marking | Meaning |
| --- | --- |
| **AUTO** | Proven by an automated test against the **built package**. A failure on a clean machine would mean an environment difference, not a packaging defect. |
| **PARTIAL** | Proven in the development environment but not against the packaged binary, or proven for one half of the criterion. |
| **NO** | Nothing about this can be checked without a clean machine. This is the work Phase 13 exists to do. |

**Nothing in this document may be marked PASS by anyone who did not run the step.** A
run-book filled in from expectation is worse than no run-book, because it converts an
untested claim into a signed one.

---

## 1. PREREQUISITES

| # | Requirement | Why |
| --- | --- | --- |
| P-1 | Windows 10 x64 and Windows 11 x64, clean images | Two OS generations; P13-A14 needs both |
| P-2 | **No Python**, no FFmpeg, no MediaInfo, no developer tooling | The package must be self-contained |
| P-3 | No Visual C++ redistributable beyond the stock image | A missing runtime DLL is exactly what this phase catches |
| P-4 | A **standard (non-administrator)** user account | The target user often cannot elevate |
| P-5 | SmartScreen enabled, default settings | Reputation behaviour must be observed, not assumed |
| P-6 | A firewall rule that can block the machine's outbound traffic | AC-12 / P13-A9 |
| P-7 | A copy of the golden corpus results from the build machine | P13-A7 compares against them |
| P-8 | **An installer in its declared signing state** | Signed path: a signed installer (G-11). Unsigned path: Policy U declared and verified (`docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md`) |

> **Which path applies must be decided before the session starts.** No certificate
> exists (gate G-11 OPEN), so under the signed path A2 and A8 cannot produce a
> meaningful result — do not run the run-book "except for signing" and call it passed.
> Under **Policy U** (the formalized V1 unsigned path), run the **A2-U and A8-U
> variants** below instead: they validate the *declared* unsigned state and the honest
> disclosure around it, and they do not pretend to be a signing pass.

---

## 2. THE RUN-BOOK

Record the observed result and the evidence for every row. Where a step says *read the
file*, attach it.

### A1 — Installer runs without an administrator prompt

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — the compiled installer's manifest declares `requestedExecutionLevel level="asInvoker"`, and `installer.iss` sets `PrivilegesRequired=lowest` (asserted by test). No UAC prompt is *possible* from the manifest. Actual behaviour under a managed policy is untested. |

1. Log in as the standard user.
2. Run `PreflightQC-<version>-setup.exe`.
3. **Expect:** no UAC elevation prompt; default install path under
   `%LOCALAPPDATA%\Programs\PreflightQC`.
4. Record the exact install path.

**PASS / FAIL:** ☐  **Evidence:**

---

### A2 — SmartScreen does not block the signed installer

| | |
| --- | --- |
| **Pre-verified** | **NO — and currently unrunnable.** The build is unsigned (G-11). |

1. Download or copy the installer to the clean machine by the route real users will use.
2. Run it and record SmartScreen's exact behaviour.
3. **Expect:** either no warning, or a reputation warning that a user can proceed through.
4. A new certificate has no reputation and will warn initially. **Record the observed
   behaviour and the mitigation plan; do not treat a reputation warning as a correctness
   failure.**

**PASS / FAIL / ACCEPTED-WITH-NOTE:** ☐  **Evidence:**

#### A2-U — Policy U variant (unsigned release path)

1. Download the unsigned installer to the clean machine **by the route real users will
   use** so it carries Mark-of-the-Web.
2. Run it. **Expect:** the SmartScreen *"Windows protected your PC"* dialog with an
   unknown publisher, and **More info → Run anyway** proceeding to a normal install.
3. Screenshot the dialog. Record the exact wording — the support page's description
   (`UNSIGNED-RELEASE-POLICY-V1.md` §4) must match what Windows actually shows.
4. Verify the download hash against the published `RELEASE-HASHES.txt` (Policy U
   condition U-3) with `Get-FileHash`, and record both values.
5. **This step passes when the observed behaviour matches the disclosed behaviour.** A
   blocked install with no proceed path, or behaviour differing from the disclosure, is
   a FAIL.

**PASS / FAIL:** ☐  **Evidence (screenshots + hashes):**

---

### A3 — The application launches with no Python and no pre-installed inspector

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — the packaged executable runs and completes its self-check on the build machine, but that machine has Python and Qt installed. A missing plugin or runtime DLL is precisely what only a clean machine reveals. |

1. Launch PreflightQC from the Start menu.
2. **Expect:** the main window appears. No console window, no missing-DLL dialog.
3. If it fails, capture the error dialog verbatim — the DLL name is the whole diagnosis.

**PASS / FAIL:** ☐  **Evidence:**

---

### A4 — The startup self-check passes and reports both inspector versions

| | |
| --- | --- |
| **Pre-verified** | **AUTO** — `packaging/build.py` runs the packaged binary's self-check on every build and fails the build if it does not resolve both inspectors from `bin/`. |

1. From a command prompt: `"%LOCALAPPDATA%\Programs\PreflightQC\PreflightQC.exe" --self-check`
2. The executable is a GUI-subsystem binary, so **the console shows nothing**. Read the
   report it writes:
   `%LOCALAPPDATA%\PreflightQC\logs\self-check.txt`
3. **Expect** exactly:
   - `ffprobe … version : n8.1.2-34-g9b6c8969e0-20260809 … licence : LGPL-3.0-or-later`
   - `mediainfo … version : 26.05 … licence : BSD-2-Clause`
   - `SELF-CHECK PASSED`
4. Also open the About screen and confirm the same two versions appear there.

**PASS / FAIL:** ☐  **Attach:** `self-check.txt`

---

### A5 — An ffprobe planted on PATH is never invoked

| | |
| --- | --- |
| **Pre-verified** | **AUTO** — `tests/packaging/test_release_artefacts.py::test_the_packaged_app_ignores_an_ffprobe_planted_on_path` places a decoy `ffprobe.exe` **first** on PATH and asserts the packaged binary still resolves `bin\ffprobe.exe` and reports the FFmpeg version. Verified against the shipped executable. |

Repeat it on the clean machine, because PATH handling is environment-sensitive:

1. `mkdir %TEMP%\decoy`
2. Copy any executable to `%TEMP%\decoy\ffprobe.exe`.
3. `set PATH=%TEMP%\decoy;%PATH%`
4. `where ffprobe` — confirm it resolves to the decoy.
5. Run `PreflightQC.exe --self-check` from that same prompt.
6. **Expect:** `path : …\Programs\PreflightQC\bin\ffprobe.exe` and the correct FFmpeg
   version. **Any** appearance of the decoy path is an immediate FAIL and blocks release.

**PASS / FAIL:** ☐  **Attach:** `self-check.txt`

---

### A6 — Drag-and-drop, file picker and folder picker all work

| | |
| --- | --- |
| **Pre-verified** | **NO** — shell integration cannot be exercised headlessly. |

1. Drag a single video file onto the window.
2. Drag a **folder** onto the window; confirm it recurses.
3. Add files via the file picker.
4. Add a folder via the folder picker.
5. Drag a **non-video** file; confirm it is rejected clearly, not silently ignored.

**PASS / FAIL:** ☐  **Evidence:**

---

### A7 — A representative batch matches the golden corpus run

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — the golden corpus passes in the development environment against the real binaries. It has not been run through the packaged application. |

1. Copy the golden corpus to the clean machine.
2. Run the batch against **each** shipped preset.
3. Compare per-file status and per-rule findings with the build-machine results.
4. **Expect:** identical. Any difference is a packaging defect until proven otherwise —
   the inspectors are byte-identical, so the metadata must be too.

**PASS / FAIL:** ☐  **Attach:** both result exports.

---

### A8 — Application, first-party binaries and installer are Authenticode-signed

| | |
| --- | --- |
| **Pre-verified** | **NO — and currently failing by design.** `python packaging/sign.py verify` reports `UNSIGNED` for both artefacts and exits non-zero. That is the correct state to report before a certificate exists. |

1. `signtool verify /pa /v "…\PreflightQC.exe"`
2. `signtool verify /pa /v "…\PreflightQC-<version>-setup.exe"`
3. **Expect:** both verify, with an RFC 3161 timestamp.
4. Confirm the third-party binaries in `bin\` are **unmodified** — compare SHA-256 against
   `licenses\DEPENDENCY-MANIFEST.json`.

**PASS / FAIL:** ☐  **Evidence:**

#### A8-U — Policy U variant (unsigned release path)

The criterion becomes: **the artefacts are in exactly the signing state the release
declares.**

1. `python packaging/sign.py verify --expect unsigned` — **expect exit 0**, every
   artefact reported `UNSIGNED (as declared by Policy U)`. A *signed* artefact here is a
   FAIL: the release documentation would be describing a different file than the one
   shipping.
2. `python packaging/sign.py verify` (default, signed expectation) — **expect exit 1.**
   Record this failure in the evidence. Both results together are the honest record:
   G-11 not passed, declared state verified.
3. Confirm the third-party binaries in `bin\` are **unmodified** — compare SHA-256
   against `licenses\DEPENDENCY-MANIFEST.json` (unchanged from A8).

**PASS / FAIL:** ☐  **Evidence (both command outputs):**

---

### A9 — The full cycle completes with outbound network blocked

| | |
| --- | --- |
| **Pre-verified** | **AUTO (structurally)** — the package contains no socket implementation: `Qt6Network.dll`, `_socket`, `_ssl` and `libssl` are all excluded. `libcrypto-3.dll` remains for `hashlib` message digests and provides no transport. Asserted by `test_no_network_capable_library_is_shipped`. |

1. Block all outbound traffic for the machine at the firewall.
2. Run a full cycle: add files → choose preset → inspect → view findings → export both
   report formats.
3. **Expect:** no error, no delay, no retry, no dialog mentioning connectivity.
4. Optionally confirm with a packet capture that the process opens no socket.

**PASS / FAIL:** ☐  **Evidence:**

---

### A10 — The About screen renders notices and licence texts offline

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — every licence text a component references is present in the package (`test_every_referenced_licence_text_is_present`), and the notices name the correct licence version. Rendering in the About dialog is untested. |

With the network still blocked:

1. Open About.
2. Confirm both inspector versions.
3. Confirm the FFmpeg notice names the **LGPLv3** — not v2.1.
4. Open `THIRD-PARTY-NOTICES.txt` and each licence text from the About screen; all must
   open from the local package.
5. Confirm the corresponding-source URL is present and is a **real** URL, not the
   `preflightqc.example` placeholder.

> **Blocker:** step 5 fails today. `hosting_url` is a declared placeholder pending a
> release domain — see `docs/licensing/CORRESPONDING-SOURCE-PLAN.md` §6, action H-1/H-2.

**PASS / FAIL:** ☐  **Evidence:**

---

### A11 — Custom profile create / save / restart / reload

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — profile round-tripping is covered by the test suite in the development environment; not under a standard Windows account with a real `%LOCALAPPDATA%`. |

1. Create a custom profile; save it.
2. Confirm it lands under `%LOCALAPPDATA%\PreflightQC\profiles`.
3. Close the application completely; relaunch.
4. **Expect:** the profile is listed and loads.
5. Export it, delete it, re-import it.

**PASS / FAIL:** ☐  **Evidence:**

---

### A12 — Uninstall removes the application and leaves user data intact

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — `installer.iss` has an intentionally empty `[UninstallDelete]` section, asserted by test. Actual uninstaller behaviour is untested. |

1. Note the contents of `%LOCALAPPDATA%\PreflightQC`.
2. Uninstall via Settings → Apps.
3. **Expect:** the program directory is gone; `%LOCALAPPDATA%\PreflightQC` — profiles,
   config and logs — **remains**.
4. This is deliberate: a profile is a client delivery specification the user authored, and
   an uninstaller should not delete someone's work. Record the behaviour either way.

**PASS / FAIL:** ☐  **Evidence:**

---

### A13 — Source video files are unmodified after the batch

| | |
| --- | --- |
| **Pre-verified** | **PARTIAL** — proven in the development environment across three presets over the full 15-file corpus with the real binaries: byte-identical SHA-256, size and mtime. Not repeated through the packaged application. |

1. Record SHA-256, size and mtime for every test file **before** the batch.
2. Run batches against several presets, including a cancelled one.
3. Re-record and compare.
4. **Expect:** every value identical. Spec §18 forbids ever opening a source for writing;
   a changed mtime alone is a FAIL.

**PASS / FAIL:** ☐  **Attach:** both hash listings.

---

### A14 — The whole run-book passes on **both** Windows 10 and Windows 11

Execute A1–A13 independently on each OS. A pass on one is not a pass.

**Windows 10 overall:** ☐   **Windows 11 overall:** ☐

---

## 3. WHAT IS ALREADY PROVEN, AND WHAT IS NOT

| Criterion | Pre-verified | Blocking issue before it can be executed |
| --- | --- | --- |
| A1 installer without elevation | PARTIAL | — |
| A2 SmartScreen | NO | **No certificate (G-11)** — or run **A2-U** under Policy U |
| A3 launches clean | PARTIAL | — |
| A4 self-check reports versions | **AUTO** | — |
| A5 PATH ffprobe never used | **AUTO** | — |
| A6 drag-and-drop / pickers | NO | — |
| A7 batch matches golden corpus | PARTIAL | — |
| A8 Authenticode signatures | NO | **No certificate (G-11)** — or run **A8-U** under Policy U |
| A9 works offline | **AUTO (structurally)** | — |
| A10 About renders offline | PARTIAL | **Corresponding-source URL is a placeholder (H-1/H-2)** |
| A11 custom profiles | PARTIAL | — |
| A12 uninstall preserves user data | PARTIAL | — |
| A13 sources unmodified | PARTIAL | — |
| A14 both operating systems | NO | **No clean Win10/Win11 machines** |

---

## 4. SIGN-OFF

Phase 13 is complete, and **GATE-6** passes, only when **all** of the following hold:

1. Every criterion A1–A13 is marked PASS on **Windows 10**.
2. Every criterion A1–A13 is marked PASS on **Windows 11**.
3. **One** of the following, matching the declared release path:
   - **Signed path:** G-11 is satisfied — a real certificate, and `signtool verify`
     passing (A2/A8); **or**
   - **Unsigned path (Policy U):** every condition U-1 … U-6 of
     `docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md` holds, A2-U and A8-U are marked
     PASS, and the release audit records the default `sign.py verify` failure alongside
     the Policy U pass. **G-11 remains OPEN and is recorded as such.**
4. **G-12** is complete — under the amended gate (SPEC LOCK v1.1.0,
   `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`): manifest, notices, EULA and
   source obligations in place, unresolved legal questions documented, and the
   **Product Owner's written residual-risk acceptance for this specific release**
   executed (ADR-G12 §8). No attorney review occurred and none is claimed.
   **Status: executed 2026-08-09 for PreflightQC 1.0.0**
   (`docs/reports/G12-OWNER-ACCEPTANCE-V1.md`) — valid only while the release under
   validation is exactly that identity.
5. The corresponding-source URL in the shipped notices resolves to the real archive.

| Role | Name | Date | Signature |
| --- | --- | --- | --- |
| Validation operator (Win10) | | | |
| Validation operator (Win11) | | | |
| Release owner | | | |

**Current status: NOT EXECUTED. GATE-6 OPEN.**
