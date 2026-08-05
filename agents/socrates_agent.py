from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

async def run_socrates(messages: list[BaseMessage], llm) -> dict:
    prompt = """You are a wellness educator gathering symptom information.
    We need to collect the SOCRATES criteria (Site, Onset, Character, Radiation, Associated symptoms, Time course, Exacerbating/relieving factors, Severity).
    
    Review the conversation history. If any SOCRATES criteria are missing, ask exactly ONE follow-up question to clarify the missing piece.
    If all or most of the criteria have been gathered, respond with the exact word: "READY_FOR_EDUCATION"
    Keep your questions empathetic and simple."""
    
    msgs = list(messages) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    content = response.content.strip()
    
    if "READY_FOR_EDUCATION" in content:
        return {"ready_for_ddx": True, "answer": ""}
    
    return {"ready_for_ddx": False, "answer": content}
