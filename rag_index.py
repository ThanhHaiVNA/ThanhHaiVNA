from __future__ import annotations
from typing import List, Dict, Any, Tuple

import numpy as np
import google.generativeai as genai

from config import EMBED_MODEL_NAME


def embed_text(text: str) -> np.ndarray:
    out = genai.embed_content(model=EMBED_MODEL_NAME, content=text)
    emb = out["embedding"]
    return np.array(emb, dtype=np.float32)


def build_index(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    print("\n🔧 Đang tạo vector index (embedding)...")
    vecs = [embed_text(d["text"]) for d in docs]
    mat = np.vstack(vecs)
    print(f"✅ Đã index {len(docs)} documents.\n")
    return {"docs": docs, "embeddings": mat}


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def retrieve_top_k(query: str, index: Dict[str, Any], k: int = 4) -> List[Dict[str, Any]]:
    q_vec = embed_text(query)
    sims: List[Tuple[float, int]] = []
    for i, emb in enumerate(index["embeddings"]):
        sims.append((cosine_sim(q_vec, emb), i))
    sims.sort(key=lambda x: x[0], reverse=True)
    top = sims[:k]
    results: List[Dict[str, Any]] = []
    for score, idx in top:
        d = index["docs"][idx]
        results.append({
            "score": score,
            "id": d.get("id"),
            "title": d.get("title", ""),
            "type": d.get("type", ""),
            "text": d.get("text", ""),
        })
    return results


def build_context_snippet(docs: List[Dict[str, Any]]) -> str:
    parts = []
    for d in docs:
        parts.append(f"[{d['title']}]\n{d['text']}\n")
    return "\n".join(parts)
