"""
Tests for PromptProcessor.
"""

import pytest
from llm_processors import Packet
from llm_processors.processors import PromptProcessor, collect
from llm_processors.utils import StreamAdapter


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_basic_substitution():
    """Test basic template substitution."""
    prompt = PromptProcessor("Hello ${input}!")

    input_stream = StreamAdapter.from_items(["World"])
    results = await collect(prompt(input_stream))

    assert len(results) == 1
    assert results[0].content == "Hello World!"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_with_context():
    """Test template with additional context variables."""
    prompt = PromptProcessor(
        "As a ${role}, explain ${input}.",
        context={"role": "teacher"}
    )

    input_stream = StreamAdapter.from_items(["Python"])
    results = await collect(prompt(input_stream))

    assert len(results) == 1
    assert "As a teacher" in results[0].content
    assert "Python" in results[0].content


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_multiple_inputs():
    """Test prompt processor with multiple inputs."""
    prompt = PromptProcessor("Explain ${input} in one sentence.")

    input_stream = StreamAdapter.from_items(["Python", "Rust", "Go"])
    results = await collect(prompt(input_stream))

    assert len(results) == 3
    assert "Python" in results[0].content
    assert "Rust" in results[1].content
    assert "Go" in results[2].content


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_preserves_metadata():
    """Test that prompt processor adds metadata."""
    prompt = PromptProcessor("Test: ${input}")

    input_stream = StreamAdapter.from_items([Packet.from_text("hello", author="Alice")])
    results = await collect(prompt(input_stream))

    assert len(results) == 1
    # Check that template metadata is added
    assert results[0].metadata.get("template") == "Test: ${input}"
    # Check that source mimetype is preserved
    assert results[0].metadata.get("source_mimetype") == "text/plain"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_prompt_safe_substitute():
    """Test that missing variables don't raise errors."""
    # Using ${missing} that doesn't exist
    prompt = PromptProcessor("Hello ${input} and ${missing}!")

    input_stream = StreamAdapter.from_items(["World"])
    results = await collect(prompt(input_stream))

    # Should not raise error, ${missing} stays as-is
    assert len(results) == 1
    assert "World" in results[0].content
    assert "${missing}" in results[0].content
