# SPIKE 01 — INSPECTOR FINDINGS

| Field | Value |
| --- | --- |
| Phase | 1 — Inspector technical spike |
| Status | **BLOCKED — GATE-1 NOT PASSED** |
| Date | 2026-08-09 |
| Harness | `spikes/probe_matrix.py` (written, runnable, verified to fail closed) |

---

## 1. GATE-1 STATUS: BLOCKED

**The spike could not be executed.** Neither inspector binary is present on the build
machine, and per the implementation plan Phase 1 prerequisites, **this phase downloads
nothing by design** — the operator must supply checksum-verified binaries.

```
$ python spikes/probe_matrix.py
GATE-1 BLOCKED: inspector binaries not present in third-party/bin/: ffprobe, mediainfo
The operator must supply checksum-verified binaries. This script downloads nothing by design.
exit 2
```

Verified absent:

| Required | Expected location | Status |
| --- | --- | --- |
| `ffprobe` (unmodified BtbN `win64-lgpl-shared`) | `third-party/bin/ffprobe.exe` | **ABSENT** |
| MediaInfo ≥ 0.7.63 (CLI or library) | `third-party/bin/mediainfo.exe` | **ABSENT** |
| Sample media set | `spikes/samples/` | **ABSENT** |

Also confirmed absent from the machine's `PATH` — which is correct and irrelevant, since
the application never consults `PATH` (spec §22.4), but is recorded so the block is not
mistaken for a lookup bug.

### 1.1 What GATE-1 requires

Per implementation plan §16.1, GATE-1 passes only when the obtained ffprobe build is
confirmed **LGPL shared**, with no `--enable-gpl`, no `--enable-nonfree`, and none of the
prohibited components — with both inspector versions and checksums recorded.

The harness implements this audit (`audit_ffprobe_build()`), scanning `ffprobe -version`
output for all 19 prohibited tokens from `docs/licensing/LICENSING-GATE-V1.md` §7 and
returning a hard failure on any hit. **It has not been able to run.**

### 1.2 Consequence — what proceeded anyway, and why

The plan makes Phase 2 depend on Phase 1 so that the metadata model is built on
*measurement* rather than assumption. With the spike blocked, Phase 2 was built instead
against the **field-mapping and precedence table already documented in
`docs/sources/SOURCE-REGISTER.md` §5**, which was derived from the two dependency research
documents in the source pack.

This is a real, recorded deviation from the plan's dependency order, taken so that the
engine work — the actual product value — was not stalled behind an operator prerequisite.
It is safe in one specific direction and unsafe in another:

| Aspect | Assessment |
| --- | --- |
| **Safe** | The normalised model is deliberately *superset* and three-valued. Any field an inspector turns out not to report simply resolves to `Undetermined`, which the engine already handles as `UNKNOWN`. No rule can become `FAIL` because a field was assumed present. |
| **Safe** | Adapters are tested against **stub executables emitting canned JSON**, which the plan itself specifies for Phase 5. Adapter failure handling is therefore genuinely tested. |
| **UNVERIFIED** | The per-field precedence table (register §5) is documented, not measured. If a real inspector disagrees with the documented behaviour, precedence entries may need revision. Precedence is **data** (`normalise/precedence.py`), so revision is a table edit, not a rewrite. |
| **UNVERIFIED** | Gaps G-1…G-6 are implemented as documented (`UNDETERMINED` → `UNKNOWN`). Whether each is genuinely undeterminable in practice is unconfirmed. **The failure direction is conservative**: a gap that turns out to be measurable currently produces `UNKNOWN` rather than a wrong verdict. |
| **UNVERIFIED** | Q-6 — whether MediaInfo's `HDR_Format` alone suffices for V1 HDR findings, which would let us never engage the decoder. Implemented as if it does: **the bounded first-frame HDR read is implemented but disabled by default.** |

---

## 2. OPEN QUESTIONS THIS SPIKE WAS MEANT TO CLOSE

| # | Question | Status | Interim decision |
| --- | --- | --- | --- |
| Q-3 | MediaInfo CLI or library? | **UNRESOLVED** | **CLI subprocess** — as recommended in `ARCHITECTURE-V1.md` §4.3. Adapter interface is identical either way, so reversal costs one module. |
| Q-6 | Is MediaInfo `HDR_Format` alone sufficient for V1 HDR findings? | **UNRESOLVED** | Assumed **yes**. The first-frame read is implemented behind `hdr_first_frame_read`, **default `False`**. The decoder is therefore never engaged in the default configuration, which is the preferred outcome per `LICENSING-GATE-V1.md` §2.6. |
| — | Per-field precedence | **UNVERIFIED** | Documented table from register §5, encoded as data in `normalise/precedence.py`. |
| — | Gaps G-1…G-6 confirmed or refuted | **UNVERIFIED** | Implemented as documented; all resolve to `UNDETERMINED` → `UNKNOWN`. |

---

## 3. TO UNBLOCK GATE-1

1. Obtain `ffprobe.exe` and its `libav*` DLLs from **BtbN FFmpeg-Builds,
   `win64-lgpl-shared`** only. Do **not** use `gyan.dev` (GPLv3) or any static build.
2. Obtain **MediaInfo ≥ 0.7.63** (pinned target 26.05) CLI from `mediaarea.net` or the
   official MediaArea GitHub release. **Not** the GUI. **Not** a libcurl-enabled build.
3. Verify both against their publishers' published checksums.
4. Place them in `third-party/bin/` (git-ignored by design).
5. Place representative sample media in `spikes/samples/`, covering at minimum: H.264 MP4,
   HEVC MP4, VP9 WebM, MOV, an interlaced file, a VFR file, a file with no audio, an HDR
   (PQ or HLG) file, and a deliberately truncated file.
6. Run `python spikes/probe_matrix.py`.
7. If the audit passes, GATE-1 passes. Complete §4 below from the emitted matrix, then
   re-verify the precedence table and the G-1…G-6 verdicts against observation.

---

## 4. FIELD DETERMINABILITY MATRIX — **NOT YET POPULATED**

This table is the spike's primary deliverable and **cannot be completed without the
binaries**. It is left explicitly empty rather than filled with assumptions.

| Field (spec §9) | ffprobe reports? | MediaInfo reports? | Precedence | Measured cost | Verdict |
| --- | --- | --- | --- | --- | --- |
| *(all 37 required fields)* | **PENDING** | **PENDING** | documented, unverified | **PENDING** | **PENDING** |

The harness enumerates all 37 required fields (`REQUIRED_FIELDS` in
`spikes/probe_matrix.py`) and will emit a determinability verdict per field per sample.

---

## 5. §23 FAILURE-CONDITION OBSERVATIONS — **NOT YET POPULATED**

Real-inspector behaviour for corrupt files, unreadable files, permission denial, timeout,
malformed JSON, zero-byte files, oversized files, long paths, and UNC paths is
**PENDING**.

**However**, every one of these conditions *is* implemented and tested at the application
layer against stub executables (`tests/adapters/`, `tests/orchestration/`,
`tests/integration/test_failure_matrix.py`). What is unverified is only how the *real*
binaries signal each condition — not whether PreflightQC handles the signal correctly.

---

## 6. VERSIONS AND CHECKSUMS — **NOT YET RECORDED**

| Component | Version | SHA-256 |
| --- | --- | --- |
| ffprobe | **PENDING** | **PENDING** |
| MediaInfo | **PENDING** | **PENDING** |

These feed the dependency manifest (release gate G-1) and must be recorded before any
release package is produced.
