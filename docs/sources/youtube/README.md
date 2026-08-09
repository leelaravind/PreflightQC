# Source material — YouTube / YouTube Shorts

| Item | Value |
| --- | --- |
| Document | `PreflightQC Asset Research_ YouTube Video Upload Specifications (August 2026).pdf` |
| Access date | 2026-08-09 (`hl=en`, US English) |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §3 |
| Coverage | **STRONG**, but almost entirely as *recommendations* |

## The defining finding

YouTube publishes almost every encoding parameter — MP4 container, H.264 High Profile,
closed GOP, CABAC, 2 B-frames, 4:2:0 chroma, AAC-LC, 48 kHz, and the full per-resolution
bitrate tables — as **RECOMMENDED ENCODING, not as hard requirements**.

PreflightQC must therefore treat nearly all of it as WARN/INFO and must **never FAIL** a
file for violating it.

The only file-measurable FAIL conditions that survive are:

1. Container / file type not on the supported-formats list.
2. File size > 256 GB.

(YouTube's other hard limits — title length, description byte length, tag length — are
file-external API metadata constraints, not properties of the video file, and are out of
V1 scope per spec §20.1.)

## Shorts

YouTube classifies Shorts on exactly two measurable properties: **aspect ratio** (square
or vertical, ≤ 1:1) and **duration** (≤ 3 minutes for standard-channel uploads on/after
15 October 2024). No separate Shorts encoding, codec, bitrate, file-size, or
minimum-resolution spec is published.

**Standard-upload encoding rules must not be ported into Shorts FAIL rules.**

## HDR

HDR is the only area with concrete testable requirements (10/12-bit, Rec.2020 primaries,
Rec.2020 non-constant-luminance matrix, PQ or HLG transfer, HDR metadata present in codec
or container). These are **conditional** on HDR intent and are not universal rules for SDR
uploads.

## Presets derived

`youtube_standard`, `youtube_shorts`.

## Excluded from FAIL logic

All live-streaming encoder settings (CBR, keyframe ≤ 2 s, RTMPS/HLS, HEVC-over-RTMP HDR).
These are LIVE-only and must never be applied to file-upload QA.

## Do not alter

This PDF is the evidentiary record behind every YouTube rule PreflightQC ships.
