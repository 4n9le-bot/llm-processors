"""
Processor: Core abstraction for stream processing.

A Processor transforms async streams of Packets. Processors can be composed
using + (sequential) and // (parallel) operators.
"""

from typing import Protocol, AsyncIterable, AsyncIterator, runtime_checkable

from llm_processors.core.packet import Packet, PacketTypes


@runtime_checkable
class Processor(Protocol):
    """
    Protocol for processors that transform async streams of Packets.

    A Processor takes an AsyncIterable of Packets and yields transformed
    Packets. Processors can be composed using + (sequential) and // (parallel).

    Examples:
        >>> # Sequential composition
        >>> pipeline = processor1 + processor2 + processor3

        >>> # Parallel composition
        >>> parallel = processor1 // processor2

        >>> # Mixed composition
        >>> complex_pipeline = (proc1 + proc2) // (proc3 + proc4)
    """

    async def __call__(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[PacketTypes]:
        """
        Process an async stream of Packets.

        Args:
            stream: Input async iterable of Packets

        Yields:
            Transformed Packets or raw content (str/bytes/Image)
        """
        ...

    def __add__(self, other: 'Processor') -> 'Processor':
        """Chain this processor with another (sequential composition)."""
        ...

    def __floordiv__(self, other: 'Processor') -> 'Processor':
        """Run this processor in parallel with another."""
        ...


class BaseProcessor:
    """
    Base class for processors providing operator overloading.

    Subclasses should implement the process() method to define
    their transformation logic.

    Examples:
        >>> class UppercaseProcessor(BaseProcessor):
        ...     async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        ...         if packet.is_text():
        ...             yield Packet.from_text(packet.content.upper())
        ...         else:
        ...             yield packet
    """

    async def __call__(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Main entry point - delegates to process() for each packet.

        Args:
            stream: Input async iterable of Packets

        Yields:
            Transformed Packets from process() method
        """
        async for packet in stream:
            async for result in self.process(packet):
                yield result

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        """
        Process a single packet. Override in subclasses.

        Args:
            packet: Input packet

        Yields:
            Transformed packets (can yield 0, 1, or many)

        Note:
            - Yield 0 packets to filter out
            - Yield 1 packet to transform
            - Yield many packets to expand/fan-out
        """
        yield packet

    def __add__(self, other: Processor) -> 'Processor':
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

    def __floordiv__(self, other: Processor) -> 'Processor':
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
