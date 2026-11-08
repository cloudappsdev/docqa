# DocQA: document Q&A with citations

A from-scratch RAG baseline: ingest PDFs/markdown, retrieve with pgvector, answer with
validated citations, and **refuse** when the documents don't contain the answer.

```
file -> parse (page/section) -> chunk -> embed -> Postgres + pgvector
question -> embed -> top-k -> [gate: score] -> LLM (forced tool call) -> [gate: valid citations] -> answer
```

## Quickstart

```bash
cp .env.example .env            # add ANTHROPIC_API_KEY
docker compose up --build -d    # Postgres+pgvector and the API on :8000

# ingest (upload, or drop files in data/raw and use the CLI)
curl -F "file=@data/raw/my.pdf" localhost:8000/ingest

# ask
curl -s localhost:8000/ask -H 'content-type: application/json' \
  -d '{"question": "What is the rollback procedure?"}' | jq
```

Interactive docs: http://localhost:8000/docs

Local dev without Docker for the API: `docker compose up -d db`, then
`pip install -e ".[dev]"`, `python -m docqa.ingest data/raw`, `make run`.

## Response shape

```json
{
  "answer": "Roll back by re-running the previous release pipeline [1].",
  "answerable": true,
  "citations": [{"id": 1, "filename": "runbook.md", "page": null,
                 "section": "Rollback", "snippet": "...", "score": 0.71}],
  "warnings": []
}
```

## Design decisions

- **No framework.** The retrieve -> generate loop is ~100 lines you can read end to end.
- **Three refusal gates:** low retrieval score, model says "not answerable", and answer
  with no valid citations. Citation IDs are checked against what was actually retrieved.
- **Forced tool call** for structured output, so there's no JSON parsing to break.
- **Idempotent ingestion** via content hash; changed files replace their old chunks atomically.
- Prompt treats source text as untrusted (basic prompt-injection hygiene).

## Known limitations (your roadmap)

- Vector-only retrieval: add BM25 hybrid + cross-encoder rerank (project #3).
- Fixed-size-ish chunking; PDF headings aren't detected (only page numbers).
- Ingestion is synchronous; move to a background worker/queue.
- No auth or rate limiting on the API.
- `MIN_SCORE` is a guess: tune it with `eval/run_eval.py`.

## Eval seed

```bash
cp eval/golden.example.jsonl eval/golden.jsonl   # write 30-50 real questions
python -m eval.run_eval eval/golden.jsonl 5      # recall@k, MRR, correct refusals
```
