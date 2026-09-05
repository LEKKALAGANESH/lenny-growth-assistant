from typing import List, Tuple, Dict, Any
from app.rag.grounding import GroundingEngine
from app.rag.chunker import Chunk
from app.agent.prompts import ARTIFACT_GENERATION_PROMPT, GROUNDED_QA_SYSTEM_PROMPT

class ArtifactToolSkill:
    """Skill 3: Generates interactive HTML/CSS widgets and structured Markdown documents."""

    @staticmethod
    def format_system_prompt(grounded_context: str) -> str:
        return (
            f"{GROUNDED_QA_SYSTEM_PROMPT}\n\n"
            f"{ARTIFACT_GENERATION_PROMPT}\n\n"
            f"=== EVIDENCE BASE FROM LENNY'S PODCAST ===\n"
            f"{grounded_context}\n"
            f"=========================================="
        )

    @staticmethod
    def sanitize_html_for_iframe(html_content: str) -> str:
        """
        Ensures HTML content is isolated and does not attempt window breaking.
        """
        # Strip potential parent-frame escaping attacks
        cleaned = html_content.replace("window.parent", "window")
        cleaned = cleaned.replace("top.location", "window.location")
        return cleaned
