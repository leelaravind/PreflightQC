"""Collect the licence texts the release package must ship (gate G-2).

Every text is copied from a **local, authoritative source** — the installed distribution's
own metadata, CPython's own LICENSE.txt, or the FFmpeg source tree we archived for G-5.
Nothing is downloaded and nothing is retyped, because a licence text that has been
paraphrased or truncated is not the licence.

The one text that cannot be collected this way is the Microsoft Visual C++ runtime
notice: Microsoft ships no licence text alongside the runtime DLLs, so the notice is an
authored file (MS-VC-Redistributable.txt) grounded in the "Additional Conditions for this
Windows binary build" section of CPython's own LICENSE.txt — the authoritative statement
accompanying the distribution that supplied the DLLs. This script never overwrites it. If
the file ever goes missing, a fail-visible placeholder is written in its place so the
release audit reports an open action rather than quietly passing.

    python tools/collect_licences.py [--check]
"""

from __future__ import annotations

import argparse
import shutil
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_PACKAGES = Path(sysconfig.get_paths()["purelib"])
FFMPEG_SOURCE = REPO_ROOT / "third-party" / "source" / "ffmpeg-git"
TARGET = REPO_ROOT / "third-party" / "licenses"


@dataclass(frozen=True, slots=True)
class Collected:
    target: str
    source: Path
    why: str


def _dist_licence(pattern: str, *names: str) -> Path | None:
    for directory in sorted(SITE_PACKAGES.glob(pattern)):
        for name in names:
            candidate = directory / name
            if candidate.is_file():
                return candidate
    return None


def plan() -> list[Collected]:
    python_licence = Path(sys.base_prefix) / "LICENSE.txt"
    entries: list[Collected | None] = [
        Collected(
            "LGPL-3.0.txt",
            FFMPEG_SOURCE / "COPYING.LGPLv3",
            "FFmpeg (--enable-version3) and Qt/PySide6",
        ),
        Collected(
            "LGPL-2.1.txt",
            FFMPEG_SOURCE / "COPYING.LGPLv2.1",
            "incorporated by LGPLv3; also covers libzvbi",
        ),
        Collected(
            "GPL-3.0.txt",
            FFMPEG_SOURCE / "COPYING.GPLv3",
            "LGPLv3 incorporates GPLv3 by reference — no GPL component is shipped",
        ),
        Collected(
            "CPython-LICENSE.txt",
            python_licence,
            "CPython (PSF-2.0) and the third-party libraries it bundles, including libffi",
        ),
    ]

    apache = _dist_licence("packaging-*.dist-info", "licenses/LICENSE.APACHE")
    if apache is not None:
        entries.append(Collected("Apache-2.0.txt", apache, "OpenSSL 3.x"))

    for target, pattern, why in (
        ("BSD-3-Clause-Pallets.txt", "markupsafe-*.dist-info", "MarkupSafe"),
        ("MIT-jsonschema.txt", "jsonschema-*.dist-info", "jsonschema"),
        (
            "MIT-jsonschema-specifications.txt",
            "jsonschema_specifications-*.dist-info",
            "jsonschema-specifications",
        ),
        ("MIT-referencing.txt", "referencing-*.dist-info", "referencing"),
        ("MIT-rpds-py.txt", "rpds_py-*.dist-info", "rpds-py"),
        ("MIT-attrs.txt", "attrs-*.dist-info", "attrs"),
        ("BSD-3-Clause-Jinja2.txt", "jinja2-*.dist-info", "Jinja2"),
        ("PSF-2.0-typing-extensions.txt", "typing_extensions-*.dist-info", "typing-extensions"),
        ("PyInstaller-COPYING.txt", "pyinstaller-*.dist-info", "PyInstaller bootloader exception"),
    ):
        found = _dist_licence(
            pattern, "licenses/LICENSE", "licenses/LICENSE.txt", "licenses/COPYING",
            "LICENSE", "LICENSE.txt", "COPYING", "COPYING.txt",
        )
        entries.append(Collected(target, found, why) if found is not None else None)

    return [entry for entry in entries if entry is not None]


#: Written ONLY if the authored notice has gone missing. Contains the word
#: PLACEHOLDER, which generate_manifest.py detects and reports as an open action —
#: a missing notice must never regenerate as something that looks resolved.
MS_PLACEHOLDER = """\
MICROSOFT VISUAL C++ RUNTIME — NOTICE MISSING
=============================================

THIS FILE IS A PLACEHOLDER. IT IS NOT A LICENCE AND NOT THE REAL NOTICE.

The authored Microsoft Distributable Code notice for the Visual C++ runtime
components (VCRUNTIME140*.dll, MSVCP140*.dll, ucrtbase.dll and the
api-ms-win-* forwarders) normally lives at
third-party/licenses/MS-VC-Redistributable.txt in the repository, grounded in
the "Additional Conditions for this Windows binary build" section of
CPython's LICENSE.txt. It was not found, so this placeholder was written in
its place to keep the gap visible.

Restore the authored notice from version control before release. The release
audit reports this file as an open action for as long as it remains a
placeholder.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect licence texts for the package")
    parser.add_argument("--check", action="store_true", help="report only; copy nothing")
    args = parser.parse_args()

    TARGET.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    copied = 0

    for entry in plan():
        if not entry.source.is_file():
            missing.append(f"{entry.target}: source not found at {entry.source} ({entry.why})")
            continue
        destination = TARGET / entry.target
        if args.check:
            if not destination.is_file():
                missing.append(f"{entry.target}: not present in {TARGET}")
            continue
        shutil.copyfile(entry.source, destination)
        copied += 1
        print(f"  {entry.target:36} <- {entry.source.name}   [{entry.why}]")

    placeholder = TARGET / "MS-VC-Redistributable.txt"
    if not args.check and not placeholder.is_file():
        placeholder.write_text(MS_PLACEHOLDER, encoding="utf-8")
        print(f"  {'MS-VC-Redistributable.txt':36} <- PLACEHOLDER — human action required")
    elif args.check and not placeholder.is_file():
        missing.append("MS-VC-Redistributable.txt: not present")

    for problem in missing:
        print(f"[licences] {problem}", file=sys.stderr)
    if missing:
        return 1
    if not args.check:
        print(f"\nCollected {copied} licence texts into {TARGET}")
    else:
        print(f"All expected licence texts present in {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
