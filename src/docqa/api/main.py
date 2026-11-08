import shutil
from contextlib import asynccontextmanager
from pathlib import Path

import anthropic
from fastapi import FastAPI, HTTPException, UploadFile

from ..config import settings
from ..db import get_pool
from ..generation.answer import answer_question
from ..generation.schemas import AskRequest, AskResponse
from ..ingest.parsers import SUPPORTED
from ..ingest.pipeline import ingest_file


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_pool()  # creates schema + opens pool
    yield


app = FastAPI(title="DocQA", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    with get_pool().connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/ingest")
def ingest(file: UploadFile, force: bool = False) -> dict:
    # Path(...).name strips any directory components from the client-supplied filename
    name = Path(file.filename or "").name
    if Path(name).suffix.lower() not in SUPPORTED:
        raise HTTPException(400, f"Unsupported file type. Use one of: {sorted(SUPPORTED)}")
    dest = Path(settings.data_dir) / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        shutil.copyfileobj(file.file, out)
    return ingest_file(dest, force=force)


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        return answer_question(req.question, req.top_k)
    except anthropic.APIError as exc:
        raise HTTPException(502, f"LLM provider error: {exc.__class__.__name__}") from exc
