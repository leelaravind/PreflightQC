"""Verify the archived FFmpeg source corresponds to the shipped ffprobe binary (gate G-5).

The LGPL obligation is not "ship some FFmpeg source". It is to make available the source
*corresponding to the binary you distributed*. A tarball that is one release out of date
satisfies nobody: it neither lets a recipient rebuild what we shipped nor demonstrates
that we know what we shipped.

So this module refuses to take correspondence on trust. It proves it four ways, from the
archive's own contents against the binary's own self-report:

    1. RELEASE                 -> the release number inside the version string
    2. commit hash             -> the ``-g<hash>`` suffix in the version string
    3. seven library versions  -> the seven ``libav*``/``libsw*`` lines ffprobe prints
    4. SHA-256                 -> the archive is the one recorded in binaries.lock.json

Any single mismatch is a hard failure. A near miss is the dangerous case: 8.1.1 source
against an 8.1.2 binary looks right in a listing and is wrong in a courtroom.

    python packaging/verify_source.py
    python packaging/verify_source.py --archive PATH --ffprobe PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"
DEFAULT_FFPROBE = REPO_ROOT / "third-party" / "bin" / "ffprobe.exe"

#: The seven libraries a shared FFmpeg build ships and ffprobe reports on startup.
FFMPEG_LIBRARIES: tuple[str, ...] = (
    "libavutil",
    "libavcodec",
    "libavformat",
    "libavdevice",
    "libavfilter",
    "libswscale",
    "libswresample",
)

#: ``ffprobe version n8.1.2-34-g9b6c8969e0-20260809 Copyright ...``
_VERSION_LINE = re.compile(r"^ffprobe version (\S+)", re.MULTILINE)

#: ``n8.1.2-34-g9b6c8969e0-20260809`` -> release 8.1.2, 34 commits ahead, at 9b6c8969e0.
#: The ``-<n>-g<hash>`` part is what ``git describe`` emits, and it is absent from a build
#: made exactly on a release tag — hence the optional group.
_DESCRIBE = re.compile(r"^n(?P<release>\d+(?:\.\d+)*)(?:-(?P<ahead>\d+)-g(?P<commit>[0-9a-f]+))?")

#: ``libavcodec     62. 28.102 / 62. 28.102`` — spacing varies with the number widths.
_LIBRARY_LINE = re.compile(
    r"^(?P<name>lib[a-z]+)\s+(?P<major>\d+)\.\s*(?P<minor>\d+)\.\s*(?P<micro>\d+)", re.MULTILINE
)

_DEFINE = "#define {symbol}"


@dataclass(frozen=True, slots=True)
class Problem:
    detail: str

    def __str__(self) -> str:
        return f"[G-5] {self.detail}"


@dataclass(frozen=True, slots=True)
class BinaryIdentity:
    """What the shipped ffprobe says about itself."""

    version: str
    release: str
    commits_ahead: int | None
    commit: str | None
    libraries: dict[str, tuple[int, int, int]]


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    """What the archived source tree says about itself."""

    release: str
    libraries: dict[str, tuple[int, int, int]]


def parse_binary_identity(version_output: str) -> BinaryIdentity:
    """Read ffprobe's ``-version`` output.

    Raises ValueError rather than returning a partially-populated identity: an
    unparseable version string must stop the gate, never silently weaken it.
    """
    match = _VERSION_LINE.search(version_output)
    if match is None:
        raise ValueError("no 'ffprobe version' line in the output")
    version = match.group(1)

    described = _DESCRIBE.match(version)
    if described is None:
        raise ValueError(f"version string is not a git-describe of a release tag: {version!r}")

    ahead = described.group("ahead")
    libraries = {
        found.group("name"): (
            int(found.group("major")),
            int(found.group("minor")),
            int(found.group("micro")),
        )
        for found in _LIBRARY_LINE.finditer(version_output)
    }
    return BinaryIdentity(
        version=version,
        release=described.group("release"),
        commits_ahead=int(ahead) if ahead is not None else None,
        commit=described.group("commit"),
        libraries=libraries,
    )


def _read_member(archive: tarfile.TarFile, suffix: str) -> str | None:
    """Return the text of the single member whose path ends with ``suffix``."""
    for member in archive.getmembers():
        if member.isfile() and member.name.endswith(suffix):
            handle = archive.extractfile(member)
            if handle is None:  # pragma: no cover - only for non-regular members
                return None
            return handle.read().decode("utf-8", errors="replace")
    return None


def _version_component(text: str, symbol: str) -> int | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(_DEFINE.format(symbol=symbol)):
            tail = stripped[len(_DEFINE.format(symbol=symbol)) :].strip()
            # Ignore anything that is not a plain integer literal; FFmpeg also defines
            # feature macros whose names begin with the same prefix.
            if tail.isdigit():
                return int(tail)
    return None


def parse_source_identity(archive_path: Path) -> SourceIdentity:
    """Read RELEASE and the seven library version headers out of the source tarball."""
    libraries: dict[str, tuple[int, int, int]] = {}
    with tarfile.open(archive_path, "r:*") as archive:
        release_text = _read_member(archive, "/RELEASE")
        if release_text is None:
            raise ValueError(f"{archive_path.name} contains no RELEASE file")
        release = release_text.strip()

        for library in FFMPEG_LIBRARIES:
            prefix = library.upper()
            version_h = _read_member(archive, f"/{library}/version.h")
            major_h = _read_member(archive, f"/{library}/version_major.h") or ""
            if version_h is None:
                continue
            combined = version_h + "\n" + major_h
            major = _version_component(combined, f"{prefix}_VERSION_MAJOR")
            minor = _version_component(version_h, f"{prefix}_VERSION_MINOR")
            micro = _version_component(version_h, f"{prefix}_VERSION_MICRO")
            if major is None or minor is None or micro is None:
                continue
            libraries[library] = (major, minor, micro)

    return SourceIdentity(release=release, libraries=libraries)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def compare(binary: BinaryIdentity, source: SourceIdentity) -> list[Problem]:
    """Every way the archive can fail to correspond to the binary."""
    problems: list[Problem] = []

    if source.release != binary.release:
        problems.append(
            Problem(
                f"release mismatch: the binary reports {binary.release} but the archived "
                f"source RELEASE says {source.release}"
            )
        )

    missing = [name for name in FFMPEG_LIBRARIES if name not in source.libraries]
    if missing:
        problems.append(Problem(f"source archive has no version header for: {', '.join(missing)}"))

    if not binary.libraries:
        problems.append(Problem("the binary reported no library versions to compare against"))

    for name, binary_version in sorted(binary.libraries.items()):
        source_version = source.libraries.get(name)
        if source_version is None:
            continue
        if source_version != binary_version:
            problems.append(
                Problem(
                    f"{name} mismatch: binary {'.'.join(map(str, binary_version))} vs source "
                    f"{'.'.join(map(str, source_version))}"
                )
            )

    return problems


def _component(lock: dict[str, object], name: str) -> dict[str, object]:
    components = lock.get("components")
    if not isinstance(components, list):
        raise ValueError("binaries.lock.json has no components list")
    for entry in components:
        if isinstance(entry, dict) and entry.get("name") == name:
            return entry
    raise ValueError(f"binaries.lock.json has no {name} component")


def verify(
    *,
    archive: Path,
    version_output: str,
    lock: dict[str, object] | None = None,
) -> list[Problem]:
    """Full G-5 check: archive present, hash pinned, contents correspond to the binary."""
    if not archive.is_file():
        return [
            Problem(
                f"corresponding-source archive is missing: {archive}. "
                "Run tools/fetch_corresponding_source.py to reconstruct it."
            )
        ]

    problems: list[Problem] = []
    binary = parse_binary_identity(version_output)
    source = parse_source_identity(archive)
    problems.extend(compare(binary, source))

    if lock is not None:
        recorded = _component(lock, "ffprobe").get("corresponding_source")
        if not isinstance(recorded, dict):
            problems.append(Problem("binaries.lock.json records no corresponding_source block"))
        else:
            expected_hash = recorded.get("archive_sha256")
            actual_hash = sha256(archive)
            if expected_hash != actual_hash:
                problems.append(
                    Problem(
                        f"archive SHA-256 does not match binaries.lock.json: "
                        f"recorded {expected_hash}, actual {actual_hash}"
                    )
                )
            recorded_commit = recorded.get("commit")
            if (
                binary.commit is not None
                and isinstance(recorded_commit, str)
                and not recorded_commit.startswith(binary.commit)
            ):
                problems.append(
                    Problem(
                        f"the binary was built from commit {binary.commit}* but the lock file "
                        f"records corresponding source at {recorded_commit}"
                    )
                )
            recorded_ahead = recorded.get("commits_ahead_of_tag")
            if (
                binary.commits_ahead is not None
                and isinstance(recorded_ahead, int)
                and recorded_ahead != binary.commits_ahead
            ):
                problems.append(
                    Problem(
                        f"the binary is {binary.commits_ahead} commits past its release tag but "
                        f"the lock file records {recorded_ahead}"
                    )
                )
            if not recorded.get("hosting_url"):
                problems.append(
                    Problem(
                        "no hosting_url recorded — the LGPL offer requires a location from "
                        "which the corresponding source is actually served"
                    )
                )

    return problems


def read_version_output(ffprobe: Path) -> str:
    completed = subprocess.run(
        [str(ffprobe), "-hide_banner", "-version"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return completed.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify FFmpeg corresponding source (G-5)")
    parser.add_argument("--archive", type=Path, default=None)
    parser.add_argument("--ffprobe", type=Path, default=DEFAULT_FFPROBE)
    args = parser.parse_args()

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    recorded = _component(lock, "ffprobe").get("corresponding_source")
    archive = args.archive
    if archive is None:
        relative = recorded.get("archive") if isinstance(recorded, dict) else None
        if not isinstance(relative, str):
            print("[G-5] binaries.lock.json records no corresponding_source.archive", file=sys.stderr)
            return 1
        archive = REPO_ROOT / relative

    if not args.ffprobe.is_file():
        print(f"[G-5] ffprobe not found: {args.ffprobe}", file=sys.stderr)
        return 1

    problems = verify(archive=archive, version_output=read_version_output(args.ffprobe), lock=lock)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"\nG-5 FAILED: {len(problems)} problem(s).", file=sys.stderr)
        return 1

    print(f"G-5 passed: {archive.name} corresponds to the shipped ffprobe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
