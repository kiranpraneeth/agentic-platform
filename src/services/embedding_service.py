"""Embedding service for generating vector embeddings."""

import asyncio
from typing import Any

from src.core.config import settings


class EmbeddingService:
    """Service for generating text embeddings.

    Supports both local models (sentence-transformers) and OpenAI API.
    Defaults to local models to avoid requiring API keys.
    """

    def __init__(self, model: str = "all-MiniLM-L6-v2", provider: str = "local"):
        """Initialize embedding service.

        Args:
            model: Model name (for local: sentence-transformers model, for openai: OpenAI model)
            provider: "local" for sentence-transformers or "openai" for OpenAI API
        """
        self.model = model
        self.provider = provider
        self.batch_size = 100 if provider == "openai" else 32  # Smaller batches for local

        if provider == "local":
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(model)
            self._local_model.eval()  # Set to evaluation mode
        elif provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI embeddings")
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        # Clean text - remove excessive whitespace and newlines
        text = " ".join(text.split())

        if self.provider == "local":
            # Run in thread pool to avoid blocking
            embedding = await asyncio.to_thread(
                self._local_model.encode,
                text,
                convert_to_numpy=False,
                show_progress_bar=False,
            )
            return embedding.tolist()

        elif self.provider == "openai":
            # OpenAI has a limit on input length
            if len(text) > 8000:  # Conservative limit
                text = text[:8000]

            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Clean texts
        texts = [" ".join(text.split()) for text in texts]

        if self.provider == "local":
            # Process in batches to manage memory
            all_embeddings = []
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]

                # Run in thread pool
                embeddings = await asyncio.to_thread(
                    self._local_model.encode,
                    batch,
                    convert_to_numpy=False,
                    show_progress_bar=False,
                    batch_size=self.batch_size,
                )

                # Convert to list of lists
                all_embeddings.extend([emb.tolist() for emb in embeddings])

            return all_embeddings

        elif self.provider == "openai":
            embeddings = []

            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]

                # Truncate texts
                batch = [text[:8000] for text in batch]

                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                # Small delay to avoid rate limiting
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.1)

            return embeddings

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Generate embedding for a search query.

        This is an alias for generate_embedding but can be customized
        for query-specific optimization in the future.

        Args:
            query: Search query text

        Returns:
            Embedding vector as list of floats
        """
        return await self.generate_embedding(query)

    def get_embedding_dimensions(self) -> int:
        """Get the dimensionality of embeddings for the current model.

        Returns:
            Number of dimensions
        """
        if self.provider == "local":
            # Common sentence-transformers models
            dimensions_map = {
                "all-MiniLM-L6-v2": 384,
                "all-mpnet-base-v2": 768,
                "multi-qa-MiniLM-L6-cos-v1": 384,
                "paraphrase-multilingual-MiniLM-L12-v2": 384,
            }
            return dimensions_map.get(self.model, 384)

        elif self.provider == "openai":
            dimensions_map = {
                "text-embedding-3-small": 1536,
                "text-embedding-3-large": 3072,
                "text-embedding-ada-002": 1536,
            }
            return dimensions_map.get(self.model, 1536)


class CachedEmbeddingService(EmbeddingService):
    """Embedding service with Redis caching to avoid re-embedding same content."""

    def __init__(
        self,
        model: str = "all-MiniLM-L6-v2",
        provider: str = "local",
        redis_client: Any | None = None,
    ):
        """Initialize cached embedding service.

        Args:
            model: Model name
            provider: "local" or "openai"
            redis_client: Redis client for caching (optional)
        """
        super().__init__(model, provider)
        self.redis_client = redis_client
        self.cache_ttl = 86400 * 7  # 7 days

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding with caching.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not self.redis_client:
            return await super().generate_embedding(text)

        # Create cache key
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cache_key = f"embedding:{self.provider}:{self.model}:{text_hash}"

        # Try to get from cache
        try:
            import json
            cached = await self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            # If cache fails, continue to generate
            pass

        # Generate embedding
        embedding = await super().generate_embedding(text)

        # Store in cache
        try:
            import json
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(embedding)
            )
        except Exception:
            # Cache write failure is non-critical
            pass

        return embedding

    async def generate_embeddings_batch(
        self, texts: list[str]
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts with caching.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not self.redis_client:
            return await super().generate_embeddings_batch(texts)

        import hashlib
        import json

        embeddings = []
        texts_to_generate = []
        text_indices = []

        # Check cache for each text
        for idx, text in enumerate(texts):
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            cache_key = f"embedding:{self.provider}:{self.model}:{text_hash}"

            try:
                cached = await self.redis_client.get(cache_key)
                if cached:
                    embeddings.append((idx, json.loads(cached)))
                else:
                    texts_to_generate.append(text)
                    text_indices.append(idx)
            except Exception:
                texts_to_generate.append(text)
                text_indices.append(idx)

        # Generate missing embeddings
        if texts_to_generate:
            new_embeddings = await super().generate_embeddings_batch(texts_to_generate)

            # Cache new embeddings and add to results
            for text, embedding, idx in zip(texts_to_generate, new_embeddings, text_indices):
                embeddings.append((idx, embedding))

                # Cache it
                try:
                    text_hash = hashlib.sha256(text.encode()).hexdigest()
                    cache_key = f"embedding:{self.provider}:{self.model}:{text_hash}"
                    await self.redis_client.setex(
                        cache_key,
                        self.cache_ttl,
                        json.dumps(embedding)
                    )
                except Exception:
                    pass

        # Sort by original index and extract embeddings
        embeddings.sort(key=lambda x: x[0])
        return [emb for _, emb in embeddings]


def get_default_embedding_service() -> EmbeddingService:
    """Get the default embedding service based on configuration.

    Returns:
        EmbeddingService instance
    """
    # Use OpenAI if API key is configured and valid, otherwise use local
    # Check that the key is not a placeholder
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your-"):
        return EmbeddingService(
            model="text-embedding-3-small",
            provider="openai"
        )
    else:
        return EmbeddingService(
            model="all-MiniLM-L6-v2",
            provider="local"
        )
