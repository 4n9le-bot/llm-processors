"""
Specialized processor implementations for the llm-processors framework.

This module provides concrete implementations of processors for common patterns.
"""

from typing import List, Optional, Dict, Any, Callable
import asyncio

from .base import Processor, ProcessingResult, ProcessingStatus
from .context import Context


class PromptProcessor(Processor):
    """
    A processor that sets up prompts for LLM processing.
    
    This processor takes a prompt template and prepares it for LLM consumption.
    """
    
    def __init__(self, prompt: str, output_key: str = "prompt", name: Optional[str] = None):
        """
        Initialize prompt processor.
        
        Args:
            prompt: The prompt text to use
            output_key: The key to store the prompt in context
            name: Optional name for the processor
        """
        super().__init__(name)
        self.prompt = prompt
        self.output_key = output_key
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt and add it to context.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Result of the prompt processing
        """
        try:
            # Add the prompt to context using the specified output key
            context.set(self.output_key, self.prompt)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=self.prompt,
                metadata={
                    "processor_type": "prompt", 
                    "prompt_length": len(self.prompt),
                    "output_key": self.output_key
                }
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def validate_input(self, context: Context) -> bool:
        """Prompt processor doesn't require any specific input."""
        return True


class LLMProcessor(Processor):
    """
    A processor that simulates LLM processing.
    
    In a real implementation, this would call an actual LLM API.
    For now, it provides a mock response.
    """
    
    def __init__(
        self, 
        model: str = "gpt-3.5-turbo", 
        input_key: str = "prompt",
        output_key: str = "llm_response",
        name: Optional[str] = None
    ):
        """
        Initialize LLM processor.
        
        Args:
            model: The model name to use (currently for documentation only)
            input_key: The key to read the prompt from context
            output_key: The key to store the LLM response in context
            name: Optional name for the processor
        """
        super().__init__(name)
        self.model = model
        self.input_key = input_key
        self.output_key = output_key
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt using LLM (currently mocked).
        
        Args:
            context: The processing context containing the prompt
            
        Returns:
            ProcessingResult: Result of the LLM processing
        """
        try:
            prompt = context.get(self.input_key)
            if not prompt:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(f"No data found for input key '{self.input_key}' in context")
                )
            
            # Mock LLM response - in real implementation, this would call an API
            mock_response = self._generate_mock_response(prompt)
            
            # Add the response to context using the specified output key
            context.set(self.output_key, mock_response)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=mock_response,
                metadata={
                    "processor_type": "llm",
                    "model": self.model,
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "response_length": len(mock_response)
                }
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response for the given prompt.
        
        Args:
            prompt: The input prompt
            
        Returns:
            str: Mock response
        """
        if "API" in prompt:
            return (
                "API（Application Programming Interface，应用程序编程接口）是一组预定义的规则和协议，"
                "它允许不同的软件应用程序之间进行通信和数据交换。\n\n"
                "简单来说，API 就像是一个'翻译官'或'服务员'：\n"
                "- 当你在餐厅点菜时，服务员帮你把需求传达给厨房\n"
                "- API 就是帮助不同程序之间传递信息的'服务员'\n\n"
                "例如，当你在手机上查看天气时，天气应用通过调用天气服务的 API 来获取最新的天气数据。"
            )
        else:
            return f"这是一个关于 '{prompt[:50]}...' 的模拟回答。在实际应用中，这里会调用真正的 LLM API。"
    
    def validate_input(self, context: Context) -> bool:
        """Validate that the required input key exists in context."""
        return context.has(self.input_key)


class NoOpProcessor(Processor):
    """
    A processor that does nothing but logs its execution.
    
    Useful for testing and debugging pipelines. Can optionally pass through
    data from input_key to output_key.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        passthrough: bool = False
    ):
        """
        Initialize no-op processor.
        
        Args:
            name: Optional name for the processor
            metadata: Optional metadata to include in results
            input_key: Optional input key to read from context
            output_key: Optional output key to write to context
            passthrough: If True and both keys provided, copies input to output
        """
        super().__init__(name)
        self._metadata = metadata or {}
        self.input_key = input_key
        self.output_key = output_key
        self.passthrough = passthrough
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Do nothing but return success, optionally with passthrough.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Success result with metadata
        """
        try:
            # If passthrough is enabled and keys are provided, copy input to output
            if (self.passthrough and self.input_key and self.output_key 
                and context.has(self.input_key)):
                input_data = context.get(self.input_key)
                context.set(self.output_key, input_data)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                metadata={
                    "processor_type": "noop",
                    "context_keys": list(context.get_all().keys()),
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "passthrough": self.passthrough,
                    **self._metadata
                }
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def validate_input(self, context: Context) -> bool:
        """
        Validate input if required.
        
        Returns True if no input required, or if required input exists.
        """
        if self.input_key:
            return context.has(self.input_key)
        return True


class DataTransformProcessor(Processor):
    """
    A generic processor that transforms data from one key to another.
    
    Useful for data type conversion, formatting, or simple transformations.
    """
    
    def __init__(
        self,
        input_key: str,
        output_key: str,
        transform_func: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None
    ):
        """
        Initialize data transform processor.
        
        Args:
            input_key: The key to read input data from context
            output_key: The key to store transformed data in context
            transform_func: Optional function to transform the data. If None, data is copied as-is
            name: Optional name for the processor
        """
        super().__init__(name)
        self.input_key = input_key
        self.output_key = output_key
        self.transform_func = transform_func or (lambda x: x)
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Transform data from input_key to output_key.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Result of the transformation
        """
        try:
            input_data = context.get(self.input_key)
            if input_data is None:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(f"No data found for input key '{self.input_key}' in context")
                )
            
            # Apply transformation
            transformed_data = self.transform_func(input_data)
            
            # Store in context
            context.set(self.output_key, transformed_data)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=transformed_data,
                metadata={
                    "processor_type": "data_transform",
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "input_type": type(input_data).__name__,
                    "output_type": type(transformed_data).__name__
                }
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def validate_input(self, context: Context) -> bool:
        """Validate that the required input key exists in context."""
        return context.has(self.input_key)
