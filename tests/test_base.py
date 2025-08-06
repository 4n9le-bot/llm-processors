"""
Tests for the base module components.
"""

import pytest
from typing import List

from core.base import Context, ProcessingStatus, ProcessingResult, Processor
from tests.conftest import assert_result_success, assert_result_failed


class TestContext:
    """Test cases for the Context class."""
    
    def test_context_initialization_empty(self):
        """Test creating an empty context."""
        context = Context()
        assert context.get_all() == {}
        assert context.get_history() == []
    
    def test_context_initialization_with_data(self):
        """Test creating a context with initial data."""
        initial_data = {"key1": "value1", "key2": 42}
        context = Context(initial_data)
        assert context.get_all() == initial_data
    
    def test_context_get_set(self):
        """Test getting and setting values in context."""
        context = Context()
        
        # Test setting and getting
        context.set("test_key", "test_value")
        assert context.get("test_key") == "test_value"
        
        # Test getting with default
        assert context.get("nonexistent", "default") == "default"
        assert context.get("nonexistent") is None
    
    def test_context_dictionary_access(self):
        """Test dictionary-style access to context."""
        context = Context()
        
        # Test setting and getting with dictionary syntax
        context["test_key"] = "test_value"
        assert context["test_key"] == "test_value"
        
        # Test membership
        assert "test_key" in context
        assert "nonexistent" not in context
    
    def test_context_update(self):
        """Test updating context with multiple values."""
        context = Context()
        update_data = {"key1": "value1", "key2": "value2"}
        
        context.update(update_data)
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
    
    def test_context_has(self):
        """Test checking if key exists in context."""
        context = Context({"existing_key": "value"})
        
        assert context.has("existing_key") is True
        assert context.has("nonexistent_key") is False
    
    def test_context_remove(self):
        """Test removing values from context."""
        context = Context({"key1": "value1", "key2": "value2"})
        
        removed_value = context.remove("key1")
        assert removed_value == "value1"
        assert not context.has("key1")
        
        # Test removing nonexistent key
        assert context.remove("nonexistent") is None
    
    def test_context_clear(self):
        """Test clearing all data from context."""
        context = Context({"key1": "value1", "key2": "value2"})
        context.clear()
        assert context.get_all() == {}
    
    def test_context_metadata(self):
        """Test metadata functionality."""
        context = Context()
        
        context.add_metadata("meta_key", "meta_value")
        assert context.get_metadata("meta_key") == "meta_value"
        assert context.get_metadata("nonexistent", "default") == "default"
    
    def test_context_history(self):
        """Test execution history functionality."""
        context = Context()
        
        context.add_to_history("Processor1")
        context.add_to_history("Processor2")
        
        history = context.get_history()
        assert history == ["Processor1", "Processor2"]
        
        # Ensure returned history is a copy
        history.append("Modified")
        assert context.get_history() == ["Processor1", "Processor2"]
    
    def test_context_string_representation(self):
        """Test string representation of context."""
        context = Context({"key": "value"})
        context.add_metadata("meta", "data")
        context.add_to_history("TestProcessor")
        
        str_repr = str(context)
        assert "Context" in str_repr
        assert "key" in str_repr
        assert "meta" in str_repr
        assert "TestProcessor" in str_repr


class TestProcessingResult:
    """Test cases for ProcessingResult."""
    
    def test_processing_result_creation(self):
        """Test creating ProcessingResult instances."""
        result = ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            data="test_data",
            metadata={"key": "value"}
        )
        
        assert result.status == ProcessingStatus.COMPLETED
        assert result.data == "test_data"
        assert result.error is None
        assert result.metadata == {"key": "value"}
        assert result.execution_time is None
    
    def test_processing_result_with_error(self):
        """Test ProcessingResult with error."""
        error = ValueError("Test error")
        result = ProcessingResult(
            status=ProcessingStatus.FAILED,
            error=error
        )
        
        assert result.status == ProcessingStatus.FAILED
        assert result.error == error
        assert result.data is None


class TestProcessingStatus:
    """Test cases for ProcessingStatus enum."""
    
    def test_processing_status_values(self):
        """Test all ProcessingStatus enum values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.RUNNING.value == "running"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.SKIPPED.value == "skipped"


# Mock processor for testing abstract base class
class MockProcessor(Processor):
    """Mock processor for testing purposes."""
    
    def __init__(self, name: str = "MockProcessor", should_fail: bool = False):
        super().__init__(name)
        self.should_fail = should_fail
        self.process_called = False
        self.validate_called = False
    
    async def process(self, context: Context) -> ProcessingResult:
        self.process_called = True
        
        if self.should_fail:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=RuntimeError("Mock processor failed")
            )
        
        context.set("mock_output", "processed")
        return ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            data="mock_result"
        )
    
    def validate_input(self, context: Context) -> bool:
        self.validate_called = True
        return not self.should_fail
    
    def get_required_inputs(self) -> List[str]:
        return ["mock_input"] if self.should_fail else []
    
    def get_output_keys(self) -> List[str]:
        return ["mock_output"]


class TestProcessor:
    """Test cases for the Processor abstract base class."""
    
    def test_processor_initialization(self):
        """Test processor initialization."""
        processor = MockProcessor("TestProcessor")
        assert processor.name == "TestProcessor"
        
        # Test default name
        processor2 = MockProcessor()
        assert processor2.name == "MockProcessor"
    
    @pytest.mark.asyncio
    async def test_processor_process_success(self, empty_context):
        """Test successful processing."""
        processor = MockProcessor()
        result = await processor.process(empty_context)
        
        assert_result_success(result, "mock_result")
        assert processor.process_called
        assert empty_context.get("mock_output") == "processed"
    
    @pytest.mark.asyncio
    async def test_processor_process_failure(self, empty_context):
        """Test failed processing."""
        processor = MockProcessor(should_fail=True)
        result = await processor.process(empty_context)
        
        assert_result_failed(result, RuntimeError)
        assert processor.process_called
    
    def test_processor_validate_input(self, empty_context):
        """Test input validation."""
        processor = MockProcessor()
        assert processor.validate_input(empty_context) is True
        assert processor.validate_called
        
        processor_fail = MockProcessor(should_fail=True)
        assert processor_fail.validate_input(empty_context) is False
    
    def test_processor_required_inputs(self):
        """Test getting required inputs."""
        processor = MockProcessor()
        assert processor.get_required_inputs() == []
        
        processor_fail = MockProcessor(should_fail=True)
        assert processor_fail.get_required_inputs() == ["mock_input"]
    
    def test_processor_output_keys(self):
        """Test getting output keys."""
        processor = MockProcessor()
        assert processor.get_output_keys() == ["mock_output"]
    
    def test_processor_string_representation(self):
        """Test processor string representation."""
        processor = MockProcessor("TestName")
        repr_str = repr(processor)
        assert "MockProcessor" in repr_str
        assert "TestName" in repr_str
