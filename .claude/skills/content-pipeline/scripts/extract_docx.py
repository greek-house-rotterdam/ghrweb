#!/usr/bin/env python3
"""Extract markdown from a .docx file using python-docx.

Preserves heading hierarchy (Heading 1/2/3 → #/##/###), bullet/numbered lists,
and tables. Other paragraphs become plain prose.

Requires python-docx (in the project's [skills] optional-dependencies group).
Install with:
    uv sync --extra skills
Then run via:
    uv run python3 .claude/skills/content-pipeline/scripts/extract_docx.py <path>

If you can't or don't want to install python-docx, the previous stdlib-only
version of this script is recoverable from git history.

Usage:
    uv run python3 extract_docx.py <path-to-file.docx>

Outputs markdown to stdout. Errors go to stderr; exit code 1 on failure.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import docx  # python-docx
    from docx.document import Document as DocxDoc
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
except ImportError:
    print(
        "error: python-docx is not installed. Run:\n"
        "    uv sync --extra skills\n"
        "(or `uv pip install python-docx` if you're not using the project's venv).",
        file=sys.stderr,
    )
    sys.exit(1)


def _iter_block_items(parent: DocxDoc):
    """Yield paragraphs and tables in document order.

    python-docx exposes them as separate collections, but for a faithful
    rendering we need their original sequence.
    """
    body = parent.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)


_HEADING_RE = re.compile(r"^Heading\s+(\d+)$", re.IGNORECASE)


def _heading_level(style_name: str) -> int | None:
    if not style_name:
        return None
    m = _HEADING_RE.match(style_name.strip())
    if m:
        return min(int(m.group(1)), 6)
    if style_name.strip().lower() == "title":
        return 1
    return None


def _is_list_item(p: Paragraph) -> bool:
    style = (p.style.name if p.style else "") or ""
    if "list" in style.lower():
        return True
    # Direct numbering reference on the paragraph (w:numPr)
    pPr = p._p.find(qn("w:pPr"))
    if pPr is not None and pPr.find(qn("w:numPr")) is not None:
        return True
    return False


def _is_numbered(p: Paragraph) -> bool:
    style = (p.style.name if p.style else "") or ""
    return "number" in style.lower()


def _render_paragraph(p: Paragraph) -> str | None:
    text = (p.text or "").strip()
    if not text:
        return None

    level = _heading_level(p.style.name if p.style else "")
    if level:
        return f"{'#' * level} {text}"

    if _is_list_item(p):
        bullet = "1." if _is_numbered(p) else "-"
        return f"{bullet} {text}"

    return text


def _render_table(t: Table) -> str | None:
    rows: list[list[str]] = []
    for row in t.rows:
        rows.append([" ".join(cell.text.split()) for cell in row.cells])
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return None

    n_cols = max(len(r) for r in rows)
    rows = [r + [""] * (n_cols - len(r)) for r in rows]
    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * n_cols) + " |",
    ]
    for r in body:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def extract_markdown(docx_path: Path) -> str:
    doc = docx.Document(str(docx_path))
    blocks: list[str] = []
    for item in _iter_block_items(doc):
        if isinstance(item, Paragraph):
            rendered = _render_paragraph(item)
        elif isinstance(item, Table):
            rendered = _render_table(item)
        else:
            continue
        if rendered:
            blocks.append(rendered)
    return "\n\n".join(blocks)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: extract_docx.py <path-to-file.docx>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1
    if path.suffix.lower() != ".docx":
        print(f"error: expected .docx, got {path.suffix}", file=sys.stderr)
        return 1
    try:
        md = extract_markdown(path)
    except Exception as e:  # python-docx raises a variety of types
        print(f"error: failed to parse {path}: {e}", file=sys.stderr)
        return 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
