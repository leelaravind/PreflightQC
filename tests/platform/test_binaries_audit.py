"""The ffprobe build-configuration audit (release gate G-4, runtime self-check).

The bug this file exists to prevent: a naive substring scan flags `--disable-libx264`
as a libx264 violation, so a *compliant* build reads as non-compliant. A scanner that
cries wolf on every good build teaches people to ignore it, which is worse than having
no scanner at all.

The fixture below is the verbatim configuration string of a real BtbN
`win64-lgpl-shared` build, so this is anchored to what the tool actually emits rather
than to what we imagine it emits.
"""

from __future__ import annotations

import pytest

from preflightqc.platform.binaries import (
    PROHIBITED_COMPONENTS,
    audit_configuration,
    licence_version,
)

#: Verbatim from ffprobe n8.1.2-34-g9b6c8969e0-20260809 (BtbN win64-lgpl-shared),
#: trimmed to the licence-relevant switches. It *disables* every GPL library and carries
#: --enable-version3, which is what makes it LGPL v3 rather than v2.1.
REAL_BTBN_LGPL_SHARED = (
    "--prefix=/ffbuild/prefix --arch=x86_64 --target-os=mingw32 --enable-version3 "
    "--disable-debug --enable-shared --disable-static --enable-gmp --enable-libaribb24 "
    "--disable-avisynth --disable-libdavs2 --disable-libfdk-aac --disable-frei0r "
    "--disable-librubberband --disable-libvidstab --disable-libx264 --disable-libx265 "
    "--disable-libxavs2 --disable-libxvid --enable-libzvbi --enable-libaom "
    "--enable-libdav1d --enable-libopus --enable-libvpx"
)

#: A hypothetical fully-conforming build: no version3, no prohibited component enabled.
CONFORMING = (
    "--arch=x86_64 --target-os=mingw32 --enable-shared --disable-static "
    "--disable-libx264 --disable-libx265 --disable-libxvid --disable-libfdk-aac "
    "--disable-frei0r --disable-libvidstab --disable-avisynth --disable-libzvbi "
    "--enable-libdav1d --enable-libopus --enable-zlib"
)


class TestDisabledComponentsAreNotViolations:
    """The regression that motivated this module."""

    @pytest.mark.parametrize(
        "component",
        ["libx264", "libx265", "libxvid", "libfdk-aac", "frei0r", "libvidstab", "avisynth"],
    )
    def test_a_disabled_prohibited_component_is_not_flagged(self, component: str) -> None:
        violations = audit_configuration(f"--enable-shared --disable-{component}")
        assert violations == (), f"--disable-{component} was wrongly flagged"

    def test_a_fully_conforming_build_produces_no_violations(self) -> None:
        assert audit_configuration(CONFORMING) == ()


class TestEnabledComponentsAreViolations:
    @pytest.mark.parametrize(
        "component", ["libx264", "libx265", "libxvid", "frei0r", "libvidstab", "libsmbclient"]
    )
    def test_an_enabled_prohibited_component_is_flagged(self, component: str) -> None:
        violations = audit_configuration(f"--enable-shared --enable-{component}")
        assert f"--enable-{component}" in violations

    def test_hyphen_and_underscore_spellings_both_match(self) -> None:
        """configure uses `--enable-libfdk-aac`; the internal list says `libfdk_aac`."""
        assert audit_configuration("--enable-libfdk-aac") == ("--enable-libfdk_aac",)


class TestProhibitedSwitches:
    def test_enable_gpl_is_flagged(self) -> None:
        assert "--enable-gpl" in audit_configuration("--enable-gpl --enable-shared")

    def test_enable_nonfree_is_flagged(self) -> None:
        assert "--enable-nonfree" in audit_configuration("--enable-nonfree")


class TestLicenceVersionDetection:
    """`--enable-version3` is permitted; it selects which notices we must ship."""

    def test_version3_is_not_a_violation(self) -> None:
        assert audit_configuration("--enable-version3 --enable-shared") == ()

    def test_version3_reports_lgplv3(self) -> None:
        assert licence_version("--enable-version3 --enable-shared") == "LGPL-3.0-or-later"

    def test_absence_of_version3_reports_lgpl21(self) -> None:
        assert licence_version("--enable-shared --disable-static") == "LGPL-2.1-or-later"

    @pytest.mark.parametrize("component", ["gmp", "libaribb24", "liblensfun"])
    def test_lgplv3_libraries_are_permitted(self, component: str) -> None:
        """FFmpeg's LICENSE.md lists these under 'LGPL version 3', enabled via version3.

        They upgrade the licence; they do not make it copyleft.
        """
        assert audit_configuration(f"--enable-version3 --enable-{component}") == ()

    def test_libzvbi_without_enable_gpl_is_permitted(self) -> None:
        """FFmpeg's configure only demands --enable-gpl for libzvbi below 0.2.28.

        A build that enables libzvbi *without* --enable-gpl has, by FFmpeg's own
        check, linked the LGPL-2.1+ version.
        """
        assert audit_configuration("--enable-libzvbi --enable-shared") == ()

    def test_libzvbi_alongside_enable_gpl_still_fails(self) -> None:
        """--enable-gpl remains disqualifying whatever prompted it."""
        assert "--enable-gpl" in audit_configuration("--enable-gpl --enable-libzvbi")


class TestAgainstTheRealBuild:
    """Anchored to the configuration string a real BtbN build actually emits."""

    def test_the_real_build_has_no_violations(self) -> None:
        """Post-amendment: this build is acceptable, under LGPL v3."""
        assert audit_configuration(REAL_BTBN_LGPL_SHARED) == ()

    def test_the_real_build_is_identified_as_lgplv3(self) -> None:
        assert licence_version(REAL_BTBN_LGPL_SHARED) == "LGPL-3.0-or-later"

    def test_the_real_build_is_not_gpl_or_nonfree(self) -> None:
        """The two switches that would be outright disqualifying are absent."""
        violations = audit_configuration(REAL_BTBN_LGPL_SHARED)
        assert "--enable-gpl" not in violations
        assert "--enable-nonfree" not in violations

    def test_no_disabled_gpl_library_is_reported(self) -> None:
        """The whole point: eleven GPL libraries are disabled and none is flagged."""
        violations = audit_configuration(REAL_BTBN_LGPL_SHARED)
        for disabled in ("libx264", "libx265", "libxvid", "frei0r", "libvidstab", "avisynth"):
            assert not any(disabled in v for v in violations)


def test_the_prohibited_list_covers_the_licensing_gate() -> None:
    """Every component named in the gate document must be in the scanner's list."""
    required = {
        "libx264", "libx265", "libxvid", "libxavs", "libxavs2", "libdavs2", "frei0r",
        "libcdio", "librubberband", "libvidstab", "avisynth", "libsmbclient",
        "libfdk_aac", "libnpp", "cuda_nvcc",
    }
    assert required <= set(PROHIBITED_COMPONENTS)


def test_lgplv3_libraries_are_deliberately_not_prohibited() -> None:
    """The LGPLv3 spec-lock amendment: these are permitted via --enable-version3."""
    for permitted in ("gmp", "libaribb24", "liblensfun", "libzvbi"):
        assert permitted not in PROHIBITED_COMPONENTS
