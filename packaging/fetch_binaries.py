"""Fetch and install the pinned inspector binaries (Phase 11, gates G-3/G-4/G-7/G-10).

Two rules govern this script, and both exist because the failure they prevent is silent:

**It fails hard on a checksum mismatch. It never warns and continues.** A mismatch means
the bytes are not the bytes the licensing gate was cleared against — a different build, a
corrupted transfer, or a substituted file. None of those is a warning.

**It installs only the files named in the lock file.** The archives contain more than we
are willing to ship: ``ffmpeg.exe`` (an encoder, forbidden by spec §20), ``ffplay.exe``,
development headers, and MediaInfo's ``LIBCURL.DLL`` (a network feature the licensing gate
forbids). An allow-list cannot let those through by accident; a deny-list would.

    python packaging/fetch_binaries.py                  # download, verify, install
    python packaging/fetch_binaries.py --verify-only    # check what is already installed
    python packaging/fetch_binaries.py --archive-dir D  # use archives already on disk
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"
DEFAULT_TARGET = REPO_ROOT / "third-party" / "bin"

#: Files that must never be installed even if a lock file were edited to name them.
#: This is belt and braces on top of the allow-list: two independent mistakes would be
#: needed to ship an encoder.
NEVER_INSTALL: frozenset[str] = frozenset(
    {"ffmpeg.exe", "ffplay.exe", "libcurl.dll", "mediainfo_gui.exe"}
)


class FetchError(RuntimeError):
    """Raised for any condition that must stop the build."""


@dataclass(frozen=True, slots=True)
class Expectation:
    """The digest this component is verified against, and how strong that is."""

    digest: str
    kind: str
    source: str

    @property
    def is_publisher_digest(self) -> bool:
        return self.kind == "published"


def expectation_for(component: dict[str, object]) -> Expectation:
    """Pick the strongest available authenticity evidence for a component.

    A publisher-published checksum is the real thing. When a vendor publishes none — as
    MediaArea does not for the Windows CLI zip — the fallback is a hash we obtained by
    downloading from the vendor's own TLS origin. That is weaker, and it is labelled
    weaker rather than being quietly written into the same field.
    """
    published = str(component.get("published_sha256", ""))
    if len(published) == 64:
        return Expectation(
            digest=published.lower(),
            kind="published",
            source=str(component.get("published_sha256_source", "publisher checksum file")),
        )

    origin = str(component.get("origin_verified_sha256", ""))
    if len(origin) == 64:
        return Expectation(
            digest=origin.lower(),
            kind="origin",
            source=str(component.get("origin_verified_method", "vendor HTTPS origin")),
        )

    raise FetchError(
        f"{component.get('name')}: no verifiable digest in binaries.lock.json. "
        "Set published_sha256 (preferred) or origin_verified_sha256. "
        "Downloading an unverifiable binary is not an option."
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path) -> Path:
    if not url.startswith("https://"):
        raise FetchError(f"refusing to download over a non-HTTPS URL: {url}")
    print(f"    downloading {url}")
    with urlopen(url) as response, destination.open("wb") as handle:  # noqa: S310 - https enforced
        shutil.copyfileobj(response, handle)
    return destination


def _members_to_install(archive: zipfile.ZipFile, wanted: set[str]) -> dict[str, zipfile.ZipInfo]:
    """Map each wanted filename to its member, matching on basename, case-insensitively.

    Archives nest their payload under a versioned directory whose name changes with every
    release, so matching on full paths would break on the next version bump.
    """
    found: dict[str, zipfile.ZipInfo] = {}
    lowered = {name.lower(): name for name in wanted}
    for info in archive.infolist():
        if info.is_dir():
            continue
        base = Path(info.filename).name.lower()
        if base in NEVER_INSTALL:
            continue
        canonical = lowered.get(base)
        if canonical is not None and canonical not in found:
            found[canonical] = info
    return found


def install_component(
    component: dict[str, object],
    archive_path: Path,
    target: Path,
) -> list[tuple[str, str]]:
    """Extract exactly the allow-listed files. Returns (name, sha256) for each."""
    wanted = {str(name) for name in component["files"]}  # type: ignore[union-attr]
    installed: list[tuple[str, str]] = []
    target.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        members = _members_to_install(archive, wanted)
        missing = sorted(wanted - members.keys())
        if missing:
            raise FetchError(
                f"{component['name']}: archive does not contain {', '.join(missing)}. "
                "The lock file and the archive disagree about what this build ships."
            )
        for name, info in sorted(members.items()):
            with archive.open(info) as source, (target / name).open("wb") as handle:
                shutil.copyfileobj(source, handle)
            installed.append((name, sha256(target / name)))
    return installed


def check_installed(component: dict[str, object], target: Path) -> list[str]:
    """Compare installed files against the per-file hashes recorded in the lock file."""
    problems: list[str] = []
    recorded = component.get("installed_files")
    if not isinstance(recorded, dict) or not recorded:
        return [f"{component['name']}: no installed_files recorded to verify against"]

    for name, expected in sorted(recorded.items()):
        path = target / name
        if not path.is_file():
            problems.append(f"{component['name']}: missing {name}")
            continue
        actual = sha256(path)
        if actual != expected:
            problems.append(
                f"{component['name']}: {name} hash mismatch — expected {expected}, got {actual}"
            )

    for stray in sorted(p.name for p in target.glob("*") if p.is_file()):
        if stray.lower() in NEVER_INSTALL:
            problems.append(f"{stray} must never be installed — it is on the forbidden list")
    return problems


def fetch_all(
    *,
    target: Path,
    archive_dir: Path | None,
    work_dir: Path,
) -> list[str]:
    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    problems: list[str] = []

    for component in lock["components"]:
        name = str(component["name"])
        expectation = expectation_for(component)
        archive_name = str(component.get("download_archive") or component["supplied_archive"])
        print(f"\n{name}")

        local = None
        if archive_dir is not None:
            candidate = archive_dir / archive_name
            if candidate.is_file():
                local = candidate
                print(f"    using local archive {candidate}")
        if local is None:
            url = str(component.get("download_url", ""))
            if not url:
                problems.append(f"{name}: no download_url and no local archive")
                continue
            local = download(url, work_dir / archive_name)

        actual = sha256(local)
        if actual != expectation.digest:
            problems.append(
                f"{name}: CHECKSUM MISMATCH — expected {expectation.digest} "
                f"({expectation.kind}, {expectation.source}), got {actual}"
            )
            continue

        label = "publisher checksum" if expectation.is_publisher_digest else "vendor origin hash"
        print(f"    verified against {label}: {actual}")
        if not expectation.is_publisher_digest:
            print(
                "    NOTE: this vendor publishes no checksum file; verification is "
                "origin-authenticated, not digest-authenticated."
            )

        installed = install_component(component, local, target)
        for filename, digest in installed:
            recorded = component.get("installed_files", {})
            expected = recorded.get(filename) if isinstance(recorded, dict) else None
            if expected is not None and expected != digest:
                problems.append(
                    f"{name}: installed {filename} hashes to {digest}, but the lock file "
                    f"records {expected}"
                )
            print(f"    installed {filename}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and install pinned inspector binaries")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--archive-dir", type=Path, default=None)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))

    if args.verify_only:
        problems: list[str] = []
        for component in lock["components"]:
            problems.extend(check_installed(component, args.target))
        for problem in problems:
            print(f"[fetch] {problem}", file=sys.stderr)
        if problems:
            print(f"\nVERIFY FAILED: {len(problems)} problem(s).", file=sys.stderr)
            return 1
        print(f"All pinned binaries verified in {args.target}")
        return 0

    try:
        with tempfile.TemporaryDirectory(prefix="preflightqc-fetch-") as tmp:
            problems = fetch_all(
                target=args.target, archive_dir=args.archive_dir, work_dir=Path(tmp)
            )
    except FetchError as error:
        print(f"[fetch] {error}", file=sys.stderr)
        return 1

    for problem in problems:
        print(f"[fetch] {problem}", file=sys.stderr)
    if problems:
        print(f"\nFETCH FAILED: {len(problems)} problem(s). Nothing may be built.", file=sys.stderr)
        return 1
    print(f"\nAll pinned binaries fetched and verified into {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
