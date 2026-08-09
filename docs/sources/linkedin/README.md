# Source material — LinkedIn

| Item | Value |
| --- | --- |
| Document | `LinkedIn Video Specifications_ Source-Verified Register for PreflightQC Validation Rules (August 2026).pdf` |
| Access date | 2026-08-09 |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §4 |
| Coverage | **SUFFICIENT** for three placements |

## Coverage summary

LinkedIn publishes three separate, numerically deterministic video specifications, each
with a first-party numeric page and (for ads) a corroborating versioned developer API doc.

**Organic and advertising requirements differ enough that they must never be merged.**

| Preset | Envelope |
| --- | --- |
| `linkedin_organic` | up to 5 GB, many containers, 256×144–4096×2304, 10–60 FPS |
| `linkedin_video_ads` | MP4 only, 75 KB–500 MB, 360–1920 px both dimensions, AR 0.563–1.778 ±5% |
| `linkedin_ctv` | MP4/H.264, 16:9, exactly 1920×1080 or 1280×720, 6–60 s, ≥12 Mbps, 48 kHz stereo |

## Out of scope

- **LinkedIn Live** — RTMP/RTMPS streaming ingest. There is no delivered media file to
  inspect.
- **Message / Conversation Ads** — image + banner creative only; no video asset.
- **LinkedIn Learning** — an LMS authoring surface, not a commercial placement.

## The most important conflict

LinkedIn Video Ads maximum file size is **500 MB**, per LinkedIn's own Video Ads
Specifications page and the Microsoft Learn Videos API docs. The **200 MB** figure widely
repeated in third-party blogs is NON-AUTHORITATIVE and likely stale. **Use 500 MB.**

## Two things that must not gate

- **Captions.** Supplied as an external SRT sidecar or burned into pixels. Not reliably
  determinable from the delivered media file.
- **CTV loudness (−23 LUFS).** Requires an `ebur128` decode-and-measure pass, not a static
  metadata field. Out of the V1 inspection cost boundary; ships as UNKNOWN.

## Byte convention

LinkedIn does not state whether its "500 MB" / "5 GB" / "75 KB" figures are binary or
decimal. PreflightQC adopts the **conservative decimal interpretation** so it never passes
a file LinkedIn would reject, and emits a WARN band within ~2% of a ceiling to absorb the
ambiguity. See register §4.5 conflict L-C5.

## Do not alter

This PDF is the evidentiary record behind every LinkedIn rule PreflightQC ships.
