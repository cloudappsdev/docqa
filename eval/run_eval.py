"""Retrieval eval seed: recall@k, MRR, and refusal rate on unanswerable questions.

Usage: cp eval/golden.example.jsonl eval/golden.jsonl  (edit it), then
       python -m eval.run_eval [path] [k]
"""

import json
import sys
from pathlib import Path

from docqa.config import settings
from docqa.retrieval.retriever import retrieve


def _matches(hit, row) -> bool:
    pages = row.get("expected_pages") or []
    return hit.filename == row["expected_file"] and (not pages or hit.page in pages)


def main(path: str = "eval/golden.jsonl", k: int = 5) -> None:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    answerable = [r for r in rows if r.get("answerable", True)]
    unanswerable = [r for r in rows if not r.get("answerable", True)]

    hits_at_k, rr_sum = 0, 0.0
    for row in answerable:
        results = retrieve(row["question"], k)
        rank = next((i for i, h in enumerate(results, 1) if _matches(h, row)), None)
        if rank:
            hits_at_k += 1
            rr_sum += 1 / rank

    refused = 0
    for row in unanswerable:
        results = retrieve(row["question"], 1)
        if not results or results[0].score < settings.min_score:
            refused += 1

    if answerable:
        print(f"recall@{k}: {hits_at_k / len(answerable):.2%}   MRR: {rr_sum / len(answerable):.3f}"
              f"   (n={len(answerable)})")
    if unanswerable:
        print(f"correct refusals: {refused / len(unanswerable):.2%}   (n={len(unanswerable)})")


if __name__ == "__main__":
    main(*(sys.argv[1:2] or ["eval/golden.jsonl"]), *(int(a) for a in sys.argv[2:3]))
