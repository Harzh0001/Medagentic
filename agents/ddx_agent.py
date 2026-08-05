from langchain_core.messages import BaseMessage, HumanMessage

async def run_ddx(messages: list[BaseMessage], llm) -> dict:
    prompt = """You are a wellness and health educator. Look at the patient's symptom history gathered so far.
    Provide a list of potential conditions for educational purposes ONLY. 
    Explain the potential conditions simply and empathetically.
    
    End the message by strictly advising them that this is not a diagnosis and they should see a doctor for formal medical advice."""
    
    msgs = list(messages) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    
    return {"answer": response.content.strip()}
