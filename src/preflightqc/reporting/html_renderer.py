"""HTML report rendering.

Autoescaping is on: a filename is attacker-influenced text, and a report is a document
users email to clients. An unescaped `<` in a filename would at best break the layout.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from preflightqc.reporting.model import ReportModel

TEMPLATE_DIR = Path(__file__).parent / "templates"
TEMPLATE_NAME = "report.html.j2"

#: Anything that would make a rendered report reach the network when opened.
_EXTERNAL_REFERENCE = re.compile(
    r"""(?:src|href)\s*=\s*["']\s*(?:https?:|//|ftp:)""", re.IGNORECASE
)


@lru_cache(maxsize=1)
def _environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(default=True, default_for_string=True),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render(report: ReportModel) -> str:
    """Render the self-contained HTML report."""
    template = _environment().get_template(TEMPLATE_NAME)
    return template.render(report=report)


def find_external_references(html: str) -> tuple[str, ...]:
    """Any src/href that would fetch from the network. Empty means self-contained.

    Source URLs are printed as *text* in the report so a reader can verify a rule, but
    they are never link targets — a report must not be able to phone anywhere when it
    is opened.
    """
    return tuple(match.group(0) for match in _EXTERNAL_REFERENCE.finditer(html))
