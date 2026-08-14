"""The customer README must state only what the shipped catalogue and posture support.

The README is Gumroad content a paying customer reads before and after purchase. Every
claim in it that can be checked against the repository is checked here, so the document
cannot drift from the product: preset names and rule counts come from the real loader
over the shipped presets, the verification dates come from the shipped metadata, and
the claims the release posture forbids (signing, legal clearance, the retired network
wording, roadmap-as-current) are asserted absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
README_MD = REPO_ROOT / "docs" / "customer" / "README-PreflightQC-1.0.0.md"
README_TXT = REPO_ROOT / "dist" / "customer" / "README-PreflightQC-1.0.0.txt"


@pytest.fixture(scope="module")
def text() -> str:
    return README_MD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def catalog():
    from preflightqc.rules.loader import load_catalog

    result = load_catalog([REPO_ROOT / "presets"])
    assert result.rejected == ()
    return result


class TestPresetClaimsMatchTheCatalogue:
    def test_every_shipped_preset_appears_with_its_exact_name_and_rule_count(
        self, text: str, catalog
    ) -> None:
        for preset in catalog.presets:
            expected = f"{preset.display_name} ({len(preset.rules)} rules)"
            assert expected in text, (
                f"the README must list the shipped preset exactly as "
                f"'{expected}' — names and rule counts come from the catalogue, "
                "not from memory"
            )

    def test_the_headline_counts_are_derived_not_remembered(self, text: str, catalog) -> None:
        total_rules = sum(len(p.rules) for p in catalog.presets)
        assert f"({len(catalog.presets)} presets, {total_rules} rules)" in text

    def test_the_verification_date_and_ruleset_version_match_the_shipped_metadata(
        self, text: str, catalog
    ) -> None:
        dates = {p.last_verified_date for p in catalog.presets}
        versions = {p.ruleset_version for p in catalog.presets}
        assert len(dates) == 1 and len(versions) == 1, (
            "presets no longer share one verification date/version; the README's "
            "single blanket statement is no longer accurate and must be rewritten"
        )
        assert next(iter(dates)) in text
        assert next(iter(versions)) in text


class TestVersionAndPosture:
    def test_the_version_is_the_frozen_release_identity(self, text: str) -> None:
        from preflightqc import __version__

        assert __version__ == "1.0.0"
        assert "PreflightQC 1.0.0" in text
        assert "Version 1.0.0 — initial commercial release." in text

    def test_it_discloses_the_unsigned_state_and_never_claims_signing(self, text: str) -> None:
        assert "not digitally signed" in text
        # Every mention of signing must be the negated disclosure, never a claim.
        assert text.count("digitally signed") == text.count("not digitally signed")
        assert "code-signed" not in text.lower()

    def test_it_carries_the_validated_installer_hash(self, text: str) -> None:
        assert "5d71cec80d5972eb42734e77ad89b079b9f64426ec87574c73c8ab2d13517504" in text

    def test_no_legal_clearance_or_acceptance_guarantee_is_claimed(self, text: str) -> None:
        lowered = text.lower()
        assert "legal clearance" not in lowered
        assert "attorney" not in lowered
        assert "does not guarantee acceptance" in text
        assert "guaranteed acceptance" not in lowered

    def test_the_refund_window_is_the_canonical_seven_days(self, text: str) -> None:
        """COMMERCIAL-TERMS-V1.md is the single source of the refund policy: 7 calendar
        days, full price, merchant-of-record mechanism, statutory rights preserved. A
        30-day window was once stated in error and must never reach customer copy."""
        assert "request a refund within 7 calendar days" in text
        assert "full purchase price" in text
        assert "statutory rights" in text
        lowered = text.lower()
        assert "30 day" not in lowered
        assert "30-day" not in lowered
        assert "thirty day" not in lowered
        assert "14 day" not in lowered and "14-day" not in lowered

    def test_the_retired_network_wording_stays_retired(self, text: str) -> None:
        """'No socket implementation' was withdrawn with the first clean-machine fix
        (packaging/frozen_excludes.py); customer copy must not resurrect it."""
        assert "no socket implementation" not in text.lower()

    def test_the_roadmap_is_future_tense_and_not_presented_as_current(self, text: str) -> None:
        assert (
            "Future releases are planned to expand preset and rule-management "
            "capabilities" in text
        )
        # The one rule-management feature 1.0.0 lacks must be stated as absent.
        assert "no in-app editor" in text


class TestTheDistCopyIsTheSameDocument:
    @pytest.mark.skipif(not README_TXT.is_file(), reason="no dist/customer copy generated")
    def test_the_gumroad_txt_is_byte_identical_to_the_source_markdown(self) -> None:
        assert README_TXT.read_bytes() == README_MD.read_bytes(), (
            "dist/customer/README-PreflightQC-1.0.0.txt has drifted from "
            "docs/customer/README-PreflightQC-1.0.0.md — regenerate it by copying "
            "the markdown file; two diverging customer documents is how a stale "
            "claim ships"
        )
