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
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


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
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize processor.
        
        Args:
            name: Optional name for the processor
        """
        self.name = name or self.__class__.__name__
    
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
    
    @abstractmethod
    def validate_input(self, context: Context) -> bool:
        """
        Validate that the context contains required input data.
        
        Args:
            context: The processing context
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        pass
    
    def get_required_inputs(self) -> List[str]:
        """
        Get list of required input keys from context.
        
        Returns:
            List[str]: List of required context keys
        """
        return []
    
    def get_output_keys(self) -> List[str]:
        """
        Get list of output keys this processor will add to context.
        
        Returns:
            List[str]: List of output context keys
        """
        return []
    
    def __repr__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(name='{self.name}')"


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
    
    @abstractmethod
    def add_processor(self, processor: Processor) -> 'Pipeline':
        """
        Add a processor to the pipeline.
        
        Args:
            processor: The processor to add
            
        Returns:
            Pipeline: Self for method chaining
        """
        pass
    
    @abstractmethod
    def validate_pipeline(self) -> List[str]:
        """
        Validate the pipeline configuration.
        
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        pass
