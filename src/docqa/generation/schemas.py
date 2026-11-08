from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: int  # matches the [n] marker in the answer text
    filename: str
    page: int | None = None
    section: str | None = None
    snippet: str
    score: float


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class AskResponse(BaseModel):
    answer: str
    answerable: bool
    citations: list[Citation]
    warnings: list[str] = []
