from typing import List, Tuple, Dict, Any, Optional
from app.rag.grounding import GroundingEngine, Citation
from app.rag.chunker import Chunk
from app.agent.prompts import GROUNDED_QA_SYSTEM_PROMPT

class GroundedQASkill:
    """Skill 1: Conversational Q&A grounded strictly in Lenny's Podcast transcripts."""

    @staticmethod
    def build_prompt_context(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]]) -> str:
        return GroundingEngine.format_grounded_context(retrieval_results)

    @staticmethod
    def format_system_prompt(grounded_context: str) -> str:
        return (
            f"{GROUNDED_QA_SYSTEM_PROMPT}\n\n"
            f"=== RETRIEVED PODCAST TRANSCRIPTS (YOUR SOURCE OF TRUTH) ===\n"
            f"{grounded_context}\n"
            f"============================================================"
        )

    @staticmethod
    def create_citations(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]]) -> List[Citation]:
        return GroundingEngine.build_citations(retrieval_results)
