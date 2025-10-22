from typing import List
from openai import AsyncOpenAI
from config import settings
from models import Chunk, Message


class LLMService:
    """
    Handles LLM interactions for answer generation.
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model

    async def generate_answer(
        self,
        query: str,
        chunks: List[Chunk],
        conversation_history: List[Message] = None
    ) -> str:
        """
        Generate answer using retrieved chunks and LLM.

        Args:
            query: User's question
            chunks: Retrieved and reranked chunks
            conversation_history: Previous conversation for context

        Returns:
            Generated answer
        """
        # Build context from chunks
        context = self._build_context(chunks)

        # Build messages for LLM
        messages = self._build_messages(query, context, conversation_history)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I apologize, but I encountered an error generating an answer. Please try again."

    async def generate_summarization(
        self,
        content: str,
        instruction: str = None
    ) -> str:
        """
        Generate summarization for content.

        Used for query routing when user asks for summary.
        """
        instruction = instruction or "Provide a comprehensive summary of the following content"

        prompt = f"""{instruction}:

{content}

Summary:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating summary: {e}")
            return "I apologize, but I encountered an error generating the summary."

    async def answer_metadata_query(
        self,
        query: str,
        chunks: List[Chunk]
    ) -> str:
        """
        Answer query about metadata (author, date, etc.).

        Used for query routing when user asks about metadata.
        """
        # Extract metadata from chunks
        metadata_list = [chunk.metadata for chunk in chunks]

        # Build metadata summary
        metadata_text = self._format_metadata_list(metadata_list)

        prompt = f"""Based on the following document metadata, answer this question: {query}

Metadata:
{metadata_text}

Answer:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error answering metadata query: {e}")
            return "I apologize, but I encountered an error answering your question."

    def _build_context(self, chunks: List[Chunk]) -> str:
        """
        Build context string from chunks.

        Based on blog learning #4: Metadata to LLM
        - Includes chunk text AND metadata for better context
        """
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Format metadata if available
            metadata_str = ""
            if chunk.metadata:
                metadata_parts = []
                if "title" in chunk.metadata:
                    metadata_parts.append(f"Title: {chunk.metadata['title']}")
                if "author" in chunk.metadata:
                    metadata_parts.append(f"Author: {chunk.metadata['author']}")
                if "source" in chunk.metadata:
                    metadata_parts.append(f"Source: {chunk.metadata['source']}")

                if metadata_parts:
                    metadata_str = " | ".join(metadata_parts) + "\n"

            context_parts.append(
                f"[Context {i}]\n{metadata_str}{chunk.text}\n"
            )

        return "\n".join(context_parts)

    def _build_messages(
        self,
        query: str,
        context: str,
        conversation_history: List[Message] = None
    ) -> List[dict]:
        """Build message list for LLM."""
        system_message = """You are a helpful AI assistant that answers questions based on the provided context.

Instructions:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so
3. Cite which context section(s) you used (e.g., "According to Context 1...")
4. Be concise but comprehensive
5. If metadata (title, author, source) is relevant, include it in your answer
"""

        messages = [{"role": "system", "content": system_message}]

        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Add current query with context
        user_message = f"""Context:
{context}

Question: {query}

Answer:"""

        messages.append({"role": "user", "content": user_message})

        return messages

    def _format_metadata_list(self, metadata_list: List[dict]) -> str:
        """Format metadata list for metadata queries."""
        formatted = []

        for i, metadata in enumerate(metadata_list, 1):
            parts = [f"Document {i}:"]
            if "title" in metadata:
                parts.append(f"  Title: {metadata['title']}")
            if "author" in metadata:
                parts.append(f"  Author: {metadata['author']}")
            if "source" in metadata:
                parts.append(f"  Source: {metadata['source']}")
            if "date" in metadata:
                parts.append(f"  Date: {metadata['date']}")

            formatted.append("\n".join(parts))

        return "\n\n".join(formatted)
