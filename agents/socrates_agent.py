from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

async def run_socrates(messages: list[BaseMessage], llm) -> dict:
    prompt = """You are an empathetic wellness educator. The user has mentioned a physical symptom.
    Your goal is to understand their symptom better by asking ONE very natural, conversational follow-up question.
    DO NOT interrogate the user. DO NOT ask a list of multiple questions at once.
    Instead of rigidly following a medical checklist, just ask whatever feels most natural to keep the conversation flowing smoothly.
    
    If you feel you have enough context to provide educational information, OR if the user is explicitly asking for advice/treatment, respond with the exact word: "READY_FOR_EDUCATION"."""
    
    msgs = list(messages) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    content = response.content.strip()
    
    if "READY_FOR_EDUCATION" in content:
        return {"ready_for_ddx": True, "answer": ""}
    
    return {"ready_for_ddx": False, "answer": content}
