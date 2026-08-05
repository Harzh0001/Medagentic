import httpx

from config import settings
from lib.pubmed import fetch_abstracts, search_pubmed
from schemas import Citation, EvidencePiece

SYSTEM_PROMPT = '''You are MedAgentic, an evidence-based medical information
assistant for healthcare professionals and informed patients.

RULES:
1. Answer using ONLY the retrieved evidence below. Ground every claim in a
   numbered source: [1], [2], etc.
2. If the evidence does not cover an aspect of the question, explicitly say:
   "Not covered by the retrieved evidence."
3. Mention the study type (RCT, systematic review, guideline) of each source.
4. Never give personal dosage advice. If dosing is asked, say a clinician
   must decide and cite relevant guideline evidence if present.
5. Never claim statistics that are not present in the sources.
6. Structure your answer: concise summary first, then key findings with
   citations, then caveats.'''


def _build_messages(query: str, articles: list[dict]) -> list[dict]:
    evidence_block = "\n\n".join(
        f"[{i + 1}] PMID: {a['pmid']} | {a['title']} | "
        f"{a['journal']} {a['year']}\n{a['abstract']}"
        for i, a in enumerate(articles)
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "QUESTION:\n" + query +
                "\n\nRETRIEVED EVIDENCE:\n" + evidence_block
            ),
        },
    ]


async def _extract_keywords(query: str) -> str:
    body = {
        "model": settings.zen_model,
        "messages": [
            {
                "role": "system", 
                "content": "You are a medical search query extractor. Extract 2-4 essential medical keywords from the user's question for a PubMed search. Correct any spelling mistakes or typos (e.g. 'correa' -> 'chorea'). Output ONLY the keywords separated by spaces, nothing else."
            },
            {"role": "user", "content": query}
        ],
        "temperature": 0.0,
        "max_tokens": 50,
    }
    headers = {
        "Authorization": f"Bearer {settings.zen_api_key}",
        "Content-Type": "application/json",
    }
    try:
        url = f"{settings.zen_base_url}/chat/completions" if settings.zen_base_url else "https://api.openai.com/v1/chat/completions"
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=body, headers=headers, timeout=10)
            r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return query


async def answer(query: str):
    search_query = await _extract_keywords(query)
    pmids = await search_pubmed(search_query, settings.top_k)
    articles = await fetch_abstracts(pmids)

    if not articles:
        return (
            "I could not retrieve relevant evidence from PubMed for this "
            "question. Please rephrase or try a broader topic.",
            [], [],
        )

    body = {
        "model": settings.zen_model,
        "messages": _build_messages(query, articles),
        "temperature": 0.2,
        "max_tokens": 900,
    }
    headers = {
        "Authorization": f"Bearer {settings.zen_api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.zen_base_url}/chat/completions",
                json=body,
                headers=headers,
                timeout=60,
            )
            r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return (
            f"LLM call failed: {exc}\n\nCheck ZEN_API_KEY and ZEN_BASE_URL "
            "in .env, then restart.",
            [], [],
        )

    citations = [
        Citation(
            pmid=a["pmid"],
            title=a["title"],
            url=f"https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/",
        )
        for a in articles
    ]
    retrieved = [
        EvidencePiece(
            pmid=a["pmid"],
            title=a["title"],
            snippet=a["abstract"][:400],
            url=f"https://pubmed.ncbi.nlm.nih.gov/{a['pmid']}/",
        )
        for a in articles
    ]
    return text, citations, retrieved

async def run_evidence(query: str) -> dict:
    text, citations, retrieved = await answer(query)
    return {"answer": text, "citations": [c.model_dump() for c in citations]}
