from langchain_core.messages import BaseMessage, HumanMessage

async def run_translator(answer: str, language: str, llm) -> str:
    # If the language is English, just apply plain language (grade-6 readability)
    # Otherwise, translate to the target language as well.
    
    prompt = f"""You are a wellness and health education assistant. Rewrite the following text to a 6th-grade reading level (plain language).
    Remove or explain any complex medical jargon. Ensure the tone is empathetic, educational, and clear. Do not provide a diagnosis.
    
    The target language is: {language}.
    If the target language is NOT English, translate the simplified text into {language} accurately, ensuring cultural appropriateness.
    
    Text to translate/simplify:
    {answer}
    """
    
    # We don't need the whole conversation history for translation, just the final answer
    msgs = [HumanMessage(content=prompt)]
    response = await llm.ainvoke(msgs)
    
    return response.content.strip()
