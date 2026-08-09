"""Reconstruct the archived FFmpeg corresponding source from its public commit (gate G-5).

The source archive is deliberately *not* committed to this repository — it is 17 MB of
someone else's code, and Git is the wrong place for it. What is committed is everything
needed to rebuild it byte-for-byte:

    git fetch --depth 1 <upstream> <commit>
    git archive --format=tar.gz --prefix=<prefix>/ <commit>

``git archive`` is deterministic for a fixed commit and prefix, so the SHA-256 recorded in
``packaging/binaries.lock.json`` is reproducible by anyone — including a recipient checking
that what we host really is the source of what we shipped.

This is a developer/release tool. It needs network access and is never invoked by the
application.

    python tools/fetch_corresponding_source.py            # rebuild if absent
    python tools/fetch_corresponding_source.py --force    # rebuild unconditionally
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"


def _run(command: list[str], cwd: Path) -> None:
    # S607: `git` is resolved from PATH on purpose. This is a developer/release tool run
    # by a human who has git installed; hard-coding a path would make it less portable
    # without making it safer.
    completed = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{' '.join(command)} failed:\n{completed.stderr.strip()}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rebuild(spec: dict[str, object], *, work_root: Path, keep_checkout: bool) -> Path:
    upstream = str(spec["upstream_repository"])
    commit = str(spec["commit"])
    prefix = str(spec["archive_prefix"])
    destination = REPO_ROOT / str(spec["archive"])
    destination.parent.mkdir(parents=True, exist_ok=True)

    checkout = work_root / f"{prefix}-checkout"
    if checkout.exists():
        shutil.rmtree(checkout)
    checkout.mkdir(parents=True)

    print(f"  git init                       {checkout}")
    _run(["git", "init", "-q"], cwd=checkout)
    _run(["git", "remote", "add", "origin", upstream], cwd=checkout)
    print(f"  git fetch --depth 1            {commit[:12]} from {upstream}")
    _run(["git", "fetch", "--depth", "1", "--quiet", "origin", commit], cwd=checkout)
    _run(["git", "checkout", "-q", "FETCH_HEAD"], cwd=checkout)

    # Git verifies content addressing end to end: if the tree did not hash to this commit,
    # the fetch would have failed. Re-reading HEAD guards against a silently wrong ref.
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=checkout, capture_output=True, text=True, check=True
    ).stdout.strip()
    if head != commit:
        raise RuntimeError(f"checked out {head}, expected {commit}")

    print(f"  git archive                    -> {destination.name}")
    _run(
        [
            "git",
            "archive",
            "--format=tar.gz",
            f"--prefix={prefix}/",
            "-o",
            str(destination),
            "HEAD",
        ],
        cwd=checkout,
    )

    if not keep_checkout:
        shutil.rmtree(checkout, ignore_errors=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild archived corresponding source (G-5)")
    parser.add_argument("--force", action="store_true", help="rebuild even if the archive exists")
    parser.add_argument("--keep-checkout", action="store_true", help="leave the git checkout behind")
    parser.add_argument("--work-root", type=Path, default=REPO_ROOT / "third-party" / "source")
    args = parser.parse_args()

    lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
    specs: list[dict[str, object]] = []
    for component in lock["components"]:
        for key in ("corresponding_source", "build_recipe_source"):
            spec = component.get(key)
            if isinstance(spec, dict) and spec.get("commit"):
                specs.append(spec)

    if not specs:
        print("no corresponding-source specifications in binaries.lock.json", file=sys.stderr)
        return 1

    failures = 0
    args.work_root.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        destination = REPO_ROOT / str(spec["archive"])
        expected = str(spec["archive_sha256"])
        print(f"\n{destination.name}")
        if destination.is_file() and not args.force:
            print("  present; verifying hash only (use --force to rebuild)")
        else:
            rebuild(spec, work_root=args.work_root, keep_checkout=args.keep_checkout)

        actual = _sha256(destination)
        if actual == expected:
            print(f"  SHA-256 OK                     {actual}")
        else:
            failures += 1
            print("  SHA-256 MISMATCH", file=sys.stderr)
            print(f"    recorded {expected}", file=sys.stderr)
            print(f"    actual   {actual}", file=sys.stderr)

    if failures:
        print(f"\n{failures} archive(s) did not match binaries.lock.json.", file=sys.stderr)
        return 1
    print("\nAll corresponding-source archives match binaries.lock.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
