"""The freeze's exclusion policy — one list, imported by the spec AND by the tests.

This file exists because of the Phase 13 clean-machine failure (2026-08-12): release
candidate ``d9e6f907…aadf05f`` installed cleanly on a fresh Windows 11 VM and then died
on first launch with ``No module named 'urllib.request'``. The spec had excluded
``urllib.request`` (and its closure) to make the no-network claim structural, but
``jsonschema`` 4.23.0 imports ``urllib.request`` at module scope
(``jsonschema/validators.py`` line 12, ``from urllib.request import urlopen``), so the
GUI launch path — app → main_window → profiles.compiler → rules.loader → jsonschema —
could not even be imported. The build's ``--self-check`` gate passed because it never
imported the GUI closure. Two lessons, both enforced mechanically now:

1. The exclusion list must be testable against the real launch import closure on every
   dev machine, not discovered on a customer's. ``tests/packaging/
   test_frozen_import_closure.py`` imports this list, blocks every excluded module in a
   fresh interpreter, and imports the full launch closure.
2. The self-check must exercise the same import closure the launch uses
   (``preflightqc.ui.app._self_check``).

**The minimum stdlib closure that MUST ship, and why it is safe.**

``jsonschema``'s module-scope ``from urllib.request import urlopen`` exists to serve the
deprecated ``RefResolver``'s remote-``$ref`` path. PreflightQC never resolves a remote
reference — every schema and preset is a local file — but the *import* is unconditional,
so the module must be present. ``urllib.request`` in turn imports, unconditionally and at
module scope: ``http.client`` (which needs ``email.parser``/``email.message``) and
``socket`` (which needs ``_socket`` and ``selectors``). That is the whole forced closure:

    urllib.request → http.client → email
                   → socket      → _socket, selectors

What it does NOT force is a TLS stack: both ``urllib.request`` and ``http.client`` wrap
``import ssl`` in ``try/except ImportError`` and degrade cleanly. Verified empirically
(Python 3.12.10, jsonschema 4.23.0): with ``ssl``, ``_ssl``, ``ftplib``, ``smtplib``,
``socketserver`` and ``xmlrpc`` all absent, ``import jsonschema`` succeeds
(``urllib.request._have_ssl`` is False) and full schema validation works.

So the honest posture, post-fix: the package ships CPython's socket *module* because the
schema-validation library's import graph demands it, but ships **no TLS stack** (no
``ssl``/``_ssl``/``libssl``), **no Qt network layer** (Qt6Network is pruned by
``build.py``), **no libcurl**, and no application code that opens a connection (enforced
by the AST scan in ``test_nothing_in_the_product_fetches_a_url``). AC-12 — a full QC
cycle with outbound traffic blocked — is unaffected. The previous, stronger wording
("no socket implementation at all") was retired from the customer-facing documents when
this file was introduced; see docs/reports/CLEAN-MACHINE-VALIDATION-V1.md.
"""

from __future__ import annotations

#: Qt bindings the product does not use. QtNetwork above all: the product must be
#: provably incapable of a network request (spec §18), and the cleanest way to make that
#: true is to not ship the module that could make one. (The native Qt6*.dll files are
#: additionally pruned by packaging/build.py — see PRUNED_QT_LIBRARIES there.)
QT_EXCLUDES: tuple[str, ...] = (
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
)

#: Stdlib modules the application does not use and the freeze must not carry.
#:
#: The network-facing entries are the deliberate ones: no TLS (``ssl``/``_ssl``), and no
#: protocol *services* (``ftplib``, ``smtplib``, ``socketserver``, ``xmlrpc``) — all of
#: which ``urllib.request`` and ``http.client`` tolerate being absent (the first two by
#: ``try/except``, the rest by importing lazily or not at all on our paths).
#:
#: NOT in this list, deliberately — the closure jsonschema forces (see module docstring):
#: ``urllib.request``, ``http``, ``email``, ``socket``, ``_socket``. Re-adding any of
#: them will fail tests/packaging/test_frozen_import_closure.py on every machine, which
#: is exactly the point.
STDLIB_EXCLUDES: tuple[str, ...] = (
    "tkinter",
    "unittest",
    "pydoc",
    "xmlrpc",
    "ftplib",
    "smtplib",
    "socketserver",
    "ssl",
    "_ssl",
    "asyncio",
    "multiprocessing",
    "webbrowser",
)

#: What the PyInstaller Analysis consumes.
EXCLUDES: list[str] = [*QT_EXCLUDES, *STDLIB_EXCLUDES]

#: The stdlib modules that MUST be importable in the frozen package because the launch
#: closure needs them (see module docstring). The built-package test asserts their
#: compiled extension / package presence; the closure test proves they are sufficient.
REQUIRED_STDLIB_CLOSURE: tuple[str, ...] = (
    "urllib.request",
    "http.client",
    "email.parser",
    "socket",
    "selectors",
)
