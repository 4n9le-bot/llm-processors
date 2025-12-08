"""
Pytest configuration and fixtures for llm-processors tests.
"""

import pytest
from typing import List, AsyncIterator

from llm_processors import Packet


@pytest.fixture
def sample_packets() -> List[Packet]:
    """Sample packets for testing."""
    return [
        Packet.from_text("Hello"),
        Packet.from_text("World"),
        Packet.from_text("Test"),
    ]


@pytest.fixture
def sample_texts() -> List[str]:
    """Sample text strings for testing."""
    return ["Hello", "World", "Test"]


async def async_iterable_from_list(items: List) -> AsyncIterator:
    """
    Helper to create async iterable from list.

    Args:
        items: List of items

    Yields:
        Items from list
    """
    for item in items:
        yield item


@pytest.fixture
def async_stream(sample_packets):
    """
    Async stream fixture.

    Returns:
        Function that creates async iterable from sample_packets
    """
    def _create_stream():
        return async_iterable_from_list(sample_packets)
    return _create_stream
