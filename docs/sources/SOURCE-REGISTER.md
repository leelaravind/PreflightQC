# PREFLIGHTQC — AUTHORITATIVE SOURCE REGISTER

| Field | Value |
| --- | --- |
| Status | Populated from the V1 research pack |
| Register version | `2026-08-09.1` |
| Source-pack access date | 2026-08-09 (all six research documents) |
| Authority | This register is the authority for **rule values and their provenance**. It is subordinate only to `docs/specification/PREFLIGHTQC-V1-SPEC.md`. |

## How to read this register

Every shipped rule must be traceable: **report finding → `rule_id` → register row →
named source + URL + access date**.

Column meanings:

| Column | Meaning |
| --- | --- |
| Property | Canonical property in the normalised metadata model (§9 of the spec) |
| Rule / value / range | The value **verbatim from the source**, with explicit units |
| Class | `HARD_REQUIREMENT` / `DOCUMENTED_LIMIT` / `RECOMMENDATION` / `BEST_PRACTICE` / `ELIGIBILITY` / `UNKNOWN` |
| Conf | Source confidence: `HIGH` / `MEDIUM` / `LOW` |
| Src | Source id within that platform's section |
| Behaviour | The severity PreflightQC emits, bounded by §7.3 of the spec |

**Severity ceiling** (spec §7.3), repeated here because this register is where it is
most easily violated:

```
HARD_REQUIREMENT -> may be FAIL
DOCUMENTED_LIMIT -> may be FAIL
RECOMMENDATION   -> WARN maximum, NEVER FAIL
BEST_PRACTICE    -> WARN maximum, NEVER FAIL
ELIGIBILITY      -> WARN maximum, NEVER FAIL
UNKNOWN          -> INFO maximum, NEVER FAIL or WARN
```

### Register rules

1. Values are recorded **verbatim** from the source. Units are always explicit.
2. Uncertain material is **never** promoted to a hard rule.
3. Where sources conflict, **both values are preserved** with their sources. The conflict
   is recorded in the platform's Conflicts section and is surfaced to the user, never
   silently resolved.
4. A row with no first-party source cannot back a `FAIL` rule.
5. Third-party / blog values are recorded only as **leads** and are explicitly marked
   NON-AUTHORITATIVE. They must never be promoted.
6. Every row carries the access date of its source. Rules whose sources have not been
   re-verified within 6 months are flagged stale at the release gate.

---

## 0. SOURCE PACK INVENTORY

All six research documents are **present** in this repository, unaltered.

| # | Research area | File | Location | Status |
| --- | --- | --- | --- | --- |
| 1 | Instagram / Meta technical video specifications | `PreflightQC_ Instagram and Meta Video Specification Research for Engineering Validation.pdf` | `docs/sources/meta/` | **PRESENT** |
| 2 | TikTok technical video specifications | `TikTok Video Technical Specifications for PreflightQC Offline Deliverable QA_ August 2026 Reference.pdf` | `docs/sources/tiktok/` | **PRESENT** |
| 3 | YouTube / Shorts technical video specifications | `PreflightQC Asset Research_ YouTube Video Upload Specifications (August 2026).pdf` | `docs/sources/youtube/` | **PRESENT** |
| 4 | LinkedIn technical video specifications | `LinkedIn Video Specifications_ Source-Verified Register for PreflightQC Validation Rules (August 2026).pdf` | `docs/sources/linkedin/` | **PRESENT** |
| 5 | MediaInfo commercial licensing + metadata capability | `MediaInfo 26_05 Licensing and Technical Due-Diligence for PreflightQC.pdf` | `docs/sources/mediainfo/` | **PRESENT** |
| 6 | FFmpeg / ffprobe commercial distribution + licensing | `PreflightQC FFmpeg and ffprobe Dependency Licensing Review for Commercial Distribution.pdf` | `docs/sources/ffmpeg/` | **PRESENT** |

**Outstanding source material: NONE.** No research document is missing from the
repository.

### 0.1 Source-pack coverage status per area

| Area | Coverage | Gate implication |
| --- | --- | --- |
| Meta / Instagram | **PARTIAL.** Tier 1 complete and HIGH for the Content Publishing API (Reels + Stories). PARTIAL/BLOCKED for the per-objective Ads Guide numeric tables (JavaScript-rendered; the Reels ad page body was not extractable). Two deliberate Tier 1 gaps: audio loudness targets and HDR/colour-space input requirements. | Feed preset ships WARN/INFO-dominant. No Instagram **ad** preset ships in V1. |
| TikTok | **STRONG** on developer API + ads; **verbatim Tier 1** for Studio/in-app organic limits. **SILENT** on codec profile/level, audio hard rules, HDR/colour/bit-depth/chroma, faststart, PAR, GOP, loudness, VFR policy. | Profile-based presets required; almost everything below container/codec/dimension/fps/duration/size is `UNKNOWN`. |
| YouTube | **STRONG.** Nearly all encoding parameters are documented, but almost all as *recommendations*. | Only 2 file-measurable `FAIL` rules exist for V1 (container list, 256 GB). Everything else is `WARN`/`INFO`. |
| LinkedIn | **SUFFICIENT** for three placements (Organic, Video Ads, CTV), each with a first-party numeric spec. **OUT OF SCOPE**: LinkedIn Live, Conversation Ads. | Three separate presets, never merged. |
| MediaInfo | **COMPLETE** for licensing and field capability. | Approved with conditions; see §7. |
| FFmpeg / ffprobe | **COMPLETE** for licensing, packaging and field capability. | Approved with conditions; see §6. |

---

## 1. META / INSTAGRAM

Research file: `docs/sources/meta/PreflightQC_ Instagram and Meta Video Specification Research for Engineering Validation.pdf`
Access date: 2026-08-09.

### 1.1 Sources

| Src | Title | URL | Conf | Notes |
| --- | --- | --- | --- | --- |
| M-S1 | Content Publishing (Instagram Platform), Meta for Developers | `https://developers.facebook.com/docs/instagram-platform/content-publishing/` | HIGH | API v25.0 |
| M-S2 | IG User Media reference (Reel / Story video specifications) | `https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/` | HIGH | **The Tier 1 backbone.** Contains the explicit Reel and Story specification blocks. |
| M-S3 | Upload a Video, Meta Business Help Center | `https://www.facebook.com/business/help/163131210928551` | HIGH (wording) / MEDIUM (currency) | Page still references Creator Studio |
| M-S4 | Specifications for Live Video on Facebook | `https://www.facebook.com/business/help/162540111070395` | HIGH | **Scope = live streaming only.** Not a file-upload rule source. |
| M-S5 | Ads Guide, Instagram Feed video (Awareness) | `https://www.facebook.com/business/ads-guide/update/video/instagram-feed` | MEDIUM | JavaScript-rendered; captured via indexed snippet |
| M-S6 | Ads Guide, Instagram Stories video (Awareness) | `https://www.facebook.com/business/ads-guide/update/video/instagram-story` | MEDIUM | Partially JS-rendered |
| M-S7 | Ads Guide, Instagram Reels video (Awareness) | `https://www.facebook.com/business/ads-guide/update/video/instagram-reels` | **LOW / BLOCKED** | Page body NOT extractable |
| M-S8 | Ads Guide, Facebook Feed video (Awareness) | `https://www.facebook.com/business/ads-guide/update/video` | HIGH (wording) | |
| M-S9 | Instagram Help Center, Reels length | `https://help.instagram.com/2720958398006062` | HIGH | 3-minute in-app editing statement |
| M-S10 | About Instagram, Reels feature page | `https://about.instagram.com/features/reels` | HIGH | |
| M-S11 | Engineering at Meta, "Bringing HDR video to Reels" | `https://engineering.fb.com/2023/07/17/video-engineering/hdr-video-reels-meta/` | HIGH | Evidence that **no HDR input requirement exists** |
| M-S12 | Video API Overview / Publishing, Meta for Developers | `https://developers.facebook.com/docs/video-api/overview/` | HIGH | Transport-layer only |

### 1.2 Preset `ig_reels` — Instagram Reels (Content Publishing API)

Scope note: these are the API-publishing hard requirements. Violating them produces a
hard Graph API rejection, which is what makes them safe as `FAIL`.

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MOV or MP4 (MPEG-4 Part 14) | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if not MOV/MP4 |
| `container.edit_lists_present` | None ("no edit lists") | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if `elst` present |
| `container.faststart` | `moov` atom at front of file | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if `moov` not at front |
| `video.codec` | HEVC or H264 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if other |
| `video.scan_type` | Progressive | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if interlaced; **UNKNOWN if scan type undetermined** |
| `video.gop_closed` | Closed GOP | HARD_REQUIREMENT | HIGH | M-S2 | UNKNOWN in V1 — only partially derivable (see 1.7) |
| `video.chroma_subsampling` | 4:2:0 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if not 4:2:0 |
| `video.frame_rate` | 23–60 FPS | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside range |
| `video.width` | Maximum 1920 columns | DOCUMENTED_LIMIT | HIGH | M-S2 | FAIL if > 1920 |
| `video.display_aspect_ratio` | Between 0.01:1 and 10:1 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside range |
| `video.display_aspect_ratio` | 9:16 recommended | RECOMMENDATION | HIGH | M-S2 | **WARN only** |
| `video.bitrate` | VBR, 25 Mbps maximum | DOCUMENTED_LIMIT | HIGH | M-S2 | FAIL if > 25 Mbps |
| `audio.codec` | AAC | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if audio present and not AAC |
| `audio.sample_rate` | 48 kHz maximum | DOCUMENTED_LIMIT | HIGH | M-S2 | FAIL if > 48 000 Hz |
| `audio.channels` | 1 or 2 (mono/stereo) | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if > 2 |
| `audio.bitrate` | 128 kbps | RECOMMENDATION | HIGH | M-S2 | **WARN only** if below |
| `file.duration` | 15 minutes maximum, 3 seconds minimum | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside 3 s – 900 s |
| `file.size` | 300 MB maximum | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if > 300 MB |
| `file.duration` + `video.display_aspect_ratio` | Reels-tab eligibility: 5–90 s **and** 9:16 | **ELIGIBILITY** | MEDIUM | M-S2 | **WARN only. NEVER FAIL.** Discovery condition, not an acceptance requirement. |

### 1.3 Preset `ig_stories` — Instagram Stories (Content Publishing API)

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MOV or MP4, no edit lists, `moov` at front | HARD_REQUIREMENT | HIGH | M-S2 | FAIL |
| `video.codec` | HEVC or H264 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL |
| `video.scan_type` | Progressive | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if interlaced |
| `video.gop_closed` | Closed GOP | HARD_REQUIREMENT | HIGH | M-S2 | UNKNOWN in V1 |
| `video.chroma_subsampling` | 4:2:0 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL |
| `video.frame_rate` | 23–60 FPS | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside |
| `video.width` | Maximum 1920 columns | DOCUMENTED_LIMIT | HIGH | M-S2 | FAIL if > 1920 |
| `video.display_aspect_ratio` | Between **0.1:1** and 10:1 | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside. **Note the lower bound differs from Reels — see 1.6 conflict C-4.** |
| `video.display_aspect_ratio` | 9:16 recommended | RECOMMENDATION | HIGH | M-S2 | WARN only |
| `video.bitrate` | VBR, 25 Mbps maximum | DOCUMENTED_LIMIT | HIGH | M-S2 | FAIL if > 25 Mbps |
| `audio.codec` / `audio.sample_rate` / `audio.channels` | AAC, 48 kHz max, 1–2 channels | HARD_REQUIREMENT | HIGH | M-S2 | FAIL |
| `audio.bitrate` | 128 kbps | RECOMMENDATION | HIGH | M-S2 | WARN only |
| `file.duration` | 60 seconds maximum, 3 seconds minimum | HARD_REQUIREMENT | HIGH | M-S2 | FAIL outside 3 s – 60 s |
| `file.size` | 100 MB maximum | HARD_REQUIREMENT | HIGH | M-S2 | FAIL if > 100 MB |

### 1.4 Preset `ig_feed` — Instagram Feed video (reduced)

Instagram Feed video has **no dedicated file-spec block** in the Content Publishing API.
Its values come from the Ads Guide (MEDIUM) and general upload help. This preset is
therefore **WARN/INFO-dominant by construction** and carries very few `FAIL` rules.

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MP4, MOV or GIF | RECOMMENDATION | MEDIUM | M-S5 | WARN |
| `video.display_aspect_ratio` | 9:16 (Awareness variant), 1% tolerance | RECOMMENDATION | MEDIUM | M-S5 | WARN — **conflict C-3** |
| `video.width` × `video.height` | 1080 × 1920 px | RECOMMENDATION | MEDIUM | M-S5 | WARN |
| `video.width` | Minimum 250 px | DOCUMENTED_LIMIT | MEDIUM | M-S5 | WARN (confidence below HIGH → capped at WARN) |
| `file.size` | 4 GB maximum | DOCUMENTED_LIMIT | MEDIUM | M-S5 | WARN |
| `file.duration` | 1 second to 60 minutes | DOCUMENTED_LIMIT | MEDIUM | M-S5 | WARN |
| `container.edit_lists_present` | "Videos should not contain edit lists or special boxes" | RECOMMENDATION | MEDIUM | M-S5 / M-S8 | WARN |
| `file.duration` | "Videos must be less than 240 minutes long" (general upload) | DOCUMENTED_LIMIT | HIGH | M-S3 | WARN (general-surface limit, not Feed-specific) |
| `video.frame_rate_mode` | "fixed frame rate" | RECOMMENDATION | HIGH | M-S8 | WARN if VFR |
| `audio.bitrate` | "Stereo AAC ... 128kbps or more is recommended" | RECOMMENDATION | HIGH | M-S3 / M-S8 | WARN |

> **Policy note.** Even though `min width 250 px`, `4 GB`, and `1 s – 60 min` are
> classified `DOCUMENTED_LIMIT`, their source confidence is MEDIUM (JS-rendered, captured
> from indexed snippets). Per register rule 4 and spec §6.6, `ig_feed` ships them as
> `WARN`. No Instagram Feed rule is `FAIL` in V1.

### 1.5 Not shipped in V1

- **Instagram Reels ad preset.** M-S7 was BLOCKED; the page body was not extractable.
  Third-party transcriptions exist but are NON-AUTHORITATIVE. No Instagram ad preset
  ships in V1.
- **Facebook Feed / Facebook Live presets.** Out of the V1 preset families (spec §6).
  M-S4 (Live) is retained here only to prevent its values (44.1/48 kHz, H.264 Level
  4.1/4.2, 2 s keyframe) from being mistaken for file-upload rules. **They are not.**

### 1.6 Conflicts — PRESERVED, NOT RESOLVED

| ID | Conflict | Values | Behaviour |
| --- | --- | --- | --- |
| C-1 | Reels duration | API (M-S2) = 15 min max; in-app editor (M-S9/M-S10) = 3 min | FAIL only at the API's 15 min. The 3-minute in-app figure is `INFO`. |
| C-2 | Organic vs ads durations/sizes | API organic Stories = 60 s / 100 MB; Ads Guide Stories (M-S6) = 1 s – 60 min / 4 GB | **Separate rule sets per surface.** Never merged. |
| C-3 | Feed aspect ratio | Awareness snippet = 9:16 @ 1080×1920, min width 250 px; other objectives / Tier-2 transcription = 4:5 @ ≥1080×1080, min width 500 px | Both documented. WARN only on either. |
| C-4 | Aspect-ratio lower bound **within M-S2 itself** | Reels 0.01:1 vs Stories 0.1:1 | **Preserve verbatim per preset. Do not normalise.** |
| C-5 | Reels file size | M-S2 (Tier 1) = 300 MB; ContentStudio (third party) = 100 MB | Trust 300 MB. The 100 MB figure is NON-AUTHORITATIVE and is not shipped. |
| C-6 | Audio sample rate | M-S2 = 48 kHz max (file upload); M-S4 = 44.1 or 48 kHz (**live**) | Different scopes. Live values are not file-upload rules. |

### 1.7 UNKNOWN — do not fill

| Topic | Status | Behaviour |
| --- | --- | --- |
| Audio loudness (LUFS / LKFS / dBFS true peak) | **UNKNOWN at Tier 1.** Meta publishes no loudness normalisation target anywhere. The −14 LUFS figure is a **music-streaming** norm (Spotify/YouTube/TIDAL/Amazon/SoundCloud −14; Deezer −15; Apple Music −16) and is **not** a Meta target. | `UNKNOWN`. **Do NOT import.** |
| HDR / colour space as an **input requirement** | **UNKNOWN at Tier 1.** Meta accepts HDR uploads and tone-maps server-side to BT.709 SDR (M-S11), but publishes no creator-facing HDR/colour-space requirement. M-S2 is silent on colour space for video. | `INFO` only. |
| Closed GOP verification | Requires packet-level inspection beyond the V1 inspection cost boundary (spec §10.5). | `UNKNOWN` in V1 with an explicit "not verified by PreflightQC V1" explanation. |
| Instagram Reels **ad** numeric table | BLOCKED (M-S7). | Not shipped. |

### 1.8 Not offline-measurable — must never become rules

Server-side transcoding outcomes, account eligibility, remixing / branded-content flags,
text and logo safe zones, algorithmic reach.

---

## 2. TIKTOK

Research file: `docs/sources/tiktok/TikTok Video Technical Specifications for PreflightQC Offline Deliverable QA_ August 2026 Reference.pdf`
Access date: 2026-08-09.

> **Design consequence, recorded here because it is a source finding, not a preference:**
> TikTok publishes **four different official numbers** for maximum organic duration and
> file size across overlapping upload paths. The upload path must therefore be an
> **explicit preset the user selects**. A single merged "TikTok" preset is not
> constructible from the sources.

### 2.1 Sources

| Src | Tier | Title | URL | Conf |
| --- | --- | --- | --- | --- |
| T-S1 | 1 (consumer Help Center) | "Tools for creators" (TikTok Studio) | `support.tiktok.com/en/using-tiktok/creating-videos/creator-tools-on-tiktok` | HIGH |
| T-S2 | 1 | "Camera tools" | `support.tiktok.com/en/using-tiktok/creating-videos/camera-tools` | HIGH |
| T-S3 | 2 (Business Help Center) | "TikTok Auction In-Feed Ads" | `ads.tiktok.com/help/article/tiktok-auction-in-feed-ads` | HIGH (last updated June 2026) |
| T-S4 | 2 | "TopView ad specifications" | `ads.tiktok.com/help/article/tiktok-reservation-topview` | HIGH (June 2026) |
| T-S5 | 2 | "TikTok reservation in-feed ad specifications (Reach & Frequency)" | `ads.tiktok.com/help/article/tiktok-reservation-in-feed-ads-reach-frequency` | HIGH |
| T-S6 | 2 | "Global App Bundle video ad specifications" | `ads.tiktok.com/help/article/global-app-bundle-video-ad-specifications` | HIGH (July 2025) |
| T-S7 | 2 | "Specifications for TikTok Pangle ad assets" | `ads.tiktok.com/help/article/specifications-for-pangle-ad-assets` | HIGH (July 2025) |
| T-S8 | 3 (Developer) | "Media Transfer Guide" → Video restrictions table | `developers.tiktok.com/doc/content-posting-api-media-transfer-guide` | HIGH |
| T-S9 | 3 | "Get Started — Direct Post / Upload" | `developers.tiktok.com/doc/content-posting-api-get-started` | HIGH |

Third-party sources (Renderforest, PostFast, StackInfluence, Riverside, Descript, Aiarty,
Insense, Adnabu, Triple Whale, Recharm, TikAdSuite, Sovran, soona, AdRate, Moda) are
**LEADS ONLY** and are never promoted to authority.

### 2.2 Preset `tiktok_content_posting_api`

Verbatim source (T-S8): *"Supported media formats: MP4 (recommended) WebM MOV"*;
*"Supported codecs: H.264 (recommended) H.265 VP8 VP9"*; *"Framerate restrictions:
Minimum of 23 FPS Maximum of 60 FPS"*; *"Picture size restrictions: Minimum of 360 pixels
for both height and width Maximum of 4096 pixels for both height and width"*;
*"Size restrictions: Maximum of 4GB."*

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MP4, WebM, MOV | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL if not in set |
| `video.codec` | H.264, H.265, VP8, VP9 | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL if not in set |
| `video.width`, `video.height` | Minimum 360 px, maximum 4096 px, **both** dimensions | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL outside |
| `video.frame_rate` | 23–60 FPS | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL outside (nominal/average; see caveat 2.7) |
| `file.duration` | 10 minutes maximum (API endpoint) | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL if > 600 s — **only in this preset** |
| `file.size` | 4 GB maximum | DOCUMENTED_LIMIT | HIGH | T-S8 | FAIL if > 4 GB |
| `audio.codec` | AAC recommended (H.264+AAC example) | RECOMMENDATION | MEDIUM | T-S9 | WARN only |
| `video.display_aspect_ratio` | 9:16 native/recommended | RECOMMENDATION | MEDIUM | T-S1 | WARN only |

### 2.3 Preset `tiktok_studio_web`

Verbatim (T-S1): *"Uploaded videos must be: In MP4 or WebM file format; 720x1280
resolution or higher; Up to 30 minutes in length; Less than 10 GB."*

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MP4 or WebM | DOCUMENTED_LIMIT | HIGH | T-S1 | FAIL if not in set |
| `video.width` × `video.height` | 720×1280 or higher | DOCUMENTED_LIMIT | HIGH | T-S1 | FAIL if below |
| `file.duration` | Up to 30 minutes | DOCUMENTED_LIMIT | HIGH | T-S1 | FAIL if > 1800 s |
| `file.size` | Less than 10 GB | DOCUMENTED_LIMIT | HIGH | T-S1 | FAIL if ≥ 10 GB |

### 2.4 Preset `tiktok_infeed_auction_nonspark`

Verbatim (T-S3): *"File size: Less than or equal to 500 MB. Bitrate: More than or equal
to 516 kbps"*.

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `file.size` | ≤ 500 MB | DOCUMENTED_LIMIT | HIGH | T-S3 | FAIL if > 500 MB |
| `video.bitrate` | ≥ 516 kbps | DOCUMENTED_LIMIT | HIGH | T-S3 | FAIL if < 516 kbps |
| `container.format` | `.mp4`, `.mov`, `.mpeg`, `.3gp`, `.avi` | DOCUMENTED_LIMIT | HIGH | T-S3 | FAIL if not in set |
| `video.width` × `video.height` | 9:16 ≥ 540×960; 16:9 ≥ 960×540; 1:1 ≥ 640×640 | DOCUMENTED_LIMIT | HIGH | T-S3 | FAIL if below the minimum for the detected ratio |
| `file.duration` | Up to 10 minutes | DOCUMENTED_LIMIT | HIGH | T-S3 | FAIL if > 600 s |
| `video.codec` | Not authoritatively enumerated for ads | RECOMMENDATION | LOW | — | WARN if not H.264 |

### 2.5 Preset `tiktok_topview_reservation`

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `file.duration` | 5–60 s (9–15 s recommended) | DOCUMENTED_LIMIT | HIGH | T-S4 | FAIL outside 5–60 s; WARN outside 9–15 s |
| `video.bitrate` | ≥ 2 500 kbps | DOCUMENTED_LIMIT | HIGH | T-S4 | FAIL if below |
| `file.size` | ≤ 500 MB | DOCUMENTED_LIMIT | HIGH | T-S4 | FAIL if above |
| `video.width` × `video.height` | 9:16 ≥ 540×960 | DOCUMENTED_LIMIT | HIGH | T-S4 | FAIL if below |
| `container.format` | `.mp4`, `.mov`, `.mpeg`, `.3gp` | DOCUMENTED_LIMIT | HIGH | T-S4 | FAIL if not in set |
| Audio "must not be completely silent" | **Creative policy, not a file-metadata rule** | UNKNOWN | — | T-S4 | INFO only |

### 2.6 Not shipped in V1

Spark Ads (Pull) — "no restrictions", inherits the organic file; Global App Bundle;
Pangle; Carousel (image-only); Streaming/Automotive/Video Packages. Values are retained
in the research document. Adding any of these is a preset-data change, not an engine
change.

### 2.7 WARN-only rules (never FAIL, any TikTok preset)

Aspect ratio ≠ 9:16; resolution < 1080×1920; audio codec ≠ AAC; missing audio track;
duration 30–60 min (Studio-vs-in-app ambiguity); video bitrate below ~2 000–2 500 kbps for
1080p; VFR detected; GAB "≥516 kbps" (page says *recommended*).

### 2.8 Conflicts — PRESERVED

| ID | Conflict | Values |
| --- | --- | --- |
| T-C1 | **Max organic duration — four official numbers** | Camera tools = 60 min upload / 10 min record; Studio = 30 min; Content Posting API = 10 min; Creator Academy marketing = 60 min |
| T-C2 | **Max organic file size** | Studio < 10 GB; API ≤ 4 GB; Creator Academy 30 GB; third-party mobile ~72 MB Android / ~287.6 MB iOS (NON-AUTHORITATIVE) |

**Required behaviour for T-C1 / T-C2:** surface the contradiction to the user rather than
silently choosing. A 45-minute file checked against an organic preset must be told it
exceeds Studio's 30 min and the API's 10 min but is within Camera-tools' 60 min figure.
This is why the preset is path-specific.

### 2.9 UNKNOWN — do not fill

Exhaustive in-app container list; codec profile/level constraints; audio codec /
sample-rate / channel hard rules; minimum duration in primary docs; min/max bitrate for
organic; HDR / colour / bit-depth / chroma acceptance; faststart requirement; PAR /
anamorphic handling; GOP / keyframe rules; interlacing acceptance; loudness normalization
targets; VFR vs CFR policy; whether the API "Video restrictions" table governs in-app
uploads; whether ad codecs beyond container are enforced.

TikTok enabled 10-bit HDR **capture** on the Pixel 7 (2022) but publishes no HDR
**delivery** spec. `INFO` only.

### 2.10 Engineering caveats from the source

- TikTok **re-encodes every upload**. Many properties are silently normalised, not
  rejected. Over-strict local failing rejects files TikTok would ingest.
- Anchor all rules to **English** pages; non-English mirrors lag.
- Evaluate **displayed** dimensions after applying rotation metadata.
- Chunk-transfer mechanics (5–64 MB chunks, ≤128 MB final, ≤1000 chunks) are
  **transfer-layer**, not file-conformance rules. `INFO` when the API preset is selected.
- Safe zones are a layout concern, **not** a file-metadata property. Never judged.

---

## 3. YOUTUBE

Research file: `docs/sources/youtube/PreflightQC Asset Research_ YouTube Video Upload Specifications (August 2026).pdf`
Access date: 2026-08-09 (`hl=en`, US English).

> **The defining finding:** YouTube publishes almost every encoding parameter — MP4,
> H.264 High Profile, closed GOP, CABAC, 2 B-frames, 4:2:0, AAC-LC, 48 kHz, the
> per-resolution bitrate tables — as **RECOMMENDED ENCODING, not as hard requirements**.
> PreflightQC must never `FAIL` a file for violating them.

### 3.1 Sources

| Src | Title | URL |
| --- | --- | --- |
| Y-S1 | YouTube recommended upload encoding settings | `https://support.google.com/youtube/answer/1722171?hl=en` |
| Y-S2 | Supported YouTube file formats | `https://support.google.com/youtube/troubleshooter/2888402?hl=en` |
| Y-S3 | Video resolution & aspect ratios | `https://support.google.com/youtube/answer/6375112?hl=en` |
| Y-S4 | Upload High Dynamic Range (HDR) videos | `https://support.google.com/youtube/answer/7126552?hl=en` |
| Y-S5 | Upload videos longer than 15 minutes | `https://support.google.com/youtube/answer/71673?hl=en` |
| Y-S6 | Understand three-minute YouTube Shorts | `https://support.google.com/youtube/answer/15424877?hl=en` |
| Y-S7 | Get started creating YouTube Shorts | `https://support.google.com/youtube/answer/10059070?hl=en` |
| Y-S10 | Videos — YouTube Data API | `https://developers.google.com/youtube/v3/docs/videos` |
| Y-S13 | Choose live encoder settings — **LIVE ONLY, NOT UPLOAD** | `https://support.google.com/youtube/answer/2853702?hl=en` |

All 15 sources are enumerated in the research document; the rows above are those that back
shipped V1 rules.

### 3.2 Preset `youtube_standard` — the ONLY file-measurable FAIL rules

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | Must be on the supported list: `.MOV`, `.MPEG-1`, `.MPEG-2`, `.MPEG4`, `.MP4`, `.MPG`, `.AVI`, `.WMV`, `.MPEGPS`, `.FLV`, 3GPP, WebM, DNxHR, ProRes, CineForm, HEVC (H.265) | HARD_REQUIREMENT | HIGH | Y-S2 | **FAIL if not on list** |
| `file.size` | 256 GB maximum | DOCUMENTED_LIMIT | HIGH | Y-S5 | **FAIL if > 256 GB** |

Verbatim (Y-S5): *"The maximum file size you can upload is 256 GB or 12 hours, whichever
is less"* and *"By default, you can upload videos that are up to 15 minutes long."*

### 3.3 Preset `youtube_standard` — WARN rules (never FAIL)

| Property | Rule / value | Class | Src | Behaviour |
| --- | --- | --- | --- | --- |
| `container.format` | MP4 recommended | RECOMMENDATION | Y-S1 | WARN if not MP4 |
| `video.codec` | H.264 | RECOMMENDATION | Y-S1 | WARN if not H.264 |
| `video.profile` | High Profile | RECOMMENDATION | Y-S1 | WARN/INFO |
| `video.chroma_subsampling` | 4:2:0 | RECOMMENDATION | Y-S1 | WARN |
| `video.scan_type` | Progressive; deinterlace before upload | RECOMMENDATION | Y-S1 | WARN if interlaced |
| `container.faststart` | `moov` atom at front (Fast Start) | RECOMMENDATION | Y-S1 | WARN |
| `container.edit_lists_present` | "No Edit Lists" | RECOMMENDATION | Y-S1 | WARN |
| `audio.codec` | AAC-LC or Opus or Eclipsa Audio | RECOMMENDATION | Y-S1 | WARN |
| `audio.sample_rate` | 48 kHz | RECOMMENDATION | Y-S1 | INFO/WARN |
| `audio.bitrate` | Mono 128 / Stereo 384 / 5.1 512 kbps | RECOMMENDATION | Y-S1 | WARN if materially below |
| `video.bitrate` | SDR standard-FR: 360p 1 / 480p 2.5 / 720p 5 / 1080p 8 / 1440p 16 / 4K 35–45 / 8K 80–160 Mbps. High-FR (48/50/60): 360p 1.5 / 480p 4 / 720p 7.5 / 1080p 12 / 1440p 24 / 4K 53–68 / 8K 120–240 Mbps | RECOMMENDATION | Y-S1 | INFO; WARN only if grossly below. **YouTube explicitly states no bitrate limit is required.** |
| `video.colour_space` | BT.709 for SDR | RECOMMENDATION | Y-S1 | INFO |
| `file.duration` | > 15 minutes requires a phone-verified account | DOCUMENTED_LIMIT (account-tier-gated) | Y-S5 | **WARN**, not FAIL |
| `file.duration` | 12 hours (verified accounts) | DOCUMENTED_LIMIT | Y-S5 | WARN |
| `video.gop_closed`, B-frames, CABAC | Closed GOP, GOP of half the frame rate, 2 consecutive B-frames, CABAC | RECOMMENDATION | Y-S1 | INFO |

### 3.4 Preset `youtube_shorts` — minimal by necessity

YouTube defines Shorts classification **only** by aspect ratio and duration. Verbatim
(Y-S6): *"Any videos uploaded on or after this date with a square or vertical aspect ratio
up to three minutes in length will be categorized as Shorts on YouTube."*

| Property | Rule / value | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `video.display_aspect_ratio` | Square or vertical (≤ 1:1) — required to *be* a Short | HARD_REQUIREMENT (classification) | HIGH | Y-S6 | INFO — drives classification, reported not gated |
| `file.duration` | ≤ 3 minutes (standard channels, uploads on/after 15 Oct 2024) | DOCUMENTED_LIMIT (classification) | HIGH | Y-S6 | INFO — drives classification |
| `video.display_aspect_ratio` | 9:16 recommended | BEST_PRACTICE | MEDIUM | Y-S7 | WARN |
| Resolution 1080×1920 | Industry convention, **not a published YouTube Shorts spec** | UNKNOWN | LOW | non-official | INFO |
| Codec / container / bitrate / min resolution / file size for Shorts | **No separate Shorts spec published** | UNKNOWN | LOW | — | **DO NOT CHECK** |

> **Locked rule:** standard-upload encoding rules must **not** be ported into Shorts
> `FAIL` rules. The Shorts preset checks the standard container list and the 256 GB limit
> (which apply platform-wide) and otherwise reports classification and `UNKNOWN`.

### 3.5 HDR — conditional rules only

HDR requirements are **testable but conditional on HDR intent**. Evaluate only when the
file signals HDR: transfer ∈ {PQ, HLG} or primaries = Rec.2020.

| Property | Rule / value | Class | Src | Behaviour |
| --- | --- | --- | --- | --- |
| `video.bit_depth` | 10-bit or 12-bit | HARD_REQUIREMENT (conditional) | Y-S4 | WARN (guarded by HDR intent) |
| `video.colour_primaries` | Rec.2020 | HARD_REQUIREMENT (conditional) | Y-S4 | WARN |
| `video.matrix_coefficients` | Rec.2020 non-constant luminance | HARD_REQUIREMENT (conditional) | Y-S4 | WARN |
| `video.transfer_characteristics` | PQ or HLG (Rec.2100) | HARD_REQUIREMENT (conditional) | Y-S4 | WARN |
| `video.height` | 720p, 1080p, 1440p or 2160p; prefer UHD widths over DCI | RECOMMENDATION | Y-S4 | WARN |
| `video.frame_rate` | 23.976, 24, 25, 29.97, 30, 48, 50, 59.94, 60 | RECOMMENDATION | Y-S4 | WARN |
| `container.format` | MOV/QuickTime, MP4, MKV tested to work | RECOMMENDATION | Y-S4 | WARN |
| HDR metadata presence | **MUST be present** in codec or container or the video will not be processed as HDR | HARD_REQUIREMENT (conditional) | Y-S4 | **WARN** — an HDR transfer with missing HDR metadata is a genuine defect but not an upload rejection |
| MaxCLL / MaxFALL | SMPTE ST 2086 + CEA 861-3; YouTube substitutes Sony BVM-X300 values if missing | RECOMMENDATION | Y-S4 | INFO |
| Dolby Vision | **Not listed** among YouTube's supported HDR upload formats | UNKNOWN | Y-S4 | `UNKNOWN` — flag, do not validate against |

### 3.6 Not shipped as file rules in V1

YouTube's API metadata limits (title ≤ 100 characters; description ≤ 5000 **bytes**, not
characters; tags ≤ 500 characters total; `<` and `>` excluded) are **file-external** —
they constrain user-entered text, not the video file. Per spec §20.1 they ship as `INFO`
guidance in the report, not as findings against the file. Optional metadata entry is a
FUTURE candidate.

Custom thumbnail and caption-file format rules are likewise out of V1 scope (separate
assets, not the video file).

### 3.7 Conflicts and UNKNOWNs

| ID | Item | Resolution |
| --- | --- | --- |
| Y-C1 | 512 GB file-size claim (Compresto, third party) vs official 256 GB (Y-S5) | **Trust 256 GB.** The 512 GB figure is NON-AUTHORITATIVE. |
| Y-C2 | "5000 characters" description myth | The API states 5000 **bytes**. Measure byte length if ever implemented. |
| Y-U1 | Minimum upload resolution | **No official hard floor.** 240p is the lowest *recommended* encoding resolution, not a rejection threshold. `UNKNOWN`; do not FAIL. |
| Y-U2 | Pixel aspect ratio / anamorphic | Not officially documented. `UNKNOWN`. |
| Y-U3 | SDR bit-depth requirement | Not documented. `UNKNOWN`. |
| Y-U4 | Upload-side keyframe interval as a hard rule | Only documented as *recommended*. The "keyframe every 2 seconds" figure belongs to **live encoder** guidance (Y-S13) and must not be applied to uploads. |
| Y-U5 | AV1 (SDR) upload acceptance | Explicit only for HDR; general SDR acceptance inferred at MEDIUM confidence, not stated verbatim. |
| Y-U6 | Dolby Vision upload support | `UNKNOWN`. |

**Explicitly excluded from FAIL logic:** all live-streaming encoder settings (CBR,
keyframe ≤ 2 s, RTMPS/HLS, HEVC-over-RTMP HDR) from Y-S13. These are LIVE-only.

---

## 4. LINKEDIN

Research file: `docs/sources/linkedin/LinkedIn Video Specifications_ Source-Verified Register for PreflightQC Validation Rules (August 2026).pdf`
Access date: 2026-08-09.

> LinkedIn publishes **three separate numerically deterministic specifications**. Organic
> and advertising requirements differ enough that they **must never be merged**.

### 4.1 Sources

| Src | Title | URL | Conf notes |
| --- | --- | --- | --- |
| L-S1 | Video specifications for your LinkedIn Pages and Career Pages | `linkedin.com/help/linkedin/answer/a1311816` | Robots-blocked; values from indexed snippet, cross-checked |
| L-S2 | Video sharing troubleshooting | `linkedin.com/help/linkedin/answer/a548372` | Robots-blocked |
| L-S3 | Video Ads Specifications | `business.linkedin.com/advertise/ads/sponsored-content/video-ads/specs` | © 2026, fully retrieved |
| L-S4 | Video ads advertising specifications | `linkedin.com/help/lms/answer/a424737` | Robots-blocked |
| L-S5 | Connected TV Ads Specifications | `business.linkedin.com/advertise/ads/sponsored-content/connected-tv-ads/specs` | © 2026, fully retrieved |
| L-S6 | CTV Ads specifications | `linkedin.com/help/lms/answer/a6282198` | CTV noted as "currently in testing" |
| L-S7 | Videos API (Microsoft Learn) | `learn.microsoft.com/.../community-management/shares/videos-api` | `li-lms-2026-07` |
| L-S8 | Create and Manage Creatives (Microsoft Learn) | `learn.microsoft.com/.../account-structure/create-and-manage-creatives` | `ms.date 2026-04-10` |

### 4.2 Preset `linkedin_organic`

Verbatim (L-S1): *"Max file size - 5 GB · Minimum file size - 75 KB · Max video duration -
10 minutes · Minimum video duration - 3 seconds · Resolution range - 256x144 – 4096x2304 ·
Aspect ratio - 1:2.4 – 2.4:1 · Frame rates - 10 FPS – 60 FPS · Bit rates - 192 KBPS –
30 MBPS."*

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | ASF, FLV, MP3, MP4, MPEG-1, MPEG-4, MKV, WebM, H264/AVC, Vorbis, VP8, VP9, WMV2, WMV3. **AVI, QuickTime and MOV are NOT supported.** | HARD_REQUIREMENT | HIGH | L-S1 | FAIL if not in list |
| `file.size` | Maximum 5 GB | HARD_REQUIREMENT | HIGH | L-S1 | FAIL if > 5 GB |
| `file.size` | Minimum 75 KB | HARD_REQUIREMENT | HIGH | L-S1 | FAIL if < 75 KB |
| `file.duration` | Minimum 3 seconds | HARD_REQUIREMENT | HIGH | L-S1 | FAIL if < 3 s |
| `file.duration` | Maximum 10 min (L-S1) / 15 min desktop, 10 min mobile (L-S2) | HARD_REQUIREMENT | MEDIUM (pages differ) | L-S1 / L-S2 | **WARN 10–15 min; FAIL only above 15 min.** See L-C2. |
| `video.width` × `video.height` | 256×144 – 4096×2304 | HARD_REQUIREMENT | HIGH | L-S1 | FAIL outside range |
| `video.display_aspect_ratio` | 1:2.4 – 2.4:1 (≈ 0.417 – 2.4) | HARD_REQUIREMENT | HIGH | L-S1 | FAIL outside range |
| `video.frame_rate` | 10–60 FPS | HARD_REQUIREMENT | HIGH | L-S1 | FAIL outside range |
| `video.bitrate` | 192 kbps – 30 Mbps | RECOMMENDATION (stated as guideline) | MEDIUM | L-S1 | **WARN outside** |
| `audio.present` | **UNDOCUMENTED by LinkedIn** | UNKNOWN | — | — | **Do not gate on missing audio** |
| `audio.sample_rate`, `audio.channels` | UNDOCUMENTED for organic | UNKNOWN | — | — | INFO |

### 4.3 Preset `linkedin_video_ads`

Verbatim (L-S3): *"Video File Type: MP4 · Video Sound Format: AAC or MPEG4 · Recommended
frame rate: 30 frames per second · Video File Size: 75 KB (min) - 500 MB (max) · Video
Duration: 3 seconds - 30 minutes · Video Captions: Optional · Video Sound Rate: Less than
64 KHz · Minimum width: 360 pixels · Maximum width: 1920 pixels · Minimum height: 360
pixels · Maximum height: 1920 pixels · Minimum aspect ratio: 9:16 (0.563) · Maximum aspect
ratio: 16:9 (1.778) · Aspect ratio tolerance: 5%."*

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `container.format` | MP4 only | HARD_REQUIREMENT | HIGH | L-S3/L-S4/L-S7 | FAIL if not MP4 |
| `file.size` | 75 KB – 500 MB | HARD_REQUIREMENT | HIGH | L-S3/L-S7/L-S8 | FAIL outside |
| `file.duration` | 3 seconds – 30 minutes | HARD_REQUIREMENT | HIGH | L-S3/L-S4/L-S7 | FAIL outside |
| `video.width` | 360 – 1920 px | HARD_REQUIREMENT | HIGH | L-S3 | FAIL outside |
| `video.height` | 360 – 1920 px | HARD_REQUIREMENT | HIGH | L-S3 | FAIL outside |
| `video.display_aspect_ratio` | 0.563 – 1.778, **tolerance 5%** | HARD_REQUIREMENT | HIGH | L-S3 | FAIL outside (tolerance applied) |
| `audio.sample_rate` | Less than 64 kHz | HARD_REQUIREMENT | HIGH | L-S3 | FAIL if ≥ 64 000 Hz |
| `video.codec` | ProRes not supported | HARD_REQUIREMENT | HIGH | L-S4 | FAIL if ProRes |
| `video.codec` | H.264/AVC — **LinkedIn does not publish a hard video-codec whitelist for ads** | RECOMMENDATION | MEDIUM | L-S3 | **WARN if not H.264** |
| `audio.codec` | AAC or MPEG4 | HARD_REQUIREMENT | HIGH | L-S3 | **WARN if other** (source wording is a "sound format" statement, not a stated rejection) |
| `video.frame_rate` | 30 fps recommended | RECOMMENDATION | HIGH | L-S3 | WARN if > 30 fps |
| Recommended dims per ratio | 4:5 360×450→1080×1350; 9:16 360×640→1080×1920; 16:9 640×360→1920×1080; 1:1 360×360→1920×1920 | RECOMMENDATION | HIGH | L-S3 | WARN outside |
| Captions | Optional; SRT sidecar or burned in | — | HIGH | L-S3 | **IGNORE — not locally inspectable** |

### 4.4 Preset `linkedin_ctv`

Verbatim (L-S5): *"Dimensions: General: 1920 x 1080 pixels, 1280 x 720 pixels ·
Aspect Ratio: 16:9 · Format: MP4 · Max File Size: 500MB · Video Duration: Min/Max:
6 seconds - 60 seconds · Bit Rate: General: 12 Mbps or higher; Recommended: 15 - 40 Mbps ·
Audio: 2-channel, -23 integrated LUFS; PCM (16 or 24 bit only, preferred) or AAC codec;
192 Kbps minimum; 48 kHz sample rate · Frame rate (must be constant): General: 23.98, 24,
25, or 29.97, 30 fps · Codec ID: H.264 · Chroma Subsampling: General: 4:2:0;
Recommended: 4:2:2."*

| Property | Rule / value / range | Class | Conf | Src | Behaviour |
| --- | --- | --- | --- | --- | --- |
| `video.width` × `video.height` | Exactly 1920×1080 or 1280×720 | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if neither |
| `video.display_aspect_ratio` | 16:9 | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if not 16:9 |
| `container.format` | MP4 | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if not MP4 |
| `file.size` | ≤ 500 MB | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if above |
| `file.duration` | 6–60 s (6/15/30/45/60 s recommended) | HARD_REQUIREMENT | HIGH | L-S5 | FAIL outside; WARN if not a recommended value |
| `video.bitrate` | ≥ 12 Mbps | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if < 12 Mbps |
| `video.bitrate` | 15–40 Mbps recommended | RECOMMENDATION | HIGH | L-S5 | WARN if < 15 Mbps |
| `video.frame_rate_mode` | **Must be constant** | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if VFR; **UNKNOWN if mode undetermined** |
| `video.frame_rate` | 23.98, 24, 25, 29.97, 30 | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if outside set |
| `video.codec` | H.264 | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if not H.264 |
| `video.chroma_subsampling` | 4:2:0 general; 4:2:2 recommended | HARD_REQUIREMENT / RECOMMENDATION | HIGH | L-S5 | WARN if not 4:2:0 or 4:2:2 |
| `audio.channels` | 2-channel (stereo) | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if not stereo |
| `audio.bitrate` | ≥ 192 kbps | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if below |
| `audio.sample_rate` | 48 kHz | HARD_REQUIREMENT | HIGH | L-S5 | FAIL if not 48 000 Hz |
| `audio.codec` | PCM (16/24-bit preferred) or AAC | HARD_REQUIREMENT | HIGH | L-S5 | WARN if other |
| Audio loudness | −23 integrated LUFS | HARD_REQUIREMENT | HIGH | L-S5 | **`UNKNOWN` in V1.** Requires an `ebur128` decode-and-measure pass, which exceeds the V1 inspection cost boundary (spec §10.5, §20.1). Reported as "not measured by PreflightQC V1". |
| Audio duration | Must match video | HARD_REQUIREMENT | HIGH | L-S5 | WARN if mismatch |

L-S6 notes CTV is "currently in testing" and that *"Uploading a video that meets the
recommended requirements doesn't guarantee delivery to all publishers."* This caveat must
appear in the CTV preset's description.

### 4.5 Conflicts

| ID | Conflict | Resolution |
| --- | --- | --- |
| L-C1 | Ad max file size: **500 MB** (L-S3, L-S7) vs **200 MB** (Sendspark, Linkboost — third-party blogs) | **RESOLVED → 500 MB.** The 200 MB figure is NON-AUTHORITATIVE and likely stale. Not shipped. |
| L-C2 | Organic max duration: 10 min (L-S1) vs 15 min desktop / 10 min mobile (L-S2) | **Report both. WARN 10–15 min, FAIL only above 15 min.** |
| L-C3 | Ad video codec: "VP8 for ads" (TotalMedia, third party) | NON-AUTHORITATIVE. Non-H.264 is `WARN`, not `FAIL`. |
| L-C4 | Ad loop wording (current vs legacy pages) | Playback behaviour only. Not a QA gate. |
| L-C5 | **MB vs MiB** — LinkedIn does not state whether "500 MB" / "5 GB" / "75 KB" are binary or decimal | **Adopt the conservative decimal interpretation** so PreflightQC never passes a file LinkedIn would reject: 500 MB = 500 000 000 bytes; 5 GB = 5 000 000 000 bytes; 75 KB floor treated as 76 800 bytes. Emit a WARN band within ~2% of a ceiling to absorb the ambiguity. **This convention applies to all LinkedIn byte thresholds and must be recorded in the preset.** |

### 4.6 UNKNOWN / IGNORE

- Audio mandatory? **UNDOCUMENTED** for both organic and ads. Do not require an audio
  track.
- Colour space, HDR, interlacing, rotation metadata, VFR for organic and ads:
  **UNDOCUMENTED**. Only CTV specifies constant frame rate and chroma subsampling.
  Everything else is `INFO`.
- **Captions are not locally inspectable.** Supplied as an external SRT sidecar or burned
  into pixels. **Must not gate.**
- Out of scope: LinkedIn Live (RTMP ingest, no delivered file); Conversation / Message Ads
  (no video asset); LinkedIn Learning (LMS ingest surface, not a placement).

---

## 5. INSPECTOR FIELD MAPPING

Consolidated from all four platform documents plus the two dependency reviews. This is
the mapping the normalised metadata model (spec §9) is built from.

| Normalised property | ffprobe | MediaInfo | Precedence | Reliability note |
| --- | --- | --- | --- | --- |
| `file.size` | `format.size` | `General FileSize` | ffprobe | Filesystem value |
| `file.duration` | `format.duration` (fallback `stream.duration`) | `General Duration` (ms) | ffprobe (container) | Container and stream values can differ; record both |
| `container.format` | `format.format_name` | `General Format`, `CodecID` | ffprobe | ffprobe may list several (`mov,mp4,m4a`) — match by membership |
| `container.major_brand` | `format.tags.major_brand` | `Format_Profile` | ffprobe | |
| `container.stream_count` | `format.nb_streams` | per-track | ffprobe | Also count by type |
| `container.faststart` | `moov`-vs-`mdat` order heuristic | `IsStreamable` | **MediaInfo** | ffprobe has no direct field |
| `container.edit_lists_present` | atom-level inspection | — | — | **Requires atom-level parse; see gap G-1** |
| `video.codec` | `stream.codec_name`, `codec_tag_string` | `Video Format`, `CodecID` | ffprobe | Use tag for MP4 fourcc (`avc1`) |
| `video.profile` | `stream.profile` | `Format_Profile` | ffprobe | MediaInfo combines `profile@level@tier` in one string |
| `video.level` | `stream.level` | embedded in `Format_Profile` | ffprobe | ffprobe returns `-99`/`N/A` when absent |
| `video.width` / `height` | `stream.width` / `height` | `Width` / `Height` | ffprobe | Coded pixels |
| `video.coded_width` / `coded_height` | `stream.coded_width` / `coded_height` | `Stored_Width/Height` | ffprobe | |
| `video.sample_aspect_ratio` | `stream.sample_aspect_ratio` | `PixelAspectRatio` | ffprobe | |
| `video.display_aspect_ratio` | `stream.display_aspect_ratio` | `DisplayAspectRatio` | **computed** | **Must compute** `(width/height) × SAR` and cross-check; a non-square SAR changes displayed AR |
| `video.rotation` | `stream.side_data_list` (Display Matrix), `tags.rotate` | `Rotation` | ffprobe | **Required to compute displayed W×H** |
| `video.frame_rate` | `r_frame_rate`, `avg_frame_rate` | `FrameRate`, `FrameRate_Num`/`_Den` | ffprobe | Keep as exact rational (24000/1001) |
| `video.frame_rate_mode` | compare `avg` vs `r`; packet-PTS analysis | `FrameRate_Mode` (CFR/VFR) | **MediaInfo** | Container-dependent; may be absent → `UNDETERMINED` |
| `video.bitrate` | `stream.bit_rate`, else `format.bit_rate`, else size×8/duration | `Video BitRate`, `General OverallBitRate` | ffprobe | `stream.bit_rate` frequently absent in MP4. **Record which source was used.** |
| `video.pixel_format` | `stream.pix_fmt` | — | ffprobe | Source of chroma + bit depth |
| `video.chroma_subsampling` | derived from `pix_fmt` | `ChromaSubsampling` | ffprobe (derived) | Map `yuv420p` → 4:2:0 |
| `video.bit_depth` | `bits_per_raw_sample`, `pix_fmt` | `BitDepth` | ffprobe | ProRes may not carry explicit depth |
| `video.scan_type` / `field_order` | `stream.field_order` | `ScanType`, `ScanOrder` | **MediaInfo** | ffprobe often returns `unknown`. **MediaInfo reads container flags, not pixels — treat as advisory.** |
| `video.colour_range` | `color_range` | — | ffprobe | |
| `video.colour_space` | `color_space` | `matrix_coefficients` | ffprobe | |
| `video.transfer_characteristics` | `color_transfer` | `transfer_characteristics` | ffprobe | Key HDR discriminator (`PQ`, `HLG`) |
| `video.colour_primaries` | `color_primaries` | `colour_primaries` | ffprobe | Absent if stream carries no colour description |
| `video.gop` / keyframe interval | keyframe interval via frame flags | — | — | **Beyond V1 inspection cost boundary; see gap G-2** |
| `video.hdr_format` | `-show_frames` `side_data_list` with `-read_intervals "%+#1"` | `HDR_Format`, `HDR_Format_Compatibility` | **MediaInfo** | MediaInfo gives cleaner naming |
| `video.mastering_display`, `max_cll`, `max_fall` | frame side data | `MasteringDisplay_*`, `MaxCLL`, `MaxFALL` | MediaInfo | Only present if the encoder wrote them |
| `video.dolby_vision` | `AV_FRAME_DATA_DOVI_METADATA` side data | `HDR_Format` profile (e.g. `dvhe.08.06, BL+RPU`) | **MediaInfo** | **Known limitation:** Dolby Vision in raw HEVC (NALU type 62) historically not reported (MediaInfoLib #1482) |
| `audio.present` / count | stream enumeration | per-track | ffprobe | |
| `audio.codec` | `stream.codec_name` | `Audio Format` | ffprobe | Distinguish AAC vs MPEG4 vs PCM |
| `audio.sample_rate` | `stream.sample_rate` | `SamplingRate` | ffprobe | |
| `audio.channels` / layout | `stream.channels`, `channel_layout` | `Channel(s)`, `ChannelLayout` | ffprobe | |
| `audio.bitrate` | `stream.bit_rate` | `Audio BitRate` | ffprobe | |

### 5.1 Known measurement gaps (V1)

| ID | Gap | V1 behaviour |
| --- | --- | --- |
| G-1 | Edit-list (`elst`) presence requires atom-level inspection, not top-level metadata | Attempt via MediaInfo/ffprobe where available; otherwise `UNDETERMINED` → rule emits `UNKNOWN`. **Never FAIL on undetermined edit-list state.** |
| G-2 | Closed GOP / keyframe interval requires packet-level analysis | `UNDETERMINED` → `UNKNOWN`. Not measured in V1. |
| G-3 | Field order / scan type is heuristic in both inspectors; MediaInfo "doesn't have eyes" | Advisory. `UNDETERMINED` → `UNKNOWN`. A FAIL on scan type is emitted **only** when the inspector positively reports interlaced. |
| G-4 | Integrated loudness (LUFS) requires a decode-and-measure pass | Not measured in V1 (spec §20.1). LinkedIn CTV's −23 LUFS rule ships as `UNKNOWN`. |
| G-5 | VFR detection may require packet-PTS analysis; a single field is insufficient | Use `FrameRate_Mode` where signalled; compare `avg` vs `r` as a secondary signal; otherwise `UNDETERMINED`. **A FAIL on "must be constant" (LinkedIn CTV) is emitted only when VFR is positively reported.** |
| G-6 | HDR side data requires reading the first frame (engages the decoder) | Bounded first-frame read only, behind an explicit setting (spec §10.5). |

### 5.2 Never measurable — must never become rules

Perceptual quality; watermark presence; safe-zone compliance; content-policy or music
licensing; server-side re-encode outcome; per-account limits (e.g. TikTok's
`max_video_post_duration_sec`); account eligibility; algorithmic reach; caption presence
(LinkedIn SRT sidecar or burned-in pixels).

---

## 6. FFMPEG / FFPROBE — LICENSING AND DISTRIBUTION

Research file: `docs/sources/ffmpeg/PreflightQC FFmpeg and ffprobe Dependency Licensing Review for Commercial Distribution.pdf`
Access date: August 2026. **Verdict: APPROVED WITH CONDITIONS.**

Full detail is in `docs/licensing/LICENSING-GATE-V1.md`. Summary of source findings:

| Finding | Source |
| --- | --- |
| FFmpeg's default licence is **LGPL v2.1-or-later**. GPL parts are off by default and require `--enable-gpl`. | `github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md` |
| `--enable-nonfree` produces a binary that is **"unredistributable"** (verbatim). | LICENSE.md |
| GPL is triggered by `--enable-gpl` or any GPL external library: libx264, libx265, libxvid, libxavs/libxavs2, libdavs2, frei0r, libcdio, librubberband, libvidstab, avisynth. `libsmbclient` forces GPL-v3. | LICENSE.md |
| Nonfree: Fraunhofer FDK AAC (`libfdk-aac`), OpenSSL in incompatible combinations, CUDA SDK components (`libnpp`, `cuda-nvcc`). | LICENSE.md + `configure` |
| LGPL compliance checklist: no `--enable-gpl`/`--enable-nonfree`; dynamic linking; ship corresponding source matching the binaries; document the configure line; host source on the same webserver; download-page notice; about-box notice; EULA mention; disclaim FFmpeg ownership; **remove reverse-engineering prohibition**; do not obfuscate DLL names. | `ffmpeg.org/legal.html` |
| **BtbN FFmpeg-Builds** `win64-lgpl-shared` is the mainstream source of LGPL **shared** Windows binaries. | `github.com/BtbN/FFmpeg-Builds` |
| **gyan.dev main builds are GPLv3** — unsuitable for bundling. **evermeet.cx is GPL and Intel-only** — unsuitable. | `gyan.dev/ffmpeg/builds`, `evermeet.cx/ffmpeg` |
| Subprocess invocation: FSF GPL FAQ (#MereAggregation) — pipes, sockets and command-line arguments are normally separate programs. But this is *"a legal question, which ultimately judges will decide."* **Process isolation is defence-in-depth, not the sole compliance mechanism.** | `gnu.org/licenses/gpl-faq.html` |
| Patent posture: `-show_streams`/`-show_format` parse headers without decoding. `-show_frames` (needed for HDR side data) **does engage the decoder**. Practical exposure very low, **not formally zero**. AVC US patents to 29 Nov 2027; HEVC well beyond 2030. | `ffmpeg.org/legal.html`, ffprobe docs, `fftools/ffprobe.c` |

### 6.1 Prohibited components (locked)

`libx264`, `libx265`, `libxvid`, `libxavs`, `libxavs2`, `libdavs2`, `frei0r`, `libcdio`,
`librubberband`, `libvidstab`, `avisynth`, `libsmbclient`, `libaribb24`, `liblensfun`,
`gmp`, `libfdk-aac`, OpenSSL in incompatible combinations, `libnpp` / `cuda-nvcc`.

Plus: **no `ffmpeg` encoder binary in V1.**

---

## 7. MEDIAINFO — LICENSING AND CAPABILITY

Research file: `docs/sources/mediainfo/MediaInfo 26_05 Licensing and Technical Due-Diligence for PreflightQC.pdf`
Access date: August 2026. **Verdict: APPROVED WITH CONDITIONS.**

| Finding | Detail |
| --- | --- |
| Version checked | **MediaInfo 26.05**, released 2026-05-12 (GPG-verified GitHub release; ChangeLog "Version 26.05, 2026-05-12") |
| Licence | **BSD 2-Clause** for MediaInfoLib, MediaInfo CLI, and MediaInfo's own GUI code. **ZenLib (`libzen`) is zlib-licensed.** |
| Licence history — **material** | Up to 0.7.62 the library was **LGPL** and GUI/CLI were **GPL**. From **0.7.63** the project switched to BSD-2-Clause. **Versions ≤ 0.7.62 must not be used.** |
| Commercial use | Permitted; no field-of-use restriction, no copyleft. |
| Source disclosure | **Not required** for library, CLI, or MediaInfo's own GUI code. |
| Attribution | Required in binary distributions: either the full BSD notice + conditions + disclaimer, **or** the short form: *"This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL"* (with the website link). |
| **GUI — prohibited** | The GUI links Qt or wxWidgets, introducing toolkit licence obligations and potential copyleft re-entry. **Do not ship the GUI.** |
| libcurl / network feature | Default DLL does **not** include libcurl; network support requires a sidecar `libcurl.dll`. **Do not enable it** — it enlarges the notice obligation (curl, typically OpenSSL/libssh2/Brotli) for no benefit to a local-only tool. |
| Windows runtime | MediaArea's build is statically linked to the multithreaded C++ runtime, so `MediaInfo.dll` generally does not require a separately installed MSVC redistributable. **Verify against the pinned build.** |
| Code signing | Authenticode signing status of the official `MediaInfo.dll` could not be confirmed. **Treat as unsigned; Authenticode-sign the full PreflightQC bundle.** |
| Supply chain | Download **only** from `mediaarea.net` or the official MediaArea GitHub releases. Verify SHA-256. Third-party DLL-download sites are unsafe and must not be used. |

### 7.1 Documented MediaInfo limitations that affect rules

- HDR: Dolby Vision in raw HEVC (NALU type 62) historically not reported (MediaInfoLib
  #1482); HLG can be mis-labelled where ST 2086 is present (MediaInfo #833);
  MaxCLL/MaxFALL only present if the encoder actually wrote them.
- Scan type / scan order: MediaInfo reads container/stream flags, **not pixels**.
  Mislabelled or soft-telecined files can report misleading values. **Advisory only.**
- Bitrate: reliable when signalled; otherwise estimated from size/duration ("risky bitrate
  estimation") and may require a full parse.
- Frame-rate mode: container-dependent; may be absent or inferred.

### 7.2 CLI vs library

The MediaInfo research recommends the **library** on engineering grounds (no spawn cost,
no output-parsing fragility), while noting that **subprocess isolation is a genuine
security and stability advantage for a QC tool ingesting untrusted customer files**, and
that a hybrid is defensible. Licensing does **not** favour either (both BSD-2-Clause;
linking mode is legally irrelevant under BSD).

The FFmpeg research independently proposes bundling the **MediaInfo CLI**.

**This is a recorded tension, not a contradiction.** The decision is made on engineering
grounds in `docs/architecture/ARCHITECTURE-V1.md` §5 and
`docs/architecture/ADR-001-TECH-STACK.md`. Either choice satisfies the source-pack
licensing constraints. The register's constraint is only: **BSD-era version, no GUI, no
libcurl.**

---

## 8. REGISTER MAINTENANCE

1. **Staleness.** Every entry carries an access date. At the release gate, any rule whose
   source has not been re-verified within 6 months is flagged. Ad pages carry visible
   "Last updated" dates (TikTok In-Feed and TopView: June 2026; GAB and Pangle: July
   2025) — a changed date requires re-verification of that placement's numbers.
2. **Change triggers.** Re-verify immediately on: a change to TikTok's developer "Video
   restrictions" table; a new "Last updated" date on any TikTok ads page; any edit to
   YouTube's encoding-settings, file-formats, HDR, Shorts, or Data API pages; any change
   to Meta's Content Publishing API spec blocks; any change to LinkedIn's Video Ads or
   CTV spec pages.
3. **Promotion.** A rule may be promoted from `UNKNOWN` to `WARN` or `FAIL` **only** when
   a first-party source publishes the requirement. Never from a third-party source.
4. **Demotion.** If a source that backed a `FAIL` rule becomes unavailable or ambiguous,
   the rule is demoted to `WARN` or `UNKNOWN` until re-verified. Conservative direction
   only.
5. **New rules** require: a first-party source, a URL, an access date, a classification,
   a confidence, and a row in this register **before** the rule may be added to a preset.
