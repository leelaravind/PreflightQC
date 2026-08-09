"""Turns design tokens into a Qt palette and one application style sheet.

Two mechanisms, because Qt needs both. The `QPalette` covers what Qt draws natively —
native dialogs, tooltips, text-cursor and selection colours inside `QTextBrowser`. The
style sheet covers the widgets we lay out ourselves. Setting only one of them produces an
application that is dark until the first message box.

Every value comes from `design.py`. There is no hex literal in this file, and a test says
there must not be one anywhere else in the UI package either.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

from preflightqc.ui import design as d


def _q(colour: str) -> QColor:
    return QColor(colour)


def build_palette() -> QPalette:
    """The palette Qt uses where the style sheet does not reach."""
    palette = QPalette()
    roles = (
        (QPalette.ColorRole.Window, d.SURFACE_SUNKEN),
        (QPalette.ColorRole.WindowText, d.TEXT_PRIMARY),
        (QPalette.ColorRole.Base, d.SURFACE_BASE),
        (QPalette.ColorRole.AlternateBase, d.SURFACE_RAISED),
        (QPalette.ColorRole.Text, d.TEXT_PRIMARY),
        (QPalette.ColorRole.Button, d.SURFACE_RAISED),
        (QPalette.ColorRole.ButtonText, d.TEXT_PRIMARY),
        (QPalette.ColorRole.BrightText, d.FAIL_TONE.foreground),
        (QPalette.ColorRole.Highlight, d.ACCENT),
        (QPalette.ColorRole.HighlightedText, d.TEXT_ON_ACCENT),
        (QPalette.ColorRole.ToolTipBase, d.SURFACE_OVERLAY),
        (QPalette.ColorRole.ToolTipText, d.TEXT_PRIMARY),
        (QPalette.ColorRole.PlaceholderText, d.TEXT_MUTED),
        (QPalette.ColorRole.Link, d.ACCENT),
        (QPalette.ColorRole.LinkVisited, d.ACCENT_PRESSED),
    )
    for role, colour in roles:
        palette.setColor(role, _q(colour))

    # Disabled controls must read as inert, never as invisible.
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, _q(d.TEXT_MUTED))
    return palette


def base_font() -> QFont:
    font = QFont()
    # The stack in design.py is a CSS-style list; QFont takes families in preference
    # order, which is the same idea expressed differently.
    font.setFamilies([name.strip().strip('"') for name in d.FONT_UI.split(",")])
    font.setPointSizeF(d.TYPE_BODY)
    return font


def mono_font(point_size: float | None = None) -> QFont:
    font = QFont()
    font.setFamilies([name.strip().strip('"') for name in d.FONT_MONO.split(",")])
    font.setPointSizeF(point_size if point_size is not None else d.TYPE_BODY)
    font.setStyleHint(QFont.StyleHint.Monospace)
    return font


def style_sheet() -> str:
    """The single application style sheet, composed from tokens."""
    return f"""
/* ---- foundations ------------------------------------------------------ */
/*
 * Colour and type are inherited by every widget; backgrounds are NOT set here.
 * A universal `QWidget {{ background-color: ... }}` makes every QLabel opaque, so
 * text inside a panel paints a rectangle of the *window* colour on top of the
 * panel. Backgrounds belong to the widgets that are actually surfaces.
 */
QWidget {{
    color: {d.TEXT_PRIMARY};
    font-family: {d.FONT_UI};
    font-size: {d.TYPE_BODY}pt;
}}
QLabel {{ background: transparent; }}
QMainWindow, QDialog {{ background-color: {d.SURFACE_SUNKEN}; }}
QMainWindow > QWidget {{ background-color: {d.SURFACE_SUNKEN}; }}
QToolTip {{
    background-color: {d.SURFACE_OVERLAY};
    color: {d.TEXT_PRIMARY};
    border: 1px solid {d.BORDER_STRONG};
    border-radius: {d.RADIUS_CONTROL}px;
    padding: {d.SPACE_XS}px {d.SPACE_SM}px;
}}

/* ---- menu bar --------------------------------------------------------- */
QMenuBar {{
    background-color: {d.SURFACE_SUNKEN};
    border-bottom: 1px solid {d.BORDER_SUBTLE};
    padding: {d.SPACE_XXS}px {d.SPACE_XS}px;
}}
QMenuBar::item {{
    padding: {d.SPACE_XS}px {d.SPACE_MD}px;
    border-radius: {d.RADIUS_CONTROL}px;
    background: transparent;
}}
QMenuBar::item:selected {{ background-color: {d.SURFACE_OVERLAY}; }}
QMenu {{
    background-color: {d.SURFACE_OVERLAY};
    border: 1px solid {d.BORDER_STRONG};
    border-radius: {d.RADIUS_PANEL}px;
    padding: {d.SPACE_XS}px;
}}
QMenu::item {{ padding: {d.SPACE_SM}px {d.SPACE_LG}px; border-radius: {d.RADIUS_CHIP}px; }}
QMenu::item:selected {{ background-color: {d.ACCENT_SUBTLE}; }}

/* ---- panels ----------------------------------------------------------- */
QFrame#Panel, QFrame#Toolbar, QFrame#ContextStrip, QFrame#Readout {{
    background-color: {d.SURFACE_RAISED};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_PANEL}px;
}}
QFrame#EmptyState {{
    background-color: {d.SURFACE_BASE};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_PANEL}px;
}}
QLabel#SectionHeading {{
    color: {d.TEXT_SECONDARY};
    font-size: {d.TYPE_LABEL}pt;
    font-weight: {d.WEIGHT_SEMIBOLD};
    letter-spacing: 0.6px;
}}
QLabel#EmptyTitle {{
    color: {d.TEXT_PRIMARY};
    font-size: {d.TYPE_TITLE}pt;
    font-weight: {d.WEIGHT_SEMIBOLD};
}}
QLabel#EmptyBody {{ color: {d.TEXT_SECONDARY}; }}
QLabel#EmptyStep {{ color: {d.TEXT_SECONDARY}; }}
QLabel#EmptyStepNumber {{
    color: {d.ACCENT};
    font-family: {d.FONT_MONO};
    font-weight: {d.WEIGHT_SEMIBOLD};
}}
QLabel#PrivacyNote {{ color: {d.TEXT_MUTED}; font-size: {d.TYPE_CAPTION}pt; }}
QLabel#ContextPrimary {{ color: {d.TEXT_PRIMARY}; font-weight: {d.WEIGHT_SEMIBOLD}; }}
QLabel#ContextDetail {{
    color: {d.TEXT_MUTED};
    font-family: {d.FONT_MONO};
    font-size: {d.TYPE_CAPTION}pt;
}}
QLabel#FieldLabel {{
    color: {d.TEXT_SECONDARY};
    font-size: {d.TYPE_LABEL}pt;
    font-weight: {d.WEIGHT_MEDIUM};
}}
QLabel#Wordmark {{
    color: {d.TEXT_PRIMARY};
    font-size: {d.TYPE_HEADING}pt;
    font-weight: {d.WEIGHT_SEMIBOLD};
    letter-spacing: 0.3px;
}}
QLabel#Publisher {{ color: {d.TEXT_MUTED}; font-size: {d.TYPE_CAPTION}pt; }}

/* ---- buttons ---------------------------------------------------------- */
QPushButton {{
    background-color: {d.SURFACE_RAISED};
    color: {d.TEXT_PRIMARY};
    border: 1px solid {d.BORDER_STRONG};
    border-radius: {d.RADIUS_CONTROL}px;
    padding: 0 {d.SPACE_LG}px;
    min-height: {d.CONTROL_HEIGHT}px;
}}
QPushButton:hover {{ background-color: {d.SURFACE_OVERLAY}; }}
QPushButton:pressed {{ background-color: {d.SURFACE_SUNKEN}; }}
QPushButton:disabled {{ color: {d.TEXT_MUTED}; border-color: {d.BORDER_SUBTLE}; }}
QPushButton:focus {{
    border-color: {d.ACCENT};
    outline: {d.FOCUS_RING_WIDTH}px solid {d.ACCENT};
    outline-offset: 1px;
}}
QPushButton#PrimaryAction {{
    background-color: {d.ACCENT};
    color: {d.TEXT_ON_ACCENT};
    border: 1px solid {d.ACCENT};
    font-weight: {d.WEIGHT_SEMIBOLD};
    min-height: {d.PRIMARY_HEIGHT}px;
    padding: 0 {d.SPACE_XL}px;
}}
QPushButton#PrimaryAction:hover {{
    background-color: {d.ACCENT_HOVER}; border-color: {d.ACCENT_HOVER};
}}
QPushButton#PrimaryAction:pressed {{
    background-color: {d.ACCENT_PRESSED}; border-color: {d.ACCENT_PRESSED};
}}
QPushButton#PrimaryAction:disabled {{
    background-color: {d.SURFACE_RAISED};
    color: {d.TEXT_MUTED};
    border-color: {d.BORDER_SUBTLE};
}}
QPushButton#FilterChip {{
    background-color: transparent;
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_CHIP}px;
    color: {d.TEXT_SECONDARY};
    font-size: {d.TYPE_LABEL}pt;
    padding: 0 {d.SPACE_MD}px;
    min-height: 22px;
}}
QPushButton#FilterChip:hover {{ background-color: {d.SURFACE_OVERLAY}; }}
QPushButton#FilterChip:checked {{
    background-color: {d.ACCENT_SUBTLE};
    border-color: {d.ACCENT};
    color: {d.TEXT_PRIMARY};
}}
QPushButton#FilterChip:disabled {{ color: {d.TEXT_MUTED}; border-color: {d.BORDER_SUBTLE}; }}

/* ---- inputs ----------------------------------------------------------- */
QComboBox {{
    background-color: {d.SURFACE_BASE};
    color: {d.TEXT_PRIMARY};
    border: 1px solid {d.BORDER_STRONG};
    border-radius: {d.RADIUS_CONTROL}px;
    padding: 0 {d.SPACE_MD}px;
    min-height: {d.CONTROL_HEIGHT}px;
}}
QComboBox:hover {{ border-color: {d.BORDER_STRONG}; background-color: {d.SURFACE_OVERLAY}; }}
QComboBox:focus {{ border-color: {d.ACCENT}; outline: {d.FOCUS_RING_WIDTH}px solid {d.ACCENT}; }}
QComboBox:disabled {{ color: {d.TEXT_MUTED}; border-color: {d.BORDER_SUBTLE}; }}
QComboBox::drop-down {{ border: none; width: {d.SPACE_2XL}px; }}
QComboBox QAbstractItemView {{
    background-color: {d.SURFACE_OVERLAY};
    border: 1px solid {d.BORDER_STRONG};
    selection-background-color: {d.ACCENT_SUBTLE};
    selection-color: {d.TEXT_PRIMARY};
    outline: none;
    padding: {d.SPACE_XS}px;
}}

/* ---- tables ----------------------------------------------------------- */
QTableWidget, QTableView {{
    background-color: {d.SURFACE_BASE};
    alternate-background-color: {d.SURFACE_RAISED};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_PANEL}px;
    gridline-color: {d.BORDER_SUBTLE};
    selection-background-color: {d.ACCENT_SUBTLE};
    selection-color: {d.TEXT_PRIMARY};
    outline: none;
}}
QTableWidget::item, QTableView::item {{
    padding: {d.SPACE_XS}px {d.SPACE_MD}px;
    border: none;
}}
QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {d.ACCENT_SUBTLE};
    color: {d.TEXT_PRIMARY};
}}
QTableWidget:focus, QTableView:focus {{ border-color: {d.ACCENT}; }}
QHeaderView::section {{
    background-color: {d.SURFACE_RAISED};
    color: {d.TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {d.BORDER_STRONG};
    padding: {d.SPACE_SM}px {d.SPACE_MD}px;
    font-size: {d.TYPE_LABEL}pt;
    font-weight: {d.WEIGHT_SEMIBOLD};
}}

/* ---- text views ------------------------------------------------------- */
QTextBrowser {{
    background-color: {d.SURFACE_BASE};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_PANEL}px;
    padding: {d.SPACE_MD}px;
    selection-background-color: {d.ACCENT_SUBTLE};
    selection-color: {d.TEXT_PRIMARY};
}}
QTextBrowser:focus {{ border-color: {d.ACCENT}; }}

/* ---- tabs ------------------------------------------------------------- */
QTabWidget::pane {{
    background-color: {d.SURFACE_BASE};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_PANEL}px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {d.TEXT_SECONDARY};
    padding: {d.SPACE_SM}px {d.SPACE_LG}px;
    margin-right: {d.SPACE_XXS}px;
    border: 1px solid transparent;
    border-top-left-radius: {d.RADIUS_CONTROL}px;
    border-top-right-radius: {d.RADIUS_CONTROL}px;
}}
QTabBar::tab:hover {{ color: {d.TEXT_PRIMARY}; background-color: {d.SURFACE_OVERLAY}; }}
QTabBar::tab:selected {{
    color: {d.TEXT_PRIMARY};
    background-color: {d.SURFACE_BASE};
    border-color: {d.BORDER_SUBTLE};
    border-bottom-color: {d.SURFACE_BASE};
}}
QTabBar::tab:focus {{ border-color: {d.ACCENT}; }}

/* ---- progress and readout -------------------------------------------- */
QProgressBar {{
    background-color: {d.SURFACE_BASE};
    border: 1px solid {d.BORDER_SUBTLE};
    border-radius: {d.RADIUS_CHIP}px;
    text-align: center;
    color: {d.TEXT_SECONDARY};
    font-size: {d.TYPE_LABEL}pt;
    min-height: 18px;
    max-height: 18px;
}}
QProgressBar::chunk {{ background-color: {d.ACCENT}; border-radius: 1px; }}

/* ---- splitter and scrollbars ----------------------------------------- */
QSplitter::handle {{ background-color: transparent; }}
QSplitter::handle:horizontal {{ width: {d.SPACE_MD}px; }}
QSplitter::handle:hover {{ background-color: {d.BORDER_SUBTLE}; }}

QScrollBar:vertical {{
    background: transparent; width: {d.SPACE_2XL}px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {d.BORDER_STRONG};
    border-radius: {d.RADIUS_CONTROL}px;
    min-height: {d.SPACE_2XL}px;
    margin: {d.SPACE_XS}px;
}}
QScrollBar::handle:vertical:hover {{ background: {d.TEXT_MUTED}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QScrollBar:horizontal {{ background: transparent; height: {d.SPACE_2XL}px; margin: 0; }}
QScrollBar::handle:horizontal {{
    background: {d.BORDER_STRONG};
    border-radius: {d.RADIUS_CONTROL}px;
    min-width: {d.SPACE_2XL}px;
    margin: {d.SPACE_XS}px;
}}
QScrollBar::handle:horizontal:hover {{ background: {d.TEXT_MUTED}; }}

/* ---- status bar ------------------------------------------------------- */
QStatusBar {{
    background-color: {d.SURFACE_SUNKEN};
    color: {d.TEXT_SECONDARY};
    border-top: 1px solid {d.BORDER_SUBTLE};
}}
QStatusBar::item {{ border: none; }}

/* ---- dialogs ---------------------------------------------------------- */
QDialogButtonBox QPushButton {{ min-width: 88px; }}
QMessageBox {{ background-color: {d.SURFACE_BASE}; }}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the palette, base font and style sheet to the whole application."""
    # Fusion is the only Qt style that honours a palette consistently across Windows
    # versions; the native Windows style ignores several roles and would leave light
    # patches in a dark interface.
    app.setStyle("Fusion")
    app.setPalette(build_palette())
    app.setFont(base_font())
    app.setStyleSheet(style_sheet())
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)
