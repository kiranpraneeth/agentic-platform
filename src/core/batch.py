"""Batch processing utilities for performance optimization."""

import asyncio
from typing import Any, Callable, List, TypeVar

from src.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")


async def batch_process(
    items: List[T],
    process_fn: Callable[[List[T]], Any],
    batch_size: int = 100,
    max_concurrent: int = 5,
) -> List[R]:
    """Process items in batches with concurrency control.

    Args:
        items: Items to process
        process_fn: Async function to process batch
        batch_size: Number of items per batch
        max_concurrent: Maximum concurrent batches

    Returns:
        List of results
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(batch: List[T]) -> List[R]:
        """Process a single batch with semaphore."""
        async with semaphore:
            try:
                return await process_fn(batch)
            except Exception as e:
                logger.error(
                    "batch_process_error",
                    error=str(e),
                    batch_size=len(batch),
                )
                raise

    # Split into batches
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    logger.info(
        "batch_processing_started",
        total_items=len(items),
        num_batches=len(batches),
        batch_size=batch_size,
        max_concurrent=max_concurrent,
    )

    # Process batches concurrently
    batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])

    # Flatten results
    for batch_result in batch_results:
        if isinstance(batch_result, list):
            results.extend(batch_result)
        else:
            results.append(batch_result)

    logger.info(
        "batch_processing_completed",
        total_items=len(items),
        results_count=len(results),
    )

    return results


class BatchProcessor:
    """Batch processor with automatic flushing."""

    def __init__(
        self,
        process_fn: Callable[[List[T]], Any],
        batch_size: int = 100,
        flush_interval: float = 5.0,
    ):
        """Initialize batch processor.

        Args:
            process_fn: Async function to process batch
            batch_size: Maximum batch size before auto-flush
            flush_interval: Maximum time between flushes (seconds)
        """
        self.process_fn = process_fn
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: List[T] = []
        self._last_flush = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def add(self, item: T) -> None:
        """Add item to batch.

        Args:
            item: Item to add
        """
        async with self._lock:
            self._batch.append(item)

            # Auto-flush if batch is full
            if len(self._batch) >= self.batch_size:
                await self._flush()

    async def _flush(self) -> None:
        """Flush current batch."""
        if not self._batch:
            return

        batch = self._batch
        self._batch = []
        self._last_flush = asyncio.get_event_loop().time()

        try:
            await self.process_fn(batch)
            logger.debug("batch_flushed", size=len(batch))
        except Exception as e:
            logger.error("batch_flush_error", error=str(e), size=len(batch))
            # Re-add failed items
            self._batch.extend(batch)

    async def flush(self) -> None:
        """Manually flush current batch."""
        async with self._lock:
            await self._flush()

    async def start_auto_flush(self) -> None:
        """Start background auto-flush task."""
        while True:
            await asyncio.sleep(self.flush_interval)

            async with self._lock:
                # Check if enough time has passed
                now = asyncio.get_event_loop().time()
                if now - self._last_flush >= self.flush_interval:
                    await self._flush()


# Batch embedding generation
async def batch_generate_embeddings(
    texts: List[str],
    embedding_fn: Callable[[str], List[float]],
    batch_size: int = 50,
    max_concurrent: int = 3,
) -> List[List[float]]:
    """Generate embeddings for multiple texts in batches.

    Args:
        texts: Texts to embed
        embedding_fn: Async function to generate embedding
        batch_size: Texts per batch
        max_concurrent: Max concurrent batches

    Returns:
        List of embeddings
    """

    async def process_batch(batch: List[str]) -> List[List[float]]:
        """Process a batch of texts."""
        tasks = [embedding_fn(text) for text in batch]
        return await asyncio.gather(*tasks)

    return await batch_process(
        texts,
        process_batch,
        batch_size=batch_size,
        max_concurrent=max_concurrent,
    )


# Batch database inserts
async def batch_insert(
    session: Any,
    items: List[Any],
    batch_size: int = 1000,
) -> None:
    """Insert items in batches for better performance.

    Args:
        session: Database session
        items: Items to insert
        batch_size: Items per batch
    """
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        session.add_all(batch)
        await session.flush()

    logger.info("batch_insert_completed", total=len(items), batch_size=batch_size)


# Bulk operations helper
class BulkOperationHelper:
    """Helper for efficient bulk database operations."""

    def __init__(self, session: Any, batch_size: int = 1000):
        """Initialize bulk operation helper.

        Args:
            session: Database session
            batch_size: Batch size for operations
        """
        self.session = session
        self.batch_size = batch_size
        self._inserts: List[Any] = []
        self._updates: List[Any] = []

    async def add_insert(self, item: Any) -> None:
        """Queue item for insertion.

        Args:
            item: Item to insert
        """
        self._inserts.append(item)
        if len(self._inserts) >= self.batch_size:
            await self.flush_inserts()

    async def add_update(self, item: Any) -> None:
        """Queue item for update.

        Args:
            item: Item to update
        """
        self._updates.append(item)
        if len(self._updates) >= self.batch_size:
            await self.flush_updates()

    async def flush_inserts(self) -> None:
        """Flush pending inserts."""
        if not self._inserts:
            return

        self.session.add_all(self._inserts)
        await self.session.flush()

        logger.debug("bulk_inserts_flushed", count=len(self._inserts))
        self._inserts = []

    async def flush_updates(self) -> None:
        """Flush pending updates."""
        if not self._updates:
            return

        for item in self._updates:
            await self.session.merge(item)

        await self.session.flush()

        logger.debug("bulk_updates_flushed", count=len(self._updates))
        self._updates = []

    async def flush_all(self) -> None:
        """Flush all pending operations."""
        await self.flush_inserts()
        await self.flush_updates()
