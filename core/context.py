"""
Context module for the llm-processors framework.

This module provides the Context class that acts as a "cart" moving through
the processing pipeline, allowing data to flow between processing steps.
"""

from typing import Any, Dict, List, Optional


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
