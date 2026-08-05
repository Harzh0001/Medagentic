# MedAgentic - Phase 0

Evidence-based medical Q&A: PubMed retrieval -> GPT via OpenCode Zen -> cited answer.

## Run

1. Edit `.env` - put your OpenCode Zen API key in `ZEN_API_KEY`
2. Double-click `start.bat` -> API at http://localhost:8000
3. In a second terminal: `streamlit run ui/chat.py` -> UI at http://localhost:8501

## Test the API directly

    curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d "{"message": "What is first-line treatment for type 2 diabetes?"}"

## Known limits (Phase 0)

- Only PubMed abstracts - no full text, no guidelines corpus yet
- No symptom analysis, no DDx, no drug-interaction agent (Phase 2)
- No vector DB - retrieval is straight search. RAG + embeddings come in Phase 1.
