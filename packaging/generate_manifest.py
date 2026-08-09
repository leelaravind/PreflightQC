"""Release gates G-1 and G-2: generate the dependency manifest and third-party notices.

Both are generated **from the built package**, never hand-maintained. A hand-written
manifest drifts from what actually shipped within one release, and a notice file that
describes a different build than the one in the installer is worse than no notice file:
it is a confident, checkable, false statement.

**The completeness rule has teeth.** Every file in the package is attributed to exactly
one component. There is no "miscellaneous" bucket, and an unattributed file fails G-1 —
because an unattributed file is an unattributed licence. That is what caught the fact
that the package was shipping OpenSSL and Qt libraries nobody had written a notice for.

    python packaging/generate_manifest.py --package DIR [--out DIR]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"

#: Notices that must appear verbatim. These are contractual, not editorial.
FFMPEG_NOTICE = "This software uses libraries from the FFmpeg project under the LGPLv3."
FFMPEG_DISCLAIMER = (
    "PreflightQC does not own FFmpeg. FFmpeg is the property of its copyright holders, "
    "and is used here under the terms of the GNU Lesser General Public License v3."
)

#: The shipped build carries --enable-version3, which upgrades FFmpeg from LGPL v2.1 to
#: LGPL v3. The notice must state the licence the binary is actually under; saying v2.1
#: over a v3 build would be a false statement in a legal notice.
FFMPEG_VERSION3_NOTE = (
    "The bundled FFmpeg build is configured with --enable-version3, which places it "
    "under the GNU Lesser General Public License version 3. The libraries gmp and "
    "libaribb24 are themselves LGPL v3 and are enabled by that option."
)
MEDIAINFO_NOTICE = (
    "This product uses MediaInfo library, Copyright (c) 2002-2026 MediaArea.net SARL. "
    "https://mediaarea.net/MediaInfo"
)
ZENLIB_NOTICE = "ZenLib — (c) MediaArea.net SARL, zlib license."


@dataclass(frozen=True, slots=True)
class BundledComponent:
    """A third-party component identified by the files it contributes to the package."""

    name: str
    version: str
    licence: str
    notice: str
    patterns: tuple[str, ...]
    linkage: str = "dynamic"
    source_url: str = ""
    licence_text: str = ""


#: Everything the frozen application bundles, keyed by the files it puts in the package.
#:
#: Patterns are matched against package-relative POSIX paths. Order matters only in that
#: each file is attributed to the first component that claims it.
#:
#: `Qt6Network` is deliberately absent: packaging/build.py removes it, and if a future
#: build reinstates it the file becomes unattributed and G-1 fails — which is the point.
BUNDLED: tuple[BundledComponent, ...] = (
    BundledComponent(
        name="Qt 6 (via PySide6)",
        version="6.8.1.1",
        licence="LGPL-3.0-only",
        notice=(
            "This software uses the Qt toolkit via PySide6 under the GNU Lesser General "
            "Public License version 3. Qt is a trademark of The Qt Company Ltd. The Qt "
            "libraries are shipped as separate, unmodified, unobfuscated DLL files in "
            "_internal/PySide6/ and may be replaced by the user with compatible versions."
        ),
        patterns=("_internal/PySide6/*", "_internal/PySide6/**"),
        source_url="https://download.qt.io/official_releases/QtForPython/",
        licence_text="LGPL-3.0.txt",
    ),
    BundledComponent(
        name="Shiboken6",
        version="6.8.1.1",
        licence="LGPL-3.0-only",
        notice="Shiboken6 binding runtime, part of the Qt for Python project, LGPLv3.",
        patterns=("_internal/shiboken6/**",),
        source_url="https://download.qt.io/official_releases/QtForPython/",
        licence_text="LGPL-3.0.txt",
    ),
    BundledComponent(
        name="OpenSSL",
        version="3.x (bundled with CPython)",
        licence="Apache-2.0",
        notice=(
            "This product includes software developed by the OpenSSL Project for use in "
            "the OpenSSL Toolkit (https://www.openssl.org/). OpenSSL 3.x is licensed "
            "under the Apache License 2.0. PreflightQC makes no network connections; "
            "these libraries are present because CPython's standard library links them."
        ),
        patterns=("_internal/libcrypto-*.dll", "_internal/libssl-*.dll", "_internal/_ssl.pyd"),
        source_url="https://www.openssl.org/source/",
        licence_text="Apache-2.0.txt",
    ),
    BundledComponent(
        name="libffi",
        version="8 (bundled with CPython)",
        licence="MIT",
        notice="libffi, Copyright (c) 1996-2024 Anthony Green and contributors. MIT licence.",
        patterns=("_internal/libffi-*.dll",),
        source_url="https://github.com/libffi/libffi",
        # CPython's own LICENSE.txt carries the libffi notice verbatim, so that is the
        # authoritative local text rather than a separately sourced copy.
        licence_text="CPython-LICENSE.txt",
    ),
    BundledComponent(
        name="Microsoft Visual C++ Runtime",
        version="14.x",
        licence="Microsoft Redistributable",
        notice=(
            "Microsoft Visual C++ runtime components (Microsoft Distributable Code, "
            "copyright Microsoft Corporation), shipped unmodified as supplied by the "
            "python.org CPython distribution and the Qt for Python wheels. "
            "Redistribution conditions: licenses/MS-VC-Redistributable.txt and the "
            "Additional Conditions section of licenses/CPython-LICENSE.txt."
        ),
        patterns=(
            "_internal/VCRUNTIME140*.dll",
            "_internal/**/VCRUNTIME140*.dll",
            "_internal/**/MSVCP140*.dll",
            "_internal/MSVCP140*.dll",
            "_internal/ucrtbase.dll",
            "_internal/api-ms-win-*.dll",
        ),
        source_url="https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist",
        licence_text="MS-VC-Redistributable.txt",
    ),
    BundledComponent(
        name="MarkupSafe",
        version="3.0.3",
        licence="BSD-3-Clause",
        notice="MarkupSafe, Copyright the Pallets team. BSD-3-Clause.",
        patterns=("_internal/markupsafe/**", "_internal/markupsafe-*.dist-info/**"),
        source_url="https://github.com/pallets/markupsafe",
        licence_text="BSD-3-Clause-Pallets.txt",
    ),
    BundledComponent(
        name="jsonschema",
        version="4.23.0",
        licence="MIT",
        notice="jsonschema, Copyright (c) 2013 Julian Berman. MIT licence.",
        patterns=("_internal/jsonschema/**", "_internal/jsonschema-*.dist-info/**"),
        source_url="https://github.com/python-jsonschema/jsonschema",
        licence_text="MIT-jsonschema.txt",
    ),
    BundledComponent(
        name="jsonschema-specifications",
        version="2025.9.1",
        licence="MIT",
        notice="jsonschema-specifications, Copyright (c) 2022 Julian Berman. MIT licence.",
        patterns=("_internal/jsonschema_specifications/**",),
        source_url="https://github.com/python-jsonschema/jsonschema-specifications",
        licence_text="MIT-jsonschema-specifications.txt",
    ),
    BundledComponent(
        name="attrs",
        version="26.1.0",
        licence="MIT",
        notice="attrs, Copyright (c) 2015 Hynek Schlawack and contributors. MIT licence.",
        patterns=("_internal/attrs-*.dist-info/**", "_internal/attr/**", "_internal/attrs/**"),
        source_url="https://github.com/python-attrs/attrs",
        licence_text="MIT-attrs.txt",
    ),
    BundledComponent(
        name="rpds-py",
        version="2026.6.3",
        licence="MIT",
        notice="rpds-py, Copyright (c) 2023 Julian Berman. MIT licence.",
        patterns=("_internal/rpds/**",),
        source_url="https://github.com/crate-py/rpds",
        licence_text="MIT-rpds-py.txt",
    ),
    BundledComponent(
        name="CPython",
        version="3.12",
        licence="PSF-2.0",
        notice=(
            "Python is distributed under the Python Software Foundation License "
            "Version 2. Copyright (c) 2001-2026 Python Software Foundation."
        ),
        patterns=(
            "_internal/python3*.dll",
            "_internal/base_library.zip",
            "_internal/*.pyd",
            "_internal/**/*.py",
        ),
        source_url="https://www.python.org/downloads/",
        licence_text="CPython-LICENSE.txt",
    ),
    BundledComponent(
        name="PyInstaller bootloader",
        version="6.11.1",
        licence="GPL-2.0-or-later WITH Bootloader-exception",
        notice=(
            "The application executable embeds the PyInstaller bootloader, which is "
            "distributed under GPL 2.0 or later with the PyInstaller bootloader "
            "exception permitting its use in closed-source applications."
        ),
        patterns=("PreflightQC.exe",),
        linkage="static",
        source_url="https://github.com/pyinstaller/pyinstaller",
        licence_text="PyInstaller-COPYING.txt",
    ),
)

#: Files that are first-party or generated, and therefore need no third-party notice.
FIRST_PARTY_PATTERNS: tuple[str, ...] = (
    "presets/**",
    "licenses/**",
    "_internal/preflightqc/**",
)

#: Pure-Python dependencies that PyInstaller compiles into the PYZ archive **inside**
#: ``PreflightQC.exe`` and therefore contribute no files to the package.
#:
#: They are invisible to a file-based scan, which is exactly why they are listed
#: separately rather than left to the attribution pass. Jinja2 is the clearest example:
#: it is genuinely shipped, genuinely third-party, and a purely file-driven manifest
#: would have omitted its notice entirely.
#:
#: The set is the runtime dependency closure of the declared dependencies in
#: pyproject.toml. ``verify_closure`` re-derives it from the installed environment so it
#: cannot drift when a dependency gains or loses a requirement.
EMBEDDED_PURE_PYTHON: tuple[BundledComponent, ...] = (
    BundledComponent(
        name="Jinja2",
        version="3.1.4",
        licence="BSD-3-Clause",
        notice="Jinja2, Copyright the Pallets team. BSD-3-Clause. Used to render HTML reports.",
        patterns=(),
        linkage="embedded in PreflightQC.exe (PYZ archive)",
        source_url="https://github.com/pallets/jinja",
        licence_text="BSD-3-Clause-Jinja2.txt",
    ),
    BundledComponent(
        name="referencing",
        version="0.37.0",
        licence="MIT",
        notice="referencing, Copyright (c) 2022 Julian Berman. MIT licence.",
        patterns=(),
        linkage="embedded in PreflightQC.exe (PYZ archive)",
        source_url="https://github.com/python-jsonschema/referencing",
        licence_text="MIT-referencing.txt",
    ),
    # Reached only transitively, through attrs/referencing. Nothing declares it directly,
    # which is precisely why the closure check exists — it was the one component a
    # hand-written dependency list had missed.
    BundledComponent(
        name="typing-extensions",
        version="4.16.0",
        licence="PSF-2.0",
        notice=(
            "typing-extensions, Copyright (c) Python Software Foundation. Distributed "
            "under the Python Software Foundation License Version 2."
        ),
        patterns=(),
        linkage="embedded in PreflightQC.exe (PYZ archive)",
        source_url="https://github.com/python/typing_extensions",
        licence_text="PSF-2.0-typing-extensions.txt",
    ),
)


#: The runtime dependencies declared in pyproject.toml. The closure is walked from here.
DECLARED_RUNTIME_DEPENDENCIES: tuple[str, ...] = ("PySide6", "Jinja2", "jsonschema")

#: PySide6 ships as several distributions; the manifest covers them under one component.
_DISTRIBUTION_ALIASES: frozenset[str] = frozenset(
    {"pyside6", "pyside6_essentials", "pyside6_addons", "shiboken6", "qt_6_via_pyside6"}
)

#: ``Jinja2>=3.1; extra == "docs"`` -> name ``Jinja2``. Deliberately not using the
#: `packaging` library: this file lives in a directory called ``packaging/``, and
#: importing a same-named top-level module from here is a trap waiting to be sprung.
_REQUIREMENT_NAME = __import__("re").compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _normalise_dist(name: str) -> str:
    return name.lower().replace("-", "_").replace(" ", "_").replace("(", "").replace(")", "")


def verify_closure() -> list[str]:
    """Check that everything actually shipped from the Python environment has a notice.

    A dependency that gains a new requirement would otherwise ship with no notice and no
    warning. Walking the installed environment turns that into a build failure.

    Requirements that are declared but *not installed* are skipped rather than reported:
    they are gated behind an extra or a marker that does not apply here, so they are not
    in the package and need no notice. Only something present and unlisted is a gap.
    """
    from importlib.metadata import PackageNotFoundError, distribution

    covered = {
        _normalise_dist(component.name) for component in (*BUNDLED, *EMBEDDED_PURE_PYTHON)
    } | _DISTRIBUTION_ALIASES

    seen: set[str] = set()
    missing: list[str] = []
    queue = list(DECLARED_RUNTIME_DEPENDENCIES)
    while queue:
        name = queue.pop()
        key = _normalise_dist(name)
        if key in seen:
            continue
        seen.add(key)
        try:
            dist = distribution(name)
        except PackageNotFoundError:
            continue
        if key not in covered:
            missing.append(f"{name} {dist.version} is installed and shipped but has no notice")
        for raw in dist.requires or []:
            if "extra ==" in raw:
                continue
            match = _REQUIREMENT_NAME.match(raw)
            if match is not None:
                queue.append(match.group(1))
    return missing


@dataclass
class Component:
    name: str
    version: str
    build_identifier: str
    license: str
    source_url: str
    published_checksum: str
    shipped_sha256: str
    shipped_files: list[str]
    file_count: int
    linkage: str
    notice_form: str
    licence_text_path: str = ""
    corresponding_source: str = ""
    verified: bool = False


@dataclass
class Manifest:
    product: str
    product_version: str
    generated: str
    package_path: str
    total_files: int = 0
    total_bytes: int = 0
    components: list[Component] = field(default_factory=list)
    first_party_files: int = 0
    unaccounted_files: list[str] = field(default_factory=list)
    gate_status: dict[str, str] = field(default_factory=dict)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _combined(digests: list[str]) -> str:
    """A stable digest over a set of files, so a component has one comparable hash."""
    return hashlib.sha256("".join(sorted(digests)).encode()).hexdigest() if digests else ""


def _matches(relative: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) for pattern in patterns)


def _lock() -> dict:
    return json.loads(LOCK_FILE.read_text(encoding="utf-8"))


def _corresponding_source_note(entry: dict) -> str:
    spec = entry.get("corresponding_source")
    if not isinstance(spec, dict):
        return ""
    return (
        f"{spec.get('hosting_url', '')} "
        f"(commit {str(spec.get('commit', ''))[:12]}, sha256 {str(spec.get('archive_sha256', ''))[:16]}…)"
    ).strip()


def build_manifest(package: Path, product_version: str) -> Manifest:
    lock = _lock()
    manifest = Manifest(
        product="PreflightQC",
        product_version=product_version,
        generated=datetime.now(UTC).isoformat(timespec="seconds"),
        package_path=str(package),
    )

    all_files = sorted(p for p in package.rglob("*") if p.is_file())
    manifest.total_files = len(all_files)
    manifest.total_bytes = sum(p.stat().st_size for p in all_files)
    unclaimed = {p: p.relative_to(package).as_posix() for p in all_files}

    # --- Pinned inspector binaries (the licensing-critical ones) -------------------
    for entry in lock["components"]:
        shipped: list[str] = []
        digests: list[str] = []
        for pattern in entry["files"]:
            for found in sorted(package.rglob(pattern)):
                if found.is_file() and found in unclaimed:
                    shipped.append(unclaimed[found])
                    digests.append(sha256(found))
                    del unclaimed[found]

        published = str(entry.get("published_sha256", ""))
        origin = str(entry.get("origin_verified_sha256", ""))
        if len(published) == 64:
            checksum = f"{published} (publisher checksum file)"
            verified = True
        elif len(origin) == 64:
            checksum = f"{origin} (vendor HTTPS origin; vendor publishes no checksum file)"
            verified = True
        else:
            checksum = "UNVERIFIED"
            verified = False

        manifest.components.append(
            Component(
                name=entry["name"],
                version=entry["version"],
                build_identifier=entry["build_identifier"],
                license=entry["declared_license"],
                source_url=str(entry.get("download_url") or entry.get("upstream_project", "")),
                published_checksum=checksum,
                shipped_sha256=_combined(digests),
                shipped_files=shipped,
                file_count=len(shipped),
                linkage=entry["linkage"],
                notice_form=entry["notice_form"],
                licence_text_path=(
                    "LGPL-3.0.txt" if entry["name"] == "ffprobe" else "BSD-2-Clause.txt"
                ),
                corresponding_source=_corresponding_source_note(entry),
                verified=verified and bool(shipped),
            )
        )

    # --- Everything the freeze bundled --------------------------------------------
    for bundled in BUNDLED:
        claimed = [path for path, relative in unclaimed.items() if _matches(relative, bundled.patterns)]
        if not claimed:
            continue
        digests = [sha256(path) for path in claimed]
        files = sorted(unclaimed[path] for path in claimed)
        for path in claimed:
            del unclaimed[path]
        manifest.components.append(
            Component(
                name=bundled.name,
                version=bundled.version,
                build_identifier="frozen into the application bundle",
                license=bundled.licence,
                source_url=bundled.source_url,
                published_checksum="n/a — built from the pinned Python environment",
                shipped_sha256=_combined(digests),
                # Listing 400 Qt files helps nobody; the count plus the combined digest
                # is what a reader or a re-verification actually needs.
                shipped_files=files if len(files) <= 12 else [f"{len(files)} files"],
                file_count=len(files),
                linkage=bundled.linkage,
                notice_form=bundled.notice,
                licence_text_path=bundled.licence_text,
                verified=True,
            )
        )

    # --- Embedded in the PYZ, contributing no files ---------------------------------
    for embedded in EMBEDDED_PURE_PYTHON:
        manifest.components.append(
            Component(
                name=embedded.name,
                version=embedded.version,
                build_identifier="compiled into the PYZ archive inside PreflightQC.exe",
                license=embedded.licence,
                source_url=embedded.source_url,
                published_checksum="n/a — built from the pinned Python environment",
                shipped_sha256="",
                shipped_files=[],
                file_count=0,
                linkage=embedded.linkage,
                notice_form=embedded.notice,
                licence_text_path=embedded.licence_text,
                verified=True,
            )
        )

    # --- First-party and generated -------------------------------------------------
    for path in list(unclaimed):
        if _matches(unclaimed[path], FIRST_PARTY_PATTERNS):
            manifest.first_party_files += 1
            del unclaimed[path]

    manifest.unaccounted_files = sorted(unclaimed.values())
    closure_gaps = verify_closure()

    ffprobe = next((c for c in manifest.components if c.name == "ffprobe"), None)
    manifest.gate_status = {
        "G-1_manifest_complete": (
            "PASS"
            if not manifest.unaccounted_files
            else f"FAIL — {len(manifest.unaccounted_files)} file(s) attributed to no component"
        ),
        "G-1_checksums_verified": (
            "PASS"
            if all(c.verified for c in manifest.components)
            else "FAIL — a component has no verifiable checksum"
        ),
        "G-2_dependency_closure_covered": (
            "PASS" if not closure_gaps else "FAIL — " + "; ".join(closure_gaps)
        ),
        "G-2_licence_texts_present": _licence_texts_status(package, manifest),
        "G-5_corresponding_source": (
            "PASS"
            if ffprobe is not None and ffprobe.corresponding_source
            else "FAIL — version-matched FFmpeg source location not recorded"
        ),
        # Amended 2026-08-09 (SPEC LOCK v1.1.0, ADR-G12): owner risk acceptance, not
        # attorney review. Still a human gate; tooling can only report it. No attorney
        # review occurred and none is claimed.
        "G-12_owner_risk_acceptance": (
            "NOT COMPLETE — requires the Product Owner's written residual-risk "
            "acceptance for the specific release (ADR-G12 §8); no attorney review "
            "occurred, no legal clearance is claimed"
        ),
    }
    return manifest


def _licence_texts_status(package: Path, manifest: Manifest) -> str:
    """Every licence text a component points at must actually be in the package."""
    licences = package / "licenses"
    missing = sorted(
        {
            component.licence_text_path
            for component in manifest.components
            if component.licence_text_path and not (licences / component.licence_text_path).is_file()
        }
    )
    if missing:
        return f"FAIL — referenced but absent from licenses/: {', '.join(missing)}"
    placeholder = licences / "MS-VC-Redistributable.txt"
    if placeholder.is_file() and "PLACEHOLDER" in placeholder.read_text(encoding="utf-8"):
        return (
            "PASS WITH OPEN ACTION — MS-VC-Redistributable.txt is still the placeholder; "
            "a human must supply the Microsoft redistributable terms before release"
        )
    return "PASS"


def render_notices(manifest: Manifest) -> str:
    lines = [
        "PREFLIGHTQC — THIRD-PARTY NOTICES",
        "=" * 72,
        "",
        f"PreflightQC {manifest.product_version}",
        f"Generated from the built package on {manifest.generated}.",
        "",
        "This file is generated from the actual contents of the release package. If a",
        "component is listed here it is in the package, and if it is in the package it is",
        "listed here — the generator fails the build on any file it cannot attribute.",
        "",
        "-" * 72,
        "FFmpeg",
        "-" * 72,
        "",
        FFMPEG_NOTICE,
        "",
        FFMPEG_DISCLAIMER,
        "",
        FFMPEG_VERSION3_NOTE,
        "",
        "The full text of the GNU Lesser General Public License v3 is included with this",
        "product as licenses/LGPL-3.0.txt. LGPLv3 incorporates the terms of the GNU",
        "General Public License v3, whose text is included as licenses/GPL-3.0.txt; no",
        "GPL-licensed component is present in this product.",
        "",
    ]

    for component in manifest.components:
        if component.name == "ffprobe":
            lines.extend(
                [
                    f"Build identifier    : {component.build_identifier}",
                    f"Version             : {component.version}",
                    f"Licence             : {component.license}",
                    f"Obtained from       : {component.source_url}",
                    f"Published checksum  : {component.published_checksum}",
                    f"Corresponding source: {component.corresponding_source}",
                    "",
                    "The exact configure line of the shipped build is included with this",
                    "product as licenses/ffmpeg-build-configuration.txt.",
                    "",
                    "WRITTEN OFFER: for three years from the date you received this product,",
                    "the complete corresponding source code for the FFmpeg libraries",
                    "distributed with it is available at the URL above, at no charge beyond",
                    "the cost of distribution.",
                    "",
                ]
            )

    lines.extend(
        [
            "-" * 72,
            "MediaInfo and ZenLib",
            "-" * 72,
            "",
            MEDIAINFO_NOTICE,
            "",
            ZENLIB_NOTICE,
            "",
            "The full text of the BSD 2-Clause License is included with this product as",
            "licenses/BSD-2-Clause.txt.",
            "",
        ]
    )

    for component in manifest.components:
        if component.name == "mediainfo":
            lines.extend(
                [
                    f"Version             : {component.version}",
                    f"Obtained from       : {component.source_url}",
                    f"Published checksum  : {component.published_checksum}",
                    "",
                    "The MediaInfo command-line binary is shipped unmodified. The optional",
                    "libcurl network component distributed in the same archive is NOT",
                    "included in this product.",
                    "",
                ]
            )

    lines.extend(["-" * 72, "Application runtime", "-" * 72, ""])
    for component in manifest.components:
        if component.name in {"ffprobe", "mediainfo"}:
            continue
        lines.append(f"{component.name} {component.version} ({component.license})")
        lines.append(f"    {component.notice_form}")
        if component.licence_text_path:
            lines.append(f"    Licence text: licenses/{component.licence_text_path}")
        lines.append(f"    Files shipped: {component.file_count}")
        lines.append("")

    lines.extend(
        [
            "-" * 72,
            "Trademarks",
            "-" * 72,
            "",
            "Instagram, Meta, TikTok, YouTube and LinkedIn are trademarks of their",
            "respective owners. PreflightQC is not affiliated with, endorsed by or",
            "certified by any of them. Their names are used descriptively only, to",
            "identify the delivery specifications PreflightQC validates against.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release gates G-1 and G-2 artefacts")
    parser.add_argument("--package", type=Path, default=REPO_ROOT / "dist" / "PreflightQC")
    parser.add_argument("--out", type=Path, default=None)
    # Defaults to the single authoritative version rather than a hardcoded string, so
    # the manifest cannot describe a version the product does not report.
    from preflightqc import __version__ as product_version

    parser.add_argument("--product-version", default=product_version)
    args = parser.parse_args()

    if not args.package.is_dir():
        print(f"error: package directory does not exist: {args.package}", file=sys.stderr)
        print(
            "Build the package first (packaging/build.py). Nothing can be generated from "
            "a package that does not exist.",
            file=sys.stderr,
        )
        return 2

    manifest = build_manifest(args.package, args.product_version)
    out = args.out or (args.package / "licenses")
    out.mkdir(parents=True, exist_ok=True)

    (out / "DEPENDENCY-MANIFEST.json").write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True), encoding="utf-8"
    )
    (out / "THIRD-PARTY-NOTICES.txt").write_text(render_notices(manifest), encoding="utf-8")

    print(f"Wrote {out / 'DEPENDENCY-MANIFEST.json'}")
    print(f"Wrote {out / 'THIRD-PARTY-NOTICES.txt'}")
    print(
        f"  {manifest.total_files} files, {manifest.total_bytes / 1_048_576:.1f} MB, "
        f"{len(manifest.components)} components, {manifest.first_party_files} first-party"
    )
    for unaccounted in manifest.unaccounted_files[:20]:
        print(f"  UNACCOUNTED: {unaccounted}", file=sys.stderr)
    if len(manifest.unaccounted_files) > 20:
        print(f"  ... and {len(manifest.unaccounted_files) - 20} more", file=sys.stderr)
    for gate, status in manifest.gate_status.items():
        print(f"  {gate}: {status}")

    failed = [g for g, s in manifest.gate_status.items() if not s.startswith("PASS")]
    # G-12 is a human gate and is reported, not enforced, here.
    failed = [g for g in failed if g != "G-12_owner_risk_acceptance"]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
