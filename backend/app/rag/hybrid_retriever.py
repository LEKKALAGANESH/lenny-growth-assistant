import re
from typing import List, Dict, Any, Tuple, Optional
from rank_bm25 import BM25Okapi
from app.rag.chunker import Chunk
from app.rag.vector_store import PersistentVectorStore
from app.rag.embeddings import BaseEmbeddingProvider

class HybridRetriever:
    """
    Hybrid retriever combining Dense Vector Similarity and BM25 Lexical Keyword Search
    using Reciprocal Rank Fusion (RRF) for growth concepts and exact guest terminology.
    """
    def __init__(
        self,
        vector_store: PersistentVectorStore,
        embedding_provider: BaseEmbeddingProvider,
        dense_weight: float = 0.6,
        sparse_weight: float = 0.4,
        rrf_k: int = 60
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        self.rrf_k = rrf_k
        self.bm25: Optional[BM25Okapi] = None
        self._build_bm25_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_'-]+\b", text.lower())

    def _build_bm25_index(self) -> None:
        if self.vector_store.count() > 0:
            corpus = [self._tokenize(chunk.full_content) for chunk in self.vector_store.chunks]
            self.bm25 = BM25Okapi(corpus)
        else:
            self.bm25 = None

    def reload(self) -> None:
        self.vector_store.load()
        self._build_bm25_index()

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[Chunk, float, Dict[str, float]]]:
        """
        Executes hybrid search and returns: List of (Chunk, combined_rrf_score, score_breakdown)
        """
        if self.vector_store.count() == 0:
            return []

        # 1. Dense Semantic Search
        q_emb = self.embedding_provider.embed_query(query)
        dense_results = self.vector_store.search(
            query_vector=q_emb,
            top_k=len(self.vector_store.chunks),
            filter_metadata=filter_metadata
        )

        dense_rank_map = {}
        for rank, (chunk, score) in enumerate(dense_results):
            dense_rank_map[chunk.chunk_id] = (rank, score, chunk)

        # 2. Sparse BM25 Keyword Search
        tokenized_query = self._tokenize(query)
        sparse_rank_map = {}
        if self.bm25 and tokenized_query:
            bm25_scores = self.bm25.get_scores(tokenized_query)
            bm25_ranked_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

            current_rank = 0
            for idx in bm25_ranked_indices:
                chunk = self.vector_store.chunks[idx]
                if filter_metadata:
                    match = all(chunk.metadata.get(k) == v for k, v in filter_metadata.items())
                    if not match:
                        continue
                sparse_rank_map[chunk.chunk_id] = (current_rank, float(bm25_scores[idx]), chunk)
                current_rank += 1

        # 3. Reciprocal Rank Fusion (RRF)
        all_chunk_ids = set(dense_rank_map.keys()).union(sparse_rank_map.keys())
        fused_scores = []

        for cid in all_chunk_ids:
            chunk = None
            rrf_score = 0.0

            dense_score = 0.0
            dense_rank = 9999
            if cid in dense_rank_map:
                dense_rank, dense_score, chunk = dense_rank_map[cid]
                rrf_score += self.dense_weight / (self.rrf_k + dense_rank + 1)

            sparse_score = 0.0
            sparse_rank = 9999
            if cid in sparse_rank_map:
                sparse_rank, sparse_score, chunk = sparse_rank_map[cid]
                rrf_score += self.sparse_weight / (self.rrf_k + sparse_rank + 1)

            breakdown = {
                "dense_score": round(dense_score, 4),
                "dense_rank": dense_rank,
                "sparse_score": round(sparse_score, 4),
                "sparse_rank": sparse_rank,
                "rrf_score": round(rrf_score, 6)
            }
            if chunk is not None:
                fused_scores.append((chunk, rrf_score, breakdown))

        fused_scores.sort(key=lambda x: x[1], reverse=True)
        return fused_scores[:top_k]
