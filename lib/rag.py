"""Phase 1 RAG: local guideline corpus -> ChromaDB -> grounded cited answers.

Pipeline:
  1. scripts/ingest_guidelines.py  -> chunks PDFs/TXT in data/guidelines -> ChromaDB (data/chroma_db)
  2. retrieve(question)            -> top-k guideline chunks (cosine)
  3. answer_with_rag(question)     -> LLM answer grounded in chunks; returns None if no good match
                                     (caller then falls back to the PubMed path)

Embeddings run 100% locally (sentence-transformers, all-MiniLM-L6-v2) —
no extra API cost, works offline after the one-time model download.
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

try:
    from lib.pubmed import clean_query
except ImportError:  # minimal fallback if Phase 0 cleaner is named differently
    def clean_query(q: str) -> str:
        return re.sub(r"\b(what|is|the|for|a|an|of|in|to|and|or|with|please|tell|me|about|treatment)\b",
                      " ", q, flags=re.I)

# ---------------------------------------------------------------- config --
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
GUIDELINE_DIR = DATA_DIR / "guidelines"
CHROMA_DIR = DATA_DIR / "chroma_db"
COLLECTION_NAME = "guidelines"
EMBED_MODEL = "all-MiniLM-L6-v2"
CHUNK_TOKENS = 180   # all-MiniLM-L6-v2 truncates at 256 tokens; keep chunks inside it
CHUNK_OVERLAP = 30
TOP_K = 6            # give relevant chunks a chance to be in the window
MIN_SCORE = 0.35     # cosine similarity; below this -> PubMed fallback (LLM filters junk)
# ------------------------------------------------------------- lazy init --
_embedder = None
_db = None
_collection = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        # Use FastEmbed (pure CPU, ONNX, zero PyTorch) for lightweight embeddings
        from fastembed import TextEmbedding
        class FastEmbedWrapper:
            def __init__(self):
                self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
            def embed_documents(self, texts):
                return [list(e) for e in self.model.embed(texts)]
            def embed_query(self, text):
                return list(next(self.model.embed([text])))
        _embedder = FastEmbedWrapper()
    return _embedder

def _get_collection():
    global _db, _collection
    if _collection is None:
        import chromadb
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _db = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _db.get_or_create_collection(
            COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
        )
    return _collection

# --------------------------------------------------------------- chunking --
_HEADING_RE = re.compile(r"^\s*(#{1,6}\s+)?[A-Z][A-Z0-9 .\-&()]{2,70}\s*$")

# Lines that repeat on every page of typical guideline PDFs (NICE headers/
# footers, copyright notices, page numbers). They inject near-identical text
# into every chunk, so cosine retrieval latches onto them instead of the real
# recommendation content.
_BOILERPLATE_RES = [
    re.compile(r"^\s*©\s*NICE\s*\d{4}.*$", re.I),
    re.compile(r"^\s*All rights reserved.*$", re.I),
    re.compile(r"^\s*Subject to Notice of rights.*$", re.I),
    re.compile(r"^\s*NICE guideline\b.*$", re.I),
    re.compile(r"^\s*Page\s+\d+\s+of\s+\d+\s*$", re.I),
    re.compile(r"^\s*\d+\s*$"),                       # bare page numbers
    re.compile(r"^\s*https?://\S+\s*$", re.I),
]

def _clean_boilerplate(text: str) -> str:
    """Strip per-page headers/footers that repeat verbatim across pages."""
    lines = text.splitlines()
    counts: dict[str, int] = {}
    for ln in lines:
        s = ln.strip()
        if s:
            counts[s] = counts.get(s, 0) + 1
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if counts.get(s, 0) >= 5:                     # repeated on many pages
            continue
        if any(r.match(s) for r in _BOILERPLATE_RES):
            continue
        out.append(ln)
    return "\n".join(out)

def _split_into_chunks(text: str, source: str, section: str = "Full document") -> list[dict]:
    """Split at heading-like lines first, then sliding-window within each section."""
    sections, cur_section, cur_lines = [], section, []
    for raw in text.splitlines():
        line = raw.strip()
        if (_HEADING_RE.match(line) and not line.endswith(".")
                and len(line) <= 72):
            if " ".join(cur_lines).strip():
                sections.append((cur_section, " ".join(cur_lines)))
            cur_section, cur_lines = line, []
        else:
            cur_lines.append(raw)
    if " ".join(cur_lines).strip():
        sections.append((cur_section, " ".join(cur_lines)))

    step = max(1, CHUNK_TOKENS - CHUNK_OVERLAP)
    chunks = []
    for sec_name, sec_text in sections:
        words = re.findall(r"\S+", sec_text)
        for i in range(0, len(words), step):
            window = words[i:i + CHUNK_TOKENS]
            if len(window) < 40:
                continue
            chunks.append({
                "text": " ".join(window),
                "source": source,
                "section": sec_name,
                "chunk": len(chunks) + 1,
            })
    return chunks

def ingest_text(text: str, source: str, section: str = "Full document") -> int:
    """Embed + store one document. Re-running is safe (skips stored ids)."""
    col = _get_collection()
    embedder = _get_embedder()
    text = _clean_boilerplate(text)
    chunks = _split_into_chunks(text, source, section)
    if not chunks:
        return 0
    ids = [f"{source}::{section}::{c['chunk']}" for c in chunks]
    existing = set(col.get(ids=ids)["ids"])
    todo = [(i, c) for i, c in zip(ids, chunks) if i not in existing]
    if not todo:
        return 0
    col.add(
        ids=[i for i, _ in todo],
        documents=[c["text"] for _, c in todo],
        embeddings=embedder.embed_documents([c["text"] for _, c in todo]),
        metadatas=[{"source": c["source"], "section": c["section"], "chunk": c["chunk"]}
                   for _, c in todo],
    )
    return len(todo)

# -------------------------------------------------------------- retrieval --
def retrieve(question: str, k: int = TOP_K):
    """Top-k chunks (cosine). Returns None if corpus empty or best match too weak."""
    col = _get_collection()
    if col.count() == 0:
        return None
    query = clean_query(question)
    emb = _get_embedder().embed_query(query)
    res = col.query(query_embeddings=[emb], n_results=k)
    out = []
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i]
        out.append({
            "text": res["documents"][0][i],
            "source": meta.get("source", "?"),
            "section": meta.get("section", ""),
            "score": 1.0 - res["distances"][0][i],  # cosine sim (chroma cosine distance)
        })
    if out[0]["score"] < MIN_SCORE:
        return None
    return out

# ---------------------------------------------------------------- answer ---
def _call_llm(system: str, user: str, temperature: float = 0.2,max_tokens: int = 1200) -> str:
    load_dotenv(PROJECT_ROOT / ".env")
    from config import settings
    client = OpenAI(
        api_key=settings.zen_api_key,
        base_url=settings.zen_base_url,
    )
    model = settings.zen_model
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens
    )
         
    return resp.choices[0].message.content.strip()

def answer_with_rag(question: str):
    """Grounded answer from the guideline corpus, or None -> fall back to PubMed."""
    chunks = retrieve(question)
    if chunks is None:
        return None
    ctx = "\n\n".join(
        f"[{i+1}] ({c['source']} — {c['section']})\n{c['text']}"
        for i, c in enumerate(chunks)
    )
    system = (
        "You are a cautious clinical decision-support assistant. "
        "Answer ONLY from the provided guideline excerpts, and only the part of the "
        "question those excerpts actually answer. "
        "If an excerpt covers a different topic than the question (e.g., a complication "
        "or a different disease), ignore it completely; never volunteer unrelated content. "
        "If the excerpts do not contain the answer, say so and do not guess. "
        "Cite supporting excerpts as [1], [2], etc. Never invent citations. "
        "Keep the answer focused, under ~250 words. "
        "Do not mention the corpus, retrieval process, or that you are an AI."
    )
    user = (
        "Question: {question}\n\n"
        "Guideline excerpts:\n{ctx}\n\n"
        "Requirements:\n"
        "- Only state what is supported by the excerpts.\n"
        "- Include bracketed citation numbers like [1] when supported.\n"
        "- If not supported, explicitly say: Not covered by the retrieved evidence.\n"
        "- Do not quote verbatim unless necessary; paraphrase with citations.\n"
    ).format(question=question, ctx=ctx)
    answer = _call_llm(system, user)
    citations = [
        {"label": f"[{i+1}]", "source": c["source"], "section": c["section"],
         "score": round(c["score"], 3)}
        for i, c in enumerate(chunks)
    ]
    return {"answer": answer, "citations": citations, "mode": "rag"}