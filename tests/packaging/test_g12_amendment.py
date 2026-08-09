"""The G-12 SPEC LOCK amendment — owner risk acceptance, never a clearance claim.

The amendment replaced mandatory attorney review with an owner risk-acceptance gate.
The failure mode these tests guard is drift toward pretending: a document one day
claiming review happened, the decision record losing the statements that make it an
*informed* acceptance, or the gate quietly vanishing from the machinery. The amendment
is only honest while all three stay pinned.
"""

from __future__ import annotations

from pathlib import Path

import generate_manifest
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ADR = REPO_ROOT / "docs" / "decisions" / "ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md"
SPEC = REPO_ROOT / "docs" / "specification" / "PREFLIGHTQC-V1-SPEC.md"
PACKAGE = REPO_ROOT / "dist" / "PreflightQC"

#: Phrases that would claim professional review or clearance happened. None may appear
#: anywhere in the documentation tree. Chosen so no honest negated sentence contains
#: them ("not attorney reviewed" does not match "attorney has reviewed").
FORBIDDEN_CLAIMS = (
    # "attorney has reviewed" and "reviewed by counsel" are deliberately absent:
    # honest negations ("No attorney has reviewed ...", "has not been reviewed by
    # counsel ...") would match them.
    "attorney approved",
    "attorney has approved",
    "approved by counsel",
    "counsel has approved",
    "legal clearance obtained",
    "legal clearance was obtained",
    "legal clearance has been obtained",
    "legally cleared",
    "cleared by counsel",
)


class TestTheDecisionRecord:
    @pytest.fixture(scope="class")
    def text(self) -> str:
        return ADR.read_text(encoding="utf-8")

    def test_it_exists_with_the_new_gate_name(self, text: str) -> None:
        assert "OWNER LICENSING & COMPLIANCE RISK ACCEPTANCE" in text

    def test_it_preserves_the_previous_wording_verbatim(self, text: str) -> None:
        assert (
            "Final commercial licence and EULA review by a qualified software-IP "
            "attorney is complete." in text
        )

    def test_it_records_the_mandated_reasons(self, text: str) -> None:
        flattened = " ".join(text.split())
        assert "£0" in flattened
        assert "not legal advice" in flattened.lower()
        assert "residual" in flattened.lower()
        assert "not a finding that legal review is unnecessary" in flattened

    def test_it_documents_the_unresolved_questions_and_reopening_conditions(
        self, text: str
    ) -> None:
        assert "L-1" in text and "L-14" in text
        assert "REOPEN" in text.upper()

    def test_it_claims_no_clearance_and_no_review(self, text: str) -> None:
        assert "No legal clearance is claimed" in text
        assert "No attorney has reviewed anything" in text

    def test_the_acceptance_is_executed_scoped_and_reopenable(self, text: str) -> None:
        """The acceptance was executed 2026-08-09 for exactly one release identity.
        What must never drift: the scope (1.0.0 only), the date, the pointer to the
        verbatim instruction, and the reopening rule."""
        flattened = " ".join(text.split())
        assert "COMPLETE for PreflightQC 1.0.0" in flattened
        assert "Date: **2026-08-09**" in flattened
        assert "G12-OWNER-ACCEPTANCE-V1.md" in flattened
        assert "voids this acceptance and reopens G-12" in flattened
        # Executing the acceptance answered nothing:
        assert "remains unresolved" in flattened


class TestTheAmendedSpecification:
    @pytest.fixture(scope="class")
    def text(self) -> str:
        return SPEC.read_text(encoding="utf-8")

    def test_the_version_was_incremented_with_a_changelog(self, text: str) -> None:
        assert "| Version | 1.1.0 |" in text
        assert "### Changelog" in text
        assert "G-12 amended" in text

    def test_the_gate_row_carries_the_owner_form_and_the_amendment_marker(
        self, text: str
    ) -> None:
        assert "Owner licensing & compliance risk acceptance is complete" in text
        assert "ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md" in text

    def test_the_spec_still_denies_clearance_and_review(self, text: str) -> None:
        assert "No legal clearance is claimed" in text
        assert "No attorney has reviewed this product" in text

    def test_the_gate_was_not_deleted(self, text: str) -> None:
        assert "| G-12 |" in text


class TestTheMachinery:
    def test_the_manifest_scopes_the_acceptance_to_the_accepted_version(self) -> None:
        """The recorded acceptance covers 1.0.0 and nothing else. The generator must
        report the gate complete for that version and open for any other — the O-8
        reopening rule, made mechanical."""
        if not PACKAGE.is_dir():
            pytest.skip("no built package; run packaging/build.py")
        assert generate_manifest.G12_ACCEPTED_VERSION == "1.0.0"

        accepted = generate_manifest.build_manifest(PACKAGE, "1.0.0")
        assert "G-12_attorney_review" not in accepted.gate_status
        status = accepted.gate_status["G-12_owner_risk_acceptance"]
        assert status.startswith("PASS")
        assert "no attorney review occurred" in status
        assert "no legal clearance is claimed" in status

        other = generate_manifest.build_manifest(PACKAGE, "1.0.1")
        assert other.gate_status["G-12_owner_risk_acceptance"].startswith("NOT COMPLETE")

    def test_the_eula_open_questions_survived_the_retitle(self) -> None:
        text = (REPO_ROOT / "packaging" / "EULA.txt").read_text(encoding="utf-8")
        assert "OPEN LEGAL QUESTIONS" in text
        assert "OPEN QUESTIONS FOR ATTORNEY REVIEW" not in text
        for question_marker in ("Installation Information", "Governing law", "Microsoft"):
            assert question_marker in text


class TestNoDocumentClaimsReview:
    def test_no_affirmative_review_or_clearance_claim_anywhere(self) -> None:
        """Scans every Markdown and text document. The amendment is honest exactly as
        long as nothing anywhere says review happened."""
        roots = (
            REPO_ROOT / "docs",
            REPO_ROOT / "packaging",
            REPO_ROOT / "third-party" / "licenses",
        )
        files = [REPO_ROOT / "README.md"]
        for root in roots:
            files.extend(p for p in root.rglob("*.md"))
            files.extend(p for p in root.rglob("*.txt"))

        offenders: list[str] = []
        for path in files:
            lowered = " ".join(
                path.read_text(encoding="utf-8", errors="replace").split()
            ).lower()
            offenders.extend(
                f"{path.relative_to(REPO_ROOT)}: {phrase!r}"
                for phrase in FORBIDDEN_CLAIMS
                if phrase in lowered
            )
        assert offenders == []

    def test_the_scan_would_catch_a_real_claim(self, tmp_path: Path) -> None:
        planted = "The EULA was attorney approved on Tuesday."
        assert any(phrase in planted.lower() for phrase in FORBIDDEN_CLAIMS)
