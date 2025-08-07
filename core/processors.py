"""
Specialized processor implementations for the llm-processors framework.

This module provides concrete implementations of processors for common patterns.
"""

from typing import List, Optional, Dict, Any
import asyncio

from .base import Processor, ProcessingResult, ProcessingStatus
from .context import Context


class PromptProcessor(Processor):
    """
    A processor that sets up prompts for LLM processing.
    
    This processor takes a prompt template and prepares it for LLM consumption.
    """
    
    def __init__(self, prompt: str, name: Optional[str] = None):
        """
        Initialize prompt processor.
        
        Args:
            prompt: The prompt text to use
            name: Optional name for the processor
        """
        super().__init__(name)
        self.prompt = prompt
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt and add it to context.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Result of the prompt processing
        """
        try:
            # Add the prompt to context for LLM processor to use
            context.set("prompt", self.prompt)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=self.prompt,
                metadata={"processor_type": "prompt", "prompt_length": len(self.prompt)}
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
    
    def validate_input(self, context: Context) -> bool:
        """Prompt processor doesn't require any specific input."""
        return True
    
    def get_required_inputs(self) -> List[str]:
        """No required inputs."""
        return []
    
    def get_output_keys(self) -> List[str]:
        """Outputs the prompt."""
        return ["prompt"]


class LLMProcessor(Processor):
    """
    A processor that simulates LLM processing.
    
    In a real implementation, this would call an actual LLM API.
    For now, it provides a mock response.
    """
    
    def __init__(self, model: str = "gpt-3.5-turbo", name: Optional[str] = None):
        """
        Initialize LLM processor.
        
        Args:
            model: The model name to use (currently for documentation only)
            name: Optional name for the processor
        """
        super().__init__(name)
        self.model = model
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt using LLM (currently mocked).
        
        Args:
            context: The processing context containing the prompt
            
        Returns:
            ProcessingResult: Result of the LLM processing
        """
        try:
            prompt = context.get("prompt")
            if not prompt:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError("No prompt found in context")
                )
            
            # Mock LLM response - in real implementation, this would call an API
            mock_response = self._generate_mock_response(prompt)
            
            # Add the response to context
            context.set("llm_response", mock_response)
            
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=mock_response,
                metadata={
                    "processor_type": "llm",
                    "model": self.model,
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
        """Validate that prompt exists in context."""
        return context.has("prompt")
    
    def get_required_inputs(self) -> List[str]:
        """Requires prompt as input."""
        return ["prompt"]
    
    def get_output_keys(self) -> List[str]:
        """Outputs the LLM response."""
        return ["llm_response"]


class NoOpProcessor(Processor):
    """
    A processor that does nothing but logs its execution.
    
    Useful for testing and debugging pipelines.
    """
    
    def __init__(self, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize no-op processor.
        
        Args:
            name: Optional name for the processor
            metadata: Optional metadata to include in results
        """
        super().__init__(name)
        self._metadata = metadata or {}
    
    async def process(self, context: Context) -> ProcessingResult:
        """
        Do nothing but return success.
        
        Args:
            context: The processing context
            
        Returns:
            ProcessingResult: Success result with metadata
        """
        return ProcessingResult(
            status=ProcessingStatus.COMPLETED,
            metadata={
                "processor_type": "noop",
                "context_keys": list(context.get_all().keys()),
                **self._metadata
            }
        )
    
    def validate_input(self, context: Context) -> bool:
        """Always returns True since no-op requires no specific inputs."""
        return True
    
    def get_required_inputs(self) -> List[str]:
        """No required inputs."""
        return []
    
    def get_output_keys(self) -> List[str]:
        """No outputs."""
        return []
