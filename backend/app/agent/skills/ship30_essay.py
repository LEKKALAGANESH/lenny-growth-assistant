from typing import List, Tuple, Dict, Any
from app.rag.grounding import GroundingEngine, Citation
from app.rag.chunker import Chunk
from app.agent.prompts import SHIP_30_FOR_30_SKILL_PROMPT

class Ship30EssaySkill:
    """Skill 2: Transforms podcast knowledge into structured ~1,250-word Ship 30 for 30 essays."""

    @staticmethod
    def format_system_prompt(grounded_context: str) -> str:
        return (
            f"{SHIP_30_FOR_30_SKILL_PROMPT}\n\n"
            f"=== EVIDENCE BASE FROM LENNY'S PODCAST ===\n"
            f"{grounded_context}\n"
            f"=========================================="
        )

    @staticmethod
    def create_citations(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]]) -> List[Citation]:
        return GroundingEngine.build_citations(retrieval_results)
