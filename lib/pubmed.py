import re
import xml.etree.ElementTree as ET

import httpx

from config import settings

EVIDENCE_FILTER = (
    "AND (systematic review[pt] OR meta-analysis[pt] OR guideline[pt] "
    "OR randomized controlled trial[pt] OR review[Publication Type])"
)

# Question scaffolding words that should not go into a PubMed keyword query.
# PubMed is a keyword search engine: full sentences like
# "what is the first line treatment for diabetes?" return zero hits.
QUESTION_STOPWORDS = {
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "is", "are", "was", "were", "be", "been", "being", "do", "does", "did",
    "can", "could", "should", "would", "will", "shall", "may", "might",
    "the", "a", "an", "of", "to", "for", "in", "on", "at", "with", "and",
    "or", "but", "if", "then", "than", "so", "please", "tell", "give", "me",
    "my", "i", "you", "it", "its", "there", "about", "recommend",
}


def clean_query(query: str) -> str:
    """Turn a natural-language question into PubMed-friendly keywords."""
    q = re.sub(r"[^A-Za-z0-9\s-]", " ", query)  # strip punctuation, keep hyphens
    words = [
        w for w in q.split()
        if w.lower() not in QUESTION_STOPWORDS and len(w) > 1
    ]
    cleaned = " ".join(words)
    return cleaned or query.strip()


async def _esearch(term: str, retmax: int) -> list[str]:
    params = {
        "db": "pubmed",
        "term": term,
        "retmode": "json",
        "retmax": retmax,
        "sort": "relevance",
        "tool": "medagentic",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.pubmed_base}/esearch.fcgi",
            params=params,
            timeout=30,
        )
        r.raise_for_status()
        return r.json().get("esearchresult", {}).get("idlist", [])


async def search_pubmed(query: str, retmax: int = 6) -> list[str]:
    cleaned = clean_query(query)
    if not cleaned:
        return []
    # 1) Prefer high-quality evidence types (reviews, guidelines, RCTs).
    ids = await _esearch(f"({cleaned}) {EVIDENCE_FILTER}", retmax)
    # 2) Fall back to any article type if the filtered search is empty.
    if not ids:
        ids = await _esearch(cleaned, retmax)
    return ids


async def fetch_abstracts(pmids: list[str]) -> list[dict[str, str]]:
    if not pmids:
        return []

    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{settings.pubmed_base}/efetch.fcgi",
            params=params,
            timeout=30,
        )
        r.raise_for_status()

    root = ET.fromstring(r.text)
    out: list[dict[str, str]] = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID", "")
        title = art.findtext(".//ArticleTitle", "").strip()
        abstract = " ".join(
            t.text or "" for t in art.findall(".//Abstract/AbstractText")
        ).strip()
        journal = art.findtext(".//Journal/Title", "")
        year = (
            art.findtext(".//PubDate/Year", "")
            or art.findtext(".//PubDate/MedlineDate", "")
        )
        out.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract[: settings.max_abstract_chars],
            "journal": journal,
            "year": year,
        })
    return out
