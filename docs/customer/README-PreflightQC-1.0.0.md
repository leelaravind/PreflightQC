# PreflightQC 1.0.0 — README

Thank you for purchasing PreflightQC.

## Product

- PreflightQC, version 1.0.0
- Publisher: ITISYOU
- Requires: Windows 10 x64 or Windows 11 x64 (no macOS, Linux, 32-bit or ARM)
- Installs per-user; no administrator rights required; nothing else to install
  (ffprobe and MediaInfo are bundled)
- Fully offline: your media is processed locally on your PC, PreflightQC does not
  upload your video files, and there is no account, no login, no activation, no
  telemetry and no update checks

## What it does

PreflightQC is a preflight check for video delivery. Add the files you are about to
hand over, choose the destination preset, and every technical rule in that preset is
checked against what your file actually contains. Each check reports one of four
results (shown in the application as PASS / WARN / FAIL / UNKNOWN):

- Pass — the detected value meets the documented requirement.
- Warning — the value misses a documented recommendation or best practice, or an
  eligibility condition; a recommendation never fails a file.
- Fail — the value violates a documented hard requirement.
- Unknown — the platform publishes no requirement for that property, or the property
  could not be read reliably from your file. PreflightQC reports this honestly rather
  than guessing. A file with no readable video stream is reported as inconclusive,
  never as a pass.

## What it checks

Every check below exists in the shipped rule catalogue; nothing here is aspirational.

- Video: codec, profile, width/height, display aspect ratio, frame rate and
  frame-rate mode (constant/variable), bitrate, bit depth, chroma subsampling,
  scan type (progressive/interlaced), colour space/primaries/transfer, HDR and
  Dolby Vision presence, closed GOP
- Audio: codec, bitrate, channels, sample rate, presence, duration
- Container: format, faststart (moov position), edit lists, stream count
- File: duration, size

Properties are read with the bundled ffprobe and MediaInfo; the two readings are
reconciled, and genuine disagreement is surfaced rather than hidden. Source files are
opened read-only and are never modified.

## Included presets (12 presets, 170 rules)

All shipped rules were verified against their published sources on 2026-08-09
(ruleset version 2026-08-09.1). Each preset states its own scope and caveats inside
the application.

LinkedIn

- LinkedIn — Connected TV (CTV) Ads (19 rules) — the strictest LinkedIn envelope:
  exact dimensions, fixed frame-rate set, high minimum bitrate.
- LinkedIn — Organic (Pages / native video) (14 rules) — native video posted to a
  LinkedIn Page; wide envelope with a specific supported-container list.
- LinkedIn — Video Ads (13 rules) — sponsored in-feed video ads: MP4 only, tightly
  bounded dimensions, published aspect-ratio tolerance.

Meta / Instagram

- Instagram Feed video (13 rules) — deliberately advisory: Instagram publishes no
  dedicated file specification for Feed video, so this preset carries no hard
  failures.
- Instagram Reels (22 rules) — Reels via the Content Publishing API, the only
  Instagram surface with precise, file-measurable hard requirements.
- Instagram Stories (19 rules) — same codec/container envelope as Reels with a much
  tighter duration and file-size ceiling.

TikTok

- TikTok — Content Posting API (14 rules) — TikTok's richest machine-readable
  specification: codecs, frame-rate bounds, pixel minimums and maximums.
- TikTok — In-Feed Auction ad (Non-Spark) (12 rules) — paid In-Feed Auction
  placement with Ads Manager's concrete numeric limits.
- TikTok — Studio / web upload (8 rules) — organic web upload: fewer containers, a
  resolution floor, larger size and duration ceilings.
- TikTok — TopView / Reservation ad (9 rules) — the tightest TikTok envelope: short
  fixed duration window, higher minimum bitrate.

YouTube

- YouTube — Shorts (6 rules) — deliberately minimal: YouTube classifies a Short on
  two measurable properties and publishes no separate Shorts encoding specification.
- YouTube — Standard upload (21 rules) — YouTube publishes almost every encoding
  parameter as a recommendation, so this preset warns by design rather than failing.

## Rule transparency

Each preset is a set of technical checks derived from documented platform delivery
requirements. For every finding, PreflightQC shows the detected value, the expected
value, a plain explanation, and the supporting source reference — the platform
document's title, URL, the date it was last verified, and a confidence level. Where a
platform documents nothing, the result says so.

## Reporting

- Batch checking with per-file results, filtering by outcome and a summary readout
  (one preset per batch)
- Self-contained HTML report export — the report opens offline and contains no
  external links that fetch anything
- CSV export for spreadsheets and pipelines

## Limitations

- PreflightQC is a preflight/QC aid. A Pass does not guarantee acceptance by any
  platform, broadcaster, publisher or advertising service.
- Platform requirements can change without notice, and platforms apply rules they do
  not publish. Every rule carries the date its source was last verified.
- Checks may report Unknown where file metadata cannot reliably establish the
  required fact.
- Inspection is metadata-level via the bundled inspectors; audio loudness is not
  measured. The first video/audio stream is judged.
- Custom profiles are file-based in this version (place a profile JSON under
  %LOCALAPPDATA%\PreflightQC\profiles); there is no in-app editor.

## Privacy

All processing happens locally on your machine. PreflightQC does not upload your
source video files. There is no telemetry, no analytics, no account and no update
check. Reports are written only where you choose to save them; profiles and settings
live under %LOCALAPPDATA%\PreflightQC.

## Windows SmartScreen (please read before installing)

This 1.0.0 release is intentionally not digitally signed. Windows SmartScreen will
show an "Unknown Publisher" warning; choose "More info" then "Run anyway" to proceed.
The warning reflects the unsigned installer — it does not mean the file is corrupted.
We recommend verifying your download against the official SHA-256 published on the
product page before installing:

    Get-FileHash PreflightQC-1.0.0-setup.exe -Algorithm SHA256

Official installer SHA-256 for this release:

    5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504

If the value does not match exactly, do not install; re-download and verify again.

## Version

Version 1.0.0 — initial commercial release.

Ships the 12 presets and 170 rules listed above, batch checking, HTML and CSV report
export, source-traceable findings, bundled ffprobe and MediaInfo inspectors, and
fully offline operation. Third-party licence texts and notices are installed with the
application in its "licenses" folder and shown during installation.

## Roadmap

Future releases are planned to expand preset and rule-management capabilities,
including tools for creating and managing custom presets and rules.

## Support and refunds

Support: itisyou.app/products/preflightqc/support — please include your Windows
version and, where the problem concerns a specific file, the exported HTML report.

Refunds: if PreflightQC is not right for you, request a refund within 7 calendar days
of purchase. Eligible refunds normally receive the full purchase price and are
processed through the merchant of record or platform you bought from, using their
refund mechanism. Nothing in this policy limits your statutory rights, and where the
platform's own refund rules give you more, those apply. Full policy:
itisyou.app/products/preflightqc/refunds.
