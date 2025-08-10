"""
Core package for llm-processors framework.

This package provides the fundamental building blocks for creating
modular, composable AI processing pipelines.
"""

from .base import (
    # Core abstractions
    Processor,
    # Data structures
    ProcessingResult,
    ProcessingStatus,
)

from .context import Context

from .pipeline import (
    # Pipeline implementations
    SequentialPipeline as Pipeline,
    ParallelPipeline,
)

from .processors import (
    # Specialized processors
    PromptProcessor,
    LLMProcessor,
    NoOpProcessor,
)

__all__ = [
    # Core abstractions
    "Processor",
    "Context",
    "ProcessingResult",
    "ProcessingStatus",
    # Pipeline implementations
    "Pipeline",
    "ParallelPipeline",
    # Specialized processors
    "PromptProcessor",
    "LLMProcessor",
    "NoOpProcessor",
]
