"""Final Binding guards: the approved brand asset, its derivatives, and the locked
commercial terms.

Two drift risks. The artwork: an icon regenerated from the wrong source, or a silent
replacement of the approved logo, would put unapproved branding on a commercial
product — so the approved original is pinned by hash and every wiring point is
asserted. The commercial copy: the price, one-time nature and refund policy are
locked; a listing that quietly grows a subscription word, a percentage deduction or a
second price is exactly what these tests exist to catch.
"""

from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO = REPO_ROOT / "assets" / "logo" / "logo.png"
ICO = REPO_ROOT / "assets" / "logo" / "preflightqc.ico"
WINDOW_PNG = REPO_ROOT / "src" / "preflightqc" / "ui" / "assets" / "preflightqc.png"
MARKETING_PNG = REPO_ROOT / "assets" / "logo" / "logo-512.png"
PROVENANCE = REPO_ROOT / "assets" / "logo" / "PROVENANCE.md"
MARKETING_DIR = REPO_ROOT / "docs" / "marketing"
PAGES = MARKETING_DIR / "pages"

#: The Product Owner-approved artwork, pinned. Changing the logo requires owner
#: approval first, then regeneration, then updating this hash and PROVENANCE.md.
APPROVED_LOGO_SHA256 = "54372b3e0e9e7a973b709115f0d54be242934b63e7abdbb09cfc178a880cfda3"


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    width, height = struct.unpack(">II", data[16:24])
    return width, height


class TestBrandAssets:
    def test_the_approved_logo_is_present_and_unaltered(self) -> None:
        assert hashlib.sha256(LOGO.read_bytes()).hexdigest() == APPROVED_LOGO_SHA256

    def test_the_ico_contains_the_full_size_ladder(self) -> None:
        data = ICO.read_bytes()
        reserved, ico_type, count = struct.unpack("<HHH", data[:6])
        assert (reserved, ico_type) == (0, 1)
        sizes = sorted(
            struct.unpack("<BBBBHHII", data[6 + i * 16 : 6 + (i + 1) * 16])[0] or 256
            for i in range(count)
        )
        assert sizes == [16, 24, 32, 48, 64, 128, 256]

    def test_the_shipped_window_icon_is_a_256px_png(self) -> None:
        assert _png_dimensions(WINDOW_PNG) == (256, 256)

    def test_the_marketing_derivative_is_512px(self) -> None:
        assert _png_dimensions(MARKETING_PNG) == (512, 512)

    def test_provenance_records_owner_approval_and_the_pinned_hash(self) -> None:
        text = PROVENANCE.read_text(encoding="utf-8")
        assert "Product Owner-provided and approved" in text
        assert APPROVED_LOGO_SHA256 in text
        assert "must not be redesigned" in text

    def test_the_executable_and_installer_reference_the_icon(self) -> None:
        spec = (REPO_ROOT / "packaging" / "preflightqc.spec").read_text(encoding="utf-8")
        assert 'icon=str(REPO_ROOT / "assets" / "logo" / "preflightqc.ico")' in spec
        assert '"preflightqc/ui/assets"' in spec  # window PNG ships in _internal
        iss = (REPO_ROOT / "packaging" / "installer.iss").read_text(encoding="utf-8")
        assert "SetupIconFile=..\\assets\\logo\\preflightqc.ico" in iss

    def test_the_branding_module_points_at_the_shipped_asset(self) -> None:
        from preflightqc.ui import branding

        assert branding.ICON_PATH == WINDOW_PNG
        assert branding.ICON_PATH.is_file()


class TestCommercialLock:
    """£19.99 one-time, no subscription, no automatic renewal, clean refunds."""

    @staticmethod
    def _marketing_texts() -> dict[str, str]:
        files = sorted(MARKETING_DIR.rglob("*.md"))
        return {
            str(p.relative_to(REPO_ROOT)): p.read_text(encoding="utf-8") for p in files
        }

    def test_the_only_price_anywhere_is_19_99(self) -> None:
        price = re.compile(r"£\s?\d[\d,.]*")
        for name, text in self._marketing_texts().items():
            for match in price.findall(text):
                assert match.replace(" ", "") in {"£19.99", "£0"}, f"{name}: {match}"

    def test_every_sales_surface_states_one_time_and_no_subscription(self) -> None:
        for name in (
            "docs/marketing/pages/PRODUCT-PAGE.md",
            "docs/marketing/LEMON-SQUEEZY-LISTING-V1.md",
            "docs/marketing/GUMROAD-LISTING-V1.md",
            "docs/marketing/COMMERCIAL-TERMS-V1.md",
        ):
            text = self._marketing_texts()[name.replace("/", "\\")]
            lowered = text.lower()
            assert "£19.99" in text, name
            assert "one-time" in lowered, name
            assert "no subscription" in lowered, name
            assert "renewal" in lowered, name  # the "no automatic renewal" statement

    def test_no_forbidden_refund_or_billing_language(self) -> None:
        """COMMERCIAL-TERMS-V1.md is exempt: it is the canonical definition and names
        the excluded concepts ("no 15% deduction", "no prorated refund") in order to
        forbid them — the same negation trap as the claim guards."""
        forbidden = (
            "15%",
            "restocking",
            "prorated",
            "pro-rated",
            "pro rata",
            "per month",
            "/month",
            "monthly plan",
            "recurring billing",
            "renews automatically",
        )
        for name, text in self._marketing_texts().items():
            if name.endswith("COMMERCIAL-TERMS-V1.md"):
                continue
            lowered = text.lower()
            for phrase in forbidden:
                assert phrase not in lowered, f"{name}: {phrase!r}"

    def test_the_refund_policy_core_terms_are_present(self) -> None:
        text = (PAGES / "REFUNDS-PAGE.md").read_text(encoding="utf-8")
        flattened = " ".join(text.split())
        assert "7 calendar days" in flattened
        assert "full purchase price" in flattened
        assert "merchant of record" in flattened.lower()
        assert "statutory rights" in flattened


class TestPrePurchaseDisclosure:
    """Everything the buyer must know appears in the product-page material."""

    def test_the_product_page_states_every_required_fact(self) -> None:
        text = (PAGES / "PRODUCT-PAGE.md").read_text(encoding="utf-8")
        flattened = " ".join(text.split()).lower()
        for required in (
            "windows 10 x64",
            "£19.99",
            "one-time",
            "offline",
            "no login",
            "no telemetry",
            "refund",
            "not digitally signed",
            "smartscreen",
            "sha-256",
            "support",
        ):
            assert required.lower() in flattened, f"product page missing: {required}"

    def test_all_five_pages_exist(self) -> None:
        for page in (
            "PRODUCT-PAGE.md",
            "SUPPORT-PAGE.md",
            "REFUNDS-PAGE.md",
            "LEGAL-PAGE.md",
            "SOURCE-PAGE.md",
        ):
            assert (PAGES / page).is_file(), page

    def test_the_pages_carry_the_frozen_identity_not_the_dev_one(self) -> None:
        for page in PAGES.glob("*.md"):
            text = page.read_text(encoding="utf-8")
            assert "0.1.0" not in text, page.name

    def test_both_channel_listings_carry_the_unsigned_disclosure(self) -> None:
        for name in ("LEMON-SQUEEZY-LISTING-V1.md", "GUMROAD-LISTING-V1.md"):
            text = (MARKETING_DIR / name).read_text(encoding="utf-8")
            # Strip blockquote markers before flattening, or a "> " lands mid-phrase.
            lowered = " ".join(
                line.lstrip("> ") for line in text.splitlines()
            ).lower()
            lowered = " ".join(lowered.split()).replace("**", "")
            assert "not digitally signed" in lowered, name
            assert "smartscreen" in lowered, name
            assert "no activation" in lowered, name
