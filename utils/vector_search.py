"""Vector search utilities using Pinecone and OpenAI embeddings."""

import os
from typing import List, Dict, Any
from pinecone import Pinecone
from openai import OpenAI
from utils.logger import research_logger as logger


class VectorSearch:
    """Vector search using Pinecone and OpenAI embeddings."""

    def __init__(self):
        """Initialize Pinecone and OpenAI client."""
        # Initialize Pinecone
        self.pc = Pinecone(
            api_key=os.getenv("PINECONE_API_KEY"),
            environment=os.getenv("PINECONE_ENVIRONMENT"),
        )

        self.index = self.pc.Index(os.getenv("PINECONE_INDEX_NAME"))
        self.openai_client = OpenAI()

    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small", input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.log_error("VectorSearch", e, "Error getting embedding from OpenAI")
            raise

    def add_query(self, query: str, metadata: Dict[str, Any]):
        """Add a query and its metadata to the vector store."""
        try:
            # Generate embedding using OpenAI
            embedding = self._get_embedding(query)

            # Add to Pinecone
            self.index.upsert(
                vectors=[{"id": query, "values": embedding, "metadata": metadata}]
            )
        except Exception as e:
            logger.log_error("VectorSearch", e, "Error adding query to vector store")
            raise

    def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar queries."""
        try:
            # Generate embedding for the query using OpenAI
            query_embedding = self._get_embedding(query)

            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding, top_k=limit, include_metadata=True
            )

            # Format results
            similar_queries = []
            for match in results.matches:
                similar_queries.append(
                    {"query": match.id, "score": match.score, **match.metadata}
                )

            return similar_queries
        except Exception as e:
            logger.log_error("VectorSearch", e, "Error searching similar queries")
            return []
