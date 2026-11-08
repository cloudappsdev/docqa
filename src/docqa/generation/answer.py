import anthropic

from ..config import settings
from ..retrieval.retriever import Hit, retrieve
from .citations import resolve_citations
from .prompts import ANSWER_TOOL, SYSTEM, build_user_message
from .schemas import AskResponse, Citation

NOT_FOUND = "I couldn't find this in the ingested documents."


def _citation(n: int, hit: Hit) -> Citation:
    snippet = hit.text if len(hit.text) <= 300 else hit.text[:300].rstrip() + "…"
    return Citation(
        id=n, filename=hit.filename, page=hit.page, section=hit.section,
        snippet=snippet, score=round(hit.score, 4),
    )


def _refuse(warnings: list[str] | None = None) -> AskResponse:
    return AskResponse(answer=NOT_FOUND, answerable=False, citations=[], warnings=warnings or [])


def answer_question(question: str, top_k: int | None = None) -> AskResponse:
    hits = retrieve(question, top_k or settings.top_k)

    # Gate 1: retrieval confidence. Cheap, and saves an LLM call.
    if not hits or hits[0].score < settings.min_score:
        return _refuse()

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    msg = client.messages.create(
        model=settings.llm_model,
        max_tokens=1024,
        system=SYSTEM,
        tools=[ANSWER_TOOL],
        tool_choice={"type": "tool", "name": "submit_answer"},
        messages=[{"role": "user", "content": build_user_message(question, hits)}],
    )
    payload = next((b.input for b in msg.content if b.type == "tool_use"), None)
    if payload is None:
        return _refuse(["model returned no structured answer"])

    # Gate 2: the model itself says the sources don't cover it.
    if not payload.get("answerable", False):
        return _refuse()

    answer = payload.get("answer", "")
    valid, invalid = resolve_citations(answer, payload.get("cited_sources", []), len(hits))
    warnings = [f"model cited non-existent source(s): {invalid}"] if invalid else []

    # Gate 3: an "answer" with no valid citation is ungrounded; don't return it.
    if not valid:
        return _refuse(warnings + ["answer had no valid citations"])

    return AskResponse(
        answer=answer,
        answerable=True,
        citations=[_citation(n, hits[n - 1]) for n in valid],
        warnings=warnings,
    )
