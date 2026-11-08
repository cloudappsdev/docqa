"""Citation validation. Pure functions so they're trivially unit-testable."""

import re

_INLINE = re.compile(r"\[(\d+)\]")


def resolve_citations(
    answer: str, cited_sources: list[int], n_sources: int
) -> tuple[list[int], list[int]]:
    """Return (valid_ids, invalid_ids).

    Union of the structured list and inline [n] markers, so the model can't cite
    a source in prose that it forgot to list (or vice versa). Valid means the id
    refers to a source that was actually retrieved.
    """
    claimed = set(cited_sources) | {int(m) for m in _INLINE.findall(answer)}
    valid = sorted(c for c in claimed if 1 <= c <= n_sources)
    invalid = sorted(c for c in claimed if not 1 <= c <= n_sources)
    return valid, invalid
