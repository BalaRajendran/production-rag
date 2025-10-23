import re

from openai import AsyncOpenAI

from ..core.config import settings
from ..models.models import QueryType


class QueryRouter:
    """
    Routes queries to appropriate handling strategy.

    Based on blog learning #5: Query routing
    - Detects questions that can't be answered by RAG
    - Routes to appropriate handler (summarization, metadata query, etc.)
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.llm_model

    async def route_query(self, query: str) -> tuple[QueryType, str]:
        """
        Determine the type of query and return routing decision.

        Args:
            query: The user's question

        Returns:
            Tuple of (QueryType, explanation)
        """
        # First, try pattern-based routing (fast)
        pattern_result = self._pattern_based_routing(query)
        if pattern_result:
            return pattern_result

        # If patterns don't match, use LLM for classification
        return await self._llm_based_routing(query)

    def _pattern_based_routing(self, query: str) -> tuple[QueryType, str] | None:
        """
        Fast pattern-based routing for common query types.
        """
        query_lower = query.lower().strip()

        # Summarization patterns
        summarization_patterns = [
            r"\bsummarize\b",
            r"\bsummary\b",
            r"\bgive me (a|an) (overview|summary)\b",
            r"\bwhat (is|are) the (main|key) (points|ideas)\b",
            r"\btl;?dr\b",
        ]

        for pattern in summarization_patterns:
            if re.search(pattern, query_lower):
                return (QueryType.SUMMARIZATION, "Query requests summarization")

        # Metadata query patterns
        metadata_patterns = [
            r"\bwho (wrote|authored|created)\b",
            r"\bwhen (was|did)\b.*\b(written|published|created)\b",
            r"\bwhat (is|are) the (author|title|date|source)\b",
            r"\blist (all )?(authors|titles|documents|sources)\b",
        ]

        for pattern in metadata_patterns:
            if re.search(pattern, query_lower):
                return (QueryType.METADATA_QUERY, "Query is about document metadata")

        # If no patterns match, return None to trigger LLM routing
        return None

    async def _llm_based_routing(self, query: str) -> tuple[QueryType, str]:
        """
        Use LLM to classify query type for ambiguous cases.
        """
        prompt = f"""Classify the following user query into one of these categories:

1. RAG - Questions that require searching through documents and extracting specific information
2. SUMMARIZATION - Requests to summarize content, provide overview, or extract key points
3. METADATA_QUERY - Questions about document properties (author, date, source, title)
4. GENERAL - General questions or conversational queries

User Query: {query}

Respond with ONLY the category name (RAG, SUMMARIZATION, METADATA_QUERY, or GENERAL) and a brief explanation separated by a pipe |.
Example: RAG | Query asks about specific information in documents
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=100,
            )

            content = response.choices[0].message.content
            if not content:
                return QueryType.RAG, "Default routing due to empty response"

            content = content.strip()

            # Parse response
            if "|" in content:
                category, explanation = content.split("|", 1)
                category = category.strip().upper()
                explanation = explanation.strip()
            else:
                category = content.strip().upper()
                explanation = "LLM classification"

            # Map to QueryType
            category_map = {
                "RAG": QueryType.RAG,
                "SUMMARIZATION": QueryType.SUMMARIZATION,
                "METADATA_QUERY": QueryType.METADATA_QUERY,
            }
            query_type = category_map.get(category, QueryType.GENERAL)
            return query_type, explanation

        except Exception:
            # Default to RAG on error
            return QueryType.RAG, "Default routing due to classification error"

    async def should_use_rag(self, query: str) -> bool:
        """
        Quick check if query should use full RAG pipeline.

        Returns:
            True if query should use RAG, False otherwise
        """
        query_type, _ = await self.route_query(query)
        return query_type == QueryType.RAG
