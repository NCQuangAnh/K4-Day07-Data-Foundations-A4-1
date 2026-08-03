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
        if not text or not text.strip():
            return []

        # Keep the punctuation with the preceding sentence.  The expression is
        # deliberately small and predictable for the lab: it recognizes the
        # sentence boundaries described in the docstring without requiring a
        # language-specific NLP model.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:\s+)", text.strip())
            if sentence.strip()
        ]

        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


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
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            cleaned = current_text.strip()
            return [cleaned] if cleaned else []

        # Select the highest-priority separator that is actually present.  If
        # none is available, split on characters so progress is guaranteed.
        separator_index = next(
            (
                index
                for index, separator in enumerate(remaining_separators)
                if separator and separator in current_text
            ),
            None,
        )
        if separator_index is None:
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator = remaining_separators[separator_index]
        lower_priority = remaining_separators[separator_index + 1 :]
        pieces = current_text.split(separator)
        # Reattach separators to preserve the original text (especially full
        # stops and paragraph boundaries) while packing adjacent pieces.
        units = [
            piece + (separator if index < len(pieces) - 1 else "")
            for index, piece in enumerate(pieces)
            if piece or index < len(pieces) - 1
        ]

        chunks: list[str] = []
        current_chunk = ""
        for unit in units:
            if len(unit) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.extend(self._split(unit, lower_priority))
            elif len(current_chunk) + len(unit) <= self.chunk_size:
                current_chunk += unit
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = unit

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(sum(value * value for value in vec_a))
    norm_b = math.sqrt(sum(value * value for value in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0

    similarity = _dot(vec_a, vec_b) / (norm_a * norm_b)
    # Floating-point rounding can produce values infinitesimally outside the
    # mathematical cosine range.
    return max(-1.0, min(1.0, similarity))


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (sum(map(len, chunks)) / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
