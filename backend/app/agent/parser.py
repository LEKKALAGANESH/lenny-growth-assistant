import re
from typing import List, Tuple, Optional, Dict, Any
from pydantic import BaseModel

class ExtractedArtifact(BaseModel):
    title: str
    type: str  # "markdown", "html", "code"
    content: str

class ParsedAgentResponse(BaseModel):
    display_text: str
    raw_text: str
    artifacts: List[ExtractedArtifact]
    citations: List[Dict[str, Any]]

class AgentStreamParser:
    """
    Parses LLM output streams and completed responses to extract structured
    artifact blocks (<<<ARTIFACT title="..." type="...">>>...<<<END_ARTIFACT>>>).
    """
    ARTIFACT_REGEX = re.compile(
        r'<<<ARTIFACT\s+title=["\'](.*?)["\'](?:\s+type=["\'](.*?)["\'])?\s*>>>(.*?)<<<END_ARTIFACT>>>',
        re.DOTALL | re.IGNORECASE
    )

    @classmethod
    def parse_response(cls, text: str, citations: Optional[List[Dict[str, Any]]] = None) -> ParsedAgentResponse:
        artifacts: List[ExtractedArtifact] = []

        def replacer(match):
            title = match.group(1).strip()
            art_type = (match.group(2) or "markdown").strip().lower()
            content = match.group(3).strip()

            artifacts.append(
                ExtractedArtifact(
                    title=title,
                    type=art_type,
                    content=content
                )
            )
            return f"\n\n*[Generated Artifact: **{title}** (Rendered in side panel)]*\n\n"

        clean_text = cls.ARTIFACT_REGEX.sub(replacer, text).strip()

        # If no explicit delimiter was used but code block contains full HTML document
        if not artifacts and ("<!DOCTYPE html>" in text or "<html" in text):
            html_match = re.search(r'```(?:html)?\s*(<!DOCTYPE html>.*?|<html>.*?)```', text, re.DOTALL | re.IGNORECASE)
            if html_match:
                html_content = html_match.group(1).strip()
                artifacts.append(
                    ExtractedArtifact(
                        title="Interactive Growth Widget",
                        type="html",
                        content=html_content
                    )
                )

        return ParsedAgentResponse(
            display_text=clean_text if clean_text else text,
            raw_text=text,
            artifacts=artifacts,
            citations=citations or []
        )
