import sys
from pathlib import Path
from app.core.config import settings
from app.rag.parser import TranscriptParser
from app.rag.chunker import TranscriptChunker
from app.rag.embeddings import get_embedding_provider
from app.rag.vector_store import PersistentVectorStore

def run_ingestion() -> dict:
    print("=" * 60)
    print("[*] Starting Lenny's Podcast Transcripts Ingestion Pipeline")
    print("=" * 60)
    print(f"Directory: {settings.TRANSCRIPTS_PATH}")
    print(f"Storage:   {settings.STORAGE_PATH}")

    # 1. Load raw transcripts
    episodes = TranscriptParser.load_all_transcripts(settings.TRANSCRIPTS_PATH)
    if not episodes:
        print(f"[!] No transcripts found in {settings.TRANSCRIPTS_PATH}")
        return {"status": "empty", "episodes": 0, "chunks": 0}

    print(f"[+] Loaded {len(episodes)} podcast episodes:")
    for ep in episodes:
        print(f"   - [{ep.episode_id}] {ep.title} ({ep.guest}) - {len(ep.utterances)} utterances")

    # 2. Chunk episodes
    chunker = TranscriptChunker(
        target_chunk_size=settings.CHUNK_SIZE_TOKENS,
        overlap_size=settings.CHUNK_OVERLAP_TOKENS
    )
    chunks = chunker.chunk_all(episodes)
    print(f"[+] Created {len(chunks)} contextual chunks.")

    # 3. Generate Embeddings
    print("[*] Computing dense vector embeddings...")
    embedding_provider = get_embedding_provider(
        provider_name="local",
        ollama_url=settings.OLLAMA_BASE_URL,
        openai_key=settings.OPENAI_API_KEY
    )
    texts_to_embed = [c.full_content for c in chunks]
    embeddings = embedding_provider.embed_texts(texts_to_embed)
    print(f"[+] Generated {len(embeddings)} embeddings (dim: {len(embeddings[0]) if embeddings else 0}).")

    # 4. Save to Persistent Vector Store
    vector_store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
    vector_store.clear()
    vector_store.add_chunks(chunks, embeddings)
    print(f"[+] Successfully persisted {vector_store.count()} chunks to vector index.")

    summary = {
        "status": "success",
        "episodes_count": len(episodes),
        "chunks_count": len(chunks),
        "embedding_dim": len(embeddings[0]) if embeddings else 0,
        "storage_file": str(vector_store.index_file)
    }
    print("=" * 60)
    print("[+] Ingestion Complete!")
    print("=" * 60)
    return summary

if __name__ == "__main__":
    run_ingestion()
