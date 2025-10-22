from typing import List, Dict, Any
import tiktoken
from config import settings


class ChunkingService:
    """
    Handles document chunking with configurable strategies.

    Based on blog learning #3: Chunking Strategy
    - Ensures no mid-word/sentence cuts
    - Each chunk is a logical unit
    - Captures information standalone
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces with overlap.

        Args:
            text: The text to chunk
            metadata: Metadata to attach to each chunk

        Returns:
            List of chunks with text and metadata
        """
        if not text or not text.strip():
            return []

        # Split into sentences first to avoid mid-sentence cuts
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))

            # If single sentence exceeds chunk size, split it
            if sentence_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, metadata))
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence by tokens
                chunks.extend(self._split_long_sentence(sentence, metadata))
                continue

            # If adding this sentence exceeds chunk size, save current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunks.append(self._create_chunk(current_chunk, metadata))

                # Keep last few sentences for overlap
                overlap_sentences = self._get_overlap_sentences(
                    current_chunk,
                    self.chunk_overlap
                )
                current_chunk = overlap_sentences
                current_tokens = sum(
                    len(self.encoding.encode(s)) for s in current_chunk
                )

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add remaining chunk
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, metadata))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences, handling common abbreviations."""
        # Simple sentence splitting (can be enhanced with spaCy/NLTK)
        import re

        # Add space after sentence endings if not present
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)

        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)

        return [s.strip() for s in sentences if s.strip()]

    def _split_long_sentence(
        self,
        sentence: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Split a sentence that exceeds chunk size."""
        tokens = self.encoding.encode(sentence)
        chunks = []

        for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            chunks.append({
                "text": chunk_text.strip(),
                "metadata": metadata or {},
                "token_count": len(chunk_tokens)
            })

        return chunks

    def _get_overlap_sentences(
        self,
        sentences: List[str],
        max_overlap_tokens: int
    ) -> List[str]:
        """Get sentences for overlap from the end of current chunk."""
        overlap = []
        overlap_tokens = 0

        for sentence in reversed(sentences):
            sentence_tokens = len(self.encoding.encode(sentence))
            if overlap_tokens + sentence_tokens <= max_overlap_tokens:
                overlap.insert(0, sentence)
                overlap_tokens += sentence_tokens
            else:
                break

        return overlap

    def _create_chunk(
        self,
        sentences: List[str],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a chunk from sentences with metadata."""
        text = " ".join(sentences)
        return {
            "text": text.strip(),
            "metadata": metadata or {},
            "token_count": len(self.encoding.encode(text))
        }

    def chunk_with_metadata_injection(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text and inject relevant metadata into each chunk.

        Based on blog learning #4: Metadata to LLM
        - Injects title, author, and other metadata into chunk text
        """
        chunks = self.chunk_text(text, metadata)

        if not metadata:
            return chunks

        # Inject metadata into chunk text for better context
        for chunk in chunks:
            metadata_prefix = self._format_metadata(metadata)
            if metadata_prefix:
                chunk["text"] = f"{metadata_prefix}\n\n{chunk['text']}"

        return chunks

    def _format_metadata(self, metadata: Dict[str, Any]) -> str:
        """Format metadata for injection into chunk text."""
        if not metadata:
            return ""

        parts = []
        if "title" in metadata:
            parts.append(f"Title: {metadata['title']}")
        if "author" in metadata:
            parts.append(f"Author: {metadata['author']}")
        if "source" in metadata:
            parts.append(f"Source: {metadata['source']}")
        if "date" in metadata:
            parts.append(f"Date: {metadata['date']}")

        return " | ".join(parts) if parts else ""
