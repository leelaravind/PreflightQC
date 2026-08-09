"""Phase 0 — documentation invariants (implementation plan P0-A3, P0-A4, P0-A5)."""

from __future__ import annotations

import pytest

import check_docs


@pytest.mark.parametrize("check", check_docs.ALL_CHECKS, ids=lambda c: c.__name__)
def test_documentation_invariant_holds(check) -> None:
    violations = check()
    assert not violations, "\n".join(str(v) for v in violations)


def test_all_six_research_pdfs_are_present(repo_root) -> None:
    """P0-A4 — the source pack must be complete, not merely structured."""
    missing = [
        area
        for area in check_docs.REQUIRED_SOURCE_AREAS
        if not list((repo_root / "docs" / "sources" / area).glob("*.pdf"))
    ]
    assert not missing, f"research PDFs missing for: {missing}"


def test_register_severity_ceiling_is_clean(repo_root) -> None:
    """P0-A5 — the register must never instruct a never-FAIL class to emit FAIL."""
    assert not check_docs.check_register_severity_ceiling()
    assert not check_docs.check_register_unknown_ceiling()
