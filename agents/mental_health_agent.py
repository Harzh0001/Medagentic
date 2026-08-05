from langchain_core.messages import BaseMessage, HumanMessage

async def run_mental_health(messages: list[BaseMessage], llm) -> dict:
    prompt = """You are a compassionate, empathetic mental health triage agent. The user is discussing mental health struggles (e.g., anxiety, depression, stress).
    Provide a deeply empathetic response. Avoid giving medical diagnoses or prescribing treatments.
    If the user mentions anything related to self-harm, immediately provide crisis hotline numbers (e.g., 988 in the US, 108/112 in India, AASRA).
    
    Keep the response grounded, supportive, and end by suggesting they speak with a licensed therapist or psychiatrist."""
    
    msgs = list(messages) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    
    return {"answer": response.content.strip()}
