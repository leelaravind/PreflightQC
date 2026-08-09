# Page: `itisyou.app/products/preflightqc/source` — PREPARED, NOT PUBLISHED

This page serves the staged bundle `packaging/source-release/` **byte-for-byte** —
seven files, defined normatively in `docs/licensing/CORRESPONDING-SOURCE-PLAN.md`
§5A. The page body below fronts those files; `README.txt` in the bundle carries the
full detail. After upload, re-hash every hosted file over HTTPS against `SHA256SUMS`
and flip `hosting_status` in `packaging/binaries.lock.json` (actions H-1/H-2), and
stand behind the three-year offer (H-3).

---

# PreflightQC — Open-source components & corresponding source

PreflightQC ships eight unmodified FFmpeg binaries (ffprobe and seven libav*/libsw*
libraries) under the GNU Lesser General Public License v3. This page provides the
**complete corresponding source code** for those exact binaries, as the licence
requires. The offer stands for at least **three years** from the date you received
the product, at no charge beyond the cost of distribution.

| File | What it is | SHA-256 |
| --- | --- | --- |
| `ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz` | Complete FFmpeg source for the shipped binaries (release n8.1.2 + 34 commits, commit `9b6c8969e0…`) | `39002bfe54d48326b69c36a0b72231125bb5b408fadc29e14481b5ac2583a224` |
| `ffmpeg-builds-recipe-2437e7b868da.tar.gz` | The BtbN/FFmpeg-Builds build system at the producing commit | `b23920469c23615c539b4965c0bd18b3758c8dc9416b6bef343a83fcf4f310c7` |
| `README.txt` | Which source corresponds to which shipped ffprobe, the verification chain, and reproduction commands | — |
| `SHA256SUMS` | Hashes of every file here | — |
| `COPYING.LGPLv3.txt` | The LGPL v3 licence text | `ea7d049c…363432c9` |
| `COPYING.GPLv3.txt` | GPL v3, incorporated by LGPLv3 | `0b383d5a…ac1171e6b` |
| `ffmpeg-build-configuration.txt` | The verbatim configure line of the shipped build | `ffd89a45…481866e45` |

Both archives are reproducible byte-for-byte from the upstream repositories with the
`git archive` commands in `README.txt` — you can confirm nothing was altered.

MediaInfo (BSD-2-Clause) carries no source-provision obligation; its source is at
`https://github.com/MediaArea/MediaInfo`. The full third-party notices for every
bundled component ship inside the product in `licenses/`.

PreflightQC is published by ITISYOU. Questions about this page:
[support](/products/preflightqc/support).
