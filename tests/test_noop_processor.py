"""
Tests for NoOpProcessor.
"""

import pytest

from llm_processors import Context
from llm_processors.processors.noop_processor import NoOpProcessor
from tests.conftest import assert_result_success, assert_result_failed


class TestNoOpProcessor:
    """Test cases for NoOpProcessor."""

    def test_noop_processor_creation(self):
        """Test creating NoOpProcessor instances."""
        # Test with default parameters - base class provides defaults
        processor = NoOpProcessor()
        assert processor.name == "NoOpProcessor"
        assert processor.input_key == "NoOpProcessor_input"
        assert processor.output_key == "NoOpProcessor_output"

        # Test with custom parameters
        processor = NoOpProcessor(
            name="test_noop",
            input_key="input",
            output_key="output"
        )
        assert processor.name == "test_noop"
        assert processor.input_key == "input"
        assert processor.output_key == "output"

    @pytest.mark.asyncio
    async def test_noop_processor_basic_execution(self, empty_context):
        """Test basic execution of NoOpProcessor."""
        processor = NoOpProcessor()
        result = await processor.process(empty_context)

        assert_result_success(result)
        assert result.metadata["input_key"] == "NoOpProcessor_input"
        assert result.metadata["output_key"] == "NoOpProcessor_output"
        assert result.metadata["context_keys"] == []

    @pytest.mark.asyncio
    async def test_noop_processor_with_context_data(self, sample_context):
        """Test NoOpProcessor with existing context data."""
        processor = NoOpProcessor(name="test_processor")
        result = await processor.process(sample_context)

        assert_result_success(result)
        assert "query" in result.metadata["context_keys"]
        assert "user_id" in result.metadata["context_keys"]
        assert "data" in result.metadata["context_keys"]

    @pytest.mark.asyncio
    async def test_noop_processor_passthrough_success(self):
        """Test NoOpProcessor with successful data passthrough."""
        context = Context({"input_data": "test_value"})
        processor = NoOpProcessor(
            name="passthrough_processor",
            input_key="input_data",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert context.get("output_data") == "test_value"
        assert result.metadata["input_key"] == "input_data"
        assert result.metadata["output_key"] == "output_data"
        assert "input_data" in result.metadata["context_keys"]
        assert "output_data" in result.metadata["context_keys"]

    @pytest.mark.asyncio
    async def test_noop_processor_passthrough_missing_input_key(self):
        """Test NoOpProcessor when input_key doesn't exist in context."""
        context = Context({"other_data": "value"})
        processor = NoOpProcessor(
            name="missing_input_processor",
            input_key="missing_key",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        # Should not create output_data since input_key doesn't exist
        assert not context.has("output_data")
        assert result.metadata["input_key"] == "missing_key"
        assert result.metadata["output_key"] == "output_data"

    @pytest.mark.asyncio
    async def test_noop_processor_only_input_key(self):
        """Test NoOpProcessor with only input_key specified."""
        context = Context({"input_data": "test_value"})
        processor = NoOpProcessor(
            name="input_only_processor",
            input_key="input_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert result.metadata["input_key"] == "input_data"
        assert result.metadata["output_key"] == "input_only_processor_output"
        # Passthrough should happen since both keys are set
        assert context.get("input_only_processor_output") == "test_value"

    @pytest.mark.asyncio
    async def test_noop_processor_only_output_key(self):
        """Test NoOpProcessor with only output_key specified."""
        context = Context({"some_data": "value"})
        processor = NoOpProcessor(
            name="output_only_processor",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert result.metadata["input_key"] == "output_only_processor_input"
        assert result.metadata["output_key"] == "output_data"
        # No passthrough should happen since input_key doesn't exist in context
        assert not context.has("output_data")

    @pytest.mark.asyncio
    async def test_noop_processor_complex_data_passthrough(self):
        """Test NoOpProcessor with complex data structures."""
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "string": "test"
        }
        context = Context({"complex_input": complex_data})
        processor = NoOpProcessor(
            input_key="complex_input",
            output_key="complex_output"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert context.get("complex_output") == complex_data
        # Verify it's the same object reference (passthrough)
        assert context.get("complex_output") is complex_data

    @pytest.mark.asyncio
    async def test_noop_processor_overwrite_existing_output(self):
        """Test NoOpProcessor overwrites existing output key."""
        context = Context({
            "input_data": "new_value",
            "output_data": "old_value"
        })
        processor = NoOpProcessor(
            input_key="input_data",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert context.get("output_data") == "new_value"

    @pytest.mark.asyncio
    async def test_noop_processor_metadata_content(self):
        """Test NoOpProcessor metadata contains expected information."""
        context = Context({"key1": "value1", "key2": "value2"})
        processor = NoOpProcessor(
            name="metadata_test",
            input_key="key1",
            output_key="output"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        metadata = result.metadata
        assert metadata["input_key"] == "key1"
        assert metadata["output_key"] == "output"
        assert set(metadata["context_keys"]) == {"key1", "key2", "output"}

    @pytest.mark.asyncio
    async def test_noop_processor_exception_handling(self):
        """Test NoOpProcessor handles exceptions gracefully."""
        # Create a mock context that raises an exception
        class FaultyContext(Context):
            def has(self, key):
                raise RuntimeError("Context error")
        
        faulty_context = FaultyContext()
        processor = NoOpProcessor(
            input_key="test_key",
            output_key="output_key"
        )
        
        result = await processor.process(faulty_context)

        assert_result_failed(result)
        assert isinstance(result.error, RuntimeError)
        assert str(result.error) == "Context error"

    @pytest.mark.asyncio
    async def test_noop_processor_none_values(self):
        """Test NoOpProcessor with None values in context."""
        context = Context({"input_data": None})
        processor = NoOpProcessor(
            input_key="input_data",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert context.get("output_data") is None

    @pytest.mark.asyncio
    async def test_noop_processor_empty_string_passthrough(self):
        """Test NoOpProcessor with empty string."""
        context = Context({"input_data": ""})
        processor = NoOpProcessor(
            input_key="input_data",
            output_key="output_data"
        )
        
        result = await processor.process(context)

        assert_result_success(result)
        assert context.get("output_data") == ""
