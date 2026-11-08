import hashlib
from pathlib import Path

from ..config import settings
from ..db import get_pool
from ..embeddings import embed_texts
from .chunking import chunk_text
from .parsers import PARSERS


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def ingest_file(path: str | Path, name: str | None = None, force: bool = False) -> dict:
    """Parse -> chunk -> embed -> store one file. Idempotent via content hash."""
    path = Path(path)
    name = name or path.name
    parser = PARSERS.get(path.suffix.lower())
    if parser is None:
        return {"filename": name, "status": "unsupported", "chunks": 0}

    digest = file_hash(path)
    pool = get_pool()
    with pool.connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM documents WHERE content_hash = %s", (digest,)
        ).fetchone()
    if exists and not force:
        return {"filename": name, "status": "skipped (unchanged)", "chunks": 0}

    # (page, section, text) for every chunk
    pieces: list[tuple[int | None, str | None, str]] = []
    for seg in parser(path):
        for text in chunk_text(seg.text, settings.chunk_max_chars, settings.chunk_overlap_chars):
            pieces.append((seg.page, seg.section, text))
    if not pieces:
        return {"filename": name, "status": "empty (no extractable text)", "chunks": 0}

    # Prepend the section title to what we embed; stored text stays clean for citations.
    vectors = embed_texts([f"{s}\n\n{t}" if s else t for _, s, t in pieces])

    with pool.connection() as conn:  # one transaction: replace old version atomically
        conn.execute("DELETE FROM documents WHERE filename = %s OR content_hash = %s", (name, digest))
        doc_id = conn.execute(
            "INSERT INTO documents (filename, content_hash) VALUES (%s, %s) RETURNING id",
            (name, digest),
        ).fetchone()["id"]
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO chunks (doc_id, chunk_index, page, section, text, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                [
                    (doc_id, i, page, section, text, vec)
                    for i, ((page, section, text), vec) in enumerate(zip(pieces, vectors))
                ],
            )
    return {"filename": name, "status": "ingested", "chunks": len(pieces)}


def ingest_directory(root: str | Path, force: bool = False) -> list[dict]:
    root = Path(root)
    results = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if path.suffix.lower() in PARSERS:
            results.append(ingest_file(path, name=str(path.relative_to(root)), force=force))
    return results
