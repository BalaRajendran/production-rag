import json

from openai import AsyncOpenAI

from ..core.config import settings
from ..models.models import GeneratedQuery, Message


class QueryGenerationService:
    """
    Generates multiple query variants from conversation context.

    Based on blog learning #1: Query Generation
    - Reviews conversation thread
    - Generates semantic + keyword queries
    - Covers larger surface area for retrieval
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model

    async def generate_queries(
        self, current_query: str, conversation_history: list[Message] | None = None
    ) -> list[GeneratedQuery]:
        """
        Generate multiple query variants based on conversation context.

        Args:
            current_query: The user's current question
            conversation_history: Previous conversation messages

        Returns:
            List of generated queries (semantic + keyword)
        """
        # If no history, just return the original query
        if not conversation_history or len(conversation_history) == 0:
            return [
                GeneratedQuery(query=current_query, query_type="semantic"),
                GeneratedQuery(query=self._extract_keywords(current_query), query_type="keyword"),
            ]

        # Generate queries using LLM with conversation context
        prompt = self._build_query_generation_prompt(current_query, conversation_history)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )

            content = response.choices[0].message.content
            queries = self._parse_generated_queries(content)

            # Ensure we have at least the original query
            if not queries:
                queries = [GeneratedQuery(query=current_query, query_type="semantic")]

            # Add keyword variant
            queries.append(
                GeneratedQuery(query=self._extract_keywords(current_query), query_type="keyword")
            )

            return queries[: settings.max_queries_generated]

        except Exception:
            # Fallback to original query
            return [
                GeneratedQuery(query=current_query, query_type="semantic"),
                GeneratedQuery(query=self._extract_keywords(current_query), query_type="keyword"),
            ]

    def _build_query_generation_prompt(
        self, current_query: str, conversation_history: list[Message]
    ) -> str:
        """Build prompt for query generation."""
        conversation_text = "\n".join(
            [f"{msg.role}: {msg.content}" for msg in conversation_history[-5:]]  # Last 5 messages
        )

        return f"""Given the conversation history and current query, generate 3-5 semantic search queries that capture different aspects of what the user is looking for.

Conversation History:
{conversation_text}

Current Query: {current_query}

Generate queries that:
1. Capture the main intent
2. Include relevant context from conversation history
3. Rephrase using synonyms and related terms
4. Break down multi-part questions

Return ONLY a JSON array of query strings, nothing else.
Example: ["query 1", "query 2", "query 3"]
"""

    def _parse_generated_queries(self, content: str) -> list[GeneratedQuery]:
        """Parse LLM response into GeneratedQuery objects."""
        try:
            # Try to parse as JSON array
            queries = json.loads(content)
            if isinstance(queries, list):
                return [
                    GeneratedQuery(query=q, query_type="semantic")
                    for q in queries
                    if isinstance(q, str) and q.strip()
                ]
        except json.JSONDecodeError:
            # If not valid JSON, try to extract queries line by line
            lines = content.strip().split("\n")
            queries = []
            for line in lines:
                line = line.strip()
                # Remove common prefixes
                for prefix in ["- ", "* ", "1. ", "2. ", "3. ", "4. ", "5. "]:
                    if line.startswith(prefix):
                        line = line[len(prefix) :].strip()

                if line and len(line) > 10:  # Reasonable query length
                    queries.append(GeneratedQuery(query=line, query_type="semantic"))

            return queries

        return []

    def _extract_keywords(self, query: str) -> str:
        """
        Extract keywords from query for keyword search.
        Simple implementation - can be enhanced with NLP.
        """
        # Remove common stop words and keep important terms
        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "has",
            "he",
            "in",
            "is",
            "it",
            "its",
            "of",
            "on",
            "that",
            "the",
            "to",
            "was",
            "will",
            "with",
            "what",
            "when",
            "where",
            "who",
            "why",
            "how",
        }

        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return " ".join(keywords)
