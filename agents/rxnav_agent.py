import httpx
from langchain_core.messages import BaseMessage, HumanMessage

async def run_rxnav(messages: list[BaseMessage], llm) -> dict:
    prompt = """You are a medical pharmacy assistant. The user is asking about a drug interaction.
    Extract the list of drugs they are asking about. Return ONLY a comma-separated list of the drug names.
    If you cannot identify the drugs, return "UNKNOWN"."""
    
    msgs = list(messages) + [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    drugs = response.content.strip().replace('"', '').split(',')
    drugs = [d.strip() for d in drugs if d.strip() and "UNKNOWN" not in d.upper()]
    
    if not drugs:
        return {"answer": "I couldn't identify specific drugs in your query to check for interactions. Could you clarify the medication names?"}
    
    # Normally we would query the REST API of RxNav here.
    # For now, we mock the REST API response behavior as a placeholder
    # because parsing exact RxCUI for multiple drugs requires chained API calls.
    
    answer_prompt = f"""You are a pharmacist agent. The user is asking about interactions for these drugs: {', '.join(drugs)}.
    Using your general medical knowledge, describe any known major, moderate, or minor interactions between them.
    Note that this is an AI-generated check and they should consult a real pharmacist."""
    
    final_response = await llm.ainvoke(list(messages) + [HumanMessage(content=answer_prompt)])
    
    return {"answer": final_response.content.strip()}
