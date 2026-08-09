# Source material — Instagram / Meta

| Item | Value |
| --- | --- |
| Document | `PreflightQC_ Instagram and Meta Video Specification Research for Engineering Validation.pdf` |
| Access date | 2026-08-09 |
| Status | **PRESENT** — retained unaltered |
| Register section | `docs/sources/SOURCE-REGISTER.md` §1 |
| Coverage | **PARTIAL** |

## Coverage summary

Tier 1 coverage is COMPLETE and HIGH-confidence for the Instagram Content Publishing API
(Reels + Stories file specs and Reels-tab eligibility), general upload help, Facebook Feed
ad video settings, Instagram Reels length, and the HDR engineering context.

It is PARTIAL / BLOCKED for the per-objective Instagram Ads Guide numeric tables
(JavaScript-rendered; the Reels ad video page body was not extractable).

Two deliberate Tier 1 gaps are confirmed as UNKNOWN and must **not** be filled from
third-party sources:

- **Audio loudness targets** — Meta publishes no LUFS/LKFS/true-peak figure anywhere.
  The −14 LUFS number people cite is a music-streaming norm, not a Meta target.
- **HDR / colour-space input requirements** — Meta accepts HDR and tone-maps server-side,
  but publishes no creator-facing input spec.

## Presets derived

`ig_reels`, `ig_stories`, `ig_feed` (reduced, WARN/INFO-dominant).

**Not shipped:** any Instagram *ad* preset — the Reels ad specification page was blocked.

## Do not alter

This PDF is the evidentiary record behind every Meta rule PreflightQC ships. It must not
be edited, re-exported, or reformatted. Corrections go into the source register with a new
access date, not into this file.
