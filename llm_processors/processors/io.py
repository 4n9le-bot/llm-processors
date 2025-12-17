"""
I/O Utilities: Collection functions for pipeline outputs.

This module provides utilities for collecting results from async streams.
For creating input streams, use StreamAdapter.from_items() from the utils module.
"""

from typing import AsyncIterator

from llm_processors.core import Packet


async def collect(stream: AsyncIterator[Packet]) -> list[Packet]:
    """
    Collect async stream into list.

    This is a terminal operation for pipelines, materializing
    the entire async stream into a Python list.

    Args:
        stream: Async iterator of Packets

    Returns:
        List of all Packets from the stream

    Examples:
        >>> from llm_processors.utils import StreamAdapter
        >>> pipeline = processor1 + processor2
        >>> input_stream = StreamAdapter.from_items(["Hello", "World"])
        >>> results = await collect(pipeline(input_stream))
        >>> for packet in results:
        ...     print(packet.content)
    """
    results = []
    async for packet in stream:
        results.append(packet)
    return results


async def collect_text(stream: AsyncIterator[Packet]) -> list[str]:
    """
    Collect async stream and extract text content.

    Convenience function that collects the stream and extracts text
    content from Packets. Non-text packets are converted to strings.

    Args:
        stream: Async iterator of Packets

    Returns:
        List of text strings extracted from Packets

    Examples:
        >>> from llm_processors.utils import StreamAdapter
        >>> pipeline = source + chat_processor
        >>> input_stream = StreamAdapter.from_items(["Hello"])
        >>> texts = await collect_text(pipeline(input_stream))
        >>> for text in texts:
        ...     print(text)
    """
    results = []
    async for packet in stream:
        if packet.is_text():
            results.append(packet.content)  # type: ignore
        else:
            results.append(str(packet.content))
    return results
