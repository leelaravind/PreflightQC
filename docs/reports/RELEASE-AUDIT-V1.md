# PREFLIGHTQC — COMPLETE RELEASE AUDIT (V1)

> **AMENDMENT NOTE (2026-08-09, added after this report was written).** Gate G-12 was
> amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing &
> compliance risk acceptance** — see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`.
> Statements below describing attorney review as an absolute release prerequisite record
> the gate as it stood when this report was written and are preserved unchanged.
> **No attorney review has occurred, and no legal clearance is claimed.**

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Scope | G-5 resolution, Phases 11–13, and a full audit of every release gate |
| Artefact audited | `dist/PreflightQC` — 268 files, 231.8 MB — and `PreflightQC-0.1.0-dev-setup.exe`, 68.8 MB |
| Automated gates | **G-1 … G-10 and G-13: PASS.** G-11 fails by design; G-12 is not automatable. |
| **Open gates** | **G-11 (certificate), G-12 (attorney), Phase 13 (clean machines), corresponding-source hosting, Microsoft runtime terms** — all five require a human, none can be closed by code |
| Legal status | **No clearance claimed.** |
| Repository state | **Nothing committed, pushed, published or released.** `HEAD` is still the Phase-B planning commit. |

---

## 1. WHAT WAS ASKED, AND WHAT HAPPENED

> *Resolve G-5 → finish remaining implementation-plan phases/package → run complete release
> audit → leave only genuinely human/legal gates open.*

All four are done. The last clause was the demanding one, and it is worth stating plainly
what "genuinely human" turned out to mean: of the gates that were open at the start, **only
five remain, and every one of them needs a person with something this environment does not
have** — a code-signing certificate, a lawyer, two clean Windows machines, a release domain,
or a Microsoft licence document. Nothing is left that more engineering would close.

Getting there required work in both directions. Some things were finished. Several things
that *looked* finished turned out not to work at all.

---

## 2. GATE-BY-GATE STATUS

| Gate | Before | Now | Evidence |
| --- | --- | --- | --- |
| **G-1** manifest complete, checksums match | Untested; generator crashed on first run | **PASS** | All 268 files attributed to a component; no "miscellaneous" bucket exists |
| **G-2** notices cover every entry | Untested | **PASS** | Generated from the package; 18 components; every referenced licence text present |
| **G-3** prohibited-component scan clean | **Broken** — 104 false positives on a clean package | **PASS** | Rewritten to parse flags and query the binary's own capabilities |
| **G-4** no `--enable-gpl` / `--enable-nonfree`, config captured | PASS | **PASS** | Configure line shipped verbatim in `licenses/ffmpeg-build-configuration.txt` |
| **G-5** version-matched source archived + hosted | **NOT MET** — the only tarball was FFmpeg **9.0** against an **8.1.2** binary | **PASS (engineering)** | §3. Hosting is action H-1 |
| **G-6** build recipe recorded and shipped | Partial | **PASS** | BtbN recipe archived at the identified CI commit |
| **G-7** DLL names unobfuscated | PASS | **PASS** | UPX disabled; one-dir; names asserted by test |
| **G-8** EULA carve-outs | **NOT STARTED** | **PASS (draft)** | `packaging/EULA.txt`; 7 clause tests |
| **G-9** MediaInfo BSD + ZenLib notices, real feature set | Partial | **PASS** | libcurl verified absent from the package, not merely uninstalled |
| **G-10** official source + published checksum verified | **UNSET** | **PASS** | §4 |
| **G-11** Authenticode signatures | Not available | **OPEN — fails by design** | `sign.py verify` reports `UNSIGNED` and exits non-zero |
| **G-12** attorney review | Open | **OPEN** | Cannot be satisfied by any engineering artefact |
| **G-13** GUI-framework licence posture | Partial | **PASS** | `docs/licensing/G13-QT-LICENCE-POSTURE.md`, verified against the built package |

**GATE-5 condition** — *"All of G-1…G-11 and G-13 pass automatically; G-12 initiated"* —
is met **except G-11**, which needs a certificate, and G-12, which needs a lawyer.

---

## 3. G-5 RESOLVED — THE CORRESPONDING SOURCE

The repository held `ffmpeg-9.0.tar.xz` against a binary reporting `n8.1.2`. A newer major
release. It would have looked like compliance on a shelf and satisfied nothing.

The shipped binary names its own provenance: `n8.1.2-34-g9b6c8969e0` is a `git describe` —
release tag `n8.1.2`, 34 commits on, at commit `9b6c8969e0`. Every part was checked
upstream:

| Claim | Verified against |
| --- | --- |
| release `8.1.2` | the source tree's own `RELEASE` file |
| `-34-` commits ahead | GitHub compare: `ahead_by: 34`, `behind_by: 0` |
| commit `9b6c8969e0` | `9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b`, dated 2026-07-31 |
| the binaries themselves | **all seven** `libav*`/`libsw*` version triplets match what ffprobe prints |

That fourth row is the one that ties source to *binary* rather than to a version string.

| Artefact | SHA-256 | Size |
| --- | --- | --- |
| `ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz` | `39002bfe…2583a224` | 17,014,473 |
| `ffmpeg-builds-recipe-2437e7b868da.tar.gz` | `b2392046…f4f310c7` | 103,117 |

Neither is committed — they are 17 MB of upstream code — but both are **reproducible
byte-for-byte** from the recorded commit via `tools/fetch_corresponding_source.py`, which
was confirmed by generating the archive twice and getting an identical hash.
`packaging/verify_source.py` re-derives correspondence on every build; 26 tests cover it,
most of them negative (a one-patch release difference, a single library micro difference, a
wrong commit, an empty hosting URL).

**A bonus finding.** The archived build recipe independently confirms the LGPLv3
amendment: `variants/defaults-lgpl.sh` reads `FF_CONFIGURE="--enable-version3
--disable-debug"` and `LICENSE_FILE="COPYING.LGPLv3"`. The LGPL variant is LGPLv3 **by
construction** and structurally cannot carry `--enable-gpl`.

Full detail: `docs/licensing/CORRESPONDING-SOURCE-PLAN.md`.

---

## 4. G-10 RESOLVED — AUTHENTICITY, AT TWO HONEST LEVELS

| Component | Level | Evidence |
| --- | --- | --- |
| ffprobe + libav* | **Digest-authenticated** | BtbN publishes `checksums.sha256`. The supplied archive matches it exactly, and so does the immutable dated asset. |
| MediaInfo | **Origin-authenticated** | MediaArea publishes **no** checksum file — `.sha256`, `.sha512`, `SHA256SUMS`, `checksums.txt` all 404, and the GitHub release has no assets. The archive was re-downloaded over TLS from `mediaarea.net` and is byte-identical, as is the extracted `MediaInfo.exe`. |

These are recorded in different fields, deliberately. Writing an origin hash into
`published_sha256` would make a weaker check look like a stronger one, and the whole point
of the field is to answer *"did the publisher say these are the bytes?"*

**A reproducibility defect fixed along the way.** The operator had supplied BtbN's
`latest` asset — authentic, but from a **rolling tag** that is overwritten on every
rebuild. Pinning to it would have made the build unreproducible the next day and quietly
detached the checksum from the binary it protects. The lock file now pins the **immutable
dated** release, and the eight extracted files were confirmed byte-identical to the
installed ones. A test asserts the pinned URL is not a `latest` URL.

---

## 5. WHAT THE PACKAGING WORK ACTUALLY FOUND

Phases 11 and 12 had scripts written but never run, and no test coverage at all. Running
them was the audit.

### 5.1 The prohibited-component scanner failed every compliant build

`scan_prohibited.py` substring-matched `libx264` — which appears inside
`--disable-libx264`. Worse, it scanned the raw bytes of every shipped binary, and each
`libav*` DLL embeds the full configure line. Measured against the actual package:

> **104 violations reported. All 104 false.**

A gate that goes red on every good build does not get fixed under release pressure; it
gets switched off. It now does two things that have real answers:

1. **What did the build say it linked?** — the configure string, parsed flag-aware, via
   the *same* `audit_configuration` the application uses. One implementation of the
   policy, not three. (A test asserts they are literally the same function object.)
2. **What can the binary actually do?** — its own `-encoders`, `-decoders`, `-filters`,
   `-demuxers`, `-muxers`, `-protocols` and `-devices` listings, 1,458 capability names in
   total. A linked library registers capabilities; an unlinked one cannot.

Result on the shipped build: **zero violations**, with `libx264`, `libx265`, `rubberband`,
`vidstabdetect` and every GPL-only filter confirmed absent, while permitted components like
`libopenh264` and `libvvenc` are present.

**The GPL-only filter list is derived, not remembered.** Written from memory it contained
`geq` and `pp`, neither of which is GPL-gated in FFmpeg 8.1 — either would have failed a
clean build. It is now extracted from the `*_filter_deps="… gpl …"` declarations in the
`configure` of the exact archived source, and a test regenerates it from that archive so it
cannot go stale.

### 5.2 The manifest generator had never run successfully

It read lock-file keys that do not exist and crashed on the first invocation. Rewritten,
it attributes **every file** in the package to exactly one component — no "miscellaneous"
bucket — and that completeness rule immediately earned its keep:

- **OpenSSL** (`libcrypto-3.dll`, `libssl-3.dll`) was being shipped with no notice.
- **Qt, shiboken6, the Microsoft VC runtime, libffi, attrs, rpds-py** and
  **jsonschema-specifications** likewise.
- A separate closure check over the installed environment caught **typing-extensions**,
  reachable only transitively and invisible to any file-based scan because pure-Python
  packages are compiled into the PYZ inside the executable. **Jinja2** is in the same
  category — genuinely shipped, genuinely third-party, and a purely file-driven manifest
  would have silently omitted its notice.

All 18 components now carry a notice and a licence text, collected from local
authoritative sources by `tools/collect_licences.py` — never downloaded, never retyped.

**LGPL-3.0 alone was not enough.** LGPLv3's first substantive sentence incorporates GPLv3
by reference, so `GPL-3.0.txt` now ships too, with the notices stating explicitly that no
GPL-licensed component is present.

### 5.3 The package shipped `Qt6Network.dll`

The spec excluded the *Python bindings* for QtNetwork, QML and the rest. PyInstaller
shipped the **native libraries** anyway, because Qt's DLLs depend on one another. Thirteen
Qt libraries, including `Qt6Network.dll`.

Not a licence problem — Qt is LGPLv3 either way. A **truth** problem: spec §18 and AC-12
say the product cannot make a network request.

The build now prunes the QML/Quick/Pdf cluster, which takes `Qt6Network` with it, and then
**proves the prune was safe** by re-parsing every shipped PE's import table against what
the package actually contains. The first run of that proof immediately caught two plugins
(`qtuiotouchplugin.dll`, `qpdf.dll`) still bound to removed libraries — so the pruning
became iterative rather than a hand-maintained list.

The same reasoning went one level deeper: CPython's `_socket`, `_ssl` and `libssl` were
also excluded from the freeze. What remains is `libcrypto-3.dll`, which `hashlib` links
for message digests and which provides no transport.

| | Before | After |
| --- | --- | --- |
| Qt libraries | 13 | **4** (Core, Gui, Widgets, Svg) |
| `Qt6Network.dll` | shipped | **absent** |
| Socket implementation | `_socket`, `_ssl`, `libssl` | **none** |
| Package size | 254.7 MB | **231.8 MB** |

The package now contains no socket implementation at all — a materially stronger claim
than "we choose not to call one".

### 5.4 There was no way to check the packaged application at all

Every criterion about the *packaged* app — that it launches without Python, reports both
inspector versions, resolves inspectors by absolute path — could only be checked by a
human opening a dialog. `--self-check` was added as release-validation infrastructure. It
writes its report to `%LOCALAPPDATA%\PreflightQC\logs\self-check.txt`, because the shipped
binary is GUI-subsystem and prints to a console nobody is reading.

That made **spec AC-17 testable on the real artefact**: a decoy `ffprobe.exe` is placed
*first* on PATH, `where ffprobe` resolves to the decoy, and the packaged binary still loads
`bin\ffprobe.exe` and reports the correct FFmpeg version. This now runs on every build and
as an automated test.

---

## 6. THE BUILD, END TO END

`python packaging/build.py` — 12 steps, all passing, ~114 s from clean:

```
[PASS] inspector binaries match binaries.lock.json
[PASS] G-5 corresponding source matches the shipped binary
[PASS] PyInstaller one-dir build
[PASS] stage presets, licences and inspectors at the package root
[PASS] prune unused Qt libraries (removes Qt6Network)
[PASS] verify no dangling DLL imports
[PASS] G-1/G-2 dependency manifest and notices generated from the package
[PASS] G-3/G-4/G-7 prohibited-component scan
[PASS] P11-A3 package layout matches ADR-001 §5
[PASS] preset source staleness and traceability
[PASS] packaged application self-check
[PASS] Inno Setup installer
```

Gates that can be checked *before* the freeze are checked before it. Discovering at
packaging time that the bundled ffprobe is a GPL build wastes a build; discovering it after
the installer is signed wastes a release.

### 6.1 Phase 11 acceptance

| # | Criterion | Result |
| --- | --- | --- |
| P11-A1 | Reproducible from a clean checkout plus `binaries.lock.json` | **PASS** — now genuinely true: the pinned URL is immutable |
| P11-A2 | Checksum mismatch **fails**, never warns | **PASS** — tested, including the no-digest and non-HTTPS refusals |
| P11-A3 | Layout matches ADR-001 §5 | **PASS** |
| P11-A4 | No `ffmpeg.exe` anywhere | **PASS** — allow-list plus an independent forbidden-name list |
| P11-A5 | No prohibited GPL/nonfree component | **PASS** — §5.1 |
| P11-A6 | Shared-library names unobfuscated | **PASS** — UPX disabled |
| P11-A7 | Installer is per-user, no administrator rights | **PASS** — manifest declares `asInvoker` |
| P11-A8 | Authenticode-signed | **OPEN — G-11**, no certificate |
| P11-A9 | Inspectors resolved by absolute path, never PATH | **PASS** — verified on the packaged binary against a decoy |
| P11-A10 | Package size recorded | **PASS** — 231.8 MB / 268 files; installer 68.8 MB |

### 6.2 Phase 12 acceptance

All of G-1…G-10 and G-13 pass (§2). Deliverable 6, the staleness report, ships as
`licenses/PRESET-STALENESS.txt`: **12 presets, 170 rules, 0 stale, 0 traceability
problems**. It is blocking rather than advisory — a rule whose first-party source nobody
has read in six months should not ship in a product whose entire claim is that every
finding traces to a source somebody read. A test confirms it actually goes red once the
sources age (all 170 stale at 2027-03-01); a check that has never fired is not evidence.

### 6.3 Phase 13

`docs/planning/RELEASE-VALIDATION-V1.md` — a 14-criterion run-book. **NOT EXECUTED**: it
needs clean Windows 10 and Windows 11 machines. Each criterion records what is already
proven mechanically, so the operator knows which failures would be surprising: A4, A5 and
A9 are **AUTO** (proven against the built package), seven are **PARTIAL**, four are **NO**.

---

## 7. VERIFICATION

| Check | Result |
| --- | --- |
| Full regression | **1114 passed, 3 skipped, 0 failed** (was 1037) |
| `mypy` | Success — no issues in 52 source files |
| `ruff check src tests tools packaging spikes` | All checks passed |
| Documentation invariants | All 6 hold |
| `tools/fetch_corresponding_source.py` | Both archives match `binaries.lock.json` |
| `tools/collect_licences.py --check` | All expected licence texts present |
| `packaging/sign.py verify` | **G-11 NOT SATISFIED — 2 artefacts UNSIGNED** (correct) |

**No test was weakened.** 77 new tests were added, and `packaging/` went from zero
coverage to 76 tests — which is how §5.1 and §5.2 were found at all.

---

## 8. WHAT REMAINS OPEN — AND WHY NONE OF IT IS ENGINEERING

| # | Item | Gate | Who | Why code cannot close it |
| --- | --- | --- | --- | --- |
| **H-1** | Obtain a code-signing certificate and sign the executable and installer | **G-11** | Release owner | A certificate must be purchased and identity-validated. `sign.py` is written and reports UNSIGNED until then. |
| **H-2** | **Attorney review** of licence, EULA, notices and build manifest | **G-12** | Software-IP attorney | Explicitly non-automatable. Six specific questions are recorded in `EULA.txt` §9, including the LGPLv3 "Installation Information" obligation that arrived with the v3 amendment. |
| **H-3** | Stand up the release host; publish both source archives beside the installer; replace the placeholder URL | **G-5** | Release owner | No release domain exists. `hosting_url` is a declared `PLACEHOLDER`, and a test asserts it is declared as such rather than passing quietly. |
| **H-4** | Commit to serving corresponding source for **three years** | **G-5** | Business | A commitment, not a build artefact. The written offer is already in the notices and the EULA. |
| **H-5** | Supply the **Microsoft Visual C++ redistributable** licence terms | **G-2** | Release owner | Microsoft ships no machine-readable text with the runtime DLLs. `licenses/MS-VC-Redistributable.txt` is a placeholder that says exactly what must replace it, and the manifest reports `PASS WITH OPEN ACTION` rather than silently passing. |
| **H-6** | Execute the clean-machine run-book on **Windows 10 and Windows 11** | **GATE-6** | Validation operator | Requires clean machines. Blocked on H-1 for criteria A2 and A8. |

### 8.1 Two ordering notes worth acting on

- **H-2 is the long pole.** The plan says attorney engagement starts at GATE-3, not at
  Phase 12. It has not started. Everything else on this list is days of work; this one is
  weeks of someone else's calendar.
- **H-1 blocks part of H-6.** Running the run-book against an unsigned build cannot produce
  a meaningful result for SmartScreen (A2) or signature verification (A8). Get the
  certificate before booking the validation machines.

---

## 9. SPEC DEVIATIONS

**One, and it is a strengthening.**

The Qt/CPython network-capability pruning (§5.3) removes libraries the spec never asked us
to ship and never authorised either. It brings the package *into* line with spec §18 and
AC-12, which it previously contradicted. It is recorded here rather than treated as
routine, because deleting files from a package is a real change to what ships and it is
proven safe by import-closure verification rather than by assertion.

`--self-check` (§5.4) is packaging and validation infrastructure required by P11-A9 and
P13-A3/A4/A5, not a product feature. It adds no capability to the product's inspection or
validation behaviour.

Everything else follows the approved plan.

---

## 10. `git status --short`

```
 M .gitignore
 M README.md
 M docs/FUTURE.md
 M docs/architecture/ADR-001-TECH-STACK.md
 M docs/architecture/ARCHITECTURE-V1.md
 M docs/licensing/LICENSING-GATE-V1.md
 M docs/sources/SOURCE-REGISTER.md
 M docs/specification/PREFLIGHTQC-V1-SPEC.md
?? Temp/
?? docs/licensing/CORRESPONDING-SOURCE-PLAN.md
?? docs/licensing/EULA-DRAFT.md
?? docs/licensing/G13-QT-LICENCE-POSTURE.md
?? docs/planning/RELEASE-VALIDATION-V1.md
?? docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md
?? docs/reports/
?? packaging/*.py, packaging/EULA.txt, packaging/installer.iss, packaging/binaries.lock.json
?? presets/  pyproject.toml  requirements.lock  spikes/  src/preflightqc/
?? tests/**  third-party/licenses/  tools/
```

`HEAD` is still `b353181 Initialize repository: V1 spec lock, source pack, and
implementation plan`. `dist/`, `build/`, `third-party/bin/` and `third-party/source/` are
git-ignored by design: the binaries, the built package and the 17 MB source archive are
preserved on disk and never committed, while everything needed to reproduce them is.

**Not committed. Not pushed. Not published. Not released.**

---

## 11. BOTTOM LINE

The product builds, packages, installs per-user without elevation, and passes every
automated release gate that does not require a certificate or a lawyer. The compliance
machinery is no longer aspirational: it runs on every build, it has been shown to fail on
the right inputs, and three of its four gates were silently broken until they were made to
run.

**What is left is a certificate, a lawyer, a domain, a Microsoft licence document, and two
clean Windows machines.** No further engineering will close any of them.
