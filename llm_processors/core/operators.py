"""
Operators: Sequential and parallel composition of processors.

This module implements the magic behind + (sequential) and // (parallel) operators.
"""

from typing import AsyncIterable, AsyncIterator
import asyncio

from llm_processors.core.packet import Packet
from llm_processors.core.processor import BaseProcessor


class SequentialProcessor(BaseProcessor):
    """
    Sequential composition of two processors (p1 + p2).

    Output of first processor flows into second processor.

    Examples:
        >>> pipeline = PromptProcessor(...) + ChatProcessor(...)
        >>> # stream -> prompt -> chat -> output
    """

    def __init__(self, first: BaseProcessor, second: BaseProcessor):
        """
        Initialize sequential processor.

        Args:
            first: First processor in chain
            second: Second processor in chain
        """
        super().__init__()
        self.first = first
        self.second = second

    async def _process_stream(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Chain processors: stream -> first -> second.

        Args:
            stream: Input packet stream

        Yields:
            Output from second processor
        """
        # First processor processes the input stream
        intermediate = self.first(stream)

        # Second processor processes the output of first
        async for result in self.second(intermediate):
            yield result

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.first} + {self.second})"


class ParallelProcessor(BaseProcessor):
    """
    Parallel composition of processors (p1 // p2 // ...).

    Input stream is broadcast to all processors (each processor receives
    all packets). Outputs are merged into single stream with FIFO ordering
    (whichever processor produces output first).

    Each output packet is tagged with substream_name metadata indicating
    which processor branch it came from.

    Examples:
        >>> parallel = ModelA() // ModelB()
        >>> # stream broadcast to both models, outputs merged FIFO
        >>> async for packet in parallel(input_stream):
        ...     print(f"{packet.substream_name}: {packet.content}")
    """

    def __init__(self, *processors: BaseProcessor):
        """
        Initialize parallel processor.

        Args:
            *processors: Processors to run in parallel (min 2)

        Raises:
            ValueError: If less than 2 processors provided
        """
        if len(processors) < 2:
            raise ValueError("ParallelProcessor requires at least 2 processors")
        super().__init__()
        self.processors = processors

    async def _process_stream(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Run processors in parallel and merge outputs (FIFO).

        Strategy:
        1. Materialize input stream into list (enables broadcast to all processors)
        2. Spawn async tasks for each processor
        3. Use asyncio.Queue for FIFO merging of outputs
        4. Tag outputs with substream_name metadata

        Args:
            stream: Input packet stream

        Yields:
            Merged outputs from all processors (FIFO order)
        """
        # Materialize stream (needed for broadcast to all processors)
        packets = []
        async for packet in stream:
            packets.append(packet)

        # If no packets, nothing to process
        if not packets:
            return

        # Create queue for FIFO merging
        output_queue: asyncio.Queue[Packet | None] = asyncio.Queue()

        # Track how many processors are still running
        active_processors = len(self.processors)

        async def run_processor(processor: BaseProcessor, index: int):
            """Run processor and put results in queue."""
            nonlocal active_processors
            try:
                # Create async iterable from list
                async def stream_from_list() -> AsyncIterator[Packet]:
                    for packet in packets:
                        yield packet

                # Process stream and tag with substream_name
                async for result in processor(stream_from_list()):
                    # Add substream metadata
                    tagged_result = result.with_metadata(
                        substream_name=f"branch_{index}_{processor.__class__.__name__}"
                    )
                    await output_queue.put(tagged_result)
            finally:
                # Signal completion
                active_processors -= 1
                if active_processors == 0:
                    # All processors done, signal end
                    await output_queue.put(None)

        # Start all processors
        tasks = [
            asyncio.create_task(run_processor(processor, idx))
            for idx, processor in enumerate(self.processors)
        ]

        # Yield results as they arrive (FIFO)
        while True:
            result = await output_queue.get()
            if result is None:
                # All processors finished
                break
            yield result

        # Wait for all tasks to complete (cleanup)
        await asyncio.gather(*tasks, return_exceptions=True)

    def __repr__(self) -> str:
        """String representation."""
        procs = " // ".join(str(p) for p in self.processors)
        return f"({procs})"
