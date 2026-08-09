"""Verify the built package matches the layout ADR-001 section 5 specifies.

A layout check sounds like housekeeping; it is not. Several licensing obligations are
*layout* obligations — the shared libraries must be present as separate, identifiable
files, the licence folder must be in the package, and the inspector binaries must sit
where the application resolves them by absolute path rather than anywhere on PATH.

    python packaging/layout_check.py --package DIR
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class Problem:
    detail: str

    def __str__(self) -> str:
        return f"[layout] {self.detail}"


REQUIRED_PATHS: tuple[tuple[str, str], ...] = (
    ("PreflightQC.exe", "the application executable"),
    ("_internal", "the frozen Python runtime (one-dir build)"),
    ("presets", "shipped preset data"),
    ("bin", "bundled inspector binaries"),
    ("licenses", "licence texts and generated notices"),
)

REQUIRED_BIN: tuple[str, ...] = ("ffprobe.exe", "mediainfo.exe")

REQUIRED_LIBAV_PREFIXES: tuple[str, ...] = ("avcodec-", "avformat-", "avutil-", "swresample-")

#: LGPL-3.0 covers both the bundled FFmpeg (via --enable-version3) and Qt/PySide6.
#: LGPL-2.1 is still shipped because LGPLv3 incorporates it by reference and libzvbi is
#: LGPL-2.1-or-later.
REQUIRED_LICENCE_FILES: tuple[str, ...] = (
    "LGPL-3.0.txt",
    "LGPL-2.1.txt",
    "BSD-2-Clause.txt",
    "THIRD-PARTY-NOTICES.txt",
    "DEPENDENCY-MANIFEST.json",
    "ffmpeg-build-configuration.txt",
)


def check(package: Path) -> list[Problem]:
    if not package.is_dir():
        return [Problem(f"package directory does not exist: {package}")]

    problems: list[Problem] = []

    for relative, purpose in REQUIRED_PATHS:
        if not (package / relative).exists():
            problems.append(Problem(f"missing {relative} ({purpose})"))

    bin_dir = package / "bin"
    if bin_dir.is_dir():
        for name in REQUIRED_BIN:
            if not (bin_dir / name).is_file():
                problems.append(Problem(f"missing bin/{name}"))
        for prefix in REQUIRED_LIBAV_PREFIXES:
            if not list(bin_dir.glob(f"{prefix}*.dll")):
                problems.append(
                    Problem(
                        f"no {prefix}*.dll in bin/ — a shared ffprobe build must ship its "
                        "libav libraries as separate, replaceable files"
                    )
                )
        if (bin_dir / "ffmpeg.exe").exists():
            problems.append(Problem("ffmpeg.exe must not be shipped in V1"))

    licences = package / "licenses"
    if licences.is_dir():
        problems.extend(
            Problem(f"missing licenses/{name}")
            for name in REQUIRED_LICENCE_FILES
            if not (licences / name).exists()
        )

    presets = package / "presets"
    if presets.is_dir() and not list(presets.rglob("*.json")):
        problems.append(Problem("presets/ contains no preset documents"))

    # A one-file build has no _internal directory; catching it here is cheaper than
    # discovering the LGPL replaceability problem at the licensing gate.
    if (package / "PreflightQC.exe").is_file() and not (package / "_internal").is_dir():
        problems.append(
            Problem(
                "no _internal/ directory — this looks like a one-file build, which "
                "frustrates the LGPL shared-library-replacement posture"
            )
        )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the shipped package layout")
    parser.add_argument("--package", type=Path, default=REPO_ROOT / "dist" / "PreflightQC")
    args = parser.parse_args()

    problems = check(args.package)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"\nLAYOUT CHECK FAILED: {len(problems)} problem(s).", file=sys.stderr)
        return 1
    print(f"Layout check passed: {args.package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
