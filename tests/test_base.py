"""
Tests for the base module components (excluding Context).
"""

import pytest

from core.base import ProcessingStatus, ProcessingResult
from tests.conftest import assert_result_success, assert_result_failed, MockProcessor


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
    
    def test_processor_string_representation(self):
        """Test processor string representation."""
        processor = MockProcessor("TestName")
        repr_str = repr(processor)
        assert "MockProcessor" in repr_str
        assert "TestName" in repr_str
