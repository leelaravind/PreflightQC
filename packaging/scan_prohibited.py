"""Release gate G-3 / G-4 / G-7: prohibited-component scan.

Fails the build. Never warns and continues.

This is the mechanical backstop for the whole FFmpeg licensing posture: if a GPL or
nonfree component reaches the package, every other compliance artefact in the release is
describing something that is not what shipped.

**How it decides, and why not the obvious way.**

The obvious implementation — search the shipped binaries for the string ``libx264`` —
does not work, and its failure mode is the dangerous direction. Every ``libav*`` DLL
embeds the build's full configure line, which contains ``--disable-libx264``; and
``avcodec`` legitimately contains the literal ``x264 - core`` because the H.264 decoder
reads that banner out of SEI user data. Run naively against this fully compliant package,
that scan reports **104 violations, all false**. A gate that fails on every good build
gets switched off, and then it protects nothing.

So the scan asks two questions that have real answers:

1. **What does the build say it linked?** — the configure string, parsed flag-aware, via
   the same :func:`audit_configuration` the application uses. One implementation of the
   policy, not three.
2. **What can the binary actually do?** — its own ``-encoders`` / ``-decoders`` /
   ``-filters`` / ``-demuxers`` / ``-muxers`` / ``-protocols`` listings. A linked library
   registers capabilities; an unlinked one cannot. This is behavioural evidence rather
   than textual coincidence.

    python packaging/scan_prohibited.py [--package DIR]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from preflightqc.platform.binaries import (  # noqa: E402 - path set up above
    PROHIBITED_COMPONENTS,
    audit_configuration,
    licence_version,
)

#: Binaries that must never be present, whatever their build.
PROHIBITED_FILENAMES: tuple[str, ...] = (
    "ffmpeg.exe",
    "ffmpeg",
    "ffplay.exe",
    "x264.exe",
    "x265.exe",
    "mediainfo-gui.exe",
    "MediaInfo.exe.gui",
    "libcurl.dll",
)

#: The capability listings the scan requires. If one of these cannot be produced, the
#: build has not been proven clean and the gate fails — "could not check" is not "clean".
CAPABILITY_LISTS: tuple[str, ...] = (
    "encoders",
    "decoders",
    "filters",
    "demuxers",
    "muxers",
    "protocols",
    "devices",
)

#: Capabilities a prohibited library registers under a name that is *not* the library
#: name. Without these, disabling the library and disabling only its obvious alias would
#: look identical to the scan.
#:
#: Deliberately NOT an alias for ``avisynth``: ``avs``. That is the Chinese AVS video
#: codec, which is unrelated and present in every FFmpeg build — using it as an alias
#: made this scan report a violation against a compliant package.
CAPABILITY_ALIASES: dict[str, tuple[str, ...]] = {
    "librubberband": ("rubberband",),
    "libvidstab": ("vidstabdetect", "vidstabtransform"),
    "frei0r": ("frei0r", "frei0r_src"),
    "libdvdread": ("dvdvideo",),
    "libdvdnav": ("dvdvideo",),
    "libcdio": ("libcdio",),
    "libnpp": ("scale_npp", "transpose_npp", "sharpen_npp"),
    "decklink": ("decklink",),
    "avisynth": ("avisynth",),
    "libsmbclient": ("smb",),
}

#: Filters FFmpeg gates behind ``--enable-gpl`` in its *own* tree, i.e. with no external
#: library involved. If any of these is present, the build is GPL whatever its configure
#: line claims.
#:
#: This list is not from memory. It was extracted from the ``*_filter_deps="… gpl …"``
#: declarations in the ``configure`` of the exact source that produced the shipped binary
#: (``third-party/source/ffmpeg-n8.1.2-34-g9b6c8969e0.tar.gz``), and a test regenerates it
#: from that archive so it cannot silently go stale.
#:
#: Getting this from memory produced two wrong entries on the first attempt — ``geq`` and
#: ``pp``, neither of which is GPL-gated in FFmpeg 8.1 — which would have failed a clean
#: build. Hence: derive, do not recall.
GPL_ONLY_BUILTIN_FILTERS: tuple[str, ...] = (
    "blackframe",
    "boxblur",
    "boxblur_opencl",
    "colormatrix",
    "cover_rect",
    "cropdetect",
    "delogo",
    "eq",
    "find_rect",
    "fspp",
    "histeq",
    "hqdn3d",
    "interlace",
    "kerndeint",
    "mcdeint",
    "mpdecimate",
    "mptestsrc",
    "nnedi",
    "owdenoise",
    "perspective",
    "phase",
    "pp7",
    "pullup",
    "repeatfields",
    "sab",
    "signature",
    "smartblur",
    "spp",
    "stereo3d",
    "super2xsai",
    "tinterlace",
    "uspp",
    "vaguedenoiser",
)

#: A shared library whose name has been obfuscated breaks the LGPL checklist rule that
#: the user must be able to identify and replace it.
_EXPECTED_LIBAV = re.compile(
    r"^(avcodec|avformat|avutil|avdevice|avfilter|swscale|swresample)[-_]", re.I
)

#: Library names that must not appear as a shipped DLL at all. libpostproc is GPL-only
#: and was removed from FFmpeg 8.x; its presence would mean a different, GPL build.
PROHIBITED_DLL_PREFIXES: tuple[str, ...] = ("postproc",)

#: Capability names are lowercase with digits, hyphens and underscores; the flag columns
#: are uppercase letters and dots. Taking the first token that looks like a name picks
#: the right column across every listing format ffprobe emits, which are not uniform:
#: ``-encoders`` uses a six-character flag column, ``-demuxers`` a three-character one,
#: and ``-protocols`` prints bare indented names under Input:/Output: headings.
_NAME_TOKEN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True, slots=True)
class Violation:
    check: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.check}] {self.detail}"


def _run(binary: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary), "-hide_banner", *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def parse_listing(text: str) -> frozenset[str]:
    """Pull the capability names out of one ``ffprobe -<listing>`` block."""
    names: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        # Headings ("Encoders:", "Input:"), legends (" D.. = Demuxing supported") and the
        # "---" separator carry no capability name.
        if not line or line.endswith(":") or "=" in line or set(line) <= {"-"}:
            continue
        for token in line.split():
            if _NAME_TOKEN.match(token):
                names.add(token)
                break
    return frozenset(names)


def capability_names(binary: Path, listing: str) -> frozenset[str] | None:
    """Every capability name the binary reports for one listing, or None if it failed."""
    try:
        result = _run(binary, f"-{listing}")
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 and not result.stdout:
        return None
    return parse_listing(result.stdout)


def _normalise(name: str) -> str:
    return name.replace("-", "_").lower()


def scan_capabilities(binary: Path) -> list[Violation]:
    """Gate G-3 — prove by behaviour that no prohibited component is linked in."""
    violations: list[Violation] = []
    available: set[str] = set()

    for listing in CAPABILITY_LISTS:
        names = capability_names(binary, listing)
        if names is None:
            violations.append(
                Violation(
                    "G-3",
                    f"{binary.name} could not produce its -{listing} listing, so the build "
                    "cannot be proven free of prohibited components",
                )
            )
            continue
        available |= names

    if not available:
        return violations

    for component in PROHIBITED_COMPONENTS:
        candidates = {_normalise(component), _normalise(component).removeprefix("lib")}
        candidates |= {_normalise(alias) for alias in CAPABILITY_ALIASES.get(component, ())}
        # A bare 'lib'-stripped name is too generic for a few components; require the
        # full name or a declared alias for those.
        if component in {"libcdio", "decklink"}:
            candidates.discard(_normalise(component).removeprefix("lib"))
        hits = sorted(candidates & available)
        if hits:
            violations.append(
                Violation(
                    "G-3",
                    f"{binary.name} registers capabilities from prohibited component "
                    f"{component}: {hits}",
                )
            )

    gpl_builtins = sorted({f for f in GPL_ONLY_BUILTIN_FILTERS if f in available})
    if gpl_builtins:
        violations.append(
            Violation(
                "G-3",
                f"{binary.name} provides GPL-only built-in filters {gpl_builtins}, which "
                "only exist in an --enable-gpl build",
            )
        )
    return violations


def scan_ffprobe_configuration(package: Path) -> list[Violation]:
    """Gate G-4 — read the configuration the shipped binary reports about itself."""
    candidates = sorted(package.rglob("ffprobe.exe")) + sorted(package.rglob("ffprobe"))
    if not candidates:
        return [Violation("G-4", "no ffprobe found in the package")]

    violations: list[Violation] = []
    for binary in candidates:
        try:
            result = _run(binary, "-version")
        except (OSError, subprocess.SubprocessError) as exc:
            violations.append(Violation("G-4", f"could not run {binary}: {exc}"))
            continue
        text = f"{result.stdout}\n{result.stderr}"

        # One implementation of the policy. The application, the Phase 1 spike and this
        # gate all call the same function, so they cannot drift apart.
        for finding in audit_configuration(text):
            violations.append(Violation("G-4", f"{binary.name} configuration enables {finding}"))

        if "--enable-shared" not in text:
            violations.append(
                Violation(
                    "G-4",
                    f"{binary.name} is not a --enable-shared build; a static build forces "
                    "the LGPL object-file/relink route",
                )
            )
        if licence_version(text) not in {"LGPL-2.1-or-later", "LGPL-3.0-or-later"}:
            violations.append(Violation("G-4", f"{binary.name} licence version not recognised"))

        violations.extend(scan_capabilities(binary))
    return violations


def scan_filenames(package: Path) -> list[Violation]:
    forbidden = {name.lower() for name in PROHIBITED_FILENAMES}
    return [
        Violation("G-3", f"prohibited file present: {path.relative_to(package)}")
        for path in sorted(package.rglob("*"))
        if path.is_file() and path.name.lower() in forbidden
    ]


def scan_dll_names(package: Path) -> list[Violation]:
    """Gate G-7 — shared-library filenames must not be obfuscated."""
    violations: list[Violation] = []
    bin_dirs = [d for d in package.rglob("bin") if d.is_dir()] or [package]
    for directory in bin_dirs:
        for dll in sorted(directory.glob("*.dll")):
            stem = dll.stem.lower()
            if stem.startswith(("av", "sw")) and not _EXPECTED_LIBAV.match(dll.stem):
                violations.append(
                    Violation("G-7", f"{dll.name} looks like a renamed libav* library")
                )
            if stem.startswith(PROHIBITED_DLL_PREFIXES):
                violations.append(
                    Violation("G-3", f"{dll.name} is a GPL-only FFmpeg library")
                )
    return violations


def scan_licence_folder(package: Path) -> list[Violation]:
    """Gate G-2 — the notices must actually be in the package."""
    folder = package / "licenses"
    if not folder.is_dir():
        return [Violation("G-2", "no licenses/ folder in the package")]
    required = (
        "THIRD-PARTY-NOTICES.txt",
        "DEPENDENCY-MANIFEST.json",
        "LGPL-3.0.txt",
        "LGPL-2.1.txt",
        "GPL-3.0.txt",
        "BSD-2-Clause.txt",
    )
    return [
        Violation("G-2", f"missing from licenses/: {name}")
        for name in required
        if not (folder / name).exists()
    ]


def scan(package: Path) -> list[Violation]:
    if not package.is_dir():
        return [Violation("G-3", f"package directory does not exist: {package}")]
    return [
        *scan_filenames(package),
        *scan_dll_names(package),
        *scan_licence_folder(package),
        *scan_ffprobe_configuration(package),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Release gate G-3/G-4/G-7 scan")
    parser.add_argument("--package", type=Path, default=REPO_ROOT / "dist" / "PreflightQC")
    args = parser.parse_args()

    violations = scan(args.package)
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(
            f"\nGATE FAILED: {len(violations)} prohibited-component violation(s). "
            "This package must not be released.",
            file=sys.stderr,
        )
        return 1
    print(f"Prohibited-component scan clean: {args.package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
