"""
Tests for specialized processors.
"""

import pytest

from core.processors import PromptProcessor, LLMProcessor, NoOpProcessor
from core.base import ProcessingStatus
from tests.conftest import assert_result_success, assert_result_failed


class TestPromptProcessor:
    """Test cases for PromptProcessor."""
    
    def test_prompt_processor_initialization(self):
        """Test PromptProcessor initialization."""
        prompt = "Test prompt"
        processor = PromptProcessor(prompt=prompt)
        
        assert processor.prompt == prompt
        assert processor.name == "PromptProcessor"
        
        # Test with custom name
        processor_named = PromptProcessor(prompt=prompt, name="CustomPrompt")
        assert processor_named.name == "CustomPrompt"
    
    @pytest.mark.asyncio
    async def test_prompt_processor_process_success(self, empty_context):
        """Test successful prompt processing."""
        prompt = "What is machine learning?"
        processor = PromptProcessor(prompt=prompt)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result, prompt)
        assert empty_context.get("prompt") == prompt
        assert result.metadata["processor_type"] == "prompt"
        assert result.metadata["prompt_length"] == len(prompt)
    
    def test_prompt_processor_validate_input(self, empty_context):
        """Test prompt processor input validation."""
        processor = PromptProcessor(prompt="test")
        assert processor.validate_input(empty_context) is True
    

class TestLLMProcessor:
    """Test cases for LLMProcessor."""
    
    def test_llm_processor_initialization(self):
        """Test LLMProcessor initialization."""
        processor = LLMProcessor()
        assert processor.model == "gpt-3.5-turbo"
        assert processor.name == "LLMProcessor"
        
        # Test with custom model and name
        processor_custom = LLMProcessor(model="gpt-4", name="CustomLLM")
        assert processor_custom.model == "gpt-4"
        assert processor_custom.name == "CustomLLM"
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_success_api_prompt(self, context_with_prompt):
        """Test LLM processor with API-related prompt."""
        context_with_prompt.set("prompt", "What is an API?")
        processor = LLMProcessor()
        
        result = await processor.process(context_with_prompt)
        
        assert_result_success(result)
        response = context_with_prompt.get("llm_response")
        assert response is not None
        assert "API" in response
        assert "应用程序编程接口" in response
        assert result.metadata["processor_type"] == "llm"
        assert result.metadata["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_success_generic_prompt(self, context_with_prompt):
        """Test LLM processor with generic prompt."""
        generic_prompt = "Tell me about Python programming"
        context_with_prompt.set("prompt", generic_prompt)
        processor = LLMProcessor()
        
        result = await processor.process(context_with_prompt)
        
        assert_result_success(result)
        response = context_with_prompt.get("llm_response")
        assert response is not None
        assert "模拟回答" in response
        assert generic_prompt[:20] in response
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_no_prompt(self, empty_context):
        """Test LLM processor when no prompt is provided."""
        processor = LLMProcessor()
        
        result = await processor.process(empty_context)
        
        assert_result_failed(result, ValueError)
        assert "No data found for input key 'prompt'" in str(result.error)
    
    def test_llm_processor_validate_input_success(self, context_with_prompt):
        """Test LLM processor input validation with valid input."""
        processor = LLMProcessor()
        assert processor.validate_input(context_with_prompt) is True
    
    def test_llm_processor_validate_input_failure(self, empty_context):
        """Test LLM processor input validation with missing prompt."""
        processor = LLMProcessor()
        assert processor.validate_input(empty_context) is False
    
    def test_llm_processor_mock_response_generation(self):
        """Test the mock response generation logic."""
        processor = LLMProcessor()
        
        # Test API prompt
        api_response = processor._generate_mock_response("What is an API?")
        assert "API" in api_response
        assert "应用程序编程接口" in api_response
        
        # Test generic prompt
        generic_response = processor._generate_mock_response("Random question")
        assert "模拟回答" in generic_response
        assert "Random question" in generic_response


class TestNoOpProcessor:
    """Test cases for NoOpProcessor."""
    
    def test_noop_processor_initialization(self):
        """Test NoOpProcessor initialization."""
        processor = NoOpProcessor()
        assert processor.name == "NoOpProcessor"
        assert processor._metadata == {}
        
        # Test with custom name and metadata
        custom_metadata = {"test": "value"}
        processor_custom = NoOpProcessor(name="CustomNoOp", metadata=custom_metadata)
        assert processor_custom.name == "CustomNoOp"
        assert processor_custom._metadata == custom_metadata
    
    @pytest.mark.asyncio
    async def test_noop_processor_process(self, sample_context):
        """Test NoOpProcessor processing."""
        processor = NoOpProcessor()
        
        result = await processor.process(sample_context)
        
        assert_result_success(result)
        assert result.metadata["processor_type"] == "noop"
        assert "context_keys" in result.metadata
        assert set(result.metadata["context_keys"]) == {"query", "user_id", "data"}
    
    @pytest.mark.asyncio
    async def test_noop_processor_with_custom_metadata(self, empty_context):
        """Test NoOpProcessor with custom metadata."""
        custom_metadata = {"custom_key": "custom_value"}
        processor = NoOpProcessor(metadata=custom_metadata)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.metadata["processor_type"] == "noop"
        assert result.metadata["custom_key"] == "custom_value"
    
    def test_noop_processor_validate_input(self, empty_context, sample_context):
        """Test NoOpProcessor input validation."""
        processor = NoOpProcessor()
        assert processor.validate_input(empty_context) is True
        assert processor.validate_input(sample_context) is True
    