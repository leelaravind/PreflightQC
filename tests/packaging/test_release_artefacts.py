"""The release gates are enforced by scripts. Those scripts need tests too.

Before this file existed, `packaging/` had no test coverage at all — and it showed. The
prohibited-component scanner reported **104 violations against a fully compliant package**
because it substring-matched `libx264` inside `--disable-libx264`; the manifest generator
had never run successfully at all, because it read lock-file keys that do not exist.

Both would have been discovered under release pressure, which is the worst possible moment
to be told that a compliance gate does not work. A gate that has never been run is not a
gate; it is a comment.

Tests that need the built package skip cleanly when it is absent, so a clean checkout
still runs the whole suite.
"""

from __future__ import annotations

import json
import re
import tarfile
from datetime import date as _date
from pathlib import Path

import fetch_binaries
import generate_manifest
import layout_check
import pytest
import scan_prohibited

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE = REPO_ROOT / "dist" / "PreflightQC"
LOCK_FILE = REPO_ROOT / "packaging" / "binaries.lock.json"
EULA = REPO_ROOT / "packaging" / "EULA.txt"
INSTALLER_ISS = REPO_ROOT / "packaging" / "installer.iss"

#: The configuration the shipped build actually reports, trimmed to the parts that matter.
COMPLIANT_CONFIGURATION = (
    "configuration: --enable-version3 --enable-shared --disable-static --enable-gmp "
    "--enable-libaribb24 --enable-libzvbi --disable-avisynth --disable-frei0r "
    "--disable-libdavs2 --disable-libdvdread --disable-libdvdnav --disable-libfdk-aac "
    "--disable-librubberband --disable-libvidstab --disable-libx264 --disable-libx265 "
    "--disable-libxavs2 --disable-libxvid --enable-libopenh264 --enable-libvvenc"
)


class TestTheScannerDoesNotCryWolf:
    """The regression that matters most: a compliant build must scan clean."""

    def test_a_disabled_component_is_not_a_violation(self) -> None:
        assert scan_prohibited.audit_configuration(COMPLIANT_CONFIGURATION) == ()

    def test_version3_is_not_a_violation(self) -> None:
        assert scan_prohibited.licence_version(COMPLIANT_CONFIGURATION) == "LGPL-3.0-or-later"

    @pytest.mark.parametrize(
        "switch", ["--enable-gpl", "--enable-nonfree", "--enable-libx264", "--enable-libfdk-aac"]
    )
    def test_a_genuinely_enabled_prohibited_component_is_caught(self, switch: str) -> None:
        findings = scan_prohibited.audit_configuration(f"{COMPLIANT_CONFIGURATION} {switch}")
        assert findings, f"{switch} must be reported"

    def test_the_scanner_and_the_application_share_one_implementation(self) -> None:
        """Three copies of this policy is how the spike and the app came to disagree."""
        from preflightqc.platform import binaries

        assert scan_prohibited.audit_configuration is binaries.audit_configuration
        assert scan_prohibited.PROHIBITED_COMPONENTS is binaries.PROHIBITED_COMPONENTS


class TestCapabilityListingParser:
    """ffprobe's listing formats are not uniform; each one has to actually parse."""

    def test_encoder_rows(self) -> None:
        text = (
            "Encoders:\n"
            " V..... = Video\n"
            " ------\n"
            " V....D libaom-av1           libaom AV1 (codec av1)\n"
            " A....D aac                  AAC (Advanced Audio Coding)\n"
        )
        assert scan_prohibited.parse_listing(text) == frozenset({"libaom-av1", "aac"})

    def test_demuxer_rows_with_a_narrower_flag_column(self) -> None:
        text = "Formats:\n D.. = Demuxing supported\n ---\n D   3dostr          3DO STR\n D   aa   Audible\n"
        assert scan_prohibited.parse_listing(text) == frozenset({"3dostr", "aa"})

    def test_bare_protocol_names(self) -> None:
        text = "Supported file protocols:\nInput:\n  async\n  concat\nOutput:\n  file\n"
        assert scan_prohibited.parse_listing(text) == frozenset({"async", "concat", "file"})

    def test_legend_lines_contribute_no_names(self) -> None:
        assert scan_prohibited.parse_listing(" D.. = Demuxing supported\n ..d = Is a device\n") == frozenset()


class TestTheGplFilterListIsDerivedNotRemembered:
    """The list must match FFmpeg's own configure for the exact shipped source."""

    @pytest.fixture(scope="class")
    def archived_source(self) -> Path:
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        entry = next(c for c in lock["components"] if c["name"] == "ffprobe")
        archive = REPO_ROOT / str(entry["corresponding_source"]["archive"])
        if not archive.is_file():
            pytest.skip("the corresponding-source archive is not present on this machine")
        return archive

    def test_it_matches_the_shipped_sources_configure(self, archived_source: Path) -> None:
        with tarfile.open(archived_source, "r:*") as handle:
            member = next(m for m in handle.getmembers() if m.name.endswith("/configure"))
            extracted = handle.extractfile(member)
            assert extracted is not None
            configure = extracted.read().decode("utf-8", errors="replace")

        derived = {
            match.group(1)
            for match in re.finditer(
                r'^([a-z0-9_]+)_filter_deps(?:_any)?="([^"]*)"', configure, re.MULTILINE
            )
            if "gpl" in match.group(2).split()
        }
        assert derived == set(scan_prohibited.GPL_ONLY_BUILTIN_FILTERS)

    def test_two_filters_that_are_not_gpl_gated_are_absent(self) -> None:
        """`geq` and `pp` were both wrong on the first attempt, from memory.

        Either one would have failed a clean build, which is the direction that gets a
        gate switched off rather than fixed.
        """
        assert "geq" not in scan_prohibited.GPL_ONLY_BUILTIN_FILTERS
        assert "pp" not in scan_prohibited.GPL_ONLY_BUILTIN_FILTERS

    def test_avs_is_not_treated_as_avisynth(self) -> None:
        """AVS is the Chinese video codec; it is in every build and is not AviSynth."""
        assert "avs" not in scan_prohibited.CAPABILITY_ALIASES["avisynth"]


class TestFetchAllowList:
    def test_the_forbidden_binaries_are_named(self) -> None:
        assert {"ffmpeg.exe", "ffplay.exe", "libcurl.dll"} <= fetch_binaries.NEVER_INSTALL

    def test_a_component_with_no_digest_refuses_to_download(self) -> None:
        with pytest.raises(fetch_binaries.FetchError, match="no verifiable digest"):
            fetch_binaries.expectation_for({"name": "example"})

    def test_a_publisher_checksum_outranks_an_origin_hash(self) -> None:
        expectation = fetch_binaries.expectation_for(
            {"name": "x", "published_sha256": "a" * 64, "origin_verified_sha256": "b" * 64}
        )
        assert expectation.digest == "a" * 64
        assert expectation.is_publisher_digest

    def test_an_origin_hash_is_used_but_labelled_weaker(self) -> None:
        expectation = fetch_binaries.expectation_for(
            {"name": "x", "published_sha256": "NOT PUBLISHED BY VENDOR", "origin_verified_sha256": "b" * 64}
        )
        assert expectation.digest == "b" * 64
        assert not expectation.is_publisher_digest

    def test_a_non_https_url_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(fetch_binaries.FetchError, match="non-HTTPS"):
            fetch_binaries.download("http://example.invalid/x.zip", tmp_path / "x.zip")


class TestEulaCarveOuts:
    """Gate G-8. Each clause is here because FFmpeg's checklist demands it."""

    @pytest.fixture(scope="class")
    def text(self) -> str:
        """Whitespace-normalised, because a clause's meaning does not depend on where the
        line wraps. Asserting on the wrapped form would make every reflow a test failure,
        which teaches people to edit the test instead of reading the clause."""
        return " ".join(EULA.read_text(encoding="utf-8").split())

    def test_it_names_ffmpeg_and_the_lgpl_version(self, text: str) -> None:
        assert "FFmpeg" in text
        assert "Lesser General Public License version 3" in text

    def test_it_disclaims_ownership_of_ffmpeg(self, text: str) -> None:
        assert "does not own FFmpeg" in text

    def test_it_grants_rather_than_merely_omits_reverse_engineering(self, text: str) -> None:
        assert "You may reverse engineer" in text
        assert "does not prohibit reverse engineering" in text

    def test_open_source_licences_take_precedence(self, text: str) -> None:
        assert "OPEN SOURCE LICENCE PREVAILS" in text

    def test_the_translation_obligation_is_recorded(self, text: str) -> None:
        assert "translated" in text
        assert "every translation" in text

    def test_it_offers_corresponding_source_for_three_years(self, text: str) -> None:
        assert "three years" in text

    def test_it_does_not_claim_legal_clearance(self, text: str) -> None:
        assert "NOT LEGAL ADVICE" in text
        assert "has not been reviewed" in text


class TestInstallerScript:
    @pytest.fixture(scope="class")
    def text(self) -> str:
        return INSTALLER_ISS.read_text(encoding="utf-8")

    def test_it_installs_per_user_without_elevation(self, text: str) -> None:
        assert "PrivilegesRequired=lowest" in text

    def test_it_ships_the_licence_folder_and_shows_the_eula(self, text: str) -> None:
        assert "LicenseFile=" in text
        assert "EULA.txt" in text

    def test_it_does_not_delete_user_profiles_on_uninstall(self, text: str) -> None:
        """P13-A12: a profile is the user's own work, not ours to remove."""
        body = text.split("[UninstallDelete]", 1)[1]
        assert not [
            line for line in body.splitlines() if line.strip().startswith(("Type:", "Name:"))
        ]


class TestPresetStaleness:
    """Register rule 6, mechanised. Reports age, never guesses correctness."""

    @pytest.fixture(scope="class")
    def today(self) -> object:
        import staleness_report

        return staleness_report.analyse(
            REPO_ROOT / "presets", as_of=_date(2026, 8, 9), max_age_days=183
        )

    def test_every_shipped_rule_is_currently_fresh(self, today: object) -> None:
        assert today.stale == []  # type: ignore[attr-defined]

    def test_every_rule_traces_to_a_declared_source(self, today: object) -> None:
        """S-2: a rule value with no register row must not exist."""
        assert today.integrity_problems == []  # type: ignore[attr-defined]

    def test_all_twelve_presets_and_every_rule_are_examined(self, today: object) -> None:
        assert today.total_presets == 12  # type: ignore[attr-defined]
        assert today.total_rules == 170  # type: ignore[attr-defined]

    def test_the_check_actually_fires_once_the_sources_age(self) -> None:
        """A staleness check that has never gone red is not evidence of anything."""
        import staleness_report

        future = staleness_report.analyse(
            REPO_ROOT / "presets", as_of=_date(2027, 3, 1), max_age_days=183
        )
        assert len(future.stale) == future.total_rules

    def test_the_older_of_rule_and_source_date_governs(self, tmp_path: Path) -> None:
        """Re-dating a rule without re-reading its source must not look fresh."""
        import staleness_report

        (tmp_path / "p.json").write_text(
            json.dumps(
                {
                    "preset_id": "example",
                    "sources": [{"source_ref": "S1", "access_date": "2025-01-01"}],
                    "rules": [
                        {
                            "rule_id": "example.rule",
                            "source_ref": "S1",
                            "last_verified_date": "2026-08-09",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        report = staleness_report.analyse(tmp_path, as_of=_date(2026, 8, 9), max_age_days=183)
        assert len(report.stale) == 1
        assert report.stale[0].verified == _date(2025, 1, 1)


@pytest.mark.skipif(not PACKAGE.is_dir(), reason="no built package; run packaging/build.py")
class TestTheBuiltPackage:
    """Assertions about the artefact that would actually ship."""

    def test_no_encoder_is_shipped(self) -> None:
        assert not list(PACKAGE.rglob("ffmpeg.exe"))
        assert not list(PACKAGE.rglob("ffplay.exe"))

    def test_no_libcurl_is_shipped(self) -> None:
        assert not [p for p in PACKAGE.rglob("*") if p.name.lower() == "libcurl.dll"]

    def test_the_libav_libraries_ship_as_separate_named_files(self) -> None:
        """G-7 and G-13: identifiable and replaceable, not merged or renamed."""
        names = {p.name for p in (PACKAGE / "bin").glob("*.dll")}
        assert {"avcodec-62.dll", "avformat-62.dll", "avutil-60.dll"} <= names

    def test_the_qt_libraries_ship_as_separate_named_files(self) -> None:
        names = {p.name for p in (PACKAGE / "_internal" / "PySide6").glob("Qt6*.dll")}
        assert {"Qt6Core.dll", "Qt6Gui.dll", "Qt6Widgets.dll"} <= names

    def test_no_network_capable_library_is_shipped(self) -> None:
        """Spec §18 and AC-12 claim the product cannot make a network request.

        libcrypto is the one deliberate exception: CPython's hashlib links it for
        message digests. It provides no socket and no TLS transport — libssl, _ssl and
        _socket are all excluded from the freeze.
        """
        offenders = sorted(
            p.name
            for p in PACKAGE.rglob("*")
            if p.is_file()
            and re.search(r"(network|libssl|_ssl|_socket|curl)", p.name, re.IGNORECASE)
        )
        assert offenders == []

    def test_the_layout_matches_the_adr(self) -> None:
        assert layout_check.check(PACKAGE) == []

    def test_the_prohibited_component_scan_is_clean(self) -> None:
        violations = scan_prohibited.scan(PACKAGE)
        assert violations == [], "\n".join(str(v) for v in violations)

    def test_every_shipped_file_is_attributed_to_a_component(self) -> None:
        manifest = generate_manifest.build_manifest(PACKAGE, "test")
        assert manifest.unaccounted_files == []

    def test_the_manifest_records_a_verifiable_checksum_for_each_binary(self) -> None:
        manifest = generate_manifest.build_manifest(PACKAGE, "test")
        for name in ("ffprobe", "mediainfo"):
            component = next(c for c in manifest.components if c.name == name)
            assert component.verified
            assert re.match(r"^[0-9a-f]{64} \(", component.published_checksum)

    def test_the_dependency_closure_has_no_uncovered_distribution(self) -> None:
        assert generate_manifest.verify_closure() == []

    def test_every_referenced_licence_text_is_present(self) -> None:
        manifest = generate_manifest.build_manifest(PACKAGE, "test")
        licences = PACKAGE / "licenses"
        for component in manifest.components:
            if component.licence_text_path:
                assert (licences / component.licence_text_path).is_file(), component.name

    def test_the_notices_name_the_actual_licence_version(self) -> None:
        notices = (PACKAGE / "licenses" / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
        assert "LGPLv3" in notices
        assert "under the LGPLv2.1" not in notices

    def test_the_notices_carry_the_written_offer_of_source(self) -> None:
        notices = (PACKAGE / "licenses" / "THIRD-PARTY-NOTICES.txt").read_text(encoding="utf-8")
        assert "WRITTEN OFFER" in notices
        assert "three years" in notices

    def test_the_configure_line_ships_verbatim(self) -> None:
        text = (PACKAGE / "licenses" / "ffmpeg-build-configuration.txt").read_text(encoding="utf-8")
        assert "--enable-version3" in text
        assert "--disable-libx264" in text
        assert "--enable-gpl" not in text

    def test_the_gpl_text_ships_because_lgplv3_incorporates_it(self) -> None:
        gpl = (PACKAGE / "licenses" / "GPL-3.0.txt").read_text(encoding="utf-8")
        assert "GNU GENERAL PUBLIC LICENSE" in gpl
        lgpl = (PACKAGE / "licenses" / "LGPL-3.0.txt").read_text(encoding="utf-8")
        assert "incorporates\nthe terms and conditions of version 3 of the GNU General Public" in lgpl

    def test_it_is_a_one_dir_build(self) -> None:
        """One-file would extract to a temp dir and defeat library replaceability."""
        assert (PACKAGE / "_internal").is_dir()
        assert (PACKAGE / "PreflightQC.exe").is_file()

    def test_the_packaged_app_ignores_an_ffprobe_planted_on_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Spec AC-17 and criterion P13-A5, run against the artefact that ships.

        A PATH fallback would let PreflightQC silently run an unknown build — possibly a
        GPL one, possibly a different version producing different metadata — and report
        the results as though they came from the build we tested and licensed. So the
        decoy is placed *first* on PATH and the packaged binary must still not take it.
        """
        import subprocess

        decoy = tmp_path / "decoy"
        decoy.mkdir()
        for name in ("ffprobe.exe", "mediainfo.exe"):
            shutil_copy = (PACKAGE / "bin" / "MediaInfo.exe").read_bytes()
            (decoy / name).write_bytes(shutil_copy)

        monkeypatch.setenv("PATH", f"{decoy}{';'}{__import__('os').environ['PATH']}")
        result = subprocess.run(  # noqa: S603 - absolute path, argv list, no shell
            [str(PACKAGE / "PreflightQC.exe"), "--self-check"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert str(PACKAGE / "bin" / "ffprobe.exe") in result.stdout
        assert str(decoy) not in result.stdout
        # The decoy is a MediaInfo binary; if it had been used, no FFmpeg version string
        # could appear here.
        assert "n8.1.2-34-g9b6c8969e0" in result.stdout
