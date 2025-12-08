"""
Tests for I/O processors.
"""

import pytest
from llm_processors import Packet
from llm_processors.processors import FromIterableProcessor, collect, collect_text


@pytest.mark.asyncio
@pytest.mark.unit
async def test_from_iterable_with_strings():
    """Test FromIterableProcessor with string items."""
    items = ["hello", "world", "test"]
    source = FromIterableProcessor(items)

    results = await collect(source())

    assert len(results) == 3
    assert all(isinstance(r, Packet) for r in results)
    assert results[0].content == "hello"
    assert results[1].content == "world"
    assert results[2].content == "test"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_from_iterable_with_packets():
    """Test FromIterableProcessor with Packet items."""
    packets = [
        Packet.from_text("hello", author="Alice"),
        Packet.from_text("world", author="Bob"),
    ]
    source = FromIterableProcessor(packets)

    results = await collect(source())

    assert len(results) == 2
    assert results[0].metadata["author"] == "Alice"
    assert results[1].metadata["author"] == "Bob"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_from_iterable_mixed():
    """Test FromIterableProcessor with mixed string and Packet items."""
    items = [
        "plain string",
        Packet.from_text("packet", priority=1),
    ]
    source = FromIterableProcessor(items)

    results = await collect(source())

    assert len(results) == 2
    assert results[0].content == "plain string"
    assert results[1].content == "packet"
    assert results[1].metadata.get("priority") == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_collect():
    """Test collect function."""
    source = FromIterableProcessor(["a", "b", "c"])
    results = await collect(source())

    assert len(results) == 3
    assert isinstance(results, list)
    assert all(isinstance(r, Packet) for r in results)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_collect_text():
    """Test collect_text function."""
    source = FromIterableProcessor(["hello", "world"])
    texts = await collect_text(source())

    assert len(texts) == 2
    assert isinstance(texts, list)
    assert all(isinstance(t, str) for t in texts)
    assert texts[0] == "hello"
    assert texts[1] == "world"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_from_iterable_empty():
    """Test FromIterableProcessor with empty list."""
    source = FromIterableProcessor([])
    results = await collect(source())

    assert len(results) == 0
    assert results == []
