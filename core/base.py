"""
Core base abstractions for the llm-processors framework.

This module provides the fundamental abstractions for building modular,
composable AI processing pipelines following SOLID principles.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


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


class Context:
    """
    Context acts as a "cart" that moves through the processing pipeline.
    
    Each processor can read from and write to the context, allowing
    data to flow between processing steps.
    """
    
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize context with optional initial data.
        
        Args:
            initial_data: Initial data to populate the context
        """
        self._data: Dict[str, Any] = initial_data or {}
        self._metadata: Dict[str, Any] = {}
        self._history: List[str] = []
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in context."""
        self._data[key] = value
    
    def update(self, data: Dict[str, Any]) -> None:
        """Update context with multiple key-value pairs."""
        self._data.update(data)
    
    def has(self, key: str) -> bool:
        """Check if key exists in context."""
        return key in self._data
    
    def remove(self, key: str) -> Any:
        """Remove and return value from context."""
        return self._data.pop(key, None)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all data from context."""
        return self._data.copy()
    
    def clear(self) -> None:
        """Clear all data from context."""
        self._data.clear()
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata information."""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self._metadata.get(key, default)
    
    def add_to_history(self, processor_name: str) -> None:
        """Add processor to execution history."""
        self._history.append(processor_name)
    
    def get_history(self) -> List[str]:
        """Get execution history."""
        return self._history.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to context data."""
        return self._data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style assignment to context data."""
        self._data[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator to check if key exists."""
        return key in self._data
    
    def __str__(self) -> str:
        """String representation of context for printing."""
        return f"Context(data={self._data}, metadata={self._metadata}, history={self._history})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return self.__str__()


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
