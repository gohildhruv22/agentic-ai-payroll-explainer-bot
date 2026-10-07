"""
Lightweight "RAG" over PolicyDocument: chunk text, token overlap scoring, return top excerpts.

No embeddings API — uses simple bag-of-words style relevance for demo speed.
"""
import re
import json
import math
import numpy as np
from database import SessionLocal
from models import PolicyDocument


def policy_search_rag(query: str, top_k: int = 3) -> dict:
    db = SessionLocal()
    try:
        documents = db.query(PolicyDocument).all()
        if not documents:
            return {"success": False, "error": "No policy documents found in the system."}

        query_tokens = _tokenize(query)
        results = []

        for doc in documents:
            chunks = _split_into_chunks(doc.content, chunk_size=500)
            for i, chunk in enumerate(chunks):
                score = _compute_relevance(query_tokens, _tokenize(chunk))
                if score > 0:
                    results.append({
                        "title": doc.title,
                        "category": doc.category,
                        "chunk_index": i,
                        "content": chunk.strip(),
                        "relevance_score": round(score, 4),
                        "source": doc.source_file or doc.title,
                    })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_results = results[:top_k]

        if not top_results:
            return {
                "success": True,
                "results": [],
                "message": "No relevant policy sections found for your query."
            }

        return {
            "success": True,
            "query": query,
            "results": top_results,
        }
    except Exception as e:
        return {"error": str(e), "success": False}
    finally:
        db.close()


def _tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
        'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
        'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
        'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'each',
        'every', 'all', 'any', 'few', 'more', 'most', 'other', 'some', 'such',
        'than', 'too', 'very', 'just', 'also', 'only', 'then', 'that', 'this',
        'these', 'those', 'i', 'me', 'my', 'we', 'our', 'you', 'your', 'he',
        'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their',
        'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how',
    }
    return [t for t in tokens if t not in stop_words and len(t) > 1]


def _split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = ' '.join(words[start:end])
        chunks.append(chunk)
        start = end - overlap
    return chunks


def _compute_relevance(query_tokens: list, doc_tokens: list) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0

    query_set = set(query_tokens)
    doc_set = set(doc_tokens)

    intersection = query_set & doc_set
    if not intersection:
        return 0.0

    tf_score = sum(doc_tokens.count(t) for t in intersection) / len(doc_tokens)
    coverage = len(intersection) / len(query_set)

    bigram_bonus = 0
    for i in range(len(query_tokens) - 1):
        bigram = query_tokens[i] + " " + query_tokens[i + 1]
        doc_text = " ".join(doc_tokens)
        if bigram in doc_text:
            bigram_bonus += 0.1

    return tf_score * 0.4 + coverage * 0.5 + bigram_bonus * 0.1
