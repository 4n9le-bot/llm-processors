"""
StreamAdapter: Utilities for converting between sync/async iterables and Packets.

This module provides stream conversion utilities for transforming between
synchronous iterables and asynchronous packet streams.
"""

from typing import Iterable, AsyncIterator, Union

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

from llm_processors.core.packet import Packet
from llm_processors.utils.converters import PacketConverter


class StreamAdapter:
    """
    Utility class for stream conversions and adaptations.

    Provides static methods for converting between synchronous iterables
    and asynchronous packet streams, with automatic type conversion.

    Examples:
        >>> # Create async packet stream from items
        >>> stream = StreamAdapter.from_items(["Hello", "World"])
        >>> async for packet in stream:
        ...     print(packet.content)
        'Hello'
        'World'

        >>> # Collect async stream to list
        >>> packets = await StreamAdapter.to_list(stream)
        >>> len(packets)
        2
    """

    @staticmethod
    async def from_items(
        items: Iterable[Union[str, bytes, 'Image.Image', Packet]]
    ) -> AsyncIterator[Packet]:
        """
        Convert iterable to async packet stream (one-stop solution).

        Handles both sync->async conversion AND raw type->Packet conversion.
        This is the primary entry point for creating packet streams from
        regular Python iterables.

        Args:
            items: Iterable of strings, bytes, images, or Packets

        Yields:
            Packets created from the input items

        Examples:
            >>> # From strings
            >>> stream = StreamAdapter.from_items(["Hello", "World"])
            >>> async for packet in stream:
            ...     print(packet.content)

            >>> # From mixed types
            >>> items = ["text", b"bytes", Packet.from_text("existing")]
            >>> stream = StreamAdapter.from_items(items)

            >>> # Use in pipeline
            >>> pipeline = processor1 + processor2
            >>> results = await StreamAdapter.to_list(
            ...     pipeline(StreamAdapter.from_items(["input"]))
            ... )
        """
        for item in items:
            if isinstance(item, Packet):
                yield item
            else:
                yield PacketConverter.to_packet(item)

    @staticmethod
    async def from_sync_iterable(
        iterable: Iterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Convert synchronous iterable of Packets to async stream.

        This is a lower-level method for when you already have Packet objects
        and just need sync->async conversion without type conversion.

        Args:
            iterable: Synchronous iterable of Packets

        Yields:
            Packets from the iterable

        Examples:
            >>> packets = [Packet.from_text("A"), Packet.from_text("B")]
            >>> stream = StreamAdapter.from_sync_iterable(packets)
            >>> async for packet in stream:
            ...     print(packet.content)
        """
        for item in iterable:
            yield item

    @staticmethod
    async def to_list(stream: AsyncIterator[Packet]) -> list[Packet]:
        """
        Collect async stream into a list.

        Materializes the entire async stream into a Python list.
        This is a terminal operation that consumes the entire stream.

        Args:
            stream: Async iterator of Packets

        Returns:
            List of all Packets from the stream

        Examples:
            >>> stream = StreamAdapter.from_items(["A", "B", "C"])
            >>> packets = await StreamAdapter.to_list(stream)
            >>> len(packets)
            3

            >>> # Use with pipeline
            >>> pipeline = source + processor
            >>> results = await StreamAdapter.to_list(pipeline(...))
        """
        results = []
        async for packet in stream:
            results.append(packet)
        return results

    @staticmethod
    async def to_text_list(stream: AsyncIterator[Packet]) -> list[str]:
        """
        Collect async stream and extract text content.

        Convenience method that collects the stream and extracts text
        content from Packets. Non-text packets are converted to strings.

        Args:
            stream: Async iterator of Packets

        Returns:
            List of text strings extracted from Packets

        Examples:
            >>> stream = StreamAdapter.from_items(["Hello", "World"])
            >>> texts = await StreamAdapter.to_text_list(stream)
            >>> texts
            ['Hello', 'World']
        """
        results = []
        async for packet in stream:
            if packet.is_text():
                results.append(packet.content)  # type: ignore
            else:
                results.append(str(packet.content))
        return results
