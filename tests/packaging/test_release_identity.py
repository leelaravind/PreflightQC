"""The frozen release identity: PreflightQC 1.0.0, ITISYOU, Windows x64, Policy U.

Version drift is quiet: a hardcoded default in one script, an installer field nobody
re-checked, a listing row that still says dev. These tests pin every version-bearing
surface either to the single authoritative source (`preflightqc.__version__`) or to the
frozen value, so a future bump is a one-line change plus whatever these tests then
force to be updated deliberately.
"""

from __future__ import annotations

import re
from pathlib import Path

import preflightqc

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INSTALLER = REPO_ROOT / "packaging" / "installer.iss"
LISTING = REPO_ROOT / "docs" / "marketing" / "MARKETPLACE-LISTING-V1.md"
ADR = REPO_ROOT / "docs" / "decisions" / "ADR-G12-V1-OWNER-RISK-ACCEPTANCE.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


class TestTheAuthoritativeVersion:
    def test_the_frozen_identity(self) -> None:
        assert preflightqc.__version__ == "1.0.0"
        assert preflightqc.__product_name__ == "PreflightQC"
        assert preflightqc.__publisher__ == "ITISYOU"

    def test_no_development_suffix_survives_the_freeze(self) -> None:
        assert "-dev" not in preflightqc.__version__
        assert re.fullmatch(r"\d+\.\d+\.\d+", preflightqc.__version__)

    def test_pyproject_derives_rather_than_repeats(self) -> None:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        assert 'version = { attr = "preflightqc.__version__" }' in text
        assert not re.search(r'^version\s*=\s*"\d', text, re.MULTILINE)


class TestTheInstaller:
    def test_version_info_derives_from_the_passed_version(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        assert "VersionInfoVersion={#MyAppVersion}" in text
        # The old drift: a second, hardcoded product version.
        assert not re.search(r"VersionInfoVersion=\d", text)

    def test_the_fallback_version_is_visibly_not_a_release(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        assert '#define MyAppVersion "0.0.0"' in text

    def test_the_publisher_is_itisyou(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        assert '#define MyAppPublisher "ITISYOU"' in text


class TestNoHardcodedProductVersionInReleaseScripts:
    def test_no_release_script_hardcodes_a_dev_version_default(self) -> None:
        for script in ("generate_manifest.py", "build.py"):
            text = (REPO_ROOT / "packaging" / script).read_text(encoding="utf-8")
            assert '"0.1.0-dev"' not in text, script


class TestCustomerFacingSurfaces:
    def test_the_listing_carries_the_frozen_version_and_no_dev_identity(self) -> None:
        text = LISTING.read_text(encoding="utf-8")
        assert "1.0.0" in text
        assert "0.1.0-dev" not in text.replace(
            # The D-6 history row may name what was replaced; nothing else may.
            "No development version string may appear in the listing",
            "",
        )

    def test_the_changelog_records_both_identities_honestly(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")
        assert "## 1.0.0" in text
        assert "NOT YET RELEASED" in text
        assert "0.1.0-dev" in text  # the development identity is history, not erased
        assert "Policy U" in text

    def test_the_listing_states_the_unsigned_posture(self) -> None:
        text = LISTING.read_text(encoding="utf-8")
        assert "Policy U" in text
        assert "not digitally signed" in text


class TestG12AcceptanceIsExecutedAndReleaseSpecific:
    def test_the_acceptance_names_the_frozen_release(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "PreflightQC 1.0.0 (Windows x64, Policy U unsigned)" in text

    def test_the_acceptance_is_executed_with_a_date_and_a_verbatim_record(self) -> None:
        text = " ".join(ADR.read_text(encoding="utf-8").split())
        assert "COMPLETE for PreflightQC 1.0.0" in text
        assert "executed 2026-08-09" in text
        assert "G12-OWNER-ACCEPTANCE-V1.md" in text

    def test_the_acceptance_record_preserves_the_owner_instruction(self) -> None:
        record = (
            REPO_ROOT / "docs" / "reports" / "G12-OWNER-ACCEPTANCE-V1.md"
        ).read_text(encoding="utf-8")
        flattened = " ".join(record.split())
        assert "I explicitly accept the documented residual licensing/compliance risks" in flattened
        assert "PreflightQC 1.0.0" in flattened
        assert "no attorney has reviewed the product" in flattened
        assert "L-1 through L-14 remain unresolved" in flattened
        assert "FINAL BUILD APPROVED` has not been issued" in flattened

    def test_an_identity_change_voids_the_acceptance(self) -> None:
        text = " ".join(ADR.read_text(encoding="utf-8").split())
        assert "voids this acceptance and reopens G-12" in text
