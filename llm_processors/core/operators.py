"""
Operators: Sequential and parallel composition of processors.

This module implements the magic behind + (sequential) and // (parallel) operators.
"""

from typing import AsyncIterable, AsyncIterator, List, Callable, Optional
import asyncio

from llm_processors.core.packet import Packet, PacketTypes
from llm_processors.core.processor import Processor, BaseProcessor

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore


class SequentialProcessor(BaseProcessor):
    """
    Sequential composition of two processors (p1 + p2).

    Output of first processor flows into second processor.

    Examples:
        >>> pipeline = PromptProcessor(...) + ChatProcessor(...)
        >>> # stream -> prompt -> chat -> output
    """

    def __init__(self, first: Processor, second: Processor):
        """
        Initialize sequential processor.

        Args:
            first: First processor in chain
            second: Second processor in chain
        """
        self.first = first
        self.second = second

    async def __call__(
        self,
        stream: Optional[AsyncIterable[Packet]] = None
    ) -> AsyncIterator[PacketTypes]:
        """
        Chain processors: stream -> first -> second.

        Args:
            stream: Input packet stream (optional, for pipeline start)

        Yields:
            Output from second processor
        """
        # Create empty stream if none provided
        if stream is None:
            async def empty_stream() -> AsyncIterator[Packet]:
                return
                yield  # Make it a generator
            stream = empty_stream()

        # First processor processes the input stream
        intermediate = self.first(stream)

        # Normalize intermediate output to Packets
        normalized = self._normalize_stream(intermediate)

        # Second processor processes the output of first
        async for result in self.second(normalized):
            yield result

    async def _normalize_stream(
        self,
        stream: AsyncIterable[PacketTypes]
    ) -> AsyncIterator[Packet]:
        """
        Convert PacketTypes to Packets.

        Args:
            stream: Stream of PacketTypes (Packet | str | bytes | Image)

        Yields:
            Normalized Packets
        """
        async for item in stream:
            if isinstance(item, Packet):
                yield item
            elif isinstance(item, str):
                yield Packet.from_text(item)
            elif isinstance(item, bytes):
                yield Packet.from_bytes(item)
            elif Image is not None and isinstance(item, Image.Image):
                yield Packet.from_image(item)
            else:
                # Fallback: try to wrap in text packet
                yield Packet.from_text(str(item))

    def __repr__(self) -> str:
        """String representation."""
        return f"({self.first} + {self.second})"


class ParallelProcessor(BaseProcessor):
    """
    Parallel composition of processors (p1 // p2).

    Input stream is duplicated and sent to both processors.
    Outputs are merged into single stream with substream metadata.

    Note:
        This implementation materializes the input stream into a list
        to enable fan-out. This is a trade-off: memory usage vs streaming purity.

    Examples:
        >>> parallel = ModelA() // ModelB()
        >>> # stream duplicated to both models, outputs merged
    """

    def __init__(self, *processors: Processor):
        """
        Initialize parallel processor.

        Args:
            *processors: Processors to run in parallel (min 2)

        Raises:
            ValueError: If less than 2 processors provided
        """
        if len(processors) < 2:
            raise ValueError("ParallelProcessor requires at least 2 processors")
        self.processors = processors

    async def __call__(
        self,
        stream: Optional[AsyncIterable[Packet]] = None
    ) -> AsyncIterator[PacketTypes]:
        """
        Run processors in parallel and merge outputs.

        Strategy:
        1. Materialize input stream into list (enables fan-out)
        2. Spawn async tasks for each processor
        3. Merge outputs with substream_name metadata

        Args:
            stream: Input packet stream (optional, for pipeline start)

        Yields:
            Merged outputs from all processors
        """
        # Create empty stream if none provided
        if stream is None:
            async def empty_stream() -> AsyncIterator[Packet]:
                return
                yield  # Make it a generator
            stream = empty_stream()

        # Materialize stream (needed for fan-out)
        packets = []
        async for packet in stream:
            packets.append(packet)

        # Create async tasks for each processor
        tasks = []
        for idx, processor in enumerate(self.processors):
            task = asyncio.create_task(
                self._run_processor(processor, packets, idx)
            )
            tasks.append(task)

        # Collect results from all processors as they complete
        for task in asyncio.as_completed(tasks):
            results = await task
            for result in results:
                yield result

    async def _run_processor(
        self,
        processor: Processor,
        packets: List[Packet],
        index: int
    ) -> List[PacketTypes]:
        """
        Run processor on packet list and collect results.

        Args:
            processor: Processor to run
            packets: List of packets to process
            index: Processor index (for substream naming)

        Returns:
            List of results from processor
        """
        results = []

        # Create async iterable from list
        async def stream_from_list() -> AsyncIterator[Packet]:
            for packet in packets:
                yield packet

        # Process stream and tag with substream_name
        async for result in processor(stream_from_list()):
            # Add substream metadata if result is Packet
            if isinstance(result, Packet):
                result = result.with_metadata(
                    substream_name=f"branch_{index}_{processor.__class__.__name__}"
                )
            results.append(result)

        return results

    def __repr__(self) -> str:
        """String representation."""
        procs = " // ".join(str(p) for p in self.processors)
        return f"({procs})"


def processor(
    func: Callable[[AsyncIterable[Packet]], AsyncIterator[PacketTypes]]
) -> Processor:
    """
    Decorator to convert async function into Processor.

    This enables functional-style processor definition without
    needing to subclass BaseProcessor.

    Args:
        func: Async generator function

    Returns:
        Processor instance wrapping the function

    Examples:
        >>> @processor
        ... async def uppercase(stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        ...     async for packet in stream:
        ...         if packet.is_text():
        ...             yield Packet.from_text(packet.content.upper())
        ...         else:
        ...             yield packet

        >>> # Can now use with operators
        >>> pipeline = source + uppercase + chat
    """
    class FunctionProcessor(BaseProcessor):
        async def __call__(
            self,
            stream: AsyncIterable[Packet]
        ) -> AsyncIterator[PacketTypes]:
            async for result in func(stream):
                yield result

        def __repr__(self) -> str:
            return f"Processor({func.__name__})"

    return FunctionProcessor()
