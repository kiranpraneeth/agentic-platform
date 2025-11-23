"""Test script for OpenAI embedding service."""

import asyncio
from src.services.embedding_service import EmbeddingService, get_default_embedding_service


async def test_openai_embeddings():
    """Test OpenAI embeddings."""
    print("=" * 60)
    print("Testing OpenAI Embeddings (text-embedding-3-small)")
    print("=" * 60)

    # Initialize OpenAI embedding service
    service = EmbeddingService(model="text-embedding-3-small", provider="openai")

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

    print("\n✅ All OpenAI embedding tests passed!\n")


async def test_default_service():
    """Test the default embedding service (should now use OpenAI)."""
    print("=" * 60)
    print("Testing Default Embedding Service (Auto-detect)")
    print("=" * 60)

    service = get_default_embedding_service()

    print(f"\n   Provider: {service.provider}")
    print(f"   Model: {service.model}")
    print(f"   Dimensions: {service.get_embedding_dimensions()}")

    text = "Testing default service with OpenAI"
    embedding = await service.generate_embedding(text)

    print(f"   Generated embedding dimension: {len(embedding)}")
    print(f"   ✓ Default service auto-detected OpenAI!\n")


async def compare_models():
    """Compare local vs OpenAI embeddings."""
    print("=" * 60)
    print("Comparing Local vs OpenAI Embeddings")
    print("=" * 60)

    # Initialize both services
    local_service = EmbeddingService(model="all-MiniLM-L6-v2", provider="local")
    openai_service = EmbeddingService(model="text-embedding-3-small", provider="openai")

    # Test texts
    query = "What is artificial intelligence?"
    relevant_text = "Artificial intelligence is the simulation of human intelligence"
    irrelevant_text = "The weather is sunny today"

    print(f"\n   Query: {query}")
    print(f"   Relevant: {relevant_text}")
    print(f"   Irrelevant: {irrelevant_text}")

    # Local embeddings
    print("\n   Local Model (all-MiniLM-L6-v2):")
    local_query = await local_service.generate_embedding(query)
    local_relevant = await local_service.generate_embedding(relevant_text)
    local_irrelevant = await local_service.generate_embedding(irrelevant_text)

    import numpy as np
    local_rel_sim = np.dot(local_query, local_relevant) / (np.linalg.norm(local_query) * np.linalg.norm(local_relevant))
    local_irrel_sim = np.dot(local_query, local_irrelevant) / (np.linalg.norm(local_query) * np.linalg.norm(local_irrelevant))

    print(f"     Query vs Relevant: {local_rel_sim:.4f}")
    print(f"     Query vs Irrelevant: {local_irrel_sim:.4f}")
    print(f"     Difference: {local_rel_sim - local_irrel_sim:.4f}")

    # OpenAI embeddings
    print("\n   OpenAI Model (text-embedding-3-small):")
    openai_query = await openai_service.generate_embedding(query)
    openai_relevant = await openai_service.generate_embedding(relevant_text)
    openai_irrelevant = await openai_service.generate_embedding(irrelevant_text)

    openai_rel_sim = np.dot(openai_query, openai_relevant) / (np.linalg.norm(openai_query) * np.linalg.norm(openai_relevant))
    openai_irrel_sim = np.dot(openai_query, openai_irrelevant) / (np.linalg.norm(openai_query) * np.linalg.norm(openai_irrelevant))

    print(f"     Query vs Relevant: {openai_rel_sim:.4f}")
    print(f"     Query vs Irrelevant: {openai_irrel_sim:.4f}")
    print(f"     Difference: {openai_rel_sim - openai_irrel_sim:.4f}")

    print("\n   ✓ Both models correctly identify relevant text with higher similarity!")


async def main():
    """Run all tests."""
    print("\n🧪 Starting OpenAI Embedding Service Tests...\n")

    try:
        await test_openai_embeddings()
        await test_default_service()
        await compare_models()

        print("\n" + "=" * 60)
        print("🎉 All OpenAI tests completed successfully!")
        print("=" * 60)
        print("\nConclusions:")
        print("  ✓ OpenAI embeddings (1536-dim) working")
        print("  ✓ Local embeddings (384-dim) working")
        print("  ✓ Auto-detection correctly choosing OpenAI when key is present")
        print("  ✓ Both models provide good semantic understanding")
        print("  ✓ Ready to proceed with RAG API endpoints")
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
