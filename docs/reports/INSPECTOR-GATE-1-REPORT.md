# PREFLIGHTQC — INSPECTOR DEPENDENCY AND GATE-1 REPORT

> **AMENDMENT NOTE (2026-08-09, added after this report was written).** Gate G-12 was
> amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing &
> compliance risk acceptance** — see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`.
> Statements below describing attorney review as an absolute release prerequisite record
> the gate as it stood when this report was written and are preserved unchanged.
> **No attorney review has occurred, and no legal clearance is claimed.**

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Task | Verify supplied inspector dependencies and execute Phase 1 / GATE-1 |
| Authority | `docs/planning/IMPLEMENTATION-PLAN-V1.md` §2, §16.1; `docs/licensing/LICENSING-GATE-V1.md` (as amended) |
| **Result** | **GATE-1 PASS** — engineering gate cleared |
| ffprobe | **APPROVED** — `n8.1.2-34-g9b6c8969e0-20260809`, LGPL-3.0-or-later |
| MediaInfo | **APPROVED** — 26.05, BSD-2-Clause |
| Legal gates | **G-12 and G-13 remain OPEN.** No clearance claimed. |
| Downloads | **None.** Nothing fetched from any network. |

> This report supersedes the earlier BLOCKED revision. The block was resolved by the
> authorised LGPLv3 SPEC LOCK amendment — see `docs/reports/LGPLV3-SPEC-LOCK-REPORT.md`.

---

## 1. PACKAGES DETECTED

| Package | Size | SHA-256 (as supplied) |
| --- | --- | --- |
| `ffmpeg-n8.1-latest-win64-lgpl-shared-8.1.zip` | 70,704,115 | `6d4afe797a68af283ed42254827027f7d56940ba6c9e37ebed9c0e87a9e0c54c` |
| `MediaInfo_CLI_26.05_Windows_x64.zip` | 4,136,659 | `f7f80620ce6d14f4995f0de6f98e3ef18ad29496db01899571152ee3311229f9` |
| `ffmpeg-9.0.tar.xz` (source; used only as classification evidence) | 12,032,020 | `7f607a00dd0d28a729d5a4811205812eef01cf6ef6155025febb6f36a9062d52` |

**These are "as supplied" hashes.** They prove what was inspected, not authenticity. Only
a comparison against the publishers' own checksum files does that, and it has **not** been
made — `published_sha256` remains `UNSET` in `packaging/binaries.lock.json`.

Pre-extraction identity check on the FFmpeg archive: filename contains
`win64-lgpl-shared` ✓, ZIP format ✓, contains `bin/ffprobe.exe` ✓, ships shared `libav*`
DLLs (not static) ✓.

---

## 2. FFPROBE — **APPROVED**

### 2.1 Identity

| Property | Value |
| --- | --- |
| Version | `n8.1.2-34-g9b6c8969e0-20260809` |
| Libraries | libavutil 60.26.102 · libavcodec 62.28.102 · libavformat 62.12.102 · libavdevice 62.3.102 · libavfilter 11.14.102 · libswscale 9.5.102 · libswresample 6.3.102 |
| Architecture | **x86-64**, verified from the PE header — not inferred from the filename |
| Built with | gcc 15.2.0 (crosstool-NG 1.28.0.23_185f348), `x86_64-w64-mingw32` |
| Licence | **LGPL-3.0-or-later** (`--enable-version3`; bundled `LICENSE.txt` is the LGPLv3 text) |
| Runs from `third-party/bin/` | **Yes** |

### 2.2 GPL / nonfree / prohibited-component checks — **ALL PASS**

| Check | Result |
| --- | --- |
| `--enable-gpl` | **absent** |
| `--enable-nonfree` | **absent** |
| Shared build | **yes** (`--enable-shared --disable-static`) |
| Prohibited components enabled | **none** |
| Licence version detected and accepted | **LGPL-3.0-or-later** |

Every library in FFmpeg's `EXTERNAL_LIBRARY_GPL_LIST` is explicitly disabled in this
build: `--disable-libx264 --disable-libx265 --disable-libxvid --disable-libxavs2
--disable-libdavs2 --disable-frei0r --disable-librubberband --disable-libvidstab
--disable-avisynth --disable-libdvdread --disable-libdvdnav`, plus `--disable-libfdk-aac`
from the nonfree list.

An independent corroboration surfaced during media generation: the `interlace` filter is
**absent** from this build. That filter is GPL-only, so its absence is direct behavioural
evidence that no GPL component is present.

`gmp`, `libaribb24` and `libzvbi` are enabled and are **permitted** under the amendment —
see `LGPLV3-SPEC-LOCK-REPORT.md` §1 and §2.

### 2.3 DLL inventory — resolved from the PE import table, not guessed

`ffprobe.exe` imports **all seven** libav DLLs directly, so all seven are genuinely
required.

| File | SHA-256 |
| --- | --- |
| `ffprobe.exe` | `383cd95c1884aa34feb70592762ee43199e9ae05c61ef06f6c3e60f6292cf4dd` |
| `avcodec-62.dll` | `9875527c7917979261985c893e402011f46aab692cce7071cb00ac9332326975` |
| `avdevice-62.dll` | `208ca6c8d17303ac0c90624583cdb8368ed1fa28f7876cd7d9d4074fdfb2544a` |
| `avfilter-11.dll` | `1ba6cdc114ff7f8d47d86fb6c9c3a76b885e1a9e655eb7f753d3374edef02d10` |
| `avformat-62.dll` | `e11791fdba4ff6ad5f22538b233995ee258aa37dd29e4c48743f40b03d89fd60` |
| `avutil-60.dll` | `59503fad7e49016a2f0753b01558dce1c3991bedd5c1b8f33b51f4456225c417` |
| `swresample-6.dll` | `03b8538a6834cd4442d799f7efc727b63d446b1793b0bc2561829516dede9324` |
| `swscale-9.dll` | `3a4b2d55520a9307eb1a5615ee994e65e04d6428cff16af349c40e8b9fd15667` |

All other imports are Windows system libraries and are not redistributed.

**Excluded, as required:** `ffmpeg.exe`, `ffplay.exe`, `include/`, `lib/`, `doc/`,
`presets/`. A test asserts no encoder sits beside the inspectors.

---

## 3. MEDIAINFO — **APPROVED**

| Property | Value |
| --- | --- |
| Version | **26.05** (`MediaInfoLib - v26.05`) |
| Architecture | **x86-64** (PE header) |
| Package | CLI, Windows x64 — no GUI present |
| Installed | `MediaInfo.exe`, SHA-256 `30f2828a45a1895b033c3cd7784581033327e7b393033c55f4a03bb15cab0d89` |
| Licence | BSD-2-Clause (MediaInfo) + zlib (ZenLib) |

**The libcurl decision.** The archive ships `LIBCURL.DLL`. The PE import table of
`MediaInfo.exe` shows its only imports are `KERNEL32.dll` and `SHELL32.dll` — libcurl is
an optional sidecar, not a hard dependency. It was **deliberately not installed**, and
MediaInfo runs correctly without it, keeping curl (and typically OpenSSL/libssh2/Brotli)
entirely out of the notice obligation. Also excluded: `Plugin/`, `Contrib/`, `History.txt`,
`ReadMe.txt`.

Licence texts captured to `third-party/licenses/`.

---

## 4. REAL MEDIA TESTED

15 files, generated with the **development-only** FFmpeg encoder from the same archive
(test strategy §3.2 permits this; the encoder is never bundled and never entered
`third-party/bin/`).

| # | File | Purpose |
| --- | --- | --- |
| 01 | `01_h264_1080x1920_30_aac.mp4` | conformant vertical H.264 + AAC, 30 fps, faststart |
| 02 | `02_h264_no_audio.mp4` | **no audio stream** |
| 03 | `03_h264_1920x1080_25.mp4` | landscape 16:9, 25 fps |
| 04 | `04_anamorphic_sar43.mp4` | **SAR 4:3** — displayed AR ≠ w/h |
| 05 | `05_vp9.webm` | VP9 in WebM |
| 06 | `06_h264.mov` | MOV container |
| 07 | `07_interlaced_tff.mp4` | interlaced signalling (top field first) |
| 08 | `08_hdr_pq_10bit.webm` | 10-bit, BT.2020 |
| 09 | `09_rotated90.mp4` | rotation metadata |
| 10 | `10_mono_44k.mp4` | mono, 44.1 kHz |
| 90 | `90_truncated.mp4` | truncated mid-`mdat` |
| 91 | `91_header_only.mp4` | header only, no data |
| 92 | `92_not_media.mp4` | not a media file |
| 93 | `93_zero_bytes.mp4` | zero bytes |
| 94 | `94_corrupt_moov.mp4` | `moov` atom destroyed |

Full per-file output: `spikes/phase1-findings.json`.

---

## 5. METADATA VERIFIED / UNDETERMINED / CONFLICTS

45 model properties were resolved against every file. **29 of 45 were KNOWN on 10 or more
of the 15 files.** Nothing was fabricated.

### 5.1 Verified against real output

| Category | Confirmed |
| --- | --- |
| File | size (filesystem ground truth), duration |
| Container | format family, major brand, stream counts, overall bitrate, **fast start** |
| Video | codec, profile, level, width/height, coded dimensions, **SAR**, **computed DAR**, rotation, frame rate, frame-rate mode, bitrate, pixel format, bit depth, chroma subsampling, scan type |
| Audio | presence, codec, sample rate, channels, channel layout, bitrate, duration |

Specific behaviours proven with real files:

- **Anamorphic geometry** — a real 1440×1080 file with SAR 4:3 yields a displayed DAR of
  **16:9**, not 4:3. Aspect-ratio rules judge what the viewer sees.
- **No-audio** — reports absence explicitly; no audio rule fails.
- **Fast start** — readable via MediaInfo's `IsStreamable`, which is the reason MediaInfo
  is in the design at all. ffprobe has no equivalent field.
- **Mono 44.1 kHz** — channels and sample rate read correctly.

### 5.2 Always UNDETERMINED — and correctly so

Eight properties were UNDETERMINED on all 15 files. **None is a defect**; each is an
honestly-reported gap:

| Property | Why |
| --- | --- |
| `container.edit_lists_present` | Register gap G-1 — needs atom-level inspection, not performed in V1 |
| `video.gop_closed` | Register gap G-2 — needs packet-level analysis |
| `video.hdr_format`, `video.dolby_vision`, `video.max_cll`, `video.max_fall` | No file in the corpus carries mastering-display or DV metadata |
| `video.colour_primaries`, `video.transfer_characteristics` | **ffprobe genuinely does not report these** for the VP9-in-WebM HDR encode — verified by reading its raw output directly |

The last row deserves emphasis. The HDR file *was* encoded with
`-color_primaries bt2020 -color_trc smpte2084`, yet ffprobe reports both as absent.
PreflightQC reports UNDETERMINED rather than echoing what we intended the file to contain.
**That is the required behaviour**, and it is the difference between a QC tool and a
guess.

### 5.3 Inspector conflicts

**Zero conflicts remain across all 15 real files** — after fixing four classes of
*spurious* conflict that the spike uncovered (§6.1). Genuine disagreement is still
preserved and tested.

---

## 6. DEFECTS FOUND BY GATE-1 AND FIXED

This is what running real binaries bought. All five were invisible to the simulated suite.

### 6.1 Spurious inspector conflicts — the significant one

The two inspectors describe identical facts in different words. All four pairs below were
being reported as **disagreements**:

| Property | ffprobe | MediaInfo |
| --- | --- | --- |
| `container.format` | `{mkv, webm}` (family) | `{webm}` (specific) |
| `video.colour_space` | `bt2020nc` | `BT.2020 non-constant` |
| `video.profile` | `Profile 0` / `Profile 2` | `0` / `2` |
| `audio.channel_layout` | `stereo` / `mono` | `L R` / `M` |

**Why this mattered.** A CONFLICTED field caps rule severity at WARN (spec §10.4). A
purely cosmetic spelling difference would therefore have **silently downgraded a genuine
hard requirement** — LinkedIn CTV's "audio must be 2-channel" would have become a warning
because one tool writes `stereo` and the other writes `L R`.

Fixed by `vocabulary.values_agree()`, which decides *agreement* without changing the
stored value: set-valued properties compare by intersection (a subset is a narrower
description, not a contradiction), and colour matrix / profile / channel layout compare
after canonicalisation. Genuine disagreement still conflicts, and is tested in both
directions.

### 6.2 CONFLICTED fields that never reached the report

`video.profile` and `audio.channel_layout` could become CONFLICTED without being recorded
in diagnostics, so the user would never be told the inspectors disagreed. Both now record.

### 6.3 The build scanner could not tell `--enable-` from `--disable-`

Substring matching flagged twelve components against this build, **ten of them disabled**.
Fixed to parse flags.

### 6.4 The spike harness disagreed with the application

`spikes/probe_matrix.py` had its own duplicate copy of the prohibited list and the same
substring bug — after the amendment it *rejected a build the application accepted*. It now
delegates to the shipped `audit_configuration`, so the two cannot drift again.

### 6.5 MediaInfo version parsed as "MediaInfoLib"

The regex captured the library name, not the version. Now reports 26.05 — the fact that
evidences BSD-era licensing and is printed on every report.

---

## 7. ERROR CASES, BATCH ISOLATION, SOURCE INTEGRITY

Tested with the **real binaries** against genuinely broken files.

| Case | Result |
| --- | --- |
| Truncated mid-`mdat` | Inspected; unreadable properties UNDETERMINED |
| Header only | ffprobe `FILE_UNREADABLE`; MediaInfo partial; batch continues |
| Not a media file | ffprobe `FILE_UNREADABLE`; batch continues |
| Zero bytes | ffprobe `FILE_UNREADABLE`; batch continues |
| Corrupt `moov` | ffprobe `FILE_UNREADABLE`; MediaInfo partial — see below |
| Missing file | `NOT_INSPECTED` with a reason |
| Aggressive timeout (1 ms) against the real binary | Terminated cleanly; no hang, no crash |
| Cancellation | Batch marked partial; every file still reported |
| **Batch isolation** | A 5-file batch mixing healthy and corrupt files completed; all 5 reported in input order; every healthy file still inspected |

**The key guarantee, precisely stated.** Spec §23 forbids failing **for corruption alone**
— not failing on a property that was actually read. A test now enforces the exact
invariant across **every shipped preset**: *every FAIL must rest on a `KNOWN` property.*
A failure resting on an UNDETERMINED value would mean the engine invented the evidence
against the file. None does.

One observation recorded to `docs/FUTURE.md` §3A.1b: `94_corrupt_moov.mp4` legitimately
fails the fast-start rule, because MediaInfo *positively* reports `IsStreamable = No`.
True and spec-compliant, but the user sees "FAIL: fast start" for a file whose real
problem is that it is broken. A degraded-inspection indicator would help; that is a
presentation change, not a severity change.

**Source integrity.** SHA-256, size and mtime captured for all 15 files before and after
running **three different presets** over the whole corpus with the real binaries.
**Byte-identical.** No source file was opened for writing.

---

## 8. TEST RESULTS

| Suite | Result |
| --- | --- |
| Phase 1 build audit (`spikes/probe_matrix.py`) | **PASS** — licence LGPL-3.0-or-later |
| Phase 1 verification (`spikes/phase1_verify.py`) | **PASS** — 15/15 samples processed, matrix emitted |
| Real-binary integration (`tests/integration/test_real_inspectors.py`) | **32 passed** |
| Inspector equivalence (new) | **19 passed** |
| Build-configuration audit | **31 passed** |
| **Full regression** | **1037 passed, 3 skipped, 0 failed** |
| `mypy` | Success — no issues in 52 source files |
| `ruff check` | All checks passed |
| Documentation invariants | All 6 hold |

Growth: 957 → 1037 tests. **No test was weakened, skipped or relaxed to clear the gate.**
The three skips are boundary-derivation cases for rule shapes with no derivable violating
value, each skipped with an explicit reason.

---

## 9. PHASE 1 ACCEPTANCE CRITERIA

| # | Criterion | Result |
| --- | --- | --- |
| P1-A1 | Every spec §9 field has a determinability verdict | **PASS** — 45 properties × 15 files, in `spikes/phase1-findings.json` |
| P1-A2 | Precedence table populated and justified by observation | **PASS** — validated against real output; MediaInfo confirmed as the only source of fast start; zero spurious conflicts remain |
| P1-A3 | Q-3 (CLI vs library) decided and recorded | **PASS** — **CLI subprocess**, confirmed working; process isolation kept a corrupt-file batch alive |
| P1-A4 | HDR strategy decided and recorded | **PASS** — MediaInfo `HDR_Format` suffices for V1 reporting; the bounded first-frame read stays **disabled by default**, so the decoder is never engaged (Q-6 resolved in the preferred direction) |
| P1-A5 | Every reachable §23 condition observed with real binaries | **PASS** — §7 |
| P1-A6 | ffprobe configuration contains no `--enable-gpl` / `--enable-nonfree` / prohibited component, captured verbatim | **PASS** — recorded in `packaging/binaries.lock.json` |
| P1-A7 | Gaps G-1…G-6 confirmed or refuted by observation | **PASS** — G-1 and G-2 confirmed unmeasurable; G-3 (scan type) and G-5 (frame-rate mode) confirmed **readable** via MediaInfo on real files; G-4 (loudness) unchanged; G-6 avoided entirely |

**All seven Phase 1 acceptance criteria pass using real binaries.**

---

## 10. REMAINING GATES AND BLOCKERS

**Open, unchanged by this work:**

| # | Gate | Status |
| --- | --- | --- |
| **G-12** | Attorney review of licence, EULA and notices | **OPEN — hard release gate. Not started, not marked complete.** |
| **G-13** | GUI-framework licence posture (LGPLv3 Qt) | **OPEN** — now the *same* licence family as FFmpeg, so one legal conversation rather than two |
| G-1 / G-10 | Publisher checksums | **UNSET** — a human must compare the as-supplied hashes against BtbN's and MediaArea's published checksums |
| G-5 | Version-matched FFmpeg **source** for the shipped binary | **NOT MET** — the supplied tarball is 9.0; the shipped binary is **8.1.2**. Matching 8.1 source must be archived and hosted |
| G-8 | EULA carve-outs (naming LGPLv3) | **NOT STARTED** |
| G-11 | Authenticode certificate | **NOT AVAILABLE** |
| G-2 / G-3 / G-6 / G-7 | Generated from a built package | **PENDING Phase 11** — no package exists yet |
| Phase 13 | Clean Windows 10 / 11 validation | **NOT STARTED** |

> **G-5 is worth flagging.** The `ffmpeg-9.0.tar.xz` on hand does **not** correspond to the
> shipped `n8.1.2` binary. Corresponding source must match the binary, so 8.1 source is
> required before release.

---

## 11. SPEC DEVIATIONS

**NONE.**

The LGPLv3 amendment was explicitly authorised and executed via the SPEC LOCK procedure,
with primary-source evidence, and is reported separately in
`docs/reports/LGPLV3-SPEC-LOCK-REPORT.md`.

---

## 12. NEXT AUTHORISED STEP

GATE-1 is cleared, so the plan's next phase is **Phase 11 (Windows packaging)** — Phases
2–10 are already complete. Before release, the gates in §10 must close, with **G-12 the
long-lead item.**

Per instruction, work stopped at GATE-1.

---

## 13. `git status --short`

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
?? docs/planning/SPIKE-01-INSPECTOR-FINDINGS.md
?? docs/reports/
?? packaging/binaries.lock.json
?? packaging/generate_manifest.py
?? packaging/layout_check.py
?? packaging/preflightqc.spec
?? packaging/scan_prohibited.py
?? presets/
?? pyproject.toml
?? requirements.lock
?? spikes/
?? src/preflightqc/
?? tests/adapters/
?? tests/architecture/
?? tests/conftest.py
?? tests/core/
?? tests/docs/
?? tests/factories.py
?? tests/golden/
?? tests/integration/
?? tests/normalise/
?? tests/orchestration/
?? tests/platform/
?? tests/presets/
?? tests/profiles/
?? tests/reporting/
?? tests/results/
?? tests/rules/
?? third-party/licenses/
?? tools/
```

`HEAD` is still `b353181 Initialize repository: V1 spec lock, source pack, and
implementation plan` — the Phase-B planning commit. **Nothing from the implementation,
the amendment or this gate has been committed.**

`third-party/bin/`, the supplied archives and `spikes/samples/` do not appear — all are
git-ignored by design, so the binaries and the generated corpus are preserved on disk but
never committed.

**Not committed. Not pushed. Not published. Not released.**

---

## GATE-1: **PASS** — engineering gate cleared; legal/manual release gates remain open
