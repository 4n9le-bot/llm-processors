"""
Tests for the Context class.
"""

import pytest

from llm_processors.context import Context


class TestContext:
    """Test cases for the Context class."""
    
    def test_context_initialization_empty(self):
        """Test creating an empty context."""
        context = Context()
        assert context.get_all() == {}
    
    def test_context_initialization_with_data(self):
        """Test creating a context with initial data."""
        initial_data = {"key1": "value1", "key2": 42}
        context = Context(initial_data)
        assert context.get_all() == initial_data
    
    def test_context_get_set(self):
        """Test getting and setting values in context."""
        context = Context()
        
        # Test setting and getting
        context.set("test_key", "test_value")
        assert context.get("test_key") == "test_value"
        
        # Test getting with default
        assert context.get("nonexistent", "default") == "default"
        assert context.get("nonexistent") is None
    
    def test_context_dictionary_access(self):
        """Test dictionary-style access to context."""
        context = Context()
        
        # Test setting and getting with dictionary syntax
        context["test_key"] = "test_value"
        assert context["test_key"] == "test_value"
        
        # Test membership
        assert "test_key" in context
        assert "nonexistent" not in context
    
    def test_context_update(self):
        """Test updating context with multiple values."""
        context = Context()
        update_data = {"key1": "value1", "key2": "value2"}
        
        context.update(update_data)
        assert context.get("key1") == "value1"
        assert context.get("key2") == "value2"
    
    def test_context_has(self):
        """Test checking if key exists in context."""
        context = Context({"existing_key": "value"})
        
        assert context.has("existing_key") is True
        assert context.has("nonexistent_key") is False
    
    def test_context_remove(self):
        """Test removing values from context."""
        context = Context({"key1": "value1", "key2": "value2"})
        
        removed_value = context.remove("key1")
        assert removed_value == "value1"
        assert not context.has("key1")
        
        # Test removing nonexistent key
        assert context.remove("nonexistent") is None
    
    def test_context_clear(self):
        """Test clearing all data from context."""
        context = Context({"key1": "value1", "key2": "value2"})
        context.clear()
        assert context.get_all() == {}
    
    def test_context_repr(self):
        """Test repr representation of context."""
        context = Context({"key": "value"})
        repr_str = repr(context)
        assert "Context" in repr_str
        assert "key" in repr_str
    
    def test_context_get_all_returns_copy(self):
        """Test that get_all returns a copy of the data."""
        context = Context({"key": "value"})
        data = context.get_all()
        data["new_key"] = "new_value"
        
        # Original context should not be modified
        assert "new_key" not in context
        assert context.get_all() == {"key": "value"}
    
    def test_context_keyerror_on_missing_key(self):
        """Test that KeyError is raised for missing keys with bracket notation."""
        context = Context()
        
        with pytest.raises(KeyError):
            _ = context["nonexistent_key"]
    
    def test_context_complex_data_types(self):
        """Test context with complex data types."""
        complex_data = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3}
        }
        
        context = Context(complex_data)
        
        assert context.get("list") == [1, 2, 3]
        assert context.get("dict") == {"nested": "value"}
        assert context.get("tuple") == (1, 2, 3)
        assert context.get("set") == {1, 2, 3}
    