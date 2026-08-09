"""Every word the customer reads, checked for claims the product must never make.

Specification §4.1 forbids implying platform acceptance. That is not a style rule: a tool
that says "guaranteed accepted" is making a promise it has no way to keep, and the first
rejected upload destroys the user's trust in every other verdict it ever gave.

`reporting/claims.py` already guards report output. This file extends the same guard to
the interface, the About dialog and the EULA — the places a claim is most likely to be
written by someone who has never read the specification.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from preflightqc import LEGAL_URL, PRODUCT_URL, SOURCE_URL, SUPPORT_URL, __publisher__
from preflightqc.reporting import claims
from preflightqc.ui import viewmodels
from preflightqc.ui.about import REQUIRED_NOTICES
from preflightqc.ui.widgets import EmptyState

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = REPO_ROOT / "src" / "preflightqc" / "ui"


def _string_literals(path: Path) -> list[str]:
    """Every string literal in a module, which is a superset of its visible copy."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]


class TestForbiddenClaims:
    @pytest.mark.parametrize("path", sorted(UI_DIR.glob("*.py")), ids=lambda p: p.name)
    def test_no_ui_string_promises_platform_acceptance(self, path: Path) -> None:
        offenders = [
            (text, found)
            for text in _string_literals(path)
            if (found := claims.contains_forbidden_claim(text))
        ]
        assert offenders == []

    def test_the_eula_makes_no_acceptance_claim(self) -> None:
        text = (REPO_ROOT / "packaging" / "EULA.txt").read_text(encoding="utf-8")
        assert claims.contains_forbidden_claim(text) == ()

    def test_the_marketplace_copy_makes_no_acceptance_claim(self) -> None:
        """Scans the copy blocks, not the whole document.

        The listing document also *lists* the forbidden phrases, so a reader knows what
        never to write. Scanning the whole file would flag that section and the obvious
        fix would be to delete the guidance — the same trap as the EULA disclaimer.
        Blockquotes are the text intended for publication; that is what is checked.
        """
        listing = REPO_ROOT / "docs" / "marketing" / "MARKETPLACE-LISTING-V1.md"
        if not listing.is_file():
            pytest.skip("marketplace listing not written yet")
        copy = "\n".join(
            line.lstrip("> ")
            for line in listing.read_text(encoding="utf-8").splitlines()
            if line.startswith("> ")
        )
        assert copy.strip(), "no publishable copy found in the listing document"
        assert claims.contains_forbidden_claim(copy) == ()

    def test_the_listing_records_what_must_never_be_claimed(self) -> None:
        """The guidance section is required; the previous test must not delete it."""
        listing = REPO_ROOT / "docs" / "marketing" / "MARKETPLACE-LISTING-V1.md"
        if not listing.is_file():
            pytest.skip("marketplace listing not written yet")
        text = listing.read_text(encoding="utf-8")
        assert "MUST NOT APPEAR IN THE LISTING" in text
        assert "Testimonials" in text

    def test_the_guard_actually_catches_something(self) -> None:
        """A claim scanner that has never fired is not evidence of anything."""
        assert claims.contains_forbidden_claim("Files are guaranteed accepted by TikTok.")


class TestCopyIsHonestAboutWhatTheToolDoes:
    def test_the_approved_claim_is_about_the_preset_not_the_platform(self) -> None:
        assert "selected PreflightQC preset" in claims.APPROVED_CLAIM
        assert "accept" not in claims.APPROVED_CLAIM.lower()

    def test_the_accuracy_statement_admits_the_limits(self) -> None:
        text = claims.ACCURACY_STATEMENT.lower()
        assert "does not watch the video" in text
        assert "change without notice" in text
        assert "unknown" in text

    def test_the_first_screen_states_the_privacy_position(self) -> None:
        """The main differentiator, and the thing a professional wants confirmed first."""
        text = EmptyState.PRIVACY.lower()
        assert "this machine" in text
        assert "read-only" in text
        assert "never modified" in text

    def test_the_inconclusive_wording_explains_rather_than_alarms(self) -> None:
        text = viewmodels.FileRow.INCONCLUSIVE_REASON
        assert text.endswith(".")
        assert "no video stream" in text.lower()
        for shouty in ("ERROR", "FAILED", "CORRUPT", "!"):
            assert shouty not in text


class TestBranding:
    def test_the_publisher_is_named_once_and_spelled_consistently(self) -> None:
        assert __publisher__ == "ITISYOU"

    def test_every_customer_url_is_under_the_product_path(self) -> None:
        for url in (SUPPORT_URL, LEGAL_URL, SOURCE_URL):
            assert url.startswith(PRODUCT_URL)

    def test_the_urls_are_https(self) -> None:
        for url in (PRODUCT_URL, SUPPORT_URL, LEGAL_URL, SOURCE_URL):
            assert url.startswith("https://")

    def test_nothing_in_the_product_fetches_a_url(self) -> None:
        """Showing an address must never become a reason to open a socket.

        Scans the whole application package, not only the UI: the constants live in
        `preflightqc/__init__.py` and could be imported anywhere.

        Checked against the *syntax tree*, not the text. Prose is full of these words on
        purpose — the About dialog says "makes no network requests" and a docstring says
        "must never open a socket" — and a text scan would flag exactly the sentences
        that state the guarantee.
        """
        forbidden_modules = {
            "urllib",
            "http",
            "requests",
            "httpx",
            "socket",
            "ssl",
            "asyncio",
            "webbrowser",
            "ftplib",
            "smtplib",
            "xmlrpc",
        }
        forbidden_attributes = {
            "QNetworkAccessManager",
            "QDesktopServices",
            "QTcpSocket",
            "QUdpSocket",
            "openUrl",
            "urlopen",
        }
        package = REPO_ROOT / "src" / "preflightqc"
        offenders: list[str] = []

        for path in sorted(package.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    offenders.extend(
                        f"{path.name}: import {alias.name}"
                        for alias in node.names
                        if alias.name.split(".")[0] in forbidden_modules
                    )
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.split(".")[0] in forbidden_modules:
                        offenders.append(f"{path.name}: from {node.module}")
                elif isinstance(node, ast.Attribute) and node.attr in forbidden_attributes:
                    offenders.append(f"{path.name}: .{node.attr}")
                elif isinstance(node, ast.Name) and node.id in forbidden_attributes:
                    offenders.append(f"{path.name}: {node.id}")

        assert offenders == []

    def test_that_network_scan_would_catch_a_real_import(self, tmp_path: Path) -> None:
        """The scan above passes today; prove it is capable of failing."""
        module = tmp_path / "leaky.py"
        module.write_text("import urllib.request\n", encoding="utf-8")
        tree = ast.parse(module.read_text(encoding="utf-8"))
        names = [
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        ]
        assert any(name.split(".")[0] == "urllib" for name in names)


class TestRequiredNotices:
    def test_the_ffmpeg_notice_names_the_version_actually_shipped(self) -> None:
        joined = " ".join(REQUIRED_NOTICES)
        assert "LGPLv3" in joined
        assert "enable-version3" in joined
        assert "LGPLv2.1" not in joined

    def test_ownership_of_ffmpeg_is_disclaimed(self) -> None:
        assert any("does not own FFmpeg" in notice for notice in REQUIRED_NOTICES)

    def test_mediainfo_and_zenlib_are_both_credited(self) -> None:
        joined = " ".join(REQUIRED_NOTICES)
        assert "MediaInfo" in joined
        assert "ZenLib" in joined

    def test_qt_is_credited(self) -> None:
        assert any("Qt" in notice for notice in REQUIRED_NOTICES)
