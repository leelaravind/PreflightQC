# PREFLIGHTQC — LEGAL REVIEW PACK (GATE G-12)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Prepared for | The qualified software-IP attorney conducting gate G-12 review |
| Product | PreflightQC V1 — closed-source commercial Windows desktop application; offline video-delivery QC; bundles LGPL/BSD third-party binaries |
| Publisher | ITISYOU |
| Status of this pack | Assembled by engineering. **Nothing in it is legal advice, and no clearance is claimed by it.** |
| G-12 | **OPEN.** This pack is the input to the review, not evidence it happened. |
| Amendment note (2026-08-09) | Gate G-12 was amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing & compliance risk acceptance** (`docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`). **This pack has not been reviewed by counsel and is preserved unchanged**: it is now (a) the documented evidence base for the owner's informed risk acceptance, and (b) the ready-to-hand input if professional review is later performed — which the ADR's §7 conditions may require. Questions L-1…L-14 below remain unanswered. |

How to read this pack: §2 lists facts that are mechanically established and continuously
re-verified — you may rely on them as *facts about the artefact* without re-deriving
them. §4 lists the questions that require your professional judgment — engineering has
deliberately not answered them, only framed them. §3 is the document inventory.

---

## 1. SCOPE OF THE ENGAGEMENT

Per spec §26.1 and the licensing gate §8, the review covers:

1. The **commercial licence / EULA** — `packaging/EULA.txt` is the operative text,
   shipped verbatim and shown by the installer.
2. The **third-party notices and licence texts** as shipped —
   `dist/PreflightQC/licenses/`.
3. The **dependency manifest** — `licenses/DEPENDENCY-MANIFEST.json`, generated from the
   built package.
4. The **enumerated questions** in §4 below.

Out of scope (separately gated, not legal-judgment items): code signing (G-11 /
Policy U), clean-machine validation (Phase 13), marketplace publication.

---

## 2. MECHANICALLY ESTABLISHED FACTS — WHAT YOU MAY RELY ON

Each row is enforced by a script or test that **fails the release** if the fact stops
being true. These are facts about the artefact, not legal conclusions. Current suite:
1,295 tests passing, 0 failing.

| # | Fact | Enforced by |
| --- | --- | --- |
| F-1 | Every file in the release package is attributed to exactly one component, checksummed; no unattributed file can ship | `packaging/generate_manifest.py` (fails on any unaccounted file); `test_every_shipped_file_is_attributed_to_a_component` |
| F-2 | Notices and manifest are **generated from the built package**, never hand-maintained; they cannot drift from what ships | Same generator; regenerated on every audit |
| F-3 | No GPL or nonfree FFmpeg component is present: `--enable-gpl`/`--enable-nonfree` absent, every prohibited library disabled, GPL-gated filter list derived from the shipped source's own `configure` rather than remembered | `packaging/scan_prohibited.py`; `TestTheGplFilterListIsDerivedNotRemembered` |
| F-4 | The shipped ffprobe is BtbN `win64-lgpl-shared` `n8.1.2-34-g9b6c8969e0`, **LGPL v3** by construction (`--enable-version3`); its configure line ships verbatim; publisher SHA-256 verified | `packaging/binaries.lock.json`; `fetch_binaries.py` (fails hard on mismatch) |
| F-5 | Version-matched corresponding source for that exact binary is archived, hash-pinned, reproducible byte-for-byte, and verified four independent ways (release tag, commit, commits-ahead, seven library version triplets); a hosting bundle is staged | `packaging/verify_source.py` (7 checks); 26 tests; `CORRESPONDING-SOURCE-READINESS.md` |
| F-6 | ffprobe and MediaInfo run as **separate child processes**; the application never links them | Architecture tests; `linkage: subprocess` in the manifest |
| F-7 | Qt/PySide6 ships as **separate, unmodified, unobfuscated, individually replaceable DLLs** in a one-directory build (never one-file) | `packaging/layout_check.py`; `test_it_is_a_one_dir_build`; `test_the_qt_libraries_ship_as_separate_named_files` |
| F-8 | The package contains **no socket implementation**: no `Qt6Network`, `_socket`, `_ssl`, or TLS transport; no networking import exists anywhere in the application source (checked against the syntax tree) | `test_no_network_capable_library_is_shipped`; `test_nothing_in_the_product_fetches_a_url` |
| F-9 | The EULA's required clauses are present **verbatim**: LGPLv3 named, FFmpeg ownership disclaimed, reverse-engineering carve-out granted (not merely omitted), open-source-licence-prevails clause, three-year source offer, translation obligation, "NOT LEGAL ADVICE" | `TestEulaCarveOuts` (7 tests) |
| F-10 | MediaInfo is the BSD-2-Clause-era CLI (26.05), **libcurl deliberately not shipped**; ZenLib credited | Lock file; `test_no_libcurl_is_shipped` |
| F-11 | All 50 Microsoft VC runtime files are inventoried by exact path and hash, from two provenances (CPython distribution; Qt wheels); the notice quotes the CPython licence's Additional Conditions **verbatim** (a test fails on paraphrase drift); no other Microsoft runtime family ships | `tests/packaging/test_ms_runtime.py` (13 tests); `MS-VC-Redistributable.txt` |
| F-12 | No customer-facing text claims platform acceptance, certification, or endorsement; the guard is negation-aware so required disclaimers do not mask real claims | `reporting/claims.py`; `tests/ui/test_customer_copy.py` |
| F-13 | Every preset rule traces to a declared first-party source with a verification date; staleness is mechanically reported | `staleness_report.py` tests |
| F-14 | The artefacts are currently **unsigned**, and that state is declared and verified rather than hidden (Policy U); no publishable copy may call the download "signed" | `sign.py verify --expect unsigned`; `tests/packaging/test_unsigned_policy.py` (16 tests) |

**Standing invalidation rule:** any change to a shipped binary, dependency, or version
re-opens every affected row automatically — the gates fail closed.

---

## 3. DOCUMENT INVENTORY

Read in this order.

| # | Document | What it is |
| --- | --- | --- |
| 1 | `docs/specification/PREFLIGHTQC-V1-SPEC.md` §21, §26 | The locked product specification's licensing and release-gate requirements — the authority everything below defers to |
| 2 | `docs/licensing/LICENSING-GATE-V1.md` | The compliance analysis and gate checklist, including the 2026-08-09 SPEC LOCK amendment (LGPL v2.1 → v3) and the residual-risk register R-1…R-9 |
| 3 | `packaging/EULA.txt` | **The operative EULA text** (shipped verbatim). Its §9 lists six open questions for you |
| 4 | `docs/licensing/EULA-DRAFT.md` | Drafting rationale per clause |
| 5 | `dist/PreflightQC/licenses/THIRD-PARTY-NOTICES.txt` + `DEPENDENCY-MANIFEST.json` | The generated notices and manifest for the current verification build |
| 6 | `dist/PreflightQC/licenses/` (directory) | Every shipped licence text: LGPL-3.0, LGPL-2.1, GPL-3.0, PSF, BSD, MIT, Apache-2.0, PyInstaller COPYING, `MS-VC-Redistributable.txt`, `CPython-LICENSE.txt` |
| 7 | `docs/licensing/G13-QT-LICENCE-POSTURE.md` | The Qt/PySide6 LGPLv3 compliance route and its open question |
| 8 | `docs/licensing/CORRESPONDING-SOURCE-PLAN.md` + `docs/reports/CORRESPONDING-SOURCE-READINESS.md` | LGPL source-provision compliance: what is staged, the written-offer plan (H-4 is yours to word) |
| 9 | `third-party/licenses/MS-VC-Redistributable.txt` | The Microsoft Distributable Code notice and its §3 pass-through question |
| 10 | `docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md` | Policy U — the declared unsigned release path and its mandatory disclosure |
| 11 | `docs/marketing/MARKETPLACE-LISTING-V1.md` | All prepared customer-facing listing copy, including the claims-discipline rules |
| 12 | `docs/sources/ffmpeg/README.md`, `docs/sources/mediainfo/README.md` | The dependency reviews — both concluded "APPROVED WITH CONDITIONS", one condition being this review |
| 13 | `docs/reports/RELEASE-AUDIT-V1.md`, `docs/reports/G12-AUDIT-V1.md` | The release audit trail and the G-12 mandatory-status audit |

---

## 4. QUESTIONS REQUIRING PROFESSIONAL LEGAL JUDGMENT

Engineering's position, where stated, is an input — not an answer.

### Copyleft / licence architecture

**L-1 — Qt (PySide6) LGPLv3 in a frozen Python bundle.** Is the one-directory PyInstaller
layout — separate, unmodified, replaceable Qt DLLs (fact F-7) — a "suitable shared
library mechanism" under LGPLv3 §4(d)(1)? Engineering calls this route *plausible but
not settled* (licensing gate §4.3, risk R-5; G13 doc). The fallback if you reject it is
a framework change (.NET/Avalonia, ADR-001 §7).

**L-2 — PyInstaller bootloader exception.** The bootloader is GPL-2.0-or-later **with**
an exception permitting closed-source frozen applications. Does the exception cover this
use? (Q-2 / R-6; `PyInstaller-COPYING.txt` ships in the package.)

**L-3 — LGPLv3/GPLv3 "Installation Information" (User Products).** Effect, if any, on a
commercial desktop application delivered as an installer to consumers (EULA §9.1). This
now attaches to *both* LGPLv3 surfaces: FFmpeg (post-amendment) and Qt.

**L-4 — LGPLv3 patent provisions** in commercial distribution (EULA §9.2; licensing
gate §2.0 "what this costs").

**L-5 — Subprocess / "mere aggregation".** ffprobe runs as a child process with
command-line in and JSON out (F-6). The FSF itself calls this line "a legal question,
which ultimately judges will decide" (R-3). Confirm the posture is defensible.

**L-6 — Corresponding-source written offer (H-4).** The three-year offer wording in the
notices and its EULA counterpart; whether the staged hosting arrangement
(`itisyou.app/products/preflightqc/source`, hashes published) satisfies LGPLv3 §4 once
live.

### EULA text

**L-7 — Carve-out breadth.** Is §3.2 (open-source licence prevails; reverse-engineering
carve-out) drafted broadly enough for every jurisdiction of sale? (EULA §9.3)

**L-8 — Governing law and jurisdiction** — deliberately left unstated in the draft for
you to set. (EULA §9.4)

**L-9 — Consumer-law limits** on the warranty disclaimer and liability cap (EULA §§5–6)
per target market; interaction with Merchant-of-Record resale and mandatory withdrawal
or refund rights for digital goods. (EULA §9.5; listing D-2 — no refund policy exists yet)

**L-10 — Translation obligation.** The EULA requires every translation to carry the
carve-outs. Confirm the mechanism (which language controls; how translations get
reviewed) is adequate.

### Third-party terms

**L-11 — Microsoft Distributable Code pass-through.** The notice grounds redistribution
of the CPython-provenance runtime files in CPython's "Additional Conditions" and applies
the same restrictions to the copies arriving inside the Qt wheels, which ship no
Microsoft-specific text (F-11; notice §3). Two sub-questions: (a) does the EULA bind end
users protectively enough to satisfy the pass-through; (b) is the Qt-wheel treatment
sufficient, or should the Microsoft Software License Terms document be obtained and
shipped? (EULA §9.6)

**L-12 — Re-signing third-party DLLs** (contingent). If a distribution channel ever
forces signing of third-party binaries, does signing constitute "modification"?
Engineering's conservative default is to leave them untouched; currently moot under
Policy U. (R-2)

### Product-level

**L-13 — Trademarks.** (a) "PreflightQC" is a working name with **no clearance
performed**; advise on search/registration before commercial launch. (b) Descriptive use
of Instagram/Meta/TikTok/YouTube/LinkedIn marks with the shipped disclaimer — adequate?
(R-8; the disclaimer text is in the notices, EULA and listing)

**L-14 — Patent exposure of inspection.** V1 reads container/stream **metadata** and
performs no encoding; the product statement "reads file metadata; it does not watch the
video" is enforced in copy. Confirm that no residual decode path (R-4) or patent-pool
scope question (R-7) requires attention for an inspection-only tool, and note the FUTURE
items (loudness measurement) that would reopen this.

---

## 5. WHAT WOULD CONSTITUTE G-12 COMPLETION

For the product owner's benefit — the gate closes only when **all** of these exist:

1. A written review outcome from counsel covering §1's four objects.
2. Final EULA text approved (or amended and re-verified against the G-8 clause tests —
   if counsel's edits change required clauses, the tests change **with** justification,
   never silently).
3. Each L-question either answered, or expressly accepted as a residual risk by the
   product owner **on counsel's advice**, in writing.
4. The repository updated to record the outcome (gate table, EULA header, this pack).

Until then: **G-12 remains OPEN**, every shipped artefact continues to say "no legal
clearance is claimed", and the release remains blocked by the spec's own terms.
