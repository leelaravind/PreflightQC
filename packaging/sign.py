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

``verify --expect unsigned`` exists for the V1 unsigned release path (Policy U,
``docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md``): it passes only when every first-party
artefact is present and carries **no** signature — the declared release state. It fails
if an artefact turns out to be signed, because an *unexpected* signature on a release
that is documented as unsigned is a discrepancy someone must explain, not a bonus.
Passing this check is **not** G-11: the success message says so explicitly.
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


#: The three states a signature check can find an artefact in. Classification is kept
#: separate from judgement so the same observation serves both release policies.
SIGNED_VALID = "SIGNED_VALID"
UNSIGNED = "UNSIGNED"
ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class SignatureState:
    path: Path
    state: str
    detail: str


def classify(output: str, returncode: int) -> str:
    """What signtool's verdict on one file actually was."""
    if "No signature found" in output:
        return UNSIGNED
    if returncode == 0:
        return SIGNED_VALID
    return ERROR


def assess(states: list[SignatureState], expect: str) -> list[Outcome]:
    """Judge observed signature states against the declared release policy.

    ``expect="signed"`` is gate G-11: every artefact must carry a valid signature.
    ``expect="unsigned"`` is Policy U: every artefact must carry none — a signed
    artefact under the unsigned policy is a failure, because the release documentation
    would then be describing a different file than the one shipping.
    """
    outcomes: list[Outcome] = []
    for observed in states:
        if expect == "signed":
            ok = observed.state == SIGNED_VALID
            detail = observed.detail
        else:
            ok = observed.state == UNSIGNED
            if observed.state == UNSIGNED:
                detail = "UNSIGNED (as declared by Policy U)"
            elif observed.state == SIGNED_VALID:
                detail = "SIGNED — unexpected under the declared unsigned release state"
            else:
                detail = observed.detail
        outcomes.append(Outcome(observed.path, ok, detail))
    return outcomes


def inspect_signatures(paths: list[Path]) -> list[SignatureState]:
    signtool = find_signtool()
    if signtool is None:
        return [
            SignatureState(Path("signtool"), ERROR, "signtool.exe not found; install the Windows SDK")
        ]

    states: list[SignatureState] = []
    for path in paths:
        result = subprocess.run(
            [str(signtool), "verify", "/pa", "/v", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        state = classify(output, result.returncode)
        detail = "UNSIGNED" if state == UNSIGNED else output.splitlines()[-1:][0] if output else ""
        states.append(SignatureState(path, state, detail))
    return states


def verify(paths: list[Path], *, expect: str = "signed") -> list[Outcome]:
    return assess(inspect_signatures(paths), expect)


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
    parser.add_argument(
        "--expect",
        choices=["signed", "unsigned"],
        default="signed",
        help=(
            "verify only: the declared release state to check against. 'signed' is gate "
            "G-11 (default). 'unsigned' is Policy U — every artefact must be present and "
            "carry no signature; see docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md."
        ),
    )
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
        outcomes = verify(paths, expect=args.expect)

    for outcome in outcomes:
        mark = "OK  " if outcome.ok else "FAIL"
        print(f"  [{mark}] {outcome.path.name}: {outcome.detail}")

    failed = [o for o in outcomes if not o.ok]
    if args.action == "verify" and args.expect == "unsigned":
        if failed:
            print(
                f"\nPOLICY U NOT SATISFIED: {len(failed)} artefact(s) do not match the "
                "declared unsigned release state. A signed or unverifiable artefact under "
                "an unsigned release declaration must be explained before anything ships.",
                file=sys.stderr,
            )
            return 1
        print(
            f"\nPolicy U verified: all {len(outcomes)} artefact(s) present and unsigned, "
            "as declared. This is NOT a signing pass — gate G-11 remains OPEN, and the "
            "release must carry the unsigned-installer disclosure "
            "(docs/licensing/UNSIGNED-RELEASE-POLICY-V1.md §4)."
        )
        return 0

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
