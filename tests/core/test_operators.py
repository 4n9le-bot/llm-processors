"""
Tests for operator overloading (+ and //).
"""

import pytest
from typing import AsyncIterator

from llm_processors import Packet, BaseProcessor, collect
from llm_processors.processors import FromIterableProcessor


class UppercaseProcessor(BaseProcessor):
    """Test processor that converts text to uppercase."""

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        if packet.is_text():
            yield Packet.from_text(packet.content.upper())
        else:
            yield packet


class AddExclamationProcessor(BaseProcessor):
    """Test processor that adds exclamation to text."""

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        if packet.is_text():
            yield Packet.from_text(packet.content + "!")
        else:
            yield packet


class PrefixProcessor(BaseProcessor):
    """Test processor that adds prefix to text."""

    def __init__(self, prefix: str):
        super().__init__()
        self.prefix = prefix

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        if packet.is_text():
            yield Packet.from_text(self.prefix + packet.content)
        else:
            yield packet


@pytest.mark.asyncio
@pytest.mark.unit
async def test_sequential_composition():
    """Test sequential composition with + operator."""
    source = FromIterableProcessor(["hello", "world"])
    uppercase = UppercaseProcessor()
    exclamation = AddExclamationProcessor()

    # Compose: source + uppercase + exclamation
    pipeline = source + uppercase + exclamation

    results = await collect(pipeline())

    assert len(results) == 2
    assert results[0].content == "HELLO!"
    assert results[1].content == "WORLD!"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parallel_composition():
    """Test parallel composition with // operator."""
    source = FromIterableProcessor(["test"])
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    # Compose: source + (proc1 // proc2)
    pipeline = source + (proc1 // proc2)

    results = await collect(pipeline())

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
    source = FromIterableProcessor(["test"])
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    pipeline = source + (proc1 // proc2)
    results = await collect(pipeline())

    # All results should have substream_name
    for result in results:
        assert result.substream_name is not None
        assert "branch_" in result.substream_name


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chaining_multiple_operators():
    """Test chaining multiple + operators."""
    source = FromIterableProcessor(["hi"])
    p1 = PrefixProcessor("1:")
    p2 = PrefixProcessor("2:")
    p3 = PrefixProcessor("3:")

    # Chain multiple processors
    pipeline = source + p1 + p2 + p3

    results = await collect(pipeline())

    assert len(results) == 1
    assert results[0].content == "3:2:1:hi"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_complex_composition():
    """Test complex composition mixing + and //."""
    source = FromIterableProcessor(["test"])

    upper = UppercaseProcessor()
    lower = BaseProcessor()  # Pass-through
    exclaim = AddExclamationProcessor()

    # Complex: source + ((upper + exclaim) // lower)
    pipeline = source + ((upper + exclaim) // lower)

    results = await collect(pipeline())

    # Should have 2 results
    assert len(results) == 2

    contents = {r.content for r in results}
    assert "TEST!" in contents  # From upper + exclaim
    assert "test" in contents  # From lower (pass-through)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_parallel_with_multiple_inputs():
    """Test parallel processing with multiple input packets."""
    source = FromIterableProcessor(["a", "b", "c"])
    proc1 = UppercaseProcessor()
    proc2 = AddExclamationProcessor()

    pipeline = source + (proc1 // proc2)

    results = await collect(pipeline())

    # Should have 6 results (3 inputs * 2 branches)
    assert len(results) == 6

    # Count by transformation
    uppercase_count = sum(1 for r in results if r.content.isupper())
    exclaim_count = sum(1 for r in results if r.content.endswith("!"))

    assert uppercase_count == 3
    assert exclaim_count == 3
