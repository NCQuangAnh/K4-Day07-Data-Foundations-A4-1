from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        step = max(1, step)
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        normalized_text = re.sub(r"\s+", " ", text).strip()
        if not normalized_text:
            return []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalized_text) if s.strip()]
        if not sentences:
            return []

        chunks: list[str] = []
        for index in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[index : index + self.max_sentences_per_chunk]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        normalized_text = re.sub(r"\s+", " ", text).strip()
        if len(normalized_text) <= self.chunk_size:
            return [normalized_text]
        return self._split(normalized_text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [current_text[index : index + self.chunk_size] for index in range(0, len(current_text), self.chunk_size)]

        separator = remaining_separators[0]
        if separator == "":
            return [current_text[index : index + self.chunk_size] for index in range(0, len(current_text), self.chunk_size)]

        parts = [part.strip() for part in current_text.split(separator) if part.strip()]
        if len(parts) > 1:
            chunks: list[str] = []
            current_parts: list[str] = []
            for part in parts:
                candidate = " ".join(current_parts + [part]).strip()
                if len(candidate) <= self.chunk_size:
                    current_parts.append(part)
                else:
                    if current_parts:
                        chunks.append(" ".join(current_parts).strip())
                    current_parts = [part]
            if current_parts:
                chunks.append(" ".join(current_parts).strip())
            return chunks

        return self._split(current_text, remaining_separators[1:])


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in vec_b)) or 1.0
    denominator = norm_a * norm_b
    if denominator == 0:
        return 0.0
    return dot_product / denominator


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0)
        sentence = SentenceChunker(max_sentences_per_chunk=3)
        recursive = RecursiveChunker(chunk_size=chunk_size)

        strategies = {
            "fixed_size": fixed.chunk(text),
            "by_sentences": sentence.chunk(text),
            "recursive": recursive.chunk(text),
        }

        result: dict[str, dict] = {}
        for strategy_name, chunks in strategies.items():
            lengths = [len(chunk) for chunk in chunks]
            result[strategy_name] = {
                "count": len(chunks),
                "avg_length": sum(lengths) / len(lengths) if lengths else 0,
                "chunks": chunks,
            }
        return result
