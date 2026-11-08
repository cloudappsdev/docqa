from dataclasses import dataclass

from ..db import get_pool
from ..embeddings import embed_query

_SQL = """
SELECT c.id, d.filename, c.page, c.section, c.text,
       1 - (c.embedding <=> %(q)s) AS score
FROM chunks c
JOIN documents d ON d.id = c.doc_id
ORDER BY c.embedding <=> %(q)s
LIMIT %(k)s
"""


@dataclass
class Hit:
    chunk_id: int
    filename: str
    page: int | None
    section: str | None
    text: str
    score: float  # cosine similarity, higher is better


def retrieve(query: str, k: int = 5) -> list[Hit]:
    qvec = embed_query(query)
    with get_pool().connection() as conn:
        rows = conn.execute(_SQL, {"q": qvec, "k": k}).fetchall()
    return [
        Hit(r["id"], r["filename"], r["page"], r["section"], r["text"], float(r["score"]))
        for r in rows
    ]
