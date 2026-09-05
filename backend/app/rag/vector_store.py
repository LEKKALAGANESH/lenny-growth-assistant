import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from app.rag.chunker import Chunk
from app.db.session import engine, SessionLocal
from app.models.entities import ChunkModel


def _row_to_chunk(row: ChunkModel) -> Chunk:
    return Chunk(
        chunk_id=row.id,
        episode_id=row.episode_id,
        episode_title=row.episode_title,
        guest=row.guest,
        speaker=row.speaker,
        timestamp_start=row.timestamp_start,
        timestamp_end=row.timestamp_end,
        text=row.text,
        contextual_header=row.contextual_header,
        full_content=row.full_content,
        metadata=row.chunk_metadata or {},
    )


class PersistentVectorStore:
    """
    Podcast transcript vector store. Primary backend is PostgreSQL + pgvector, using
    an HNSW index (see app/models/entities.py::ChunkModel) for approximate cosine
    nearest-neighbor search, queried through SQLAlchemy's `<=>` operator.

    Falls back transparently to a flat JSON file + numpy cosine similarity (the
    original implementation) when the configured DATABASE_URL isn't a reachable
    Postgres instance (e.g. local dev/tests without Docker) — app/db/session.py
    already does this same Postgres-with-sqlite-fallback dance for the chat DB.

    Interface (add_chunks/search/save/load/count/clear) is unchanged so callers
    (hybrid_retriever.py, ingestion.py, orchestrator.py, health.py) need no changes.
    """

    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_path / "vector_index.json"  # legacy-path only
        self.use_postgres = engine.dialect.name == "postgresql"

        self.chunks: List[Chunk] = []
        self.embeddings: np.ndarray = np.empty((0, 384), dtype=np.float32)
        self.load()

    # ------------------------------------------------------------------ #
    # Postgres + pgvector path
    # ------------------------------------------------------------------ #
    def _pg_add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        db = SessionLocal()
        try:
            for chunk, emb in zip(chunks, embeddings):
                db.merge(ChunkModel(
                    id=chunk.chunk_id,
                    episode_id=chunk.episode_id,
                    episode_title=chunk.episode_title,
                    guest=chunk.guest,
                    speaker=chunk.speaker,
                    timestamp_start=chunk.timestamp_start,
                    timestamp_end=chunk.timestamp_end,
                    text=chunk.text,
                    contextual_header=chunk.contextual_header,
                    full_content=chunk.full_content,
                    chunk_metadata=chunk.metadata,
                    embedding=emb,
                ))
            db.commit()
        finally:
            db.close()
        self.load()

    def _pg_search(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        db = SessionLocal()
        try:
            distance = ChunkModel.embedding.cosine_distance(query_vector)
            stmt = db.query(ChunkModel, distance.label("distance"))
            if filter_metadata:
                for k, v in filter_metadata.items():
                    stmt = stmt.filter(ChunkModel.chunk_metadata[k].as_string() == str(v))
            stmt = stmt.order_by(distance.asc()).limit(top_k)
            results = []
            for row, dist in stmt.all():
                similarity = 1.0 - float(dist)  # cosine_distance -> cosine similarity
                results.append((_row_to_chunk(row), similarity))
            return results
        finally:
            db.close()

    def _pg_load(self) -> None:
        db = SessionLocal()
        try:
            rows = db.query(ChunkModel).all()
            self.chunks = [_row_to_chunk(r) for r in rows]
        finally:
            db.close()

    def _pg_clear(self) -> None:
        db = SessionLocal()
        try:
            db.query(ChunkModel).delete()
            db.commit()
        finally:
            db.close()
        self.chunks = []

    def _pg_count(self) -> int:
        db = SessionLocal()
        try:
            return db.query(ChunkModel).count()
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Legacy flat-JSON path (used only when Postgres is unreachable, e.g.
    # local unit tests run without `docker compose up`)
    # ------------------------------------------------------------------ #
    def _json_add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return
        new_embeddings = np.array(embeddings, dtype=np.float32)
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        new_embeddings = new_embeddings / norms

        if len(self.chunks) == 0:
            self.chunks = list(chunks)
            self.embeddings = new_embeddings
        else:
            self.chunks.extend(chunks)
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        self._json_save()

    def _json_search(
        self,
        query_vector: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        if len(self.chunks) == 0 or self.embeddings.shape[0] == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scores = np.dot(self.embeddings, q_vec)

        valid_indices = []
        for i, chunk in enumerate(self.chunks):
            if filter_metadata:
                if any(chunk.metadata.get(k) != v for k, v in filter_metadata.items()):
                    continue
            valid_indices.append(i)
        if not valid_indices:
            return []

        filtered_scores = [(idx, float(scores[idx])) for idx in valid_indices]
        filtered_scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.chunks[idx], score) for idx, score in filtered_scores[:top_k]]

    def _json_save(self) -> None:
        data = {
            "chunks": [chunk.model_dump() for chunk in self.chunks],
            "embeddings": self.embeddings.tolist() if self.embeddings.size > 0 else []
        }
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _json_load(self) -> None:
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = [Chunk(**c) for c in data.get("chunks", [])]
                    raw_emb = data.get("embeddings", [])
                    self.embeddings = (
                        np.array(raw_emb, dtype=np.float32) if raw_emb
                        else np.empty((0, 384), dtype=np.float32)
                    )
            except Exception:
                self.chunks = []
                self.embeddings = np.empty((0, 384), dtype=np.float32)

    # ------------------------------------------------------------------ #
    # Public interface (unchanged signatures)
    # ------------------------------------------------------------------ #
    def add_chunks(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        if not chunks:
            return
        if self.use_postgres:
            self._pg_add_chunks(chunks, embeddings)
        else:
            self._json_add_chunks(chunks, embeddings)

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float]]:
        if self.use_postgres:
            return self._pg_search(query_vector, top_k, filter_metadata)
        return self._json_search(query_vector, top_k, filter_metadata)

    def save(self) -> None:
        """No-op on Postgres (writes are committed immediately in add_chunks)."""
        if not self.use_postgres:
            self._json_save()

    def load(self) -> None:
        if self.use_postgres:
            self._pg_load()
        else:
            self._json_load()

    def count(self) -> int:
        if self.use_postgres:
            return self._pg_count()
        return len(self.chunks)

    def clear(self) -> None:
        if self.use_postgres:
            self._pg_clear()
        else:
            self.chunks = []
            self.embeddings = np.empty((0, 384), dtype=np.float32)
            if self.index_file.exists():
                self.index_file.unlink()
