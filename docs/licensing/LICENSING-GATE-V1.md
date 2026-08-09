# PREFLIGHTQC — V1 LICENSING AND RELEASE GATE

| Field | Value |
| --- | --- |
| Status | Proposed. Subordinate to `docs/specification/PREFLIGHTQC-V1-SPEC.md` §21 and §26. |
| Date | 2026-08-09 |
| Executed by | `docs/planning/IMPLEMENTATION-PLAN-V1.md` Phase 12 |
| Sources | `docs/sources/ffmpeg/`, `docs/sources/mediainfo/`, `docs/sources/SOURCE-REGISTER.md` §6–§7 |

---

> ## NO LEGAL CLEARANCE IS CLAIMED
>
> This document is **engineering research and a compliance checklist**. It is **not legal
> advice**, and nothing in this repository constitutes legal clearance for commercial
> distribution.
>
> **Final commercial licence, EULA, and third-party notice review by a qualified
> software-IP attorney is a hard release prerequisite (gate G-12).** It cannot be
> satisfied by any engineering artefact, test, or automated scan in this repository.
>
> Both dependency reviews in the source pack reach the verdict **"APPROVED WITH
> CONDITIONS"**, and one of those conditions is, in both cases, attorney review.

---

## 1. WHAT IS BEING DISTRIBUTED

PreflightQC is a **closed-source, commercial, downloadable Windows desktop application**
that bundles third-party binaries. That combination — proprietary code shipping alongside
copyleft-licensed components — is the entire reason this gate exists.

| Layer | Licence posture |
| --- | --- |
| PreflightQC application code | Proprietary, closed source |
| `ffprobe` + `libav*` shared libraries | **LGPL 3.0+** — obligations, no copyleft on our source if handled correctly. *Amended 2026-08-09: the verified build carries `--enable-version3`. See §2.0.* |
| MediaInfo + ZenLib | **BSD-2-Clause / zlib** — attribution only |
| PySide6 / Qt 6 (if ADR-001 primary stack) | **LGPLv3** — obligations, and the largest open question |
| Other Python runtime dependencies | Permissive (PSF, BSD, MIT) — notices only |

---

## 2. FFMPEG / FFPROBE — LGPL 3.0

### 2.0 AMENDMENT — 2026-08-09 (SPEC LOCK)

**This section originally required LGPL v2.1. It now requires LGPL v3.**

The requirement was written before any binary had been obtained, on the assumption that
an "LGPL build" of FFmpeg meant LGPL v2.1. Verification of the actual mainstream Windows
build disproved that assumption.

**Evidence.** The BtbN `win64-lgpl-shared` build
(`n8.1.2-34-g9b6c8969e0-20260809`) reports `--enable-version3` in its configuration and
ships the **LGPL v3** licence text as its `LICENSE.txt`. FFmpeg's own `LICENSE.md` states:

> The following libraries are under LGPL version 3: gmp, libaribb24, liblensfun.
> When combining them with FFmpeg, use the configure option `--enable-version3` to
> upgrade FFmpeg to the LGPL v3.

**Decision.** `--enable-version3` is **permitted**, and `gmp`, `libaribb24` and
`liblensfun` are permitted **as part of a verified LGPLv3 build**. They upgrade the
licence version; they do not introduce copyleft over PreflightQC's own source.

**Why not build a custom LGPLv2.1 FFmpeg instead.** Doing so would make PreflightQC a
"modifier" under §2.5, taking on source-correspondence duties for a build we produced
ourselves — a materially *worse* licensing position than using an unmodified official
binary. The amendment accepts the licence version the ecosystem actually ships.

**What does not change.** `--enable-gpl` and `--enable-nonfree` remain absolutely
prohibited, as does every library in FFmpeg's `EXTERNAL_LIBRARY_GPL_LIST`, its nonfree
list, and `libsmbclient`. The verified build disables all of them.

**What this costs.** LGPL v3 carries terms v2.1 does not: installation information for
"User Products", and explicit patent provisions. Their effect on a commercial desktop
product is squarely an attorney question and is folded into **G-12**. It is the *same*
licence family as the PySide6/Qt question already open as **Q-1 / G-13**, so it is one
legal conversation rather than two.

### 2.1 The posture

Ship an **unmodified, official LGPL shared build** of `ffprobe` and its `libav*`
DLLs. The verified build is **LGPL v3**. Invoke `ffprobe` as a **separate child process**. Bundle **no GPL and no nonfree
component**. Ship **no `ffmpeg` encoder**.

Two independent protections, deliberately stacked:

1. **An LGPL build** — so the obligations are LGPL's (notices, source availability,
   replaceability), not GPL's (copyleft on our source).
2. **A separate process** — so the coupling is command-line arguments in and JSON on
   stdout out.

The FFmpeg research is explicit that process isolation is **defence-in-depth, not the sole
compliance mechanism**. The FSF's own GPL FAQ says pipes, sockets and command-line
arguments normally make two separate programs — and in the same breath concedes this is
*"a legal question, which ultimately judges will decide."* We therefore do not rely on it
alone.

### 2.2 What triggers GPL or an unredistributable binary (must never happen)

| Trigger | Effect |
| --- | --- |
| `--enable-gpl` | *"FFmpeg's license changes to GPL v2+"* — copyleft would reach PreflightQC |
| Any GPL external library | `libx264`, `libx265`, `libxvid`, `libxavs`, `libxavs2`, `libdavs2`, `frei0r`, `libcdio`, `librubberband`, `libvidstab`, `avisynth` |
| GPL-only internal files | `vf_delogo.c`, `vf_hqdn3d.c`, `vf_cropdetect.c`, `flac_dsp_gpl.asm`, `idct_mmx.c` |
| `libsmbclient` | Forces **GPL v3** |
| ~~`--enable-version3` libs~~ | **No longer a trigger.** `libaribb24`, `liblensfun` and `gmp` are LGPLv3 and are **permitted** under the §2.0 amendment. They upgrade the licence version; they do not create copyleft. |
| `--enable-nonfree` | *"will cause the resulting binary to be unredistributable"* — Fraunhofer FDK AAC, OpenSSL in incompatible combinations, CUDA SDK (`libnpp`, `cuda-nvcc`) |

**`--enable-nonfree` is an absolute no-ship.** Not a risk to manage — a build that must
never enter the package.

### 2.3 Approved and rejected build sources

| Source | Verdict |
| --- | --- |
| **BtbN `FFmpeg-Builds`, `win64-lgpl-shared`** | **APPROVED** — the mainstream source of LGPL *shared* Windows binaries |
| `gyan.dev` main Windows builds | **REJECTED** — *"All builds are 64-bit, static and licensed as GPLv3"* |
| `evermeet.cx` (macOS) | **REJECTED** — built with `--enable-gpl --enable-libx264 --enable-libx265`; also Intel-only. (Moot for V1: Windows only.) |
| Any static build | **REJECTED for V1** — static linking forces the LGPL §6 object-file/relink route, which is far more burdensome for closed source |

### 2.4 The LGPL compliance checklist

Item wording below reflects the **LGPL v3** posture set in §2.0. The structure of the
obligations is unchanged from v2.1; only the version named in the notices differs.

From FFmpeg's own `legal.html`. Every item is a Phase 12 gate.

| # | Obligation | Gate |
| --- | --- | --- |
| 1 | Build **without** `--enable-gpl` and **without** `--enable-nonfree` | G-4 |
| 2 | **Dynamic linking** — on Windows, link to DLLs (we go further: separate process) | G-4 |
| 3 | Distribute the **corresponding FFmpeg source** that *"corresponds exactly to the library binaries"* | G-5 |
| 4 | Explain the **configure line** in a text file shipped with the product | G-6 |
| 5 | **Host the source on the same webserver** as the binary | G-5 |
| 6 | Download-page notice: *"This software uses code of FFmpeg licensed under the LGPLv3 and its source can be downloaded here"* | G-2 |
| 7 | About-box notice: *"This software uses libraries from the FFmpeg project under the LGPLv3"* | G-2 |
| 8 | Mention FFmpeg and LGPLv3 **in the EULA** | G-8 |
| 9 | If the EULA claims ownership of code, **explicitly disclaim ownership of FFmpeg** | G-8 |
| 10 | **Remove any reverse-engineering prohibition** from the EULA — **and all translations** | G-8 |
| 11 | **Do not obfuscate DLL names.** `avcodec-MyProg.dll` is acceptable; `MyProgDec.dll` is not | G-7 |
| 12 | Ship the **full LGPL 3.0 licence text** (and LGPL 2.1, which v3 incorporates by reference and which covers libzvbi) | G-2 |
| 13 | Preserve all upstream copyright notices | G-2 |
| 14 | Credit the IJG *"in the documentation accompanying your program"* **if** the libjpeg-derived files (`jfdctfst.c`, `jfdctint_template.c`, `jrevdct.c`) are present in the shipped build | G-2 |

Item 10 deserves emphasis: a boilerplate EULA almost always contains a
reverse-engineering prohibition, and shipping one alongside LGPL libraries directly
conflicts with the rights LGPL grants. This is a common, avoidable failure.

### 2.5 Source correspondence — the residual risk

Relying on a third-party distributor's published source and build recipe to satisfy LGPL
§6 "corresponds exactly" is standard practice, but it means trusting a build we did not
produce.

**Mitigation (required, Phase 12):** archive the **exact source tarball and build
configuration** that produced the shipped binaries, alongside the binaries themselves, and
host both. Do not rely solely on a link to the distributor.

#### 2.5.1 Status — 2026-08-09

**Done.** The mitigation is implemented and mechanically enforced. Full detail in
`docs/licensing/CORRESPONDING-SOURCE-PLAN.md`; the short version:

| Item | Result |
| --- | --- |
| Source identified | FFmpeg commit `9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b` — the `-g9b6c8969e0` in the shipped binary's own version string |
| Correspondence proven | Four independent ways: `RELEASE` = 8.1.2; 34 commits after tag `n8.1.2` (confirmed upstream); commit hash; and **all seven** `libav*`/`libsw*` version triplets matching what the binary prints |
| Archived | `ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz`, SHA-256 `39002bfe…`, reproducible byte-for-byte via `git archive` |
| Build recipe archived | `BtbN/FFmpeg-Builds` @ `2437e7b868da…`, SHA-256 `b2392046…` |
| Enforced | `packaging/verify_source.py` fails the audit on any divergence; 26 tests, mostly negative |
| **Not done** | **Hosting.** No release domain exists yet, so `hosting_url` is a declared `PLACEHOLDER`. A human must publish both archives and commit to a 3-year offer. |

Independently, the recipe corroborates the §2.0 amendment: `variants/defaults-lgpl.sh`
sets `FF_CONFIGURE="--enable-version3 --disable-debug"` and `LICENSE_FILE="COPYING.LGPLv3"`,
so the LGPL variant is **LGPLv3 by construction** and cannot carry `--enable-gpl`.

The prior state was the near-miss this section warns about: the repository held
`ffmpeg-9.0.tar.xz` against an **8.1.2** binary — the wrong major release, which would have
looked like compliance and been worth nothing.

### 2.6 Patent posture

`-show_streams` and `-show_format` parse container and codec-parameter metadata **without
decoding**. Extracting frame-attached HDR side data requires `-show_frames`, which **does
engage the decoder** — in practice `-read_intervals "%+#1"` for a single frame.

Practical exposure is very low — inspection, not playback or output — but is **not
formally zero**. AVC US essential patents run to 29 Nov 2027; HEVC well beyond 2030.
FFmpeg's own patent FAQ declines to assert FFmpeg is patent-free.

**V1 mitigation:** the HDR first-frame read is bounded and behind an explicit setting
(spec §10.5). **Phase 1 must determine whether MediaInfo's `HDR_Format` alone is
sufficient for V1's HDR `INFO` findings — if so, the decoder is never engaged and this
question becomes moot. Prefer that outcome.**

**Encoding is out of scope for V1.** If HEVC/AVC encoding is ever added, x264/x265
commercial licences **and** the relevant codec patent-pool licences must be obtained
first.

---

## 3. MEDIAINFO — BSD-2-CLAUSE

### 3.1 The posture

Ship **MediaInfo 26.05** (or the then-current BSD-era release). BSD-2-Clause imposes no
copyleft, no source-disclosure obligation, and no field-of-use restriction. The single
active condition is reproducing the notice in binary distributions.

ZenLib (`libzen`) is zlib-licensed: no misrepresentation of origin, altered versions
plainly marked.

### 3.2 Hard constraints

| Constraint | Reason |
| --- | --- |
| **Version ≥ 0.7.63 only** (pinned: 26.05) | Up to 0.7.62 the library was **LGPL** and the GUI/CLI were **GPL**. Shipping such a version would impose copyleft obligations incompatible with closed source. |
| **Never ship the GUI** | It links Qt or wxWidgets, reintroducing toolkit obligations and potential copyleft. PreflightQC does not need it. |
| **Never enable libcurl / network support** | Enlarges the notice obligation (curl, and typically OpenSSL, libssh2, Brotli) for zero benefit to a local-only tool. The default DLL does **not** include libcurl; it requires a sidecar. **Verify the shipped binary's actual feature set — do not assume.** |
| **Official channels only** | `mediaarea.net` or the official MediaArea GitHub releases, SHA-256 verified. Third-party DLL-download sites (dll-files.com, dllme.com, iosninja.io) are unsafe. |
| **Sign our own bundle** | Authenticode signing status of the official `MediaInfo.dll` could not be confirmed. Treat as unsigned. |
| **Archive the pinned LICENSE** | BSD grants for a version already received are effectively irrevocable, so archiving the pinned version's LICENSE protects against a future upstream relicensing. |

### 3.3 Required notice

Either the full BSD-2-Clause notice (copyright line + two conditions + "AS IS"
disclaimer), **or** MediaArea's short form:

> This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL

including the website link. Plus ZenLib: *"(c) MediaArea.net SARL, zlib license."*

Use the year range from **the pinned build's own LICENSE file** (the repository LICENSE
and the website differ), and reproduce `MediaArea.net SARL` verbatim.

### 3.4 CLI vs library

Licensing does **not** favour either — both are BSD-2-Clause, and linking mode is legally
irrelevant under BSD. The choice is made on engineering grounds
(`ARCHITECTURE-V1.md` §4.3, ADR-001 Q-3, decided in Phase 1). The licensing constraint is
only: **BSD-era version, no GUI, no libcurl.**

MediaInfo also offers an "Alternate open source licenses" clause permitting relicensing
under Apache-2.0, LGPL-2.1+, GPL-2.0+, or MPL-2.0. This **widens** options; we simply rely
on the default BSD-2-Clause terms.

---

## 4. GUI FRAMEWORK — THE OPEN QUESTION (G-13)

The ADR-001 primary stack bundles **PySide6 / Qt 6 under LGPLv3**. This is the single
largest unresolved licensing question in the project, and it is **not** covered by either
source-pack dependency review — those reviews cover the inspectors only.

### 4.1 The obligation

LGPLv3 §4 offers the same two routes as LGPL 2.1 §6:

- **4(d)(0)** — ship object code enabling the user to relink (burdensome for closed
  source), or
- **4(d)(1)** — use a suitable **shared library mechanism**, so a user can substitute an
  interface-compatible version.

### 4.2 The intended compliance route

PyInstaller **one-directory** build (never one-file), so Qt DLLs and PySide6 extension
modules sit as separate, unobfuscated, replaceable files in `_internal/`. Plus: LGPL-3.0
text, notices, and the same EULA carve-outs already required for FFmpeg.

### 4.3 Why this is *plausible* but not *settled*

The obligations are the same in kind as FFmpeg's, and the compliance machinery is already
being built. But "a frozen Python bundle satisfies LGPLv3's shared-library mechanism" is
an interpretation, not an established fact, and it is materially more entangled than
shipping an inspector as a child process.

### 4.4 Handling

| Aspect | Decision |
| --- | --- |
| Gate | **G-13**, automated part (layout, notices, replaceability) in Phase 12 |
| Legal gate | **G-12** (attorney), engagement started at **GATE-3** — *before* Phase 6, not at Phase 12 |
| Checkpoint | **GATE-3** precedes the UI phase, so a reversal costs one layer, not a rebuild |
| Fallback | .NET 8 + Avalonia UI (MIT), per ADR-001 §7 |
| Enabler | The "no Qt below L6" import-boundary test, enforced from Phase 2 onward |

Also open: **Q-2 — whether the PyInstaller bootloader exception (GPL with a linking
exception permitting closed-source distribution of frozen applications) covers the
bootloader as shipped here.** Attorney review item.

---

## 5. DEPENDENCY MANIFEST — RELEASE GATE

`DEPENDENCY-MANIFEST.json` is **generated from the built package**, never hand-maintained,
so it cannot drift from what actually ships.

Per component:

| Field | Requirement |
| --- | --- |
| `name` | Component name |
| `version` | Exact version |
| `build_identifier` | Exact build variant (e.g. `BtbN win64-lgpl-shared <date/tag>`) |
| `license` | SPDX identifier |
| `license_text_path` | Path within `licenses/` |
| `source_url` | Official distribution URL |
| `published_checksum` | The publisher's checksum |
| `shipped_sha256` | SHA-256 of the file as shipped |
| `notice_form` | Full text / short attribution / none |
| `linkage` | subprocess / dynamic / static / not-linked |
| `corresponding_source` | Location of version-matched source, where required |

### 5.1 Completeness rule

Every file in the release package must map to a manifest entry, or be first-party. There
is no "miscellaneous" category. The generator enumerates the **frozen environment**, not
`requirements.in`, so transitive Python dependencies cannot be missed.

### 5.2 `published_checksum` — what counts, and what to do when there isn't one

The field exists to answer one question: *did the bytes we shipped come from the publisher?*
An operator-supplied hash cannot answer it, because it only records what we happened to be
given. Two levels of answer are acceptable, and they must never be conflated:

| Level | Meaning | Record as |
| --- | --- | --- |
| **Digest-authenticated** | The publisher publishes a checksum file; our bytes match it | `published_checksum` = the published value, with its source URL |
| **Origin-authenticated** | The publisher publishes no checksum; our bytes are byte-identical to a fresh TLS download from the publisher's own host | `published_checksum` = `NOT PUBLISHED BY VENDOR`, plus `origin_verified_sha256` and the method |

Status at 2026-08-09 (G-10 **resolved**):

| Component | Level | Evidence |
| --- | --- | --- |
| ffprobe / libav* | **Digest-authenticated** | BtbN ships `checksums.sha256` per release. Both the rolling `latest` asset and the pinned immutable asset were downloaded and matched exactly. |
| MediaInfo | **Origin-authenticated** | MediaArea publishes no checksum for the Windows CLI zip — `.sha256`, `.sha512`, `SHA256SUMS` and `checksums.txt` all return 404 and the GitHub release carries no assets. The archive was re-downloaded from `mediaarea.net` over TLS and is byte-identical, as is the extracted `MediaInfo.exe`. |

**Pinning rule (added 2026-08-09).** `download_url` must name an **immutable** release
asset. BtbN's `latest` tag is rolling — the same filename is replaced on every rebuild — so
pinning to it makes the build unreproducible the next day and quietly detaches the checksum
from the binary it was meant to protect. The dated `autobuild-*` asset is immutable and is
what is pinned; its eight extracted files were confirmed byte-identical to the installed
ones. A test asserts the pinned URL is not a `latest` URL.

---

## 6. THIRD-PARTY-NOTICES — RELEASE GATE

Generated from the manifest. Must contain, at minimum:

1. **FFmpeg**
   - *"This software uses libraries from the FFmpeg project under the LGPLv3"*
   - A statement that the build carries `--enable-version3` and is therefore LGPL v3
   - Full LGPL-3.0 text (plus LGPL-2.1, incorporated by reference and covering libzvbi)
   - A statement that PreflightQC does not own FFmpeg, and where the copyright holders can
     be found
   - The exact configure line / build variant of the shipped binaries
   - A same-server link to version-matched corresponding source
2. **Every bundled LGPL sub-library** enabled in the shipped build: notice + licence text
3. **IJG credit** if the libjpeg-derived files are present in the shipped build
4. **MediaInfo / MediaInfoLib** — attribution sentence + BSD-2-Clause text
5. **ZenLib** — zlib attribution
6. **PySide6 / Qt** — LGPLv3 notice + full LGPL-3.0 text (if the primary stack is in force)
7. **CPython** — PSF licence notice
8. **Jinja2, MarkupSafe** — BSD-3-Clause notices
9. **PyInstaller bootloader** — notice and exception statement, if applicable
10. **Inno Setup** — notice, if any stub is embedded
11. **Any other shipped runtime dependency**

### 6.2 EULA carve-outs (G-8)

| Requirement | Reason |
| --- | --- |
| **No reverse-engineering prohibition** that conflicts with LGPL rights, or an explicit carve-out for the LGPL components | Direct FFmpeg checklist item; conflicts with LGPL-granted rights |
| Explicit **disclaimer of ownership of FFmpeg** | Required if the EULA claims ownership of the software |
| **Mention FFmpeg and LGPLv3** | Required |
| **Mention Qt/PySide6 and LGPLv3**, if applicable | Same reasoning |
| **All translations carry the same edits** | Explicitly called out by the FFmpeg checklist |
| No claim of platform endorsement or certification | Spec §4.1, §28.8 |

---

## 7. PROHIBITED-COMPONENT SCAN (G-3)

Automated in Phase 12. **Fails the build**, never warns.

Checks:

1. The shipped `ffprobe`'s reported configuration contains **no** `--enable-gpl` and
   **no** `--enable-nonfree`. Output captured verbatim into the audit record.
2. No component from the prohibited list is present, by configuration string or by binary
   inspection:

```
avisynth     frei0r       libcdio      libdavs2     libdvdnav    libdvdread
librubberband             libvidstab   libx264      libx265      libxavs
libxavs2     libxvid      libsmbclient
decklink     libfdk-aac   libmpeghdec  libnpp       cuda-nvcc    cuda-sdk
OpenSSL (incompatible combinations)
```

This is exactly FFmpeg's own `EXTERNAL_LIBRARY_GPL_LIST`, `EXTERNAL_LIBRARY_GPLV3_LIST`,
`EXTERNAL_LIBRARY_NONFREE_LIST` and `HWACCEL_LIBRARY_NONFREE_LIST`. Enabling any of them
forces `--enable-gpl` or makes the binary unredistributable — the two outcomes that
actually matter.

**Removed from this list on 2026-08-09 (SPEC LOCK), with evidence:**

| Component | Was listed as | Corrected classification | Evidence |
| --- | --- | --- | --- |
| `gmp` | prohibited (LGPLv3) | **permitted** under `--enable-version3` | FFmpeg `LICENSE.md`: *"The following libraries are under LGPL version 3: gmp, libaribb24, liblensfun."* Permitted by §2.0. |
| `libaribb24` | prohibited (LGPLv3) | **permitted** under `--enable-version3` | As above. |
| `liblensfun` | prohibited (LGPLv3) | **permitted** under `--enable-version3` | As above. |
| `libzvbi` | prohibited (**"GPL-2+"**) | **permitted** — the source-pack classification was **stale** | See §7.1. |

### 7.1 libzvbi — stale classification corrected

The source pack recorded libzvbi as **GPL-2+**, which would have forced `--enable-gpl`.
FFmpeg's own `configure` (9.0, line 7510) shows otherwise:

```
enabled libzvbi && require_pkg_config libzvbi zvbi-0.2 libzvbi.h vbi_decoder_new &&
  { test_cpp_condition libzvbi.h "VBI_VERSION_MAJOR > 0 || VBI_VERSION_MINOR > 2 ||
      VBI_VERSION_MINOR == 2 && VBI_VERSION_MICRO >= 28" ||
    enabled gpl || die "ERROR: libzvbi requires version 0.2.28 or --enable-gpl."; }
```

Read that carefully: `--enable-gpl` is demanded **only** for libzvbi *below* 0.2.28.
libzvbi relicensed from GPL-2+ to **LGPL-2.1-or-later** at 0.2.28, and FFmpeg encodes
exactly that boundary. Corroborating: libzvbi appears in neither
`EXTERNAL_LIBRARY_GPL_LIST` (configure lines 2029–2043) nor the GPL-v2 list in
FFmpeg's `LICENSE.md`.

**Therefore:** a build that enables libzvbi *without* `--enable-gpl` has, by FFmpeg's own
check, linked the LGPL version. The verified BtbN build does exactly that.

**This correction is evidence-led, not convenience-led.** The prohibition was not removed
to make a gate pass — it was removed because the authoritative source shows it was
mis-recorded, and the safety property it was protecting (*no GPL component*) is already
enforced directly by the `--enable-gpl` check, which remains absolute.

3. **No `ffmpeg.exe`** anywhere in the package.
4. No shared-library filename is obfuscated.
5. The shipped MediaInfo is **not** a GUI build and **does not** include libcurl.
6. `licenses/` exists and is populated.

---

## 8. THE COMPLETE RELEASE GATE

All gates are **blocking**. No release proceeds with any gate open.

| Gate | Condition | Automated? |
| --- | --- | --- |
| **G-1** | `DEPENDENCY-MANIFEST` complete; every checksum matches the shipped file | Yes |
| **G-2** | `THIRD-PARTY-NOTICES` covers every manifest entry with the correct notice form | Yes |
| **G-3** | Prohibited-component scan clean; no `ffmpeg.exe` | Yes |
| **G-4** | Shipped ffprobe confirmed LGPL shared (no `--enable-gpl`, no `--enable-nonfree`, no prohibited component) **and its licence version recorded** (v2.1 or v3, per `--enable-version3`) | Yes |
| **G-5** | Version-matched FFmpeg source archived and same-server hosting confirmed | Partly — archiving and correspondence are fully automated (`packaging/verify_source.py`); **hosting is a human action**. See `CORRESPONDING-SOURCE-PLAN.md`. |
| **G-6** | Configure line / build recipe recorded and shipped | Yes |
| **G-7** | DLL names unobfuscated | Yes |
| **G-8** | EULA carve-outs present; translation requirement recorded | Manual |
| **G-9** | MediaInfo BSD + ZenLib zlib notices present; notice list matches the shipped binary's **actual** compiled feature set | Partly |
| **G-10** | Third-party binaries from official channels, published checksums verified | Yes |
| **G-11** | Application, first-party binaries and installer Authenticode-signed | Yes |
| **G-12** | **Attorney review of licence, EULA, notices and build manifest complete** | **No — blocking, human** |
| **G-13** | GUI-framework licence posture documented and satisfied (shared-library mechanism demonstrated; LGPL-3.0 text and notices shipped) | Partly |

### 8.1 Gate ordering

```
Phase 1  ──► GATE-1   ffprobe build conforms
Phase 3  ──► GATE-2   severity guard proven
before P6 ─► GATE-3   GUI licence question resolved; ATTORNEY ENGAGEMENT STARTS
Phase 10 ─► GATE-4   failure handling proven
Phase 12 ─► GATE-5   G-1…G-11, G-13 pass; G-12 initiated
Phase 13 ─► GATE-6   clean-machine validation passes AND G-12 complete
```

**Attorney engagement starts at GATE-3, not at Phase 12.** G-12's turnaround is the most
likely schedule risk in the whole plan, and it is the one that cannot be accelerated by
engineering effort.

---

## 9. ONGOING OBLIGATIONS AFTER RELEASE

| Obligation | Trigger |
| --- | --- |
| Keep corresponding FFmpeg source hosted and version-matched | For as long as the binary is distributed |
| Re-run the whole gate on **any** inspector version change | Every update |
| Re-run the gate on any dependency addition or version change | Every update |
| Re-verify preset sources | Every 6 months, or on a known platform documentation change |
| Re-verify checksums when re-fetching binaries | Every build |
| Keep pinned inspector versions current for security | Ongoing — process isolation limits blast radius but is not a sandbox |

---

## 10. RESIDUAL RISKS — RECORDED, NOT RESOLVED

Stated plainly so no reader mistakes this checklist for certainty:

| # | Risk |
| --- | --- |
| R-1 | **"Corresponds exactly"** for third-party binaries: relying on a distributor's published source and recipe is standard practice, but it is trust in a build we did not produce. Mitigated by archiving the exact tarball and config. |
| R-2 | Whether **re-signing** third-party DLLs with our certificate counts as "modification". Conservative view: signing is not modification of the code. **Confirm with counsel.** |
| R-3 | The **subprocess / "mere aggregation"** line is, in the FSF's own words, *"a legal question, which ultimately judges will decide."* Process isolation is strong but not adjudicated for this exact scenario. |
| R-4 | **Minimal decode** for HDR side data technically invokes a decoder. Whether inspection-only decode implicates AVC/HEVC decode patents is untested and jurisdiction-dependent. Avoidable if Phase 1 finds MediaInfo sufficient. |
| R-5 | **LGPLv3 Qt in a frozen Python bundle** — the compliance route is plausible, not settled. G-13 + G-12, with GATE-3 as the early checkpoint. |
| R-6 | **PyInstaller bootloader exception** scope as used here. Attorney item (Q-2). |
| R-7 | **Patent-pool dynamics**: AVC and HEVC royalty structures are being restructured upward. These affect encoders and decoders shipped for use, not inspection tools — but confirm scope with counsel if decode-for-inspection is retained. |
| R-8 | **Trademark**: "PreflightQC" is a working name with no clearance claimed. Third-party marks (Instagram, Meta, TikTok, YouTube, LinkedIn, MediaInfo, FFmpeg) are used descriptively only; no endorsement may be implied. |
| R-9 | **MediaInfo Windows runtime**: MediaArea's build is statically linked to the multithreaded C++ runtime and so generally needs no separate MSVC redistributable — **verify against the pinned build** rather than assuming. |

**None of these risks is closed by this document. G-12 exists precisely because they are
not.**
