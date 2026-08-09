"""The Microsoft Visual C++ runtime notice, and the runtime files it must cover.

The runtime DLLs arrive from two upstreams — the python.org CPython build and the Qt
for Python wheels — and Microsoft ships no licence text alongside them. The notice at
`third-party/licenses/MS-VC-Redistributable.txt` is therefore an authored file grounded
in the "Additional Conditions for this Windows binary build" section of CPython's own
LICENSE.txt. An authored legal notice is exactly the kind of file that drifts: the
package gains a runtime DLL the notice does not mention, or the notice quotes conditions
the cited licence no longer contains. These tests pin both ends.

Package-dependent tests skip cleanly when no built package is present, matching the
convention in test_release_artefacts.py.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

import generate_manifest
import pytest

import collect_licences

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = REPO_ROOT / "dist" / "PreflightQC"
NOTICE = REPO_ROOT / "third-party" / "licenses" / "MS-VC-Redistributable.txt"
CPYTHON_LICENCE = REPO_ROOT / "third-party" / "licenses" / "CPython-LICENSE.txt"

#: Every Microsoft runtime file the package is allowed to contain, by location.
#: Anything matching a Microsoft-runtime name pattern but not listed here is an
#: unnecessary runtime file and must fail the inventory test.
EXPECTED_INVENTORY: dict[str, frozenset[str]] = {
    "_internal": frozenset({"VCRUNTIME140.dll", "VCRUNTIME140_1.dll", "ucrtbase.dll"}),
    "_internal/PySide6": frozenset(
        {
            "MSVCP140.dll",
            "MSVCP140_1.dll",
            "MSVCP140_2.dll",
            "VCRUNTIME140.dll",
            "VCRUNTIME140_1.dll",
        }
    ),
    "_internal/shiboken6": frozenset(
        {"MSVCP140.dll", "VCRUNTIME140.dll", "VCRUNTIME140_1.dll"}
    ),
}

#: Name patterns that identify a Microsoft C/C++ runtime file wherever it appears.
MS_RUNTIME_NAME = re.compile(
    r"^(vcruntime|msvcp|msvcr|ucrtbase|api-ms-win-|concrt|vcomp|vcamp|vccorlib|mfc)",
    re.IGNORECASE,
)

#: Runtime families that must never ship: nothing in the dependency tree needs the
#: legacy CRT, OpenMP, AMP, ConcRT or MFC, so their presence would mean the freeze
#: started bundling components nobody attributed.
FORBIDDEN_FAMILIES = re.compile(r"^(msvcr\d|concrt|vcomp|vcamp|vccorlib|mfc)", re.IGNORECASE)


def _ms_runtime_files(package: Path) -> list[Path]:
    return sorted(
        p for p in package.rglob("*") if p.is_file() and MS_RUNTIME_NAME.match(p.name)
    )


class TestTheNotice:
    @pytest.fixture(scope="class")
    def text(self) -> str:
        return NOTICE.read_text(encoding="utf-8")

    def test_it_exists_and_is_not_the_placeholder(self, text: str) -> None:
        """The placeholder-detection word must not appear: generate_manifest reports an
        open action for as long as it does, and a release must not carry it."""
        assert "PLACEHOLDER" not in text
        assert "Microsoft Distributable Code" in text

    def test_it_names_every_runtime_file_class_the_package_may_contain(self, text: str) -> None:
        for name in (
            "VCRUNTIME140.dll",
            "VCRUNTIME140_1.dll",
            "MSVCP140.dll",
            "MSVCP140_1.dll",
            "MSVCP140_2.dll",
            "ucrtbase.dll",
            "api-ms-win-",
        ):
            assert name in text, f"the notice does not mention {name}"

    def test_it_names_both_provenances(self, text: str) -> None:
        assert "CPython" in text
        assert "PySide6" in text
        assert "shiboken6" in text

    def test_it_cites_the_cpython_licence_and_the_citation_is_not_dangling(
        self, text: str
    ) -> None:
        assert "CPython-LICENSE.txt" in text
        licence = CPYTHON_LICENCE.read_text(encoding="utf-8")
        assert "Additional Conditions for this Windows binary build" in licence

    def test_the_quoted_conditions_match_the_cited_licence_verbatim(self, text: str) -> None:
        """A paraphrased licence condition is not the condition. Each restriction the
        notice quotes must appear word-for-word in the licence it cites."""
        licence = " ".join(CPYTHON_LICENCE.read_text(encoding="utf-8").split())
        for quoted in (
            "you must require distributors and external end users to agree to terms "
            "that protect the Microsoft Distributable Code at least as much as "
            "Microsoft's own requirements for the Distributable Code.",
            "alter any copyright, trademark or patent notice in Microsoft's "
            "Distributable Code;",
            "use Microsoft's trademarks in your programs' names or in a way that "
            "suggests your programs come from or are endorsed by Microsoft;",
            "distribute Microsoft's Distributable Code to run on a platform other "
            "than Microsoft operating systems, run-time technologies or application "
            "platforms; or",
            "include Microsoft Distributable Code in malicious, deceptive or "
            "unlawful programs.",
        ):
            assert quoted in licence, f"not in the CPython licence verbatim: {quoted[:60]}…"
            assert quoted in " ".join(text.split()), f"not quoted in the notice: {quoted[:60]}…"

    def test_it_does_not_claim_legal_clearance(self, text: str) -> None:
        assert "does not claim legal clearance" in text
        assert "G-12" in text

    def test_the_missing_file_fallback_stays_fail_visible(self) -> None:
        """If the authored notice vanishes, collect_licences regenerates a file that
        generate_manifest will flag — never one that looks resolved."""
        assert "PLACEHOLDER" in collect_licences.MS_PLACEHOLDER

    def test_the_manifest_component_points_at_this_notice(self) -> None:
        component = next(
            c for c in generate_manifest.BUNDLED if c.name == "Microsoft Visual C++ Runtime"
        )
        assert component.licence_text == "MS-VC-Redistributable.txt"
        for relative in (
            "_internal/VCRUNTIME140.dll",
            "_internal/VCRUNTIME140_1.dll",
            "_internal/ucrtbase.dll",
            "_internal/api-ms-win-crt-runtime-l1-1-0.dll",
            "_internal/PySide6/MSVCP140.dll",
            "_internal/PySide6/VCRUNTIME140.dll",
            "_internal/shiboken6/MSVCP140.dll",
        ):
            assert any(
                fnmatch.fnmatch(relative, pattern) for pattern in component.patterns
            ), f"manifest patterns do not claim {relative}"


@pytest.mark.skipif(not PACKAGE.is_dir(), reason="no built package; run packaging/build.py")
class TestThePackagedRuntime:
    """The notice and the package must describe the same set of files."""

    def test_the_inventory_is_exactly_what_the_notice_describes(self) -> None:
        found: dict[str, set[str]] = {}
        api_forwarders: list[str] = []
        for path in _ms_runtime_files(PACKAGE):
            relative_dir = path.parent.relative_to(PACKAGE).as_posix()
            if path.name.lower().startswith("api-ms-win-"):
                api_forwarders.append(f"{relative_dir}/{path.name}")
            else:
                found.setdefault(relative_dir, set()).add(path.name)

        assert {d: frozenset(names) for d, names in found.items()} == EXPECTED_INVENTORY
        # The forwarders live only at the top level, and the notice states their count.
        assert all(f.startswith("_internal/") for f in api_forwarders)
        assert len(api_forwarders) == 39

    def test_no_forbidden_runtime_family_is_shipped(self) -> None:
        offenders = [
            p.relative_to(PACKAGE).as_posix()
            for p in PACKAGE.rglob("*")
            if p.is_file() and FORBIDDEN_FAMILIES.match(p.name)
        ]
        assert offenders == []

    def test_the_manifest_attributes_every_runtime_file_and_agrees_with_the_package(
        self,
    ) -> None:
        """Attribution is first-match: the copies inside the PySide6 and shiboken6
        directories are claimed by those components (they arrived in those wheels), and
        everything at the top level belongs to the Microsoft component. What matters is
        that the counts reconcile exactly — every runtime file in the package is
        attributed, and the Microsoft component claims precisely the top-level set."""
        manifest = generate_manifest.build_manifest(PACKAGE, "test")
        component = next(
            c for c in manifest.components if c.name == "Microsoft Visual C++ Runtime"
        )
        top_level = [p for p in _ms_runtime_files(PACKAGE) if p.parent == PACKAGE / "_internal"]
        assert component.file_count == len(top_level) == 42  # 39 forwarders + 3
        assert component.licence_text_path == "MS-VC-Redistributable.txt"
        # Nothing Microsoft-runtime-shaped may be left unattributed.
        assert manifest.unaccounted_files == []

    def test_the_packaged_notice_is_the_authored_one(self) -> None:
        packaged = (PACKAGE / "licenses" / "MS-VC-Redistributable.txt").read_text(
            encoding="utf-8"
        )
        assert "PLACEHOLDER" not in packaged
        assert "Microsoft Distributable Code" in packaged
        assert packaged == NOTICE.read_text(encoding="utf-8")

    def test_the_licence_gate_reports_a_clean_pass(self) -> None:
        manifest = generate_manifest.build_manifest(PACKAGE, "test")
        assert manifest.gate_status["G-2_licence_texts_present"] == "PASS"
