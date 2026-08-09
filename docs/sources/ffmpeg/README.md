# Source material — FFmpeg / ffprobe licensing and distribution

| Item | Value |
| --- | --- |
| Document | `PreflightQC FFmpeg and ffprobe Dependency Licensing Review for Commercial Distribution.pdf` |
| Access date | August 2026 |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §6 |
| Gate document | `docs/licensing/LICENSING-GATE-V1.md` |
| Verdict | **APPROVED WITH CONDITIONS** |

> This document is engineering research, **not legal advice**. A qualified software-IP
> attorney must review the final architecture, notices, and EULA before commercial
> release. See release gate G-12.

## Summary

Ship an **unmodified, official LGPL-2.1 shared build** of `ffprobe` (and its `libav*`
DLLs), invoke it as a **separate child process**, and bundle **no GPL or nonfree
component**. This keeps PreflightQC closed-source with minimal, well-understood LGPL
obligations.

`ffprobe` alone covers nearly all required metadata. MediaInfo (BSD-2-Clause) is added as
a complementary reader for the few fields `ffprobe` handles weakly — scan-type / field-order
heuristics, and clean Dolby Vision profile / HDR-format naming.

## Locked conditions (all must hold)

1. Unmodified official **LGPL (non-GPL, non-nonfree) shared** build of ffprobe + `libav*`.
   Windows: BtbN `win64-lgpl-shared`.
2. Invoke ffprobe as a **separate process**. Do not statically link or link `libav*` into
   the closed-source app.
3. Bundle **no GPL or nonfree component** — explicitly no `libx264`, `libx265`, `libxvid`,
   `libfdk-aac`, `libnpp`/`cuda-nvcc`, `frei0r`, `libvidstab`, `libzvbi`, `libsmbclient`,
   `libaribb24` — and ship **no `ffmpeg` encoder** in V1.
4. Ship the LGPL-2.1 text + version-matched corresponding FFmpeg source (same-server link)
   + notices. Keep DLL names **unobfuscated**. Edit the EULA per the FFmpeg checklist:
   remove the reverse-engineering ban, disclaim FFmpeg ownership.
5. Add MediaInfo only under BSD-2-Clause with its verbatim attribution sentence.
6. Treat all codec **encoding** as out of scope for V1.
7. **Attorney review** of the final notices, EULA, and build manifest before release.

## Builds that are NOT usable

| Distributor | Why |
| --- | --- |
| `gyan.dev` main Windows builds | "All builds are 64-bit, static and licensed as GPLv3" |
| `evermeet.cx` (macOS) | Built with `--enable-gpl --enable-libx264 --enable-libx265`; also Intel-only |
| Any `--enable-nonfree` build | LICENSE.md: *"will cause the resulting binary to be unredistributable"* |

## The decode nuance

`-show_streams` and `-show_format` parse container and codec-parameter metadata without
decoding. Extracting frame-attached **HDR side data** requires `-show_frames`, which
**does engage the decoder** — in practice `-read_intervals "%+#1"` to read one frame.

Practical patent exposure is very low (inspection, not playback or output) but is **not
formally zero**. AVC US essential patents run to 29 Nov 2027; HEVC well beyond 2030.

PreflightQC therefore bounds this to a **first-frame read only, behind an explicit
setting** (spec §10.5).

## Remaining legal uncertainty (recorded, not resolved)

- Whether relying on a third-party distributor's published source + recipe satisfies LGPL
  §6 "corresponds exactly". Mitigation: **archive the exact source tarball and build
  config** that produced the shipped binaries.
- Whether re-signing the DLLs with your own certificate counts as "modification".
- The subprocess / "mere aggregation" line is, in the FSF's own words, *"a legal question,
  which ultimately judges will decide."*
- Whether inspection-only decode implicates AVC/HEVC decode patents is untested and
  jurisdiction-dependent.

## Do not alter

This PDF is the evidentiary record behind PreflightQC's FFmpeg licensing posture.
