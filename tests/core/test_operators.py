"""
Tests for operator overloading (+ and //).
"""

import pytest
from typing import AsyncIterator, AsyncIterable

from llm_processors import Packet, BaseProcessor, collect
from llm_processors.utils import StreamAdapter


class UppercaseProcessor(BaseProcessor):
    """Test processor that converts text to uppercase."""

    async def _process_stream(self, stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        async for packet in stream:
            if packet.is_text():
                yield Packet.from_text(packet.content.upper())
            else:
                yield packet


class AddExclamationProcessor(BaseProcessor):
    """Test processor that adds exclamation to text."""

    async def _process_stream(self, stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        async for packet in stream:
            if packet.is_text():
                yield Packet.from_text(packet.content + "!")
            else:
                yield packet


class PrefixProcessor(BaseProcessor):
    """Test processor that adds prefix to text."""

    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    async def _process_stream(self, stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        async for packet in stream:
            if packet.is_text():
                yield Packet.from_text(self.prefix + packet.content)
            else:
                yield packet


class PassThroughProcessor(BaseProcessor):
    """Test processor that passes through all packets unchanged."""

    async def _process_stream(self, stream: AsyncIterable[Packet]) -> AsyncIterator[Packet]:
        async for packet in stream:
            yield packet


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sequential_composition():
    """Test sequential composition with + operator."""
    uppercase = UppercaseProcessor()
    exclamation = AddExclamationProcessor()

    # Compose: uppercase + exclamation
    pipeline = uppercase + exclamation

    input_stream = StreamAdapter.from_items(["hello", "world"])
    results = await collect(pipeline(input_stream))

    assert len(results) == 2
    assert results[0].content == "HELLO!"
    assert results[1].content == "WORLD!"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parallel_composition():
    """Test parallel composition with // operator."""
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    # Compose: proc1 // proc2
    pipeline = proc1 // proc2

    input_stream = StreamAdapter.from_items(["test"])
    results = await collect(pipeline(input_stream))

    # Should have 2 results (one from each branch)
    assert len(results) == 2

    # Results can be in any order due to parallel execution
    contents = {r.content for r in results}
    assert "TEST" in contents  # From uppercase
    assert "test!" in contents  # From exclamation


@pytest.mark.asyncio
@pytest.mark.unit
async def test_substream_tagging():
    """Test that parallel branches tag results with substream_name."""
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    pipeline = proc1 // proc2

    input_stream = StreamAdapter.from_items(["test"])
    results = await collect(pipeline(input_stream))

    # All results should have substream_name
    for result in results:
        assert result.substream_name is not None
        assert "branch_" in result.substream_name


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chaining_multiple_operators():
    """Test chaining multiple + operators."""
    p1 = PrefixProcessor("1:")
    p2 = PrefixProcessor("2:")
    p3 = PrefixProcessor("3:")

    # Chain multiple processors
    pipeline = p1 + p2 + p3

    input_stream = StreamAdapter.from_items(["hi"])
    results = await collect(pipeline(input_stream))

    assert len(results) == 1
    assert results[0].content == "3:2:1:hi"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complex_composition():
    """Test complex composition mixing + and //."""
    upper = UppercaseProcessor()
    passthrough = PassThroughProcessor()
    exclaim = AddExclamationProcessor()

    # Complex: (upper + exclaim) // passthrough
    pipeline = (upper + exclaim) // passthrough

    input_stream = StreamAdapter.from_items(["test"])
    results = await collect(pipeline(input_stream))

    # Should have 2 results
    assert len(results) == 2

    contents = {r.content for r in results}
    assert "TEST!" in contents  # From upper + exclaim
    assert "test" in contents  # From passthrough


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parallel_with_multiple_inputs():
    """Test parallel processing with multiple input packets."""
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    pipeline = proc1 // proc2

    input_stream = StreamAdapter.from_items(["a", "b", "c"])
    results = await collect(pipeline(input_stream))

    # Should have 6 results (3 inputs * 2 branches)
    assert len(results) == 6

    # Count by transformation
    uppercase_count = sum(1 for r in results if r.content.isupper())
    exclaim_count = sum(1 for r in results if r.content.endswith("!"))

    assert uppercase_count == 3
    assert exclaim_count == 3
