import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class SemanticVectorStore:
    """
    Lightweight, embedded semantic similarity engine.
    Uses TF-IDF + cosine similarity as a high-speed zero-dependency engine,
    with an extensible interface for sentence-transformers or ChromaDB.
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.doc_vectors: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self.vocab: set = set()

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase, clean punctuation, tokenize into unigrams and bigrams
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\.\#\+]{2,}\b", text.lower())
        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def add_documents(self, docs: List[Dict[str, Any]], text_field: str = "text"):
        """Index a list of dictionaries with text fields."""
        self.documents.extend(docs)
        self._rebuild_index(text_field)

    def _rebuild_index(self, text_field: str):
        tokenized_docs = [self._tokenize(doc.get(text_field, "")) for doc in self.documents]
        n_docs = len(tokenized_docs)
        if n_docs == 0:
            return

        # Compute document frequency
        df = Counter()
        for doc_tokens in tokenized_docs:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                df[token] += 1

        # Compute smoothed IDF
        self.idf = {token: math.log((n_docs + 1) / (count + 1)) + 1.0 for token, count in df.items()}
        self.vocab = set(self.idf.keys())

        # Compute TF-IDF vectors
        self.doc_vectors = []
        for doc_tokens in tokenized_docs:
            tf = Counter(doc_tokens)
            vec = Counter({t: (cnt / len(doc_tokens)) * self.idf.get(t, 1.0) for t, cnt in tf.items()})
            self.doc_vectors.append(vec)

    def _cosine_similarity(self, vec1: Counter, vec2: Counter) -> float:
        intersection = set(vec1.keys()) & set(vec2.keys())
        dot_product = sum(vec1[k] * vec2[k] for k in intersection)
        
        norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
        norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))
        
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def search(self, query: str, top_k: int = 3, threshold: float = 0.05) -> List[Tuple[Dict[str, Any], float]]:
        """Search indexed documents by semantic cosine similarity."""
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        tf = Counter(query_tokens)
        query_vec = Counter({t: (cnt / len(query_tokens)) * self.idf.get(t, 1.0) for t, cnt in tf.items() if t in self.vocab})

        scored_docs = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            sim = self._cosine_similarity(query_vec, doc_vec)
            if sim >= threshold:
                scored_docs.append((self.documents[idx], round(float(sim), 4)))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return scored_docs[:top_k]
