"""Paragraph-aware chunking with overlap. Pure functions: no DB or model imports."""

import re

SEP = 2  # length of the "\n\n" joiner


def _split_long(paragraph: str, max_chars: int) -> list[str]:
    """Break an oversized paragraph on sentence boundaries (hard-split as a last resort)."""
    if len(paragraph) <= max_chars:
        return [paragraph]
    out: list[str] = []
    cur = ""
    for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
        while len(sentence) > max_chars:
            if cur:
                out.append(cur)
                cur = ""
            out.append(sentence[:max_chars])
            sentence = sentence[max_chars:]
        if cur and len(cur) + 1 + len(sentence) > max_chars:
            out.append(cur)
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        out.append(cur)
    return out


def _tail(buf: list[str], overlap: int) -> list[str]:
    """Trailing paragraphs totalling <= overlap chars, carried into the next chunk."""
    out: list[str] = []
    total = 0
    for item in reversed(buf):
        if total + len(item) + SEP > overlap:
            break
        out.insert(0, item)
        total += len(item) + SEP
    return out


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces: list[str] = []
    for p in paragraphs:
        pieces.extend(_split_long(p, max_chars))

    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    has_new = False  # does buf contain anything beyond carried-over overlap?

    for piece in pieces:
        if buf and size + len(piece) + SEP > max_chars:
            if has_new:
                chunks.append("\n\n".join(buf))
            buf = _tail(buf, overlap)
            if sum(len(b) + SEP for b in buf) + len(piece) + SEP > max_chars:
                buf = []
            size = sum(len(b) + SEP for b in buf)
            has_new = False
        buf.append(piece)
        size += len(piece) + SEP
        has_new = True

    if buf and has_new:
        chunks.append("\n\n".join(buf))
    return chunks
