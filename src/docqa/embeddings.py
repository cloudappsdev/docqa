from functools import lru_cache

import numpy as np

from .config import settings

# bge models retrieve better when queries (not documents) carry this prefix
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer  # lazy: heavy import

    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed documents. Vectors are L2-normalised, so cosine distance == dot product."""
    return _model().encode(
        texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
    )


def embed_query(query: str) -> np.ndarray:
    if "bge" in settings.embedding_model.lower():
        query = _BGE_QUERY_PREFIX + query
    return _model().encode(query, normalize_embeddings=True)
