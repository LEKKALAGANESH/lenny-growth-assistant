from typing import List, Tuple, Dict, Any
from app.rag.grounding import GroundingEngine, Citation
from app.rag.chunker import Chunk
from app.agent.prompts import SHIP_30_FOR_30_SKILL_PROMPT

class Ship30EssaySkill:
    """Skill 2: Transforms podcast knowledge into structured ~1,250-word Ship 30 for 30 essays."""

    TARGET_WORD_COUNT = 1250
    MIN_WORD_COUNT = 900
    MAX_WORD_COUNT = 1600

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

    @classmethod
    def validate_word_count(cls, text: str) -> Dict[str, Any]:
        """
        The prompt asks the model for ~1,250 words, but nothing previously checked
        whether it actually delivered that — this is the enforcement/reporting step.
        """
        word_count = len(text.split())
        return {
            "word_count": word_count,
            "target_word_count": cls.TARGET_WORD_COUNT,
            "within_tolerance": cls.MIN_WORD_COUNT <= word_count <= cls.MAX_WORD_COUNT
        }
