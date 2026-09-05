import time
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.repository import ChatRepository
from app.rag.vector_store import PersistentVectorStore
from app.rag.embeddings import get_embedding_provider
from app.rag.hybrid_retriever import HybridRetriever
from app.rag.grounding import GroundingEngine
from app.llm.base import ChatMessage, LLMResponse
from app.llm.manager import llm_manager
from app.agent.prompts import GROUNDED_QA_SYSTEM_PROMPT
from app.agent.skills.grounded_qa import GroundedQASkill
from app.agent.skills.ship30_essay import Ship30EssaySkill
from app.agent.skills.artifact_tool import ArtifactToolSkill
from app.agent.parser import AgentStreamParser, ParsedAgentResponse

class GrowthAgentOrchestrator:
    """
    Main Agentic Orchestrator for The Lenny Growth Assistant.
    Coordinates session memory, hybrid RAG retrieval, skill routing,
    token streaming, artifact extraction, and database persistence.
    """
    def __init__(self):
        self.vector_store = PersistentVectorStore(storage_path=settings.STORAGE_PATH)
        self.embedding_provider = get_embedding_provider(
            provider_name="local",
            ollama_url=settings.OLLAMA_BASE_URL,
            openai_key=settings.OPENAI_API_KEY
        )
        self.retriever = HybridRetriever(
            vector_store=self.vector_store,
            embedding_provider=self.embedding_provider,
            dense_weight=settings.DENSE_WEIGHT,
            sparse_weight=settings.SPARSE_WEIGHT
        )

    def classify_intent(self, user_query: str, skill_override: Optional[str] = None) -> str:
        """Determines if the query is a Ship 30 essay, an Artifact request, or standard Grounded QA."""
        if skill_override:
            return skill_override.lower()

        q_lower = user_query.lower()
        if any(term in q_lower for term in ["ship 30", "ship30", "write an essay", "write a 1250", "essay on", "publishable essay"]):
            return "ship30_essay"
        elif any(term in q_lower for term in ["create an artifact", "calculator", "dashboard", "html widget", "interactive tool", "generate code", "prd template"]):
            return "artifact"
        return "grounded_qa"

    async def execute_turn(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        llm_provider: Optional[str] = None,
        skill_override: Optional[str] = None,
        top_k: int = 4
    ) -> Tuple[ParsedAgentResponse, LLMResponse]:
        """
        Executes a complete synchronous turn, updates the database, and returns the parsed response.
        """
        start_time = time.time()
        
        # 1. Fetch Session & History
        session = ChatRepository.get_session(db, session_id)
        if not session:
            session = ChatRepository.create_session(db, title="New Chat", llm_provider=llm_provider or "ollama")
            session_id = session.id

        # 2. Persist User Message
        user_msg_record = ChatRepository.add_message(db, session_id, role="user", content=user_message)

        # 3. Hybrid RAG Retrieval
        retrieval_results = self.retriever.retrieve(user_message, top_k=top_k)
        citations_data = [c.model_dump() for c in GroundingEngine.build_citations(retrieval_results)]
        grounded_context = GroundingEngine.format_grounded_context(retrieval_results)

        # 4. Route Skill & Build System Prompt
        intent = self.classify_intent(user_message, skill_override)
        if intent == "ship30_essay":
            system_prompt = Ship30EssaySkill.format_system_prompt(grounded_context)
        elif intent == "artifact":
            system_prompt = ArtifactToolSkill.format_system_prompt(grounded_context)
        else:
            system_prompt = GroundedQASkill.format_system_prompt(grounded_context)

        # 5. Build Message Buffer (Context Window)
        past_messages = ChatRepository.get_session_messages(db, session_id)
        llm_messages = []
        for msg in past_messages[-8:]:  # Sliding window of last 8 turns
            llm_messages.append(ChatMessage(role=msg.role, content=msg.content))

        # 6. Generate via LLM Gateway
        provider_name = llm_provider or session.llm_provider or settings.DEFAULT_LLM_PROVIDER
        llm_resp = await llm_manager.generate_with_fallback(
            preferred_provider=provider_name,
            messages=llm_messages,
            system_prompt=system_prompt
        )

        # 7. Parse Artifacts & Format Display
        parsed = AgentStreamParser.parse_response(llm_resp.content, citations=citations_data)

        # 8. Persist Assistant Message & Artifacts in DB
        assistant_msg = ChatRepository.add_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=parsed.display_text,
            citations=citations_data
        )

        for art in parsed.artifacts:
            ChatRepository.create_artifact(
                db=db,
                session_id=session_id,
                title=art.title,
                type=art.type,
                content=art.content,
                message_id=assistant_msg.id if assistant_msg else None
            )

        # 9. Audit Logging
        latency = round((time.time() - start_time) * 1000, 2)
        ChatRepository.log_audit(
            db=db,
            event_type="chat_turn",
            payload={
                "session_id": session_id,
                "provider": llm_resp.provider,
                "model": llm_resp.model,
                "intent": intent,
                "retrieved_chunks": len(retrieval_results),
                "artifacts_created": len(parsed.artifacts),
                "is_fallback": llm_resp.is_fallback
            },
            latency_ms=latency
        )

        return parsed, llm_resp

    async def stream_turn(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        llm_provider: Optional[str] = None,
        skill_override: Optional[str] = None,
        top_k: int = 4
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens in SSE format and auto-persists completed state at end.
        """
        # 1. Fetch Session
        session = ChatRepository.get_session(db, session_id)
        if not session:
            session = ChatRepository.create_session(db, title="New Chat", llm_provider=llm_provider or "ollama")
            session_id = session.id

        # 2. Persist User Message
        user_msg_record = ChatRepository.add_message(db, session_id, role="user", content=user_message)

        # 3. Hybrid RAG Retrieval
        retrieval_results = self.retriever.retrieve(user_message, top_k=top_k)
        citations_data = [c.model_dump() for c in GroundingEngine.build_citations(retrieval_results)]
        grounded_context = GroundingEngine.format_grounded_context(retrieval_results)

        # 4. Route Skill
        intent = self.classify_intent(user_message, skill_override)
        if intent == "ship30_essay":
            system_prompt = Ship30EssaySkill.format_system_prompt(grounded_context)
        elif intent == "artifact":
            system_prompt = ArtifactToolSkill.format_system_prompt(grounded_context)
        else:
            system_prompt = GroundedQASkill.format_system_prompt(grounded_context)

        # 5. Build Messages
        past_messages = ChatRepository.get_session_messages(db, session_id)
        llm_messages = [ChatMessage(role=m.role, content=m.content) for m in past_messages[-8:]]

        # 6. Stream from LLM Manager
        provider_name = llm_provider or session.llm_provider or settings.DEFAULT_LLM_PROVIDER
        accumulated_text = ""

        async for chunk in llm_manager.stream_with_fallback(
            preferred_provider=provider_name,
            messages=llm_messages,
            system_prompt=system_prompt
        ):
            accumulated_text += chunk
            yield chunk

        # 7. Post-Stream DB Persistence
        parsed = AgentStreamParser.parse_response(accumulated_text, citations=citations_data)
        assistant_msg = ChatRepository.add_message(
            db=db,
            session_id=session_id,
            role="assistant",
            content=parsed.display_text,
            citations=citations_data
        )

        for art in parsed.artifacts:
            ChatRepository.create_artifact(
                db=db,
                session_id=session_id,
                title=art.title,
                type=art.type,
                content=art.content,
                message_id=assistant_msg.id if assistant_msg else None
            )

# Global singleton
agent_orchestrator = GrowthAgentOrchestrator()
