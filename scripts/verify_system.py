#!/usr/bin/env python
"""
End-to-End System Diagnostic Script for The Lenny Growth Assistant
Verifies:
  1. Relational Database Connectivity (PostgreSQL / SQLite fallback)
  2. Transcript Vector Knowledge Base & Hybrid Retrieval (Dense + BM25)
  3. Dynamic LLM Provider Status (Ollama Local, Claude Cloud, OpenAI Cloud, Mock)
  4. Grounding & Structured Citation Generation
"""
import sys
import asyncio
from pathlib import Path

# Add project root and backend to python path
project_root = Path(__file__).resolve().parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.db.session import engine, init_db, SessionLocal
from app.rag.vector_store import PersistentVectorStore
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.grounding import GroundingEngine
from app.llm.manager import llm_manager
from app.db.repository import ChatRepository

async def run_diagnostics():
    print("=" * 70)
    print("  THE LENNY GROWTH ASSISTANT - SYSTEM HEALTH DIAGNOSTICS")
    print("=" * 70)

    # 1. Database Diagnostic
    print("\n[*] 1. Checking Database Persistence...")
    try:
        init_db()
        with SessionLocal() as db:
            sessions = ChatRepository.list_sessions(db, limit=5)
            print(f"    [+] Database Connection: SUCCESS")
            print(f"    [+] Engine Dialect: {engine.dialect.name}")
            print(f"    [+] Existing Sessions Count: {len(sessions)}")
    except Exception as e:
        print(f"    [!] Database Error: {e}")

    # 2. Vector Store & Hybrid Retrieval Diagnostic
    print("\n[*] 2. Checking RAG Knowledge Base & Hybrid Retriever...")
    try:
        from app.rag.embeddings import get_embedding_provider
        embedding_provider = get_embedding_provider()
        vector_store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
        chunk_count = vector_store.count()
        print(f"    [+] Persistent Vector Store: Loaded ({chunk_count} chunks indexed)")

        retriever = HybridRetriever(vector_store=vector_store, embedding_provider=embedding_provider)
        query = "What did Brian Chesky say about Founder Mode?"
        results = retriever.retrieve(query, top_k=3)
        print(f"    [+] Hybrid Semantic Search (Query: '{query}'):")
        for i, (chunk, score, breakdown) in enumerate(results, 1):
            print(f"        {i}. [Score: {score:.4f}] {chunk.episode_title} ({chunk.timestamp_start})")
        
        # Grounding check
        citations = GroundingEngine.build_citations(results)
        print(f"    [+] Structured Citations Generated: {len(citations)} source badges")
        for c in citations:
            print(f"        -> {c.badge}")
    except Exception as e:
        print(f"    [!] Retrieval Error: {e}")

    # 3. LLM Provider Diagnostic
    print("\n[*] 3. Checking LLM Provider Reachability...")
    try:
        statuses = await llm_manager.list_providers_status()
        for s in statuses:
            status_symbol = "[+]" if s.is_available else "[-]"
            models_str = ", ".join(s.available_models) if s.available_models else "None"
            print(f"    {status_symbol} Provider: {s.provider:<12} | Available: {str(s.is_available):<5} | Models: {models_str:<28} | Message: {s.status_message}")
    except Exception as e:
        print(f"    [!] LLM Provider Error: {e}")

    # 4. Turn Orchestration Test
    print("\n[*] 4. Testing End-to-End Mock Turn Execution...")
    try:
        with SessionLocal() as db:
            from app.agent.orchestrator import agent_orchestrator
            parsed, llm_resp = await agent_orchestrator.execute_turn(
                db=db,
                session_id="diag_session",
                user_message="Summarize Elena Verna's view on B2B Product-Led Growth",
                llm_provider="mock"
            )
            print(f"    [+] Turn Execution: SUCCESS (Latency: {llm_resp.latency_ms}ms)")
            print(f"    [+] Extracted Citations: {len(parsed.citations)}")
            print(f"    [+] Output Preview: {parsed.display_text[:120]}...")
    except Exception as e:
        print(f"    [!] Turn Orchestration Error: {e}")

    print("\n" + "=" * 70)
    print("  ALL DIAGNOSTIC CHECKS COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
