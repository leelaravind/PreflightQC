# PREFLIGHTQC — MARKETPLACE LISTING MATERIAL (PREPARED, NOT PUBLISHED)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Product | PreflightQC |
| Publisher | ITISYOU |
| Version | **1.0.0** — frozen 2026-08-09 by Product Owner decision (release identity: PreflightQC 1.0.0, ITISYOU, Windows x64, Policy U unsigned) |
| Intended channel | A Merchant of Record (Lemon Squeezy, Gumroad or equivalent) |
| **Status** | **PREPARED ONLY. Nothing published, nothing uploaded, no store account created.** |

Every number in this document is measured from the repository or the built package. There
are **no testimonials, no review counts, no customer counts and no performance claims**,
because none exist and inventing them would be the fastest way to lose the audience this
product is for.

---

## 1. WHAT TO SAY IT IS

**One line**

> Offline technical QA for video deliverables. Check your exports against a platform's
> published delivery specification before you send them.

**Short description (≈50 words)**

> PreflightQC inspects video files on your machine and checks their technical properties
> against the delivery specification for where they are going. It tells you what is wrong,
> what the platform actually requires, and which published source that requirement comes
> from. Nothing is uploaded and nothing is modified.

**Long description**

> PreflightQC is a preflight check for video delivery. Point it at the files you are about
> to hand over, choose the destination preset, and it reports every technical property
> that does not match — with the detected value, the required value, a plain explanation,
> and the first-party source the rule came from, including the date that source was last
> verified.
>
> It reads file metadata using the same tools professional pipelines already rely on:
> FFmpeg's `ffprobe` and MediaInfo, both bundled. It never re-encodes, never repairs,
> never modifies and never uploads. Source files are opened read-only.
>
> Where a platform documents a requirement, PreflightQC checks it. Where a platform
> documents nothing, PreflightQC says so rather than guessing — and where it cannot read
> a property, it reports that too instead of quietly passing the file.

### 1.1 Positioning — what this is not

The product proposition is **verified rules and honest reporting**, not novelty. Two
things to keep out of every listing:

- **AI.** PreflightQC contains no model, makes no inference and has no cloud component.
  The development tooling used to build it is not the product and must never appear in the
  listing.
- **Guarantees.** No listing copy may claim a file will be accepted, that the product is
  certified by or affiliated with any platform, or that detection is perfect. An automated
  check enforces this against this file.

---

## 2. FEATURE LIST

Each line is a capability that exists in the build.

- **12 shipped delivery presets, 170 rules** — Instagram Feed, Reels and Stories; TikTok
  Studio/web, Content Posting API, In-Feed Auction and TopView; YouTube standard upload
  and Shorts; LinkedIn organic, Video Ads and Connected TV.
- **Every rule is traceable.** Each finding names the platform document it came from, the
  URL, the date that source was last verified, and a confidence level.
- **Severity that means something.** A documented hard requirement can fail. A
  recommendation never can — it warns, and says it is a recommendation.
- **Honest unknowns.** Where a platform publishes nothing, or a property cannot be read
  from the file, PreflightQC reports `UNKNOWN` rather than inventing a verdict.
- **Inconclusive detection.** A file that yields no readable video stream is reported as
  inconclusive, never as a pass.
- **Batch checking** with per-file results, filtering by outcome, and a summary readout.
- **Two inspectors, cross-checked.** ffprobe and MediaInfo are run separately and their
  readings reconciled; where they genuinely disagree, that is surfaced rather than hidden.
- **Custom profiles (advanced, file-based)** — a client or in-house delivery
  specification supplied as a JSON profile file is loaded alongside the shipped presets
  and checked the same way. There is no in-app profile editor in this version: a custom
  profile is authored as a file, or supplied by someone who has one, and placed in the
  profiles folder. The shipped presets require no setup of any kind.
- **Reports** — a self-contained HTML report you can send or print, and a CSV with one row
  per finding.
- **Metadata inspector** — 45 normalised properties per file, each marked as read from the
  file, absent from the file, or not determinable.
- **Fully offline.** No account, no licence server, no telemetry, no update check.

---

## 3. SUPPORTED PLATFORMS AND SYSTEM REQUIREMENTS

| Item | Requirement |
| --- | --- |
| Operating system | **Windows 10 x64 or Windows 11 x64** |
| Architecture | x64 only |
| Administrator rights | **Not required.** Installs per-user. |
| Python | Not required — nothing to install separately |
| FFmpeg / MediaInfo | Not required — both are bundled |
| Disk space | ~250 MB installed |
| Download size | ~70 MB installer |
| Network | **None, ever.** Works with the machine fully offline |
| Display | 1280 × 800 or larger recommended; the window will not go below 960 × 640 |

**Not supported in this version:** macOS, Linux, 32-bit Windows, ARM Windows.

---

## 4. PRIVACY AND OFFLINE STATEMENT

Written to be verifiable, not reassuring:

> PreflightQC has no network capability. The installed application contains no HTTP
> client, no socket implementation and no networking library — these were deliberately
> excluded from the build rather than merely left unused. There is no account, no licence
> check, no telemetry, no analytics and no update check.
>
> Your video files are opened read-only. PreflightQC never writes to, moves, renames or
> re-encodes a source file. Reports are written only where you choose to save them.
>
> Nothing about your files, your results or your usage leaves your machine, because there
> is nothing in the product capable of sending it.

Backed by: the packaged application ships no `Qt6Network`, no `_socket`, no `_ssl` and no
TLS library, and an automated test fails the build if any networking import appears
anywhere in the application source.

---

## 5. SCREENSHOT CHECKLIST

Real renders exist for all of these in `docs/design/screens/after/`. For a store listing
they should be re-shot at the release version and with a realistic client batch.

| # | Shot | Shows |
| --- | --- | --- |
| 1 | Empty state | What the product is and the three-step workflow |
| 2 | Mixed batch, complete | The core value: a batch with fails, warnings and inconclusives at a glance |
| 3 | A FAIL with its finding open | Detected vs required, the explanation, the traced source |
| 4 | A recommendation | That a recommendation warns and says so — the severity model in one image |
| 5 | Metadata inspector | Known vs not-present vs not-determined |
| 6 | Preset selector | The breadth of shipped presets |
| 7 | Exported HTML report | The deliverable a user sends to a client |
| 8 | About / notices | Offline claim and third-party licensing, for the sceptical buyer |

**Do not** screenshot placeholder filenames, a licence key field (there is none), or any
state that does not exist in the build.

---

## 6. SUPPORT INFORMATION

| Item | Value |
| --- | --- |
| Support page | `https://itisyou.app/products/preflightqc/support` |
| Legal and licence | `https://itisyou.app/products/preflightqc/legal` |
| Open-source components | `https://itisyou.app/products/preflightqc/source` |
| Product page | `https://itisyou.app/products/preflightqc` |

> **None of these pages exists yet.** They are shown inside the product's About dialog as
> text, and the last one carries an LGPL obligation — see §8. They must be live before any
> listing goes up.

**A support commitment must be decided before listing**, including response time, the
supported-version window, and what happens when a platform changes its specification and a
preset needs updating. That is a business decision this document deliberately does not
make.

---

## 7. LIMITATIONS — STATE THESE IN THE LISTING

A buyer who discovers these after paying is a refund. A buyer who reads them first is a
buyer who trusts the rest of the copy.

- **PreflightQC reads metadata; it does not watch the video.** It cannot judge picture
  quality, framing, audio mix, sync or content.
- **A PASS is not a guarantee of acceptance.** Platforms change requirements without
  notice and apply rules the tool cannot see. PreflightQC reports the file against the
  rules in the selected preset, and names the date each rule's source was verified.
- **Some properties are not measured in this version:** loudness (LUFS/true peak), closed
  GOP, and edit lists. These report as `UNKNOWN` rather than being guessed.
- **Where a platform publishes nothing, there is no rule.** TikTok publishes no codec
  profile, HDR, fast-start or loudness requirement; those report `UNKNOWN`.
- **Custom profiles are file-based.** There is no in-app profile editor: a custom
  profile is a JSON file authored outside the application and placed in the profiles
  folder. An advanced capability; the shipped presets need no setup.
- **The installer is not digitally signed** (if released under the unsigned path,
  Policy U). Required disclosure, stated before purchase, never after:

  > The PreflightQC installer is **not digitally signed** in this version. When you
  > first run it, Windows SmartScreen will show a "Windows protected your PC" warning
  > naming an unknown publisher. This is the expected behaviour for an unsigned
  > installer — it is stated here so you know before buying, not after. To proceed,
  > Windows requires choosing "More info", then "Run anyway". Verify your download
  > first against the SHA-256 checksum published on the product page.
- **One preset per batch.** Mixed-destination batches must be run once per destination.
- **Windows only.** No macOS or Linux build.
- **First stream only.** Multi-stream files are enumerated, but the first video and audio
  stream are what get judged.

---

## 8. DEPENDENCY NOTES THE LISTING DEPENDS ON

| # | Item | State |
| --- | --- | --- |
| D-1 | **EULA** — must be linked from the listing and shown by the installer | Drafted (`packaging/EULA.txt`); **not attorney reviewed, and none is mandated for V1 under the amended G-12 (ADR-G12). The owner's written residual-risk acceptance for 1.0.0 was executed 2026-08-09; removal of the draft banner remains a final-build step** |
| D-2 | **Refund policy** — the Merchant of Record will require one | **Not written.** A business decision, not an engineering one |
| D-3 | **Corresponding-source page** — LGPL obligation, must serve the archived FFmpeg source for three years | **Not live.** See `docs/licensing/CORRESPONDING-SOURCE-PLAN.md` |
| D-4 | **Third-party notices** — FFmpeg LGPLv3, MediaInfo BSD-2-Clause, Qt LGPLv3, and the rest | Generated into the package; shown in About |
| D-5 | **Code-signing certificate** — an unsigned installer will trigger SmartScreen | **Not obtained (G-11 open).** V1 may instead release under **Policy U** (`docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md`): unsigned, with the §7 disclosure mandatory in this listing, `RELEASE-HASHES.txt` published on the product page, and `sign.py verify --expect unsigned` passing. The listing must never imply the download is signed |
| D-6 | **Release version number** | **RESOLVED 2026-08-09: 1.0.0**, frozen in `preflightqc.__version__` (the single authoritative source). No development version string may appear in the listing |
| D-7 | **Price** | Not set |
| **D-8** | **Custom profiles have no in-app editor.** Saved profiles load and validate, but nothing in the interface creates, edits or imports one | **RESOLVED 2026-08-09: V1 ships without an editor.** Custom profiles are described everywhere customer-facing as an advanced, file-based capability — a manually authored or supplied JSON profile file. The feature bullet in §2 and the limitation in §7 carry this wording. The editor remains deferred scope in `docs/FUTURE.md` §3A.3 |

---

## 9. WHAT MUST NOT APPEAR IN THE LISTING

| Forbidden | Why |
| --- | --- |
| "Guaranteed accepted by …" | The product cannot know this. Automatically rejected by the claim guard. |
| "Certified by / approved by / endorsed by" any platform | Untrue, and a trademark problem |
| Testimonials, review counts, user counts | None exist |
| Speed or accuracy percentages | Not measured; would be invented |
| Any AI or LLM claim | The product contains none |
| Screenshots of features that do not exist | Obvious, and worth writing down |
| Platform logos | Trademark. Names may be used descriptively, and are, with a disclaimer |
| Any claim the download is "signed", "verified" or "trusted by Windows" (while under Policy U) | The installer is unsigned; the disclosure in §7 says so. Claiming otherwise is the pretending the unsigned-release policy forbids |

The trademark disclaimer already shipped in the notices and the EULA is the wording to
reuse:

> Instagram, Meta, TikTok, YouTube and LinkedIn are trademarks of their respective owners.
> PreflightQC is not affiliated with, endorsed by or certified by any of them. Their names
> are used descriptively only, to identify the delivery specifications PreflightQC
> validates against.

---

## 10. READINESS

| Item | State |
| --- | --- |
| Product description | **Ready** |
| Feature list | **Ready** |
| OS and system requirements | **Ready** |
| Privacy / offline statement | **Ready and verifiable** |
| Screenshot checklist | **Ready**; real renders exist, re-shoot at release version |
| Limitations | **Ready** |
| Support information | **Blocked** — pages do not exist |
| Refund policy | **Blocked** — not written |
| EULA | **Nearly ready** — G-12 owner risk acceptance executed for 1.0.0 (2026-08-09); removing the draft banner is a final-build step |
| Version number | **Ready** — 1.0.0, frozen 2026-08-09 |
| Certificate | **Blocked** — G-11, **or** released unsigned under Policy U with its disclosure and published hashes (U-1 … U-6 all required) |

**Nothing here may be published until every blocked row above is resolved.**
