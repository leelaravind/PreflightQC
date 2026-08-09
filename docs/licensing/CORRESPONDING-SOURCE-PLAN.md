# PREFLIGHTQC — CORRESPONDING SOURCE PLAN (GATE G-5 / G-6)

| Field | Value |
| --- | --- |
| Date | 2026-08-09 |
| Covers | Gates G-5 (version-matched source archived and hosted) and G-6 (build recipe recorded and shipped) |
| Engineering status | **DONE** — source identified, obtained, proven to correspond, hashed, reproducible, and mechanically verified on every audit |
| Remaining | **Publishing.** A release domain must exist and serve two files. That is an operations task, not an engineering one. |
| Legal status | **No clearance claimed.** G-12 attorney review still applies to this plan. |

---

## 1. WHAT THE OBLIGATION ACTUALLY IS

PreflightQC ships eight unmodified FFmpeg binaries — `ffprobe.exe` and seven `libav*` /
`libsw*` DLLs — under **LGPL-3.0-or-later**. It does not link them; it runs `ffprobe` as a
subprocess. That reduces the obligation but does not remove it: we are still a
**distributor of LGPL binaries**, so recipients are entitled to the **corresponding
source** for those binaries.

Two distinctions do the work here, and both are easy to get wrong:

| Not sufficient | Required |
| --- | --- |
| "The latest FFmpeg source" | The source of **this** binary |
| "A link to ffmpeg.org" | Source **we** make available, on the same terms as the binary |

The second is why a bare upstream link fails: upstream may retire a tag, and the offer
must survive that. LGPL §4(d)/§6 contemplate either accompanying the source or a written
offer valid for three years; we plan for the latter, served from our own release host.

---

## 2. WHAT WAS SHIPPED, EXACTLY

The binary self-reports:

```
ffprobe version n8.1.2-34-g9b6c8969e0-20260809
```

That string is a `git describe`, and it decomposes into three independently checkable
facts:

| Part | Meaning | Verified against |
| --- | --- | --- |
| `n8.1.2` | release tag `n8.1.2` | the source tree's `RELEASE` file, which reads `8.1.2` |
| `-34-` | 34 commits after that tag | GitHub's compare API: `ahead_by: 34`, `behind_by: 0` |
| `-g9b6c8969e0` | at commit `9b6c8969e0` | commit `9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b`, dated 2026-07-31 |

A fourth, independent check ties the source to the binaries rather than to the version
string: the seven library version triplets the binary prints must equal the seven declared
in the source headers.

| Library | Binary reports | Source declares |
| --- | --- | --- |
| libavutil | 60.26.102 | 60.26.102 |
| libavcodec | 62.28.102 | 62.28.102 |
| libavformat | 62.12.102 | 62.12.102 |
| libavdevice | 62.3.102 | 62.3.102 |
| libavfilter | 11.14.102 | 11.14.102 |
| libswscale | 9.5.102 | 9.5.102 |
| libswresample | 6.3.102 | 6.3.102 |

**All seven match.** Nothing here is asserted from a filename.

> **What was wrong before.** The repository held `ffmpeg-9.0.tar.xz` — a *newer major
> release* than the 8.1.2 binary. It would have looked like compliance on a shelf and
> satisfied nothing. That is precisely the near-miss this plan exists to prevent.

---

## 3. THE TWO ARCHIVES

### 3.1 Corresponding source (G-5)

| Field | Value |
| --- | --- |
| File | `third-party/source/ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz` |
| Size | 17,014,473 bytes |
| SHA-256 | `39002bfe54d48326b69c36a0b72231125bb5b408fadc29e14481b5ac2583a224` |
| Built by | `git archive --format=tar.gz --prefix=ffmpeg-n8.1.2-34-g9b6c8969e0/ 9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b` |
| Contains | `COPYING.LGPLv3`, `COPYING.LGPLv2.1`, `LICENSE.md`, `configure`, and the full 10,138-file tree |

### 3.2 Build recipe (G-6)

| Field | Value |
| --- | --- |
| File | `third-party/source/ffmpeg-builds-recipe-2437e7b868da.tar.gz` |
| Size | 103,117 bytes |
| SHA-256 | `b23920469c23615c539b4965c0bd18b3758c8dc9416b6bef343a83fcf4f310c7` |
| Repository | `BtbN/FFmpeg-Builds` at `2437e7b868da3c11872367b15f3c613b87c24819` |
| Variant | `variants/win64-lgpl-shared.sh` → `defaults-lgpl-shared.sh` → `defaults-lgpl.sh` |

The recipe is worth having for its own sake, because it independently corroborates the
licence posture the whole SPEC LOCK amendment rests on. `variants/defaults-lgpl.sh` reads,
verbatim:

```sh
FF_CONFIGURE="--enable-version3 --disable-debug"
...
LICENSE_FILE="COPYING.LGPLv3"
```

So the LGPL variant **is LGPLv3 by construction**, and `--enable-gpl` exists only in
`defaults-gpl.sh` while `--enable-nonfree` exists only in the `*-nonfree` variants. The
build we ship structurally cannot carry either.

### 3.3 How the recipe commit was identified — and its one weakness

BtbN's release metadata does **not** name the FFmpeg-Builds commit it was built from
(`target_commitish` is just `master`, and the release body is empty). The commit was
therefore taken from the public CI run that produced the release:

- workflow *Build FFmpeg*, run **#3054**, `head_sha` `2437e7b868da…`
- started 2026-08-09T12:09:09Z, concluded **success** 13:28:11Z
- release `autobuild-2026-08-09-13-03` published 13:04:44Z

**This is an attribution, not a publisher declaration.** It is well-corroborated — the
timing brackets the release and the recipe reproduces the shipped configure line's
licence-relevant flags — but it is the one link in the chain that rests on inference
rather than on a hash. It is recorded that way in `binaries.lock.json` and flagged here
rather than smoothed over.

---

## 4. WHY THE ARCHIVES ARE NOT IN GIT

They are 17 MB of somebody else's source, and Git is the wrong container for that.

What **is** committed is everything needed to rebuild them **byte-for-byte**: the upstream
repository, the commit, the prefix, the exact command, and the expected SHA-256.
`git archive` is deterministic for a fixed commit and prefix, which was confirmed by
generating the archive twice and getting an identical hash.

```
python tools/fetch_corresponding_source.py          # rebuild if absent, then verify
python tools/fetch_corresponding_source.py --force  # rebuild unconditionally
```

This is a stronger position than committing a blob would give us: a recipient can
reproduce our archive from upstream and confirm we did not alter it.

---

## 5. MECHANISED VERIFICATION

`packaging/verify_source.py` is run by the release audit and fails the build on any
mismatch. It re-derives correspondence rather than trusting the lock file:

| # | Check |
| --- | --- |
| 1 | The archive exists |
| 2 | Its SHA-256 equals the value in `binaries.lock.json` |
| 3 | The archive's `RELEASE` equals the release in the binary's version string |
| 4 | Each of the seven library versions in the archive equals what the binary prints |
| 5 | The recorded commit matches the `-g<hash>` the binary reports |
| 6 | The recorded commits-ahead matches the `-<n>-` the binary reports |
| 7 | A hosting URL is recorded at all |

`tests/packaging/test_corresponding_source.py` covers it with 26 tests, most of them
**negative**: a one-patch release difference, a single library micro difference, a missing
library, an unparseable version string, a wrong hash, a wrong commit, an empty hosting
URL. A verifier that only ever says yes would be worse than none, so the tests are
weighted towards proving it says no.

---

## 6. WHAT REMAINS — AND WHO HAS TO DO IT

Everything below needs a human with access to the release infrastructure. **None of it can
be closed by writing more code.**

| # | Action | Why it cannot be automated here |
| --- | --- | --- |
| **H-1** | Stand up the release host and publish both archives beside the installer | No release domain exists yet; `hosting_url` is a documented `PLACEHOLDER` |
| **H-2** | Replace `hosting_url` in `binaries.lock.json` with the real URLs and re-run the audit | Depends on H-1 |
| **H-3** | Commit to serving them for **three years** after the last distribution of the corresponding binary | A business commitment, not a build artefact |
| **H-4** | Put the written offer into the EULA and `THIRD-PARTY-NOTICES.txt` | Draft text exists; wording is for G-12 |
| **H-5** | Re-run this whole process on **every** inspector version bump | The lock file's rework trigger; the audit fails closed if source and binary diverge |
| **H-6** | Attorney review (G-12) | Explicitly non-automatable |

### 6.1 Standing rule

> Any change to the shipped ffprobe — including a rebuild of the same FFmpeg release —
> invalidates §3. The archives, hashes and hosted files must be regenerated **before** the
> new binary ships. `packaging/verify_source.py` enforces this by failing the audit, so
> the failure mode is a blocked release, never a silent mismatch.

---

## 7. STATUS

| Gate | Engineering | Remaining |
| --- | --- | --- |
| **G-5** | **PASS** — correct source identified, obtained, proven to correspond four ways, hashed, reproducible, mechanically verified | H-1, H-2, H-3 (hosting) |
| **G-6** | **PASS** — configure line captured verbatim and shipped; build recipe archived at the identified commit | H-1, H-2 (hosting); recipe-commit attribution noted in §3.3 |
