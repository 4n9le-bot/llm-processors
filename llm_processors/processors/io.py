"""
I/O Processors: Entry and exit points for pipelines.

This module provides utilities for creating packet streams from iterables
and collecting results from streams.
"""

from typing import List, AsyncIterator, Iterable, Union, Optional

from llm_processors.core import Packet, PacketTypes, BaseProcessor


class FromIterableProcessor(BaseProcessor):
    """
    Create packet stream from Python iterable.

    This is the standard entry point for pipelines, converting
    a regular Python iterable into an async stream of Packets.

    Examples:
        >>> source = FromIterableProcessor(["Hello", "World"])
        >>> pipeline = source + processor1 + processor2
        >>> results = await collect(pipeline())
    """

    def __init__(self, items: Iterable[Union[str, Packet]]):
        """
        Initialize from iterable processor.

        Args:
            items: Iterable of strings or Packets
        """
        super().__init__()
        self.items = items

    async def __call__(
        self,
        stream: Optional[AsyncIterator[Packet]] = None
    ) -> AsyncIterator[Packet]:
        """
        Ignores input stream, yields from items.

        This allows FromIterableProcessor to be used as the start
        of a pipeline without requiring an input stream.

        Args:
            stream: Ignored (can be None)

        Yields:
            Packets from the items iterable
        """
        for item in self.items:
            if isinstance(item, Packet):
                yield item
            elif isinstance(item, str):
                yield Packet.from_text(item)
            else:
                raise ValueError(f"Unsupported item type: {type(item)}. Must be str or Packet.")

    def __repr__(self) -> str:
        """String representation."""
        return f"FromIterableProcessor({len(list(self.items))} items)"


async def collect(stream: AsyncIterator[PacketTypes]) -> List[PacketTypes]:
    """
    Collect async stream into list.

    This is a terminal operation for pipelines, materializing
    the entire async stream into a Python list.

    Args:
        stream: Async iterator of PacketTypes

    Returns:
        List of all items from the stream

    Examples:
        >>> pipeline = source + processor1 + processor2
        >>> results = await collect(pipeline())
        >>> for result in results:
        ...     print(result.content)
    """
    results = []
    async for item in stream:
        results.append(item)
    return results


async def collect_text(stream: AsyncIterator[PacketTypes]) -> List[str]:
    """
    Collect async stream and extract text content.

    Convenience function that collects the stream and extracts
    text content from Packets, converting non-text packets to strings.

    Args:
        stream: Async iterator of PacketTypes

    Returns:
        List of text strings

    Examples:
        >>> pipeline = source + chat_processor
        >>> texts = await collect_text(pipeline())
        >>> for text in texts:
        ...     print(text)
    """
    results = []
    async for item in stream:
        if isinstance(item, Packet):
            if item.is_text():
                results.append(item.content)  # type: ignore
            else:
                results.append(str(item.content))
        elif isinstance(item, str):
            results.append(item)
        else:
            results.append(str(item))
    return results
