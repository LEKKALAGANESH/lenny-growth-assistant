import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.rag.chunker import Chunk

class PersistentVectorStore:
    """
    Lightweight, high-performance persistent vector database with cosine similarity
    and metadata filtering. Stores vectors and chunk payloads in serialized index.
    """
    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.index_file = self.storage_path / "vector_index.json"
        self.chunks: List[Chunk] = []
        self.embeddings: np.ndarray = np.empty((0, 384), dtype=np.float32)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.load()

    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return

        new_embeddings = np.array(embeddings, dtype=np.float32)
        # Normalize embeddings
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_embeddings = new_embeddings / norms

        if len(self.chunks) == 0:
            self.chunks = list(chunks)
            self.embeddings = new_embeddings
        else:
            self.chunks.extend(chunks)
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        self.save()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        if len(self.chunks) == 0 or self.embeddings.shape[0] == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        # Cosine similarity (dot product of normalized vectors)
        scores = np.dot(self.embeddings, q_vec)

        # Apply metadata filters if provided
        valid_indices = []
        for i, chunk in enumerate(self.chunks):
            if filter_metadata:
                match = True
                for k, v in filter_metadata.items():
                    if chunk.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            valid_indices.append(i)

        if not valid_indices:
            return []

        filtered_scores = [(idx, float(scores[idx])) for idx in valid_indices]
        filtered_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in filtered_scores[:top_k]:
            results.append((self.chunks[idx], score))

        return results

    def save(self) -> None:
        data = {
            "chunks": [chunk.model_dump() for chunk in self.chunks],
            "embeddings": self.embeddings.tolist() if self.embeddings.size > 0 else []
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self) -> None:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = [Chunk(**c) for c in data.get("chunks", [])]
                    raw_emb = data.get("embeddings", [])
                    if raw_emb:
                        self.embeddings = np.array(raw_emb, dtype=np.float32)
                    else:
                        self.embeddings = np.empty((0, 384), dtype=np.float32)
            except Exception:
                self.chunks = []
                self.embeddings = np.empty((0, 384), dtype=np.float32)

    def count(self) -> int:
        return len(self.chunks)

    def clear(self) -> None:
        self.chunks = []
        self.embeddings = np.empty((0, 384), dtype=np.float32)
        if self.index_file.exists():
            self.index_file.unlink()
