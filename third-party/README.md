# third-party/ — RESERVED, EMPTY BY DESIGN

**No binaries exist here, and none are ever committed to this repository.**

## What lives here

```
third-party/
├── README.md               this file                        (committed)
├── licenses/               licence texts for shipped deps    (committed, Phase 12)
└── bin/                    fetched inspector binaries        (GIT-IGNORED)
```

`third-party/bin/` and every binary extension under this tree are blocked by
`.gitignore`. Binaries are **fetched at packaging time** from pinned, checksum-verified
official sources (`packaging/fetch_binaries.py`, `packaging/binaries.lock.json`) and
recorded in the generated dependency manifest.

## What will be fetched

| Component | Source | Licence | Constraint |
| --- | --- | --- | --- |
| `ffprobe.exe` + `libav*.dll` | **BtbN FFmpeg-Builds, `win64-lgpl-shared`** | LGPL 2.1+ | Unmodified, **shared**, no `--enable-gpl`, no `--enable-nonfree`, none of the prohibited components |
| MediaInfo (CLI or library) | `mediaarea.net` or official MediaArea GitHub releases | BSD-2-Clause | **≥ 0.7.63 only** (pinned 26.05), **no GUI**, **no libcurl** |
| ZenLib | Transitive within MediaInfo | zlib | Attribution |

## Sources that are NOT usable

| Source | Why |
| --- | --- |
| `gyan.dev` main Windows FFmpeg builds | *"All builds are 64-bit, static and licensed as GPLv3"* |
| `evermeet.cx` FFmpeg | Built with `--enable-gpl --enable-libx264 --enable-libx265`; Intel-only |
| Any `--enable-nonfree` build | *"will cause the resulting binary to be unredistributable"* |
| Third-party DLL-download sites (dll-files.com, dllme.com, iosninja.io, …) | Not authoritative; supply-chain risk |
| MediaInfo ≤ 0.7.62 | GPL (CLI/GUI) / LGPL (library) — copyleft incompatible with closed source |

## Prohibited components — never bundled

```
libx264      libx265      libxvid      libxavs      libxavs2     libdavs2
frei0r       libcdio      librubberband             libvidstab   avisynth
libsmbclient libaribb24   liblensfun   gmp          libzvbi
libfdk-aac   libnpp       cuda-nvcc    OpenSSL (incompatible combinations)
```

Plus: **no `ffmpeg` encoder binary in V1.**

`packaging/scan_prohibited.py` fails the build on any hit.

## Manual placement during the Phase 1 spike

Phase 1 requires the operator to place manually-obtained, checksum-verified binaries in
`third-party/bin/`. **Phase 1 auto-downloads nothing.** GATE-1 then confirms the ffprobe
build's reported configuration is genuinely LGPL shared before any further work proceeds.

Full obligations: `docs/licensing/LICENSING-GATE-V1.md`.
