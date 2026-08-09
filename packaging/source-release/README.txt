PREFLIGHTQC — CORRESPONDING SOURCE FOR THE BUNDLED FFMPEG LIBRARIES
===================================================================

This page provides the complete corresponding source code for the FFmpeg
binaries distributed with PreflightQC, as required by the GNU Lesser General
Public License version 3 (LGPLv3).

This offer is valid for at least three years from the date you received the
product, at no charge beyond the cost of distribution.

Published by: ITISYOU
Product:      PreflightQC (Windows x64)
Contact:      https://itisyou.app/products/preflightqc/support


WHAT SOURCE CORRESPONDS TO WHAT BINARY
--------------------------------------

PreflightQC ships these eight unmodified FFmpeg files, built by the
BtbN/FFmpeg-Builds project (variant win64-lgpl-shared):

    bin/ffprobe.exe
    bin/avcodec-62.dll
    bin/avdevice-62.dll
    bin/avfilter-11.dll
    bin/avformat-62.dll
    bin/avutil-60.dll
    bin/swresample-6.dll
    bin/swscale-9.dll

The shipped ffprobe self-reports its version as:

    ffprobe version n8.1.2-34-g9b6c8969e0-20260809

That version string is a git describe: FFmpeg release tag n8.1.2, 34 commits
ahead of the tag, at commit 9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b
(2026-07-31). The archive below is the source tree at exactly that commit.

FILES ON THIS PAGE
------------------

1. ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz
   The complete FFmpeg source tree for the shipped binaries.
   SHA-256: 39002bfe54d48326b69c36a0b72231125bb5b408fadc29e14481b5ac2583a224
   Produced from https://github.com/FFmpeg/FFmpeg.git by:
     git archive --format=tar.gz --prefix=ffmpeg-n8.1.2-34-g9b6c8969e0/ \
         9b6c8969e05b4f0b29f0f85cd501be6b3e582e6b
   git archive is deterministic for a fixed commit and prefix, so you can
   reproduce this archive yourself from the FFmpeg repository and confirm the
   hash — the source has not been altered in any way.

2. ffmpeg-builds-recipe-2437e7b868da.tar.gz
   The BtbN/FFmpeg-Builds build system at the commit that produced the shipped
   binaries (build scripts, container definitions, and the win64-lgpl-shared
   variant configuration).
   SHA-256: b23920469c23615c539b4965c0bd18b3758c8dc9416b6bef343a83fcf4f310c7
   Produced from https://github.com/BtbN/FFmpeg-Builds.git by:
     git archive --format=tar.gz --prefix=FFmpeg-Builds-2437e7b868da/ \
         2437e7b868da3c11872367b15f3c613b87c24819

3. ffmpeg-build-configuration.txt
   The exact configure line the shipped binary reports, captured verbatim from
   running the installed ffprobe.

4. COPYING.LGPLv3.txt and COPYING.GPLv3.txt
   The GNU Lesser General Public License version 3, and the GNU General Public
   License version 3 which the LGPLv3 incorporates by reference. These texts
   are also present inside the source archive.

5. SHA256SUMS
   SHA-256 hashes of every file above. Verify with:
     sha256sum -c SHA256SUMS         (Linux/macOS)
     Get-FileHash <file> -Algorithm SHA256   (Windows PowerShell)

HOW THE MATCH WAS VERIFIED
--------------------------

- The archive's RELEASE file reads 8.1.2, matching the release in the
  binary's version string.
- The seven libav*/libsw* library version triplets declared in the archive's
  version headers are identical to the seven versions the shipped binary
  prints (libavutil 60.26.102, libavcodec 62.28.102, libavformat 62.12.102,
  libavdevice 62.3.102, libavfilter 11.14.102, libswscale 9.5.102,
  libswresample 6.3.102).
- The commit and commits-ahead count in the version string were confirmed
  against the FFmpeg repository.

LICENCE
-------

The FFmpeg build distributed with PreflightQC is configured with
--enable-version3 and is licensed under the GNU Lesser General Public License
version 3 (COPYING.LGPLv3.txt). PreflightQC does not own FFmpeg; FFmpeg is the
property of its copyright holders. https://ffmpeg.org/

MediaInfo, also distributed with PreflightQC, is BSD-2-Clause licensed and
carries no source-provision obligation; its source is available at
https://github.com/MediaArea/MediaInfo.
