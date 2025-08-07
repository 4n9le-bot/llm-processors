"""
Core package for llm-processors framework.

This package provides the fundamental building blocks for creating
modular, composable AI processing pipelines.
"""

from .base import (
    # Core abstractions
    Processor,
    Pipeline, 
    
    # Data structures
    ProcessingResult,
    ProcessingStatus,
)

from .context import Context

from .pipeline import (
    # Pipeline implementations
    SequentialPipeline,
    ParallelPipeline,
    Pipeline,  # Alias for SequentialPipeline
)

from .processors import (
    # Specialized processors
    PromptProcessor,
    LLMProcessor,
    NoOpProcessor,
    DataTransformProcessor,
)

__all__ = [
    # Core abstractions
    "Processor",
    "Pipeline",
    "Context",
    "ProcessingResult", 
    "ProcessingStatus",
    
    # Pipeline implementations
    "SequentialPipeline",
    "ParallelPipeline",
    
    # Specialized processors
    "PromptProcessor",
    "LLMProcessor", 
    "NoOpProcessor",
    "DataTransformProcessor",
]
