"""
agents/rag_agent.py
Retrieval-Augmented Generation agent.
Builds a local FAISS/TF-IDF index over the knowledge-base files
and retrieves the top-k chunks relevant to a student answer + question.
"""

import os
import re
import math
from pathlib import Path
from typing import List, Tuple, Dict

KB_DIR = Path(__file__).parent.parent / "knowledge_base"

# ── Simple TF-IDF retriever (no external deps beyond stdlib) ─────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return text.split()


def _chunk_text(text: str, size: int = 300, overlap: int = 50) -> List[str]:
    """Split text into overlapping word-chunks."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


class TFIDFRetriever:
    def __init__(self):
        self.chunks: List[str] = []
        self.sources: List[str] = []
        self._idf: Dict[str, float] = {}
        self._built = False

    def _build_idf(self):
        N = len(self.chunks)
        df: Dict[str, int] = {}
        for chunk in self.chunks:
            for token in set(_tokenize(chunk)):
                df[token] = df.get(token, 0) + 1
        self._idf = {t: math.log(N / (1 + d)) for t, d in df.items()}

    def _tf_idf_vec(self, tokens: List[str]) -> Dict[str, float]:
        tf: Dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        n = len(tokens) or 1
        return {t: (c / n) * self._idf.get(t, 0) for t, c in tf.items()}

    def _cosine(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        keys = set(a) & set(b)
        num = sum(a[k] * b[k] for k in keys)
        dA = math.sqrt(sum(v * v for v in a.values()))
        dB = math.sqrt(sum(v * v for v in b.values()))
        if dA == 0 or dB == 0:
            return 0.0
        return num / (dA * dB)

    def build(self):
        """Load all .txt files from knowledge_base and index them."""
        for fpath in KB_DIR.glob("*.txt"):
            text = fpath.read_text(encoding="utf-8")
            for chunk in _chunk_text(text):
                self.chunks.append(chunk)
                self.sources.append(fpath.name)
        self._build_idf()
        self._built = True
        print(f"[RAG] Indexed {len(self.chunks)} chunks from {KB_DIR}")

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Return top_k (source, chunk, score) tuples."""
        if not self._built:
            self.build()
        q_tokens = _tokenize(query)
        q_vec = self._tf_idf_vec(q_tokens)
        scored = []
        for i, chunk in enumerate(self.chunks):
            c_vec = self._tf_idf_vec(_tokenize(chunk))
            score = self._cosine(q_vec, c_vec)
            scored.append((self.sources[i], chunk, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]


# ── Optional: use sentence-transformers + FAISS for better semantic search ────
# Uncomment and install: pip install sentence-transformers faiss-cpu
#
# from sentence_transformers import SentenceTransformer
# import faiss, numpy as np
#
# class SemanticRetriever:
#     def __init__(self, model_name="all-MiniLM-L6-v2"):
#         self.model = SentenceTransformer(model_name)
#         self.chunks = []; self.sources = []; self.index = None
#
#     def build(self):
#         for fpath in KB_DIR.glob("*.txt"):
#             for chunk in _chunk_text(fpath.read_text("utf-8")):
#                 self.chunks.append(chunk); self.sources.append(fpath.name)
#         embeddings = self.model.encode(self.chunks, convert_to_numpy=True)
#         self.index = faiss.IndexFlatL2(embeddings.shape[1])
#         self.index.add(embeddings.astype("float32"))
#
#     def retrieve(self, query, top_k=5):
#         qvec = self.model.encode([query], convert_to_numpy=True).astype("float32")
#         D, I = self.index.search(qvec, top_k)
#         return [(self.sources[i], self.chunks[i], float(D[0][j]))
#                 for j, i in enumerate(I[0])]


class RAGAgent:
    """
    Agent responsibility: retrieve relevant context chunks
    for a given question + student answer.
    """

    def __init__(self):
        self.retriever = TFIDFRetriever()
        self.retriever.build()

    def get_context(self, question: str, student_answer: str, top_k: int = 5) -> str:
        """
        Combine question + answer as query, retrieve top chunks,
        return formatted context string for the scoring prompt.
        """
        query = f"{question} {student_answer}"
        results = self.retriever.retrieve(query, top_k=top_k)

        context_parts = []
        for source, chunk, score in results:
            if score > 0.01:  # Filter near-zero relevance
                context_parts.append(f"[Source: {source}]\n{chunk}")

        if not context_parts:
            return "No highly relevant context found. Using general knowledge."

        return "\n\n---\n\n".join(context_parts)

    def get_marking_guide_context(self, question_id: int) -> str:
        """Retrieve the specific marking guide for a question."""
        results = self.retriever.retrieve(f"Q{question_id} marking guide criteria", top_k=3)
        return "\n\n".join(c for _, c, _ in results)


# ── Singleton ─────────────────────────────────────────────────────────────────
_rag_agent: RAGAgent | None = None

def get_rag_agent() -> RAGAgent:
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent()
    return _rag_agent


if __name__ == "__main__":
    agent = get_rag_agent()
    ctx = agent.get_context(
        "අනුරාධපුර යුගයේ බෞද්ධ ආගමේ භූමිකාව",
        "මිහිඳු හිමි ශ්‍රී ලංකාවට බෞද්ධ ධර්මය ගෙනාවේය"
    )
    print(ctx[:500])
