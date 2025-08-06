"""
Shared test fixtures and utilities.
"""

import pytest
from typing import Dict, Any, Optional, Type

from core import Context, ProcessingResult, ProcessingStatus


@pytest.fixture
def empty_context():
    """Create an empty context for testing."""
    return Context()


@pytest.fixture
def sample_context():
    """Create a context with sample data for testing."""
    return Context({
        "query": "test query",
        "user_id": "12345",
        "data": [1, 2, 3]
    })


@pytest.fixture
def context_with_prompt():
    """Create a context with a prompt for LLM testing."""
    return Context({
        "prompt": "What is artificial intelligence?"
    })


def create_mock_result(
    status: ProcessingStatus = ProcessingStatus.COMPLETED,
    data: Any = None,
    error: Optional[Exception] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> ProcessingResult:
    """Helper function to create ProcessingResult for testing."""
    return ProcessingResult(
        status=status,
        data=data,
        error=error,
        metadata=metadata or {}
    )


def assert_result_success(result: ProcessingResult, expected_data: Any = None):
    """Helper to assert a result is successful."""
    assert result.status == ProcessingStatus.COMPLETED
    assert result.error is None
    if expected_data is not None:
        assert result.data == expected_data


def assert_result_failed(result: ProcessingResult, expected_error_type: Optional[Type[Exception]] = None):
    """Helper to assert a result failed."""
    assert result.status == ProcessingStatus.FAILED
    assert result.error is not None
    if expected_error_type:
        assert isinstance(result.error, expected_error_type)
