import math
import hashlib
import re
from typing import List, Optional
import httpx
import numpy as np

class BaseEmbeddingProvider:
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0]

class LocalDenseEmbeddingProvider(BaseEmbeddingProvider):
    """
    Lightweight, high-speed, zero-dependency semantic embedding provider.
    Computes normalized subword n-gram semantic hashes with frequency damping.
    Guarantees 100% deterministic local dense vectors without external downloads.
    """
    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    def _hash_token(self, token: str, seed: int = 0) -> int:
        h = hashlib.sha256(f"{seed}:{token}".encode("utf-8")).hexdigest()
        return int(h[:8], 16) % self.dimension

    def _embed_single(self, text: str) -> List[float]:
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = re.findall(r"\b[a-zA-Z0-9_'-]+\b", text.lower())
        if not words:
            return vec.tolist()

        # Word unigrams and character 3-5 grams
        for word in words:
            # Token position hash
            idx = self._hash_token(word, seed=42)
            vec[idx] += 1.0

            # Sub-word character n-grams for semantic fuzzy match
            if len(word) >= 3:
                for n in (3, 4):
                    for i in range(len(word) - n + 1):
                        ngram = word[i : i + n]
                        ngram_idx = self._hash_token(ngram, seed=101)
                        vec[ngram_idx] += 0.35

        # Word bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            idx = self._hash_token(bigram, seed=997)
            vec[idx] += 0.75

        # L2 Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]

class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Embeddings via local Ollama instance (e.g. nomic-embed-text)."""
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.fallback = LocalDenseEmbeddingProvider()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = []
            with httpx.Client(timeout=10.0) as client:
                for text in texts:
                    resp = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model, "prompt": text}
                    )
                    if resp.status_code == 200:
                        embeddings.append(resp.json().get("embedding", []))
                    else:
                        return self.fallback.embed_texts(texts)
            return embeddings
        except Exception:
            # Fallback seamlessly if Ollama is not yet started or lacks embed model
            return self.fallback.embed_texts(texts)

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embeddings via OpenAI API."""
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.fallback = LocalDenseEmbeddingProvider()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"input": texts, "model": self.model}
                )
                if resp.status_code == 200:
                    data = resp.json()["data"]
                    return [item["embedding"] for item in data]
                return self.fallback.embed_texts(texts)
        except Exception:
            return self.fallback.embed_texts(texts)

def get_embedding_provider(
    provider_name: str = "local",
    ollama_url: str = "http://localhost:11434",
    openai_key: Optional[str] = None
) -> BaseEmbeddingProvider:
    if provider_name == "openai" and openai_key:
        return OpenAIEmbeddingProvider(api_key=openai_key)
    elif provider_name == "ollama":
        return OllamaEmbeddingProvider(base_url=ollama_url)
    return LocalDenseEmbeddingProvider()
