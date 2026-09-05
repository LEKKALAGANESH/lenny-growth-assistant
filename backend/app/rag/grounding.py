from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field
from app.rag.chunker import Chunk

class Citation(BaseModel):
    index: int
    badge: str
    episode_id: str
    episode_title: str
    guest: str
    timestamp_start: str
    timestamp_end: str
    quote_snippet: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GroundingEngine:
    """Formats retrieved chunks into formatted citations and creates grounded prompt contexts."""

    @staticmethod
    def build_citations(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]]) -> List[Citation]:
        citations = []
        for i, (chunk, score, breakdown) in enumerate(retrieval_results, 1):
            badge = f"[{chunk.episode_id.upper()} • {chunk.guest} @ {chunk.timestamp_start}]"
            # Extract key snippet
            first_line = chunk.text.split("\n")[0] if chunk.text else ""
            snippet = (first_line[:180] + "...") if len(first_line) > 180 else first_line

            citation = Citation(
                index=i,
                badge=badge,
                episode_id=chunk.episode_id,
                episode_title=chunk.episode_title,
                guest=chunk.guest,
                timestamp_start=chunk.timestamp_start,
                timestamp_end=chunk.timestamp_end,
                quote_snippet=snippet,
                score=score,
                metadata={
                    "breakdown": breakdown,
                    "header": chunk.contextual_header,
                    "speakers": chunk.metadata.get("speakers", [])
                }
            )
            citations.append(citation)
        return citations

    @staticmethod
    def format_grounded_context(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]]) -> str:
        """
        Builds the structured grounded reference block injected into the LLM system prompt.
        """
        if not retrieval_results:
            return "NO RELEVANT PODCAST TRANSCRIPTS FOUND IN KNOWLEDGE BASE."

        context_blocks = []
        for i, (chunk, score, _) in enumerate(retrieval_results, 1):
            block = (
                f"--- SOURCE [{i}]: {chunk.episode_title} (Guest: {chunk.guest}) ---\n"
                f"Episode ID: {chunk.episode_id} | Timestamps: {chunk.timestamp_start} to {chunk.timestamp_end}\n"
                f"{chunk.text}\n"
            )
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

    @staticmethod
    def is_sufficient_evidence(retrieval_results: List[Tuple[Chunk, float, Dict[str, float]]], min_score: float = 0.005) -> bool:
        """Determines if the retrieved context meets the minimum threshold to answer."""
        if not retrieval_results:
            return False
        top_score = retrieval_results[0][1]
        return top_score >= min_score
