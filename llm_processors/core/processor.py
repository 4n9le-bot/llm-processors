"""
Processor: Core abstraction for stream processing.

A Processor transforms async streams of Packets. Processors can be composed
using + (sequential) and // (parallel) operators.
"""

from abc import ABC, abstractmethod
from typing import AsyncIterable, AsyncIterator

from llm_processors.core.packet import Packet


class BaseProcessor(ABC):
    """
    Abstract base class for processors that transform async streams of Packets.

    A Processor takes an AsyncIterable of Packets and yields transformed
    Packets. Processors can be composed using + (sequential) and // (parallel).

    The base class provides:
    - Optional automatic error handling (errors become error packets)
    - Operator overloading for composition (+ and //)
    - Abstract _process_stream method for subclasses to implement

    Examples:
        >>> class UppercaseProcessor(BaseProcessor):
        ...     async def _process_stream(self, stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        ...         async for packet in stream:
        ...             if packet.is_text():
        ...                 yield Packet.from_text(packet.content.upper())
        ...             else:
        ...                 yield packet

        >>> # Sequential composition
        >>> pipeline = processor1 + processor2 + processor3

        >>> # Parallel composition
        >>> parallel = processor1 // processor2

        >>> # Mixed composition
        >>> complex_pipeline = (proc1 + proc2) // (proc3 + proc4)
    """

    def __init__(self, handle_errors: bool = True):
        """
        Initialize processor.

        Args:
            handle_errors: If True, exceptions are caught and converted to
                error packets. If False, exceptions propagate normally.
        """
        self.handle_errors = handle_errors

    async def __call__(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Process an async stream of Packets.

        This method handles error wrapping if enabled, then delegates
        to _process_stream for the actual processing logic.

        Args:
            stream: Input async iterable of Packets

        Yields:
            Transformed Packets (or error packets if exceptions occur)

        Examples:
            >>> processor = MyProcessor()
            >>> results = processor(input_stream)
            >>> async for packet in results:
            ...     print(packet.content)
        """
        if not self.handle_errors:
            # Direct pass-through without error handling
            async for packet in self._process_stream(stream):
                yield packet
        else:
            # Process with error handling - wrap each packet
            async for packet in stream:
                try:
                    # Create single-item stream for this packet
                    async def single_packet_stream():
                        yield packet

                    # Process and yield results
                    async for result in self._process_stream(single_packet_stream()):
                        yield result
                except Exception as e:
                    # Convert exception to error packet
                    error_metadata = {
                        'substream_name': 'error',
                        'error_type': type(e).__name__,
                    }

                    # Preserve original packet metadata
                    if packet.metadata:
                        error_metadata['source_metadata'] = packet.metadata

                    yield Packet.from_text(str(e), **error_metadata)

    @abstractmethod
    async def _process_stream(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Process a stream of packets. Subclasses must implement this method.

        Args:
            stream: Input async iterable of Packets

        Yields:
            Transformed Packets

        Note:
            - Yield 0 packets to filter out
            - Yield 1 packet to transform
            - Yield many packets to expand/fan-out

        Examples:
            >>> async def _process_stream(self, stream):
            ...     async for packet in stream:
            ...         if packet.is_text():
            ...             yield Packet.from_text(packet.content.upper())
        """
        ...

    def __add__(self, other: 'BaseProcessor') -> 'BaseProcessor':
        """
        Chain with another processor (sequential composition).

        Args:
            other: Processor to chain after this one

        Returns:
            SequentialProcessor that chains both processors

        Examples:
            >>> pipeline = processor1 + processor2
            >>> # stream -> processor1 -> processor2
        """
        from llm_processors.core.operators import SequentialProcessor
        return SequentialProcessor(self, other)

    def __floordiv__(self, other: 'BaseProcessor') -> 'BaseProcessor':
        """
        Run in parallel with another processor.

        Args:
            other: Processor to run in parallel

        Returns:
            ParallelProcessor that runs both processors concurrently

        Examples:
            >>> parallel = processor1 // processor2
            >>> # stream duplicated to both processors, outputs merged
        """
        from llm_processors.core.operators import ParallelProcessor
        return ParallelProcessor(self, other)

    def __repr__(self) -> str:
        """String representation of processor."""
        return f"{self.__class__.__name__}()"
