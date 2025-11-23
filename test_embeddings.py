"""Test script for embedding service."""

import asyncio
from src.services.embedding_service import EmbeddingService, get_default_embedding_service


async def test_local_embeddings():
    """Test local sentence-transformers embeddings."""
    print("=" * 60)
    print("Testing Local Embeddings (sentence-transformers)")
    print("=" * 60)

    # Initialize local embedding service
    service = EmbeddingService(model="all-MiniLM-L6-v2", provider="local")

    # Test single embedding
    print("\n1. Testing single embedding generation...")
    text = "This is a test document about artificial intelligence."
    embedding = await service.generate_embedding(text)

    print(f"   Text: {text}")
    print(f"   Embedding dimensions: {len(embedding)}")
    print(f"   First 5 values: {embedding[:5]}")
    print(f"   ✓ Single embedding generated successfully!")

    # Test batch embeddings
    print("\n2. Testing batch embedding generation...")
    texts = [
        "Machine learning is a subset of AI",
        "Deep learning uses neural networks",
        "Natural language processing analyzes text",
        "Computer vision processes images",
        "Reinforcement learning learns from rewards"
    ]

    embeddings = await service.generate_embeddings_batch(texts)

    print(f"   Number of texts: {len(texts)}")
    print(f"   Number of embeddings: {len(embeddings)}")
    print(f"   Each embedding dimension: {len(embeddings[0])}")
    print(f"   ✓ Batch embeddings generated successfully!")

    # Test similarity calculation
    print("\n3. Testing semantic similarity...")
    query = "What is machine learning?"
    query_embedding = await service.generate_query_embedding(query)

    # Calculate cosine similarity with first text
    import numpy as np
    query_vec = np.array(query_embedding)
    text_vec = np.array(embeddings[0])

    # Cosine similarity
    similarity = np.dot(query_vec, text_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(text_vec))

    print(f"   Query: {query}")
    print(f"   Text: {texts[0]}")
    print(f"   Cosine similarity: {similarity:.4f}")
    print(f"   ✓ Similarity calculation successful!")

    print("\n✅ All local embedding tests passed!\n")


async def test_default_service():
    """Test the default embedding service (auto-detects provider)."""
    print("=" * 60)
    print("Testing Default Embedding Service (Auto-detect)")
    print("=" * 60)

    service = get_default_embedding_service()

    print(f"\n   Provider: {service.provider}")
    print(f"   Model: {service.model}")
    print(f"   Dimensions: {service.get_embedding_dimensions()}")

    text = "Testing default service"
    embedding = await service.generate_embedding(text)

    print(f"   Generated embedding dimension: {len(embedding)}")
    print(f"   ✓ Default service works!\n")


async def main():
    """Run all tests."""
    print("\n🧪 Starting Embedding Service Tests...\n")

    try:
        await test_local_embeddings()
        await test_default_service()

        print("=" * 60)
        print("🎉 All tests completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Local embeddings are working without API keys")
        print("  2. You can optionally add OPENAI_API_KEY for better embeddings")
        print("  3. Ready to create RAG API endpoints")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
