"""
Tests for I/O utilities and StreamAdapter.
"""

import pytest
from llm_processors import Packet
from llm_processors.processors import collect, collect_text
from llm_processors.utils import StreamAdapter


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_from_items_with_strings():
    """Test StreamAdapter.from_items with string items."""
    items = ["hello", "world", "test"]
    stream = StreamAdapter.from_items(items)

    results = await collect(stream)

    assert len(results) == 3
    assert all(isinstance(r, Packet) for r in results)
    assert results[0].content == "hello"
    assert results[1].content == "world"
    assert results[2].content == "test"
    assert all(r.mimetype == "text/plain" for r in results)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_from_items_with_packets():
    """Test StreamAdapter.from_items with Packet items."""
    packets = [
        Packet.from_text("hello", author="Alice"),
        Packet.from_text("world", author="Bob"),
    ]
    stream = StreamAdapter.from_items(packets)

    results = await collect(stream)

    assert len(results) == 2
    assert results[0].metadata["author"] == "Alice"
    assert results[1].metadata["author"] == "Bob"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_from_items_mixed():
    """Test StreamAdapter.from_items with mixed string and Packet items."""
    items = [
        "plain string",
        Packet.from_text("packet", priority=1),
    ]
    stream = StreamAdapter.from_items(items)

    results = await collect(stream)

    assert len(results) == 2
    assert results[0].content == "plain string"
    assert results[1].content == "packet"
    assert results[1].metadata.get("priority") == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_from_items_with_bytes():
    """Test StreamAdapter.from_items with bytes."""
    items = [b"binary data", b"more bytes"]
    stream = StreamAdapter.from_items(items)

    results = await collect(stream)

    assert len(results) == 2
    assert all(r.is_bytes() for r in results)
    assert results[0].content == b"binary data"
    assert results[1].content == b"more bytes"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_collect():
    """Test collect function."""
    stream = StreamAdapter.from_items(["a", "b", "c"])
    results = await collect(stream)

    assert len(results) == 3
    assert isinstance(results, list)
    assert all(isinstance(r, Packet) for r in results)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_collect_text():
    """Test collect_text function."""
    stream = StreamAdapter.from_items(["hello", "world"])
    texts = await collect_text(stream)

    assert len(texts) == 2
    assert isinstance(texts, list)
    assert all(isinstance(t, str) for t in texts)
    assert texts[0] == "hello"
    assert texts[1] == "world"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_empty():
    """Test StreamAdapter.from_items with empty list."""
    stream = StreamAdapter.from_items([])
    results = await collect(stream)

    assert len(results) == 0
    assert results == []


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_to_list():
    """Test StreamAdapter.to_list method."""
    stream = StreamAdapter.from_items(["a", "b", "c"])
    results = await StreamAdapter.to_list(stream)

    assert len(results) == 3
    assert all(isinstance(r, Packet) for r in results)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_stream_adapter_to_text_list():
    """Test StreamAdapter.to_text_list method."""
    stream = StreamAdapter.from_items(["hello", "world"])
    texts = await StreamAdapter.to_text_list(stream)

    assert len(texts) == 2
    assert texts == ["hello", "world"]
