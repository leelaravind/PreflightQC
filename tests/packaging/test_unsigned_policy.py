"""Policy U — the formalized unsigned release path — and the discipline around it.

The danger of an unsigned release path is not the missing signature; it is drift toward
pretending. Three inversions would each quietly break the policy's honesty, and each has
a test aimed at it:

1. The default ``sign.py verify`` starts passing on unsigned artefacts (G-11 weakened).
2. The unsigned expectation passes on a *signed* artefact (declared state not enforced).
3. The customer-facing copy stops disclosing, or starts implying the download is signed.
"""

from __future__ import annotations

import re
from pathlib import Path

import sign

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POLICY = REPO_ROOT / "docs" / "licensing" / "UNSIGNED-RELEASE-POLICY-V1.md"
RUN_BOOK = REPO_ROOT / "docs" / "planning" / "RELEASE-VALIDATION-V1.md"
LISTING = REPO_ROOT / "docs" / "marketing" / "MARKETPLACE-LISTING-V1.md"


def _state(state: str) -> sign.SignatureState:
    return sign.SignatureState(Path("artefact.exe"), state, state)


class TestAssessment:
    """The pure judgement logic, both policies, all three observed states."""

    def test_the_default_signed_expectation_fails_an_unsigned_artefact(self) -> None:
        """G-11 must keep failing on an unsigned build. This is the not-weakened test."""
        outcomes = sign.assess([_state(sign.UNSIGNED)], "signed")
        assert [o.ok for o in outcomes] == [False]

    def test_the_default_signed_expectation_passes_only_a_valid_signature(self) -> None:
        assert sign.assess([_state(sign.SIGNED_VALID)], "signed")[0].ok
        assert not sign.assess([_state(sign.ERROR)], "signed")[0].ok

    def test_the_unsigned_expectation_passes_an_unsigned_artefact(self) -> None:
        outcome = sign.assess([_state(sign.UNSIGNED)], "unsigned")[0]
        assert outcome.ok
        assert "as declared" in outcome.detail

    def test_the_unsigned_expectation_fails_a_signed_artefact(self) -> None:
        """A signed artefact under a declared-unsigned release means the documentation
        describes a different file than the one shipping. That must never pass."""
        outcome = sign.assess([_state(sign.SIGNED_VALID)], "unsigned")[0]
        assert not outcome.ok
        assert "unexpected" in outcome.detail

    def test_the_unsigned_expectation_fails_on_a_verification_error(self) -> None:
        assert not sign.assess([_state(sign.ERROR)], "unsigned")[0].ok

    def test_verify_defaults_to_the_signed_expectation(self) -> None:
        """The G-11 posture is the default; Policy U must always be asked for by name."""
        import inspect

        signature = inspect.signature(sign.verify)
        assert signature.parameters["expect"].default == "signed"

    def test_classification_recognises_all_three_states(self) -> None:
        assert sign.classify("No signature found in the file", 1) == sign.UNSIGNED
        assert sign.classify("Successfully verified", 0) == sign.SIGNED_VALID
        assert sign.classify("some other failure", 1) == sign.ERROR


class TestThePolicyDocument:
    def test_it_exists_and_keeps_g11_open(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        assert "REMAINS OPEN" in text
        assert "does not close, waive, or redefine" in text

    def test_it_contains_the_required_disclosure(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        assert "not digitally signed" in text
        assert "Windows protected your PC" in text
        assert "More info" in text

    def test_it_defines_all_release_conditions(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        for condition in ("U-1", "U-2", "U-3", "U-4", "U-5", "U-6"):
            assert condition in text

    def test_it_is_honest_about_what_a_checksum_is_not(self) -> None:
        text = " ".join(POLICY.read_text(encoding="utf-8").split())
        assert "does not authenticate the publisher" in text

    def test_it_never_recommends_a_self_signed_certificate(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        assert "Self-signed" in text
        assert "Rejected" in text.split("Self-signed")[1][:200]


class TestTheRunBook:
    def test_it_carries_both_policy_u_variants(self) -> None:
        text = RUN_BOOK.read_text(encoding="utf-8")
        assert "A2-U" in text
        assert "A8-U" in text
        assert "UNSIGNED-RELEASE-POLICY-V1.md" in text

    def test_the_unsigned_variant_records_the_g11_failure_too(self) -> None:
        """Both command outputs — the Policy U pass and the default failure — form the
        honest record. The run-book must demand both."""
        text = " ".join(RUN_BOOK.read_text(encoding="utf-8").split())
        assert "expect exit 1" in text
        assert "--expect unsigned" in text


class TestTheListing:
    def test_the_disclosure_is_present(self) -> None:
        text = LISTING.read_text(encoding="utf-8")
        assert "not digitally signed" in text
        assert "Windows protected your PC" in text

    def test_no_publishable_copy_implies_the_download_is_signed(self) -> None:
        """In the blockquoted (publishable) copy, every use of 'signed' must be negated
        or part of 'unsigned' — a listing that says 'signed' unqualified is the
        pretending this policy forbids."""
        copy = "\n".join(
            line.lstrip("> ")
            for line in LISTING.read_text(encoding="utf-8").splitlines()
            if line.startswith("> ")
        )
        for match in re.finditer(r"\b(\w+\s+)?(\w+\s+)?signed\b", copy.lower()):
            context = match.group(0)
            assert "not" in context or "unsigned" in context, (
                f"unqualified 'signed' in publishable copy: …{context}…"
            )
