# Source material — TikTok

| Item | Value |
| --- | --- |
| Document | `TikTok Video Technical Specifications for PreflightQC Offline Deliverable QA_ August 2026 Reference.pdf` |
| Access date | 2026-08-09 |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §2 |
| Coverage | **STRONG** on developer API + ads; **SILENT** on most codec-level detail |

## Coverage summary

Strong on Tier 2 (ads) and Tier 3 (developer API), with verbatim Tier 1 Help Center
confirmation for organic Studio and in-app limits.

Weak or silent — mirroring TikTok's own silence — on: codec profile/level, audio hard
rules, HDR/colour/bit-depth/chroma, faststart, PAR, GOP, loudness, VFR policy, and whether
the API "Video restrictions" table governs in-app uploads. All of these remain UNKNOWN.

## The defining finding

TikTok publishes **four different official numbers** for maximum organic duration and file
size across overlapping upload paths (Camera tools 60 min upload / 10 min record; Studio
30 min; Content Posting API 10 min; Creator Academy 60 min), and a similar four-way split
on file size.

This is a genuine documentation inconsistency, not a research gap. PreflightQC resolves it
by making the **target upload path an explicit preset the user selects**. A single merged
"TikTok" preset is not constructible from the sources.

## Presets derived

`tiktok_content_posting_api`, `tiktok_studio_web`, `tiktok_infeed_auction_nonspark`,
`tiktok_topview_reservation`.

**Not shipped in V1** (values retained in the document): Spark Ads (Pull), Global App
Bundle, Pangle, Carousel, Streaming/Automotive/Video Packages.

## Do not alter

This PDF is the evidentiary record behind every TikTok rule PreflightQC ships.
