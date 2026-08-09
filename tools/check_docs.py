"""Documentation invariant checks (implementation plan Phase 0, deliverable 4).

These checks exist because the specification's guarantees are only as good as the
documents that carry them. They are cheap, they run in the ordinary test suite, and
they catch the failure mode where a rule table drifts away from the severity model.

Run standalone:  python tools/check_docs.py
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Classifications that the specification forbids from ever producing FAIL (spec 7.3).
NEVER_FAIL_CLASSIFICATIONS = ("RECOMMENDATION", "BEST_PRACTICE", "ELIGIBILITY")

#: The six research areas the source register must account for (spec 12, register 0).
REQUIRED_SOURCE_AREAS = ("meta", "tiktok", "youtube", "linkedin", "mediainfo", "ffmpeg")


@dataclass(frozen=True)
class Violation:
    """A single documentation invariant failure."""

    check: str
    detail: str

    def __str__(self) -> str:
        return f"[{self.check}] {self.detail}"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_readme_links_resolve() -> list[Violation]:
    """Every repository-relative document path named in README.md must exist."""
    readme = REPO_ROOT / "README.md"
    if not readme.is_file():
        return [Violation("readme-links", "README.md is missing")]

    violations: list[Violation] = []
    # Backtick-quoted paths that look like repo-relative documents.
    for match in re.finditer(r"`(docs/[A-Za-z0-9_./-]+\.md)`", _read(readme)):
        candidate = REPO_ROOT / match.group(1)
        if not candidate.is_file():
            violations.append(Violation("readme-links", f"referenced but missing: {match.group(1)}"))
    return violations


def check_source_pdfs_present() -> list[Violation]:
    """Each of the six research areas must hold at least one source PDF."""
    violations: list[Violation] = []
    for area in REQUIRED_SOURCE_AREAS:
        area_dir = REPO_ROOT / "docs" / "sources" / area
        if not area_dir.is_dir():
            violations.append(Violation("source-pack", f"missing directory: docs/sources/{area}"))
            continue
        if not list(area_dir.glob("*.pdf")):
            violations.append(Violation("source-pack", f"no source PDF in docs/sources/{area}"))
    return violations


def check_register_names_every_area() -> list[Violation]:
    """The register's inventory must name every research area."""
    register = REPO_ROOT / "docs" / "sources" / "SOURCE-REGISTER.md"
    if not register.is_file():
        return [Violation("register-inventory", "SOURCE-REGISTER.md is missing")]

    text = _read(register)
    return [
        Violation("register-inventory", f"area not referenced in register: {area}")
        for area in REQUIRED_SOURCE_AREAS
        if f"docs/sources/{area}/" not in text
    ]


def check_register_severity_ceiling() -> list[Violation]:
    """No register row may pair a never-FAIL classification with FAIL behaviour.

    This is the documentation-level mirror of the engine's load-time severity guard.
    A violation here means the register itself is telling implementers to break
    specification 7.1.
    """
    register = REPO_ROOT / "docs" / "sources" / "SOURCE-REGISTER.md"
    if not register.is_file():
        return [Violation("register-severity", "SOURCE-REGISTER.md is missing")]

    violations: list[Violation] = []
    for lineno, line in enumerate(_read(register).splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        # A classification cell must be exactly the token; a cell reading
        # "HARD_REQUIREMENT / RECOMMENDATION" is a dual-classification row and is
        # judged on its behaviour cell alone.
        if not any(cell in NEVER_FAIL_CLASSIFICATIONS for cell in cells):
            continue
        if any(re.search(r"\bFAIL\b", cell) for cell in cells):
            violations.append(
                Violation("register-severity", f"line {lineno}: never-FAIL class paired with FAIL")
            )
    return violations


def check_register_unknown_ceiling() -> list[Violation]:
    """A row classified UNKNOWN may not carry FAIL or WARN behaviour (spec 7.3)."""
    register = REPO_ROOT / "docs" / "sources" / "SOURCE-REGISTER.md"
    if not register.is_file():
        return [Violation("register-unknown", "SOURCE-REGISTER.md is missing")]

    violations: list[Violation] = []
    for lineno, line in enumerate(_read(register).splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if "UNKNOWN" not in cells:
            continue
        if any(re.search(r"\b(FAIL|WARN)\b", cell) for cell in cells):
            violations.append(
                Violation("register-unknown", f"line {lineno}: UNKNOWN class paired with FAIL/WARN")
            )
    return violations


def check_required_documents_exist() -> list[Violation]:
    """The authoritative document set must be complete."""
    required = (
        "docs/specification/PREFLIGHTQC-V1-SPEC.md",
        "docs/sources/SOURCE-REGISTER.md",
        "docs/planning/IMPLEMENTATION-PLAN-V1.md",
        "docs/architecture/ARCHITECTURE-V1.md",
        "docs/architecture/ADR-001-TECH-STACK.md",
        "docs/testing/TEST-STRATEGY-V1.md",
        "docs/licensing/LICENSING-GATE-V1.md",
        "docs/FUTURE.md",
    )
    return [
        Violation("required-docs", f"missing: {rel}")
        for rel in required
        if not (REPO_ROOT / rel).is_file()
    ]


ALL_CHECKS = (
    check_required_documents_exist,
    check_readme_links_resolve,
    check_source_pdfs_present,
    check_register_names_every_area,
    check_register_severity_ceiling,
    check_register_unknown_ceiling,
)


def run_all() -> list[Violation]:
    """Run every documentation invariant and return the accumulated violations."""
    violations: list[Violation] = []
    for check in ALL_CHECKS:
        violations.extend(check())
    return violations


def main() -> int:
    violations = run_all()
    for violation in violations:
        print(violation, file=sys.stderr)
    if violations:
        print(f"\n{len(violations)} documentation invariant violation(s)", file=sys.stderr)
        return 1
    print(f"All {len(ALL_CHECKS)} documentation invariants hold.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
