# Source material — MediaInfo licensing and capability

| Item | Value |
| --- | --- |
| Document | `MediaInfo 26_05 Licensing and Technical Due-Diligence for PreflightQC.pdf` |
| Access date | August 2026 |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §7 |
| Gate document | `docs/licensing/LICENSING-GATE-V1.md` |
| Verdict | **APPROVED WITH CONDITIONS** |

## Summary

MediaInfo 26.05 (released 2026-05-12) is licensed **BSD-2-Clause**; ZenLib (`libzen`) is
**zlib**-licensed. Both are permissive, allow closed-source commercial redistribution,
require no source disclosure, and impose no copyleft — subject only to reproducing the
copyright notice/disclaimer, or MediaArea's short-form attribution sentence, in binary
distributions.

MediaInfo technically exposes every metadata field PreflightQC requires.

## Hard constraints

| Constraint | Reason |
| --- | --- |
| **Version ≥ 0.7.63 only** (pinned: 26.05) | Up to 0.7.62 the library was LGPL and the GUI/CLI were GPL. Those versions carry copyleft obligations incompatible with a closed-source product. |
| **Do not ship the GUI** | It links Qt or wxWidgets, reintroducing toolkit licence obligations and potential copyleft. |
| **Do not enable the libcurl network feature** | Enlarges the third-party notice obligation (curl, typically OpenSSL/libssh2/Brotli) for no benefit to a local-only tool. |
| **Official channels only** | `mediaarea.net` or the official MediaArea GitHub releases, verified by SHA-256. Third-party DLL-download sites are unsafe. |
| **Sign your own bundle** | Authenticode signing status of the official `MediaInfo.dll` could not be confirmed. Treat as unsigned. |

## Documented limitations that constrain rules

- **Scan type / scan order** — MediaInfo reads container and stream flags, **not pixels**.
  Mislabelled or soft-telecined files can report misleading values. Advisory only.
- **Dolby Vision in raw HEVC** (NALU type 62) historically not reported (MediaInfoLib
  issue #1482).
- **HLG** can be mis-labelled where SMPTE ST 2086 metadata is present (MediaInfo #833).
- **MaxCLL / MaxFALL** are present only if the encoder actually wrote them — they may be
  absent from a perfectly valid HDR file.
- **Bitrate** is reliable when signalled; otherwise estimated from size ÷ duration.

## CLI vs library

The document recommends the **library** on engineering grounds, while noting that
**subprocess isolation is a genuine security and stability advantage for a QC tool
ingesting untrusted customer files**. Licensing favours neither (both BSD-2-Clause;
linking mode is legally irrelevant under BSD).

The FFmpeg research independently proposes the **CLI**. This tension is recorded in
register §7.2 and resolved on engineering grounds in
`docs/architecture/ARCHITECTURE-V1.md`.

## Do not alter

This PDF is the evidentiary record behind PreflightQC's MediaInfo licensing posture.
