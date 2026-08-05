from fastapi import FastAPI

from agents.orchestrator import run_chat
from safety.triage import check_red_flags
from schemas import ChatRequest, ChatResponse

app = FastAPI(title="MedAgentic", version="0.1.0")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "MedAgentic",
        "version": "0.1.0",
    }


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # The LangGraph orchestrator handles triage internally, but we can do a quick check
    # or just let the orchestrator handle it. We will let orchestrator handle it.
    
    answer, citations, mode = await run_chat(req.message, req.thread_id, req.language)
    
    disclaimer = (
        "Educational decision-support output, not medical advice and not a "
        "diagnosis. Always consult a qualified clinician for medical decisions."
    )
    
    if not answer.endswith(disclaimer) and mode != "emergency":
        answer = answer + "\n\n" + disclaimer
        
    return ChatResponse(
        answer=answer, citations=citations, retrieved=[], disclaimer=disclaimer
    )
