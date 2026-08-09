# PREFLIGHTQC — CORRESPONDING-SOURCE HOSTING READINESS

> **AMENDMENT NOTE (2026-08-09, added after this report was written).** Gate G-12 was
> amended by SPEC LOCK v1.1.0 from mandatory attorney review to **owner licensing &
> compliance risk acceptance** — see `docs/decisions/ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md`.
> Statements below describing attorney review as an absolute release prerequisite record
> the gate as it stood when this report was written and are preserved unchanged.
> **No attorney review has occurred, and no legal clearance is claimed.**

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Covers | Release-preparation item #1: FFmpeg corresponding-source hosting for ITISYOU |
| Public URL (future) | `https://itisyou.app/products/preflightqc/source` |
| Staging location | `packaging/source-release/` — **nothing uploaded, nothing published** |
| **Status** | **SOURCE HOSTING READY** |

---

## 1. WHAT WAS VERIFIED TODAY

The full source-to-binary chain was re-verified before staging, not assumed from the
last audit:

| Check | Result |
| --- | --- |
| `packaging/verify_source.py` | **PASS** — "ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz corresponds to the shipped ffprobe", exit 0 |
| Source archive SHA-256 | Re-hashed: `39002bfe…83a224` — equals `binaries.lock.json` `corresponding_source.archive_sha256` |
| Recipe archive SHA-256 | Re-hashed: `b2392046…4f310c7` — equals `build_recipe_source.archive_sha256` |
| FFmpeg provenance | Version string `n8.1.2-34-g9b6c8969e0-20260809` = release `n8.1.2` + 34 commits + commit `9b6c8969e0…` — decomposed and confirmed per plan §2 |
| Library triplets | All seven libav*/libsw* versions in the archive headers equal what the binary prints (verified by check #4 of `verify_source.py`) |
| Build recipe | BtbN/FFmpeg-Builds at `2437e7b868da…`, variant `win64-lgpl-shared`; CI-run attribution caveat recorded in plan §3.3, not smoothed over |
| Configure line | Captured verbatim from the shipped binary; staged as `ffmpeg-build-configuration.txt` |

## 2. WHAT IS STAGED

Seven files in `packaging/source-release/`, hashed in its `SHA256SUMS`, defined
normatively in `docs/licensing/CORRESPONDING-SOURCE-PLAN.md` §5A:

1. `ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz` — the corresponding source (17,014,473 bytes)
2. `ffmpeg-builds-recipe-2437e7b868da.tar.gz` — the build recipe (103,117 bytes)
3. `README.txt` — which source corresponds to which shipped ffprobe, verification chain, three-year offer, reproduction commands
4. `SHA256SUMS` — integrity for downloaders
5. `COPYING.LGPLv3.txt`
6. `COPYING.GPLv3.txt` — incorporated by LGPLv3
7. `ffmpeg-build-configuration.txt`

Upstream source was not altered: both archives are byte-identical copies of the
G-5/G-6 artefacts, themselves reproducible from upstream by deterministic
`git archive` commands recorded in the lock file.

## 3. WHAT REMAINS — HUMAN ACTIONS ONLY

| # | Action |
| --- | --- |
| H-1 | Upload the seven staged files to `https://itisyou.app/products/preflightqc/source` |
| H-2 | Re-hash the hosted files over HTTPS against `SHA256SUMS`; flip `hosting_status` in `binaries.lock.json` from `NOT LIVE`; re-run the audit |
| H-3 | Commit to the three-year offer (business commitment) |
| H-4 | Written-offer wording into EULA — G-12 |
| H-6 | Attorney review — G-12 remains OPEN; no clearance is claimed here |

£0 spend: the domain `itisyou.app` already exists; the bundle is static files.

---

## SOURCE HOSTING READY

Everything a human needs to publish is staged and verified. Publishing itself is
deliberately not done — per the standing constraint, nothing is uploaded.
