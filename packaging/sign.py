"""Authenticode signing and verification (Phase 11 criterion P11-A8, gate G-11).

This script deliberately contains **no certificate, no thumbprint and no credential**. It
takes what to sign with from the environment or the command line, so that a repository
that is read by many people never holds a signing identity.

What gets signed, and what does not:

* **Signed:** ``PreflightQC.exe`` and the installer — the first-party artefacts.
* **Not signed:** the third-party binaries in ``bin/`` and the Qt libraries. Re-signing
  them is *permitted* by the licensing gate, but only if they are otherwise unmodified,
  and every signature we add is one more thing to explain to a recipient checking that
  the FFmpeg binary we shipped is the one BtbN published. Leaving them exactly as
  published is the simpler, more verifiable position. ``--include-third-party`` exists
  for the case where a distribution channel forces the issue.

Two commands, because they are needed at different times by different people:

    python packaging/sign.py sign   --thumbprint <sha1>     # release engineer, needs a cert
    python packaging/sign.py verify                          # anyone, on any build

``verify`` is the one the release audit runs. On an unsigned build it reports UNSIGNED
and fails, which is the correct state to report before a certificate exists — not a pass.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist"
PACKAGE = DIST / "PreflightQC"

#: RFC 3161 timestamping is not optional in practice: without it every signature stops
#: validating the day the certificate expires, including on copies already installed.
DEFAULT_TIMESTAMP_URL = "http://timestamp.digicert.com"


@dataclass(frozen=True, slots=True)
class Outcome:
    path: Path
    ok: bool
    detail: str


def find_signtool() -> Path | None:
    """Locate signtool.exe, preferring an x64 build over the arm64 one."""
    found = shutil.which("signtool")
    if found:
        return Path(found)

    roots = [
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Windows Kits" / "10" / "bin",
    ]
    candidates: list[Path] = []
    for root in roots:
        if root.is_dir():
            candidates.extend(root.rglob("signtool.exe"))
    if not candidates:
        return None
    # Prefer the architecture that matches this machine; an arm64 signtool on an x64 host
    # is a confusing failure rather than an obvious one.
    preferred = [c for c in candidates if "x64" in c.parts]
    return sorted(preferred or candidates)[-1]


def first_party_artefacts() -> list[Path]:
    artefacts = [PACKAGE / "PreflightQC.exe"]
    artefacts.extend(sorted((DIST / "installer").glob("*.exe")))
    return [path for path in artefacts if path.is_file()]


def third_party_artefacts() -> list[Path]:
    binaries = sorted((PACKAGE / "bin").glob("*.dll")) + sorted((PACKAGE / "bin").glob("*.exe"))
    return [path for path in binaries if path.is_file()]


def sign(paths: list[Path], *, thumbprint: str, timestamp_url: str) -> list[Outcome]:
    signtool = find_signtool()
    if signtool is None:
        return [Outcome(Path("signtool"), False, "signtool.exe not found; install the Windows SDK")]

    outcomes: list[Outcome] = []
    for path in paths:
        result = subprocess.run(
            [
                str(signtool), "sign",
                "/sha1", thumbprint,
                "/fd", "SHA256",
                "/tr", timestamp_url,
                "/td", "SHA256",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        outcomes.append(
            Outcome(path, result.returncode == 0, (result.stdout + result.stderr).strip())
        )
    return outcomes


def verify(paths: list[Path]) -> list[Outcome]:
    signtool = find_signtool()
    if signtool is None:
        return [Outcome(Path("signtool"), False, "signtool.exe not found; install the Windows SDK")]

    outcomes: list[Outcome] = []
    for path in paths:
        result = subprocess.run(
            [str(signtool), "verify", "/pa", "/v", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        detail = "UNSIGNED" if "No signature found" in output else output.splitlines()[-1:][0] if output else ""
        outcomes.append(Outcome(path, result.returncode == 0, detail))
    return outcomes


def main() -> int:
    parser = argparse.ArgumentParser(description="Authenticode signing and verification")
    parser.add_argument("action", choices=["sign", "verify"])
    parser.add_argument(
        "--thumbprint",
        default=os.environ.get("PREFLIGHTQC_SIGNING_THUMBPRINT", ""),
        help="SHA-1 thumbprint of the signing certificate in the Windows certificate store",
    )
    parser.add_argument("--timestamp-url", default=DEFAULT_TIMESTAMP_URL)
    parser.add_argument("--include-third-party", action="store_true")
    args = parser.parse_args()

    paths = first_party_artefacts()
    if args.include_third_party:
        paths += third_party_artefacts()
    if not paths:
        print(f"error: nothing to {args.action} — build the package first", file=sys.stderr)
        return 2

    if args.action == "sign":
        if not args.thumbprint:
            print(
                "error: no signing certificate. Pass --thumbprint or set "
                "PREFLIGHTQC_SIGNING_THUMBPRINT.\n"
                "Gate G-11 cannot be satisfied without a code-signing certificate; this "
                "is an operator prerequisite, not something the build can supply.",
                file=sys.stderr,
            )
            return 2
        outcomes = sign(paths, thumbprint=args.thumbprint, timestamp_url=args.timestamp_url)
    else:
        outcomes = verify(paths)

    for outcome in outcomes:
        mark = "OK  " if outcome.ok else "FAIL"
        print(f"  [{mark}] {outcome.path.name}: {outcome.detail}")

    failed = [o for o in outcomes if not o.ok]
    if failed:
        print(
            f"\nG-11 NOT SATISFIED: {len(failed)} artefact(s) are unsigned or failed "
            "verification.",
            file=sys.stderr,
        )
        return 1
    print(f"\nG-11: all {len(outcomes)} artefact(s) verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
