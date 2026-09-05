import json
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field

class Utterance(BaseModel):
    speaker: str
    timestamp_start: str
    timestamp_end: str
    text: str

class Episode(BaseModel):
    episode_id: str
    title: str
    guest: str
    guest_title: Optional[str] = None
    date: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    utterances: List[Utterance] = Field(default_factory=list)
    raw_content: Optional[str] = None

class TranscriptParser:
    """Parses raw podcast transcript files into structured Episode representations."""

    @staticmethod
    def parse_file(file_path: Path) -> Episode:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Transcript file not found: {path}")

        if path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Episode(**data)
        elif path.suffix.lower() in [".txt", ".md"]:
            return TranscriptParser._parse_text_file(path)
        else:
            raise ValueError(f"Unsupported transcript format: {path.suffix}")

    @staticmethod
    def _parse_text_file(path: Path) -> Episode:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        filename = path.stem
        # Extract basic metadata from filename and raw text
        return Episode(
            episode_id=filename,
            title=filename.replace("_", " ").title(),
            guest="Unknown Guest",
            date=None,
            topics=[],
            utterances=[
                Utterance(
                    speaker="Speaker",
                    timestamp_start="00:00:00",
                    timestamp_end="00:00:00",
                    text=content
                )
            ],
            raw_content=content
        )

    @classmethod
    def load_all_transcripts(cls, directory_path: Path) -> List[Episode]:
        directory = Path(directory_path)
        if not directory.exists():
            return []
        
        episodes = []
        for file in sorted(directory.glob("*.json")):
            episodes.append(cls.parse_file(file))
        for file in sorted(directory.glob("*.txt")):
            episodes.append(cls.parse_file(file))
        for file in sorted(directory.glob("*.md")):
            episodes.append(cls.parse_file(file))
        return episodes
