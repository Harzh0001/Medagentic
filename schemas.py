from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    mode: str = "clinician"
    thread_id: str = Field(default="default_thread")
    language: str = Field(default="English")


class Citation(BaseModel):
    pmid: str
    title: str
    url: str


class EvidencePiece(BaseModel):
    pmid: str
    title: str
    snippet: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved: list[EvidencePiece]
    disclaimer: str
