from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.rag.parser import Episode, Utterance

class Chunk(BaseModel):
    chunk_id: str
    episode_id: str
    episode_title: str
    guest: str
    speaker: str
    timestamp_start: str
    timestamp_end: str
    text: str
    contextual_header: str
    full_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TranscriptChunker:
    """Chunks podcast episodes into semantically coherent segments with speaker and timestamp attribution."""

    def __init__(self, target_chunk_size: int = 450, overlap_size: int = 100):
        self.target_chunk_size = target_chunk_size
        self.overlap_size = overlap_size

    def chunk_episode(self, episode: Episode) -> List[Chunk]:
        chunks: List[Chunk] = []

        if not episode.utterances:
            return chunks

        current_utterances: List[Utterance] = []
        current_word_count = 0
        chunk_idx = 0

        for utt in episode.utterances:
            words = utt.text.split()
            utt_word_count = len(words)

            current_utterances.append(utt)
            current_word_count += utt_word_count

            # When accumulated text reaches or exceeds target chunk size
            if current_word_count >= self.target_chunk_size:
                chunk = self._create_chunk(episode, current_utterances, chunk_idx)
                chunks.append(chunk)
                chunk_idx += 1

                # Keep overlap utterances from the end
                overlap_utterances: List[Utterance] = []
                overlap_words = 0
                for prev_utt in reversed(current_utterances):
                    prev_count = len(prev_utt.text.split())
                    if overlap_words + prev_count <= self.overlap_size:
                        overlap_utterances.insert(0, prev_utt)
                        overlap_words += prev_count
                    else:
                        break

                current_utterances = overlap_utterances
                current_word_count = overlap_words

        # Flush remaining utterances
        if current_utterances:
            chunk = self._create_chunk(episode, current_utterances, chunk_idx)
            chunks.append(chunk)

        return chunks

    def _create_chunk(self, episode: Episode, utterances: List[Utterance], index: int) -> Chunk:
        speakers = list(dict.fromkeys([u.speaker for u in utterances]))
        speaker_str = ", ".join(speakers)
        start_time = utterances[0].timestamp_start
        end_time = utterances[-1].timestamp_end

        # Format utterance body
        body_lines = [f"{u.speaker} ({u.timestamp_start}): {u.text}" for u in utterances]
        text_body = "\n\n".join(body_lines)

        header = f"[Lenny's Podcast | Episode: {episode.title} | Guest: {episode.guest} | Time: {start_time} - {end_time}]"
        full_content = f"{header}\n\n{text_body}"

        metadata = {
            "episode_id": episode.episode_id,
            "title": episode.title,
            "guest": episode.guest,
            "speakers": speakers,
            "timestamp_start": start_time,
            "timestamp_end": end_time,
            "topics": episode.topics,
            "chunk_index": index
        }

        return Chunk(
            chunk_id=f"{episode.episode_id}_chunk_{index}",
            episode_id=episode.episode_id,
            episode_title=episode.title,
            guest=episode.guest,
            speaker=speaker_str,
            timestamp_start=start_time,
            timestamp_end=end_time,
            text=text_body,
            contextual_header=header,
            full_content=full_content,
            metadata=metadata
        )

    def chunk_all(self, episodes: List[Episode]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        for ep in episodes:
            all_chunks.extend(self.chunk_episode(ep))
        return all_chunks
