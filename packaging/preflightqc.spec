# PyInstaller specification for PreflightQC.
#
# ONE-DIRECTORY BUILD, NEVER ONE-FILE.
#
# This is a licensing requirement, not a preference. A one-file build extracts to a temp
# directory at runtime, which frustrates the LGPL shared-library-replacement posture that
# ADR-001 section 4.1 relies on: a user must be able to identify and substitute the Qt and
# libav* libraries. One-dir keeps them as separate, unobfuscated, replaceable files.
#
# Invoke through packaging/build.py, not directly: this spec freezes the application, but
# presets/, licenses/ and bin/ are staged afterwards (see below).
#
#   python packaging/build.py

from pathlib import Path

SPEC_DIR = Path(SPECPATH).resolve()
REPO_ROOT = SPEC_DIR.parent

block_cipher = None

# DELIBERATELY EMPTY.
#
# presets/, licenses/ and bin/ are staged by packaging/build.py into the package ROOT,
# not declared here. PyInstaller 6 places declared `datas` under `_internal/`, but
# ADR-001 section 5 requires them beside the executable — which is where
# platform.paths.application_root() resolves them, and where a licence folder has to be
# for "accompanying the distribution" to mean anything.
#
# Declaring them here as well would ship two copies of the licence folder: two things to
# keep in step, and an ambiguity about which one the dependency manifest describes.
#
# The one declared data file is the application icon: it is package-internal (loaded
# from inside preflightqc.ui at runtime), not a root-staged folder, so `_internal/` is
# exactly where it belongs. It is a resize of the Product Owner-approved logo — see
# assets/logo/PROVENANCE.md.
datas = [
    (
        str(REPO_ROOT / "src" / "preflightqc" / "ui" / "assets" / "preflightqc.png"),
        "preflightqc/ui/assets",
    ),
]

# Qt modules PreflightQC does not use are excluded deliberately. QtNetwork in particular:
# the product must be provably incapable of a network request (spec 18), and the cleanest
# way to make that true is to not ship the module that could make one.
excludes = [
    "PySide6.QtNetwork",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtMultimedia",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "tkinter",
    "unittest",
    "pydoc",
    "email",
    "http",
    "urllib.request",
    "xmlrpc",
    "ftplib",
    "smtplib",
    "socketserver",
    # Spec section 18 promises the product cannot make a network request, and AC-12
    # requires a full cycle to succeed with outbound traffic blocked. Excluding the Qt
    # binding was not enough on its own -- PyInstaller still collected Qt6Network.dll
    # (removed by packaging/build.py) and CPython's own socket and TLS extensions. With
    # these gone the package ships no socket implementation at all, which is a stronger
    # statement than "we do not call one".
    #
    # If a future dependency genuinely needs sockets, the honest fix is to reinstate
    # these and weaken the claim in the spec -- not to keep the claim and ship the
    # modules quietly.
    "ssl",
    "socket",
    "_socket",
    "_ssl",
    "asyncio",
    "multiprocessing",
    "webbrowser",
]

a = Analysis(
    [str(REPO_ROOT / "src" / "preflightqc" / "ui" / "app.py")],
    pathex=[str(REPO_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=["preflightqc.ui.main_window", "preflightqc.ui.about"],
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # one-dir: binaries stay outside the executable
    name="PreflightQC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # UPX would obfuscate shipped library names
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # The Product Owner-approved logo, as a multi-size Windows icon
    # (assets/logo/PROVENANCE.md). Regenerate with tools/generate_icons.py.
    icon=str(REPO_ROOT / "assets" / "logo" / "preflightqc.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                      # see above: names must stay identifiable
    upx_exclude=[],
    name="PreflightQC",
)
