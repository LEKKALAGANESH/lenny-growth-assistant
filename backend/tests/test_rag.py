import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from app.core.config import settings
from app.rag.parser import TranscriptParser, Episode, Utterance
from app.rag.chunker import TranscriptChunker, Chunk
from app.rag.embeddings import LocalDenseEmbeddingProvider
from app.rag.vector_store import PersistentVectorStore
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.grounding import GroundingEngine

@pytest.fixture
def sample_episode():
    return Episode(
        episode_id="ep-test",
        title="Test Growth Strategy",
        guest="Growth Expert",
        guest_title="VP Growth",
        date="2024-01-01",
        topics=["Growth", "PMF"],
        utterances=[
            Utterance(
                speaker="Lenny Rachitsky",
                timestamp_start="00:00:10",
                timestamp_end="00:00:30",
                text="Welcome. How do you define product-market fit?"
            ),
            Utterance(
                speaker="Growth Expert",
                timestamp_start="00:00:31",
                timestamp_end="00:01:15",
                text="Product-market fit is when 40% of survey respondents say they would be very disappointed without your product."
            )
        ]
    )

def test_transcript_parser():
    episodes = TranscriptParser.load_all_transcripts(settings.TRANSCRIPTS_PATH)
    assert len(episodes) >= 4
    for ep in episodes:
        assert ep.episode_id is not None
        assert ep.title is not None
        assert ep.guest is not None
        assert len(ep.utterances) > 0

def test_transcript_chunker(sample_episode):
    chunker = TranscriptChunker(target_chunk_size=100, overlap_size=20)
    chunks = chunker.chunk_episode(sample_episode)
    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.episode_id == "ep-test"
    assert "Growth Expert" in chunk.speaker or "Growth Expert" in chunk.full_content
    assert chunk.timestamp_start == "00:00:10"
    assert chunk.timestamp_end == "00:01:15"
    assert "Test Growth Strategy" in chunk.contextual_header

def test_embedding_provider():
    provider = LocalDenseEmbeddingProvider(dimension=384)
    texts = ["Product-led growth and freemium loops", "Founder mode and design reviews"]
    embeddings = provider.embed_texts(texts)
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384

    # Different text should have distinct embeddings
    assert embeddings[0] != embeddings[1]

def test_vector_store_and_search(tmp_path, sample_episode):
    store = PersistentVectorStore(storage_path=tmp_path)
    chunker = TranscriptChunker()
    chunks = chunker.chunk_episode(sample_episode)
    
    provider = LocalDenseEmbeddingProvider()
    embeddings = provider.embed_texts([c.full_content for c in chunks])
    
    store.add_chunks(chunks, embeddings)
    assert store.count() == len(chunks)
    
    # Query search
    q_emb = provider.embed_query("product-market fit survey 40%")
    results = store.search(q_emb, top_k=1)
    assert len(results) == 1
    matched_chunk, score = results[0]
    assert matched_chunk.episode_id == "ep-test"
    assert score > 0.0

def test_hybrid_retriever():
    store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
    provider = LocalDenseEmbeddingProvider()
    retriever = HybridRetriever(vector_store=store, embedding_provider=provider)

    # Test retrieval for Founder Mode
    results = retriever.retrieve("What is Founder mode and how does Brian Chesky run Airbnb?", top_k=2)
    assert len(results) > 0
    top_chunk, rrf_score, breakdown = results[0]
    assert top_chunk.guest == "Brian Chesky"
    assert "Founder Mode" in top_chunk.full_content
    assert rrf_score > 0

    # Test retrieval for Elena Verna / PLG
    results_plg = retriever.retrieve("Product-Led Growth freemium vs free trial", top_k=2)
    assert len(results_plg) > 0
    top_plg_chunk, _, _ = results_plg[0]
    assert top_plg_chunk.guest == "Elena Verna"

def test_grounding_citations():
    store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
    provider = LocalDenseEmbeddingProvider()
    retriever = HybridRetriever(vector_store=store, embedding_provider=provider)

    results = retriever.retrieve("How does Shreyas Doshi define High Agency and LNO framework?", top_k=2)
    citations = GroundingEngine.build_citations(results)
    
    assert len(citations) > 0
    cit = citations[0]
    assert cit.index == 1
    assert "SHREYAS DOSHI" in cit.badge.upper()
    assert cit.episode_id == "ep-95"
    assert len(cit.quote_snippet) > 0

    grounded_context = GroundingEngine.format_grounded_context(results)
    assert "SOURCE [1]" in grounded_context
    assert "Shreyas Doshi" in grounded_context
