import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Segment:
    """A contiguous piece of a document that shares one page / section label."""

    text: str
    page: int | None
    section: str | None


def parse_pdf(path: Path) -> list[Segment]:
    import fitz  # pymupdf

    segments: list[Segment] = []
    with fitz.open(path) as doc:
        for page_no, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            if text:
                segments.append(Segment(text, page_no, None))
    return segments


_HEADING = re.compile(r"^#{1,6}\s+(.*\S)\s*$")


def parse_markdown(path: Path) -> list[Segment]:
    """Split on markdown headings so each segment carries its section title."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    segments: list[Segment] = []
    heading: str | None = None
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            segments.append(Segment(body, None, heading))

    for line in lines:
        m = _HEADING.match(line)
        if m:
            flush()
            buf = []
            heading = m.group(1)
        else:
            buf.append(line)
    flush()
    return segments


PARSERS = {".pdf": parse_pdf, ".md": parse_markdown, ".txt": parse_markdown}
SUPPORTED = set(PARSERS)
