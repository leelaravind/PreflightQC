# Page: `itisyou.app/products/preflightqc` — PREPARED, NOT PUBLISHED

Publication-ready content. Everything a buyer must know appears **before** any buy
button. Replace `{{…}}` tokens at publication time; nothing else should need editing.

---

# PreflightQC

**Offline technical QA for video deliverables — check your exports against a
platform's published delivery specification before you send them.**

Point PreflightQC at the files you are about to hand over, choose the destination
preset, and it reports every technical property that does not match — the detected
value, the required value, a plain explanation, and the first-party source the rule
came from, including the date that source was last verified.

- **12 shipped delivery presets, 170 traceable rules** — Instagram Feed/Reels/Stories,
  TikTok (Studio, Content Posting API, In-Feed Auction, TopView), YouTube standard and
  Shorts, LinkedIn organic/Video Ads/Connected TV.
- **Honest severities.** A documented hard requirement can fail; a recommendation only
  warns, and says it is a recommendation. Where a platform publishes nothing,
  PreflightQC reports UNKNOWN rather than guessing.
- **Two inspectors, cross-checked** — FFmpeg's ffprobe and MediaInfo, both bundled.
- **Reports you can hand to a client** — self-contained HTML and CSV.
- **Fully offline. No account. No telemetry.** Your files never leave your machine —
  the application contains no networking capability at all.

**Price: £19.99 (GBP) — one-time purchase. No subscription. No automatic renewal.**

[Buy on {{MERCHANT}}]  ← single purchase link at publication

## Before you buy

- **Platform:** Windows 10 x64 / Windows 11 x64 only. No macOS, no Linux, no ARM.
- **Requirements:** ~250 MB disk space; 1280×800 or larger display recommended;
  installs per-user, **no administrator rights needed**; no Python, FFmpeg or other
  install prerequisites.
- **Offline by design:** no login, no account, no activation, no telemetry, no
  analytics, no update checks. Nothing about your files or usage leaves your machine.
- **The installer is not digitally signed.** Windows SmartScreen will show a "Windows
  protected your PC" warning naming an unknown publisher. This is expected for an
  unsigned installer — stated here so you know before buying, not after. To proceed,
  Windows requires choosing "More info", then "Run anyway".
- **Verify your download:** SHA-256 checksums for every release file are published at
  the bottom of this page (`RELEASE-HASHES.txt`). Verification instructions are on the
  [support page](/products/preflightqc/support).
- **Refunds:** request within 7 calendar days; eligible refunds normally receive the
  full purchase price, processed through the merchant of record. Full policy:
  [refunds](/products/preflightqc/refunds). Your statutory rights are unaffected.
- **What it does not do:** PreflightQC reads file metadata; it does not watch the
  video, and it cannot judge picture quality or content. A PASS is a statement about
  the file against the selected preset's rules — it is not a guarantee any platform
  will accept the upload. It never modifies, re-encodes, repairs, or uploads a file.
- **Custom profiles (advanced, file-based):** a delivery specification supplied as a
  JSON profile file loads alongside the shipped presets. There is no in-app profile
  editor in this version.

## Downloads and checksums

| File | SHA-256 |
| --- | --- |
| `PreflightQC-1.0.0-setup.exe` | `{{SHA256_INSTALLER}}` |

(`RELEASE-HASHES.txt` — same values, plain text: `{{LINK}}`)

## More

[Support](/products/preflightqc/support) ·
[Refunds](/products/preflightqc/refunds) ·
[Legal & licences](/products/preflightqc/legal) ·
[Open-source components & corresponding source](/products/preflightqc/source)

Instagram, Meta, TikTok, YouTube and LinkedIn are trademarks of their respective
owners. PreflightQC is not affiliated with, endorsed by or certified by any of them;
their names identify the delivery specifications PreflightQC validates against.

PreflightQC is published by ITISYOU.
