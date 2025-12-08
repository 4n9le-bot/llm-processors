"""
Tests for ChatProcessor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from llm_processors import Packet
from llm_processors.processors import ChatProcessor, FromIterableProcessor, collect


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chat_processor_mock():
    """Test ChatProcessor with mocked OpenAI client."""
    # Create mock response
    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked response"
    mock_choice.finish_reason = "stop"

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_usage.total_tokens = 15

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    # Mock client
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Create processor and inject mock
    processor = ChatProcessor(api_key="test-key")
    processor.client = mock_client

    # Test
    source = FromIterableProcessor(["test input"])
    pipeline = source + processor

    results = await collect(pipeline())

    # Verify results
    assert len(results) == 1
    assert results[0].content == "Mocked response"
    assert results[0].metadata["model"] == "gpt-4o-mini"
    assert results[0].metadata["usage"]["total_tokens"] == 15

    # Verify API was called correctly
    mock_client.chat.completions.create.assert_called_once()
    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o-mini"
    assert call_args.kwargs["messages"][0]["content"] == "test input"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chat_processor_skips_non_text():
    """Test that ChatProcessor skips non-text packets."""
    # Create mock (shouldn't be called)
    mock_client = AsyncMock()

    processor = ChatProcessor(api_key="test-key")
    processor.client = mock_client

    # Send bytes packet
    source = FromIterableProcessor([Packet.from_bytes(b"binary")])
    pipeline = source + processor

    results = await collect(pipeline())

    # Should have no results (skipped)
    assert len(results) == 0

    # API should not have been called
    mock_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chat_processor_multiple_inputs():
    """Test ChatProcessor with multiple inputs."""
    # Create mock
    mock_choice = MagicMock()
    mock_choice.message.content = "Response"
    mock_choice.finish_reason = "stop"

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = None

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    processor = ChatProcessor(api_key="test-key")
    processor.client = mock_client

    # Multiple inputs
    source = FromIterableProcessor(["input1", "input2", "input3"])
    pipeline = source + processor

    results = await collect(pipeline())

    # Should have 3 results
    assert len(results) == 3
    assert all(r.content == "Response" for r in results)

    # API should have been called 3 times
    assert mock_client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
@pytest.mark.unit
async def test_chat_processor_with_parameters():
    """Test ChatProcessor respects custom parameters."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Test"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = None

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    processor = ChatProcessor(
        model="gpt-4o",
        temperature=0.5,
        max_tokens=100,
        api_key="test-key"
    )
    processor.client = mock_client

    source = FromIterableProcessor(["test"])
    pipeline = source + processor

    await collect(pipeline())

    # Check parameters were passed
    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs["model"] == "gpt-4o"
    assert call_args.kwargs["temperature"] == 0.5
    assert call_args.kwargs["max_tokens"] == 100
