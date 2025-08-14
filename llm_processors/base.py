"""
Core base abstractions for the llm-processors framework.

This module provides the fundamental abstractions for building modular,
composable AI processing pipelines following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .context import Context


class ProcessingStatus(Enum):
    """Status of processing operation."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProcessingResult:
    """Result of a processing operation."""

    status: ProcessingStatus
    data: Any = None
    error: Optional[Exception] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: Optional[float] = None


class Processor(ABC):
    """
    Abstract base class for all processors.

    A processor is a single-responsibility component that performs
    one specific operation on the context data.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
    ):
        """
        Initialize processor.

        Args:
            name: Optional name for the processor
            input_key: Required input key in context data
        """
        self.name = name or self.__class__.__name__
        self.input_key = input_key or f"{self.name}_input"
        self.output_key = output_key or f"{self.name}_output"

    @abstractmethod
    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the context data.

        Args:
            context: The processing context containing data

        Returns:
            ProcessingResult: Result of the processing operation
        """
        pass

    def __repr__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(name='{self.name}', input_key='{self.input_key}', output_key='{self.output_key}')"


class Pipeline(ABC):
    """
    Abstract base class for pipelines.

    A pipeline manages the execution of multiple processors in a specific order.
    """

    @abstractmethod
    async def execute(self, context: Context) -> List[ProcessingResult]:
        """
        Execute the pipeline with the given context.

        Args:
            context: The processing context

        Returns:
            List[ProcessingResult]: Results from each processor
        """
        pass
