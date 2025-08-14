"""
Tests for PromptProcessor.
"""

import pytest

from llm_processors.processors.prompt_processor import PromptProcessor
from tests.conftest import assert_result_success, assert_result_failed


class TestPromptProcessor:
    """Test cases for PromptProcessor."""

    def test_prompt_processor_creation(self):
        """Test creating PromptProcessor instances."""
        # Test with minimal parameters
        processor = PromptProcessor("Hello, world!")
        assert processor.name == "prompt"
        assert processor.prompt == "Hello, world!"
        assert processor.input_key == "prompt_input"
        assert processor.output_key == "prompt_output"

        # Test with custom parameters
        processor = PromptProcessor(
            prompt="Custom prompt",
            name="custom_prompt",
            input_key="variables",
            output_key="rendered_prompt"
        )
        assert processor.name == "custom_prompt"
        assert processor.prompt == "Custom prompt"
        assert processor.input_key == "variables"
        assert processor.output_key == "rendered_prompt"

    @pytest.mark.asyncio
    async def test_simple_prompt_no_template(self, empty_context):
        """Test processing a simple prompt without templating."""
        prompt_text = "What is artificial intelligence?"
        processor = PromptProcessor(prompt_text)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == prompt_text
        assert empty_context.get("prompt_output") == prompt_text
        assert result.metadata["prompt_length"] == len(prompt_text)
        assert result.metadata["template_vars"] == {}

    @pytest.mark.asyncio
    async def test_jinja2_template_rendering(self, empty_context):
        """Test Jinja2 template rendering with variables."""
        template = "Hello, {{ name }}! Your age is {{ age }}."
        processor = PromptProcessor(
            prompt=template,
            input_key="user_data",
            output_key="greeting"
        )
        
        # Add template variables to context
        empty_context.set("user_data", {"name": "Alice", "age": 30})
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        expected_output = "Hello, Alice! Your age is 30."
        assert result.data == expected_output
        assert empty_context.get("greeting") == expected_output
        assert result.metadata["template_vars"] == {"name": "Alice", "age": 30}

    @pytest.mark.asyncio
    async def test_complex_jinja2_template(self, empty_context):
        """Test complex Jinja2 template with loops and conditions."""
        template = """
        {% if user.name %}
        Hello, {{ user.name }}!
        {% endif %}
        
        Your tasks:
        {% for task in tasks %}
        - {{ task.title }} ({{ task.status }})
        {% endfor %}
        """.strip()
        
        processor = PromptProcessor(
            prompt=template,
            input_key="template_data"
        )
        
        template_data = {
            "user": {"name": "Bob"},
            "tasks": [
                {"title": "Write tests", "status": "in_progress"},
                {"title": "Review code", "status": "pending"}
            ]
        }
        empty_context.set("template_data", template_data)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert "Hello, Bob!" in result.data
        assert "Write tests (in_progress)" in result.data
        assert "Review code (pending)" in result.data

    @pytest.mark.asyncio
    async def test_template_with_missing_input_key(self, empty_context):
        """Test template rendering when input_key is not in context."""
        template = "Hello, {{ name }}!"
        processor = PromptProcessor(
            prompt=template,
            input_key="missing_key"
        )
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        # Template should render with empty variables
        assert result.data == "Hello, !"
        assert result.metadata["template_vars"] == {}

    @pytest.mark.asyncio
    async def test_template_without_input_key(self, empty_context):
        """Test template rendering without input_key specified."""
        template = "Static prompt without variables"
        processor = PromptProcessor(prompt=template, input_key=None)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == template
        assert result.metadata["template_vars"] == {}

    @pytest.mark.asyncio
    async def test_template_syntax_error(self, empty_context):
        """Test handling of Jinja2 template syntax errors."""
        invalid_template = "Hello, {{ name }!"  # Missing closing brace
        processor = PromptProcessor(prompt=invalid_template)
        
        result = await processor.process(empty_context)
        
        assert_result_failed(result)
        assert isinstance(result.error, ValueError)
        assert "Template rendering error" in str(result.error)

    @pytest.mark.asyncio
    async def test_template_with_filters(self, empty_context):
        """Test Jinja2 template with built-in filters."""
        template = "Hello, {{ name|upper }}! Today is {{ date|default('unknown') }}."
        processor = PromptProcessor(
            prompt=template,
            input_key="data"
        )
        
        empty_context.set("data", {"name": "alice"})
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == "Hello, ALICE! Today is unknown."

    @pytest.mark.asyncio
    async def test_empty_template(self, empty_context):
        """Test processing an empty template."""
        processor = PromptProcessor(prompt="")
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == ""
        assert result.metadata["prompt_length"] == 0

    @pytest.mark.asyncio
    async def test_whitespace_template(self, empty_context):
        """Test processing a template with only whitespace."""
        template = "   \n\t  "
        processor = PromptProcessor(prompt=template)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == template
        assert result.metadata["prompt_length"] == len(template)

    @pytest.mark.asyncio
    async def test_unicode_template(self, empty_context):
        """Test processing templates with Unicode characters."""
        template = "Bonjour {{ nom }} ! Ça va ? 🚀"
        processor = PromptProcessor(
            prompt=template,
            input_key="french_data"
        )
        
        empty_context.set("french_data", {"nom": "Marie"})
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == "Bonjour Marie ! Ça va ? 🚀"

    @pytest.mark.asyncio
    async def test_nested_data_access(self, empty_context):
        """Test accessing nested data in templates."""
        template = "User: {{ user.profile.name }} ({{ user.profile.role }})"
        processor = PromptProcessor(
            prompt=template,
            input_key="nested_data"
        )
        
        nested_data = {
            "user": {
                "profile": {
                    "name": "John Doe",
                    "role": "developer"
                }
            }
        }
        empty_context.set("nested_data", nested_data)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.data == "User: John Doe (developer)"

    @pytest.mark.asyncio
    async def test_processor_metadata(self, empty_context):
        """Test processor metadata generation."""
        template = "Test prompt with {{ variable }}"
        processor = PromptProcessor(
            prompt=template,
            name="test_prompt",
            input_key="test_input",
            output_key="test_output"
        )
        
        empty_context.set("test_input", {"variable": "value"})
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        metadata = result.metadata
        assert metadata["input_key"] == "test_input"
        assert metadata["output_key"] == "test_output"
        assert metadata["template_vars"] == {"variable": "value"}
        assert metadata["prompt_length"] == len("Test prompt with value")

    @pytest.mark.asyncio
    async def test_multiple_processing_calls(self, empty_context):
        """Test multiple calls to the same processor with different data."""
        template = "Processing {{ item }}"
        processor = PromptProcessor(
            prompt=template,
            input_key="item_data"
        )
        
        # First call
        empty_context.set("item_data", {"item": "task1"})
        result1 = await processor.process(empty_context)
        assert_result_success(result1)
        assert result1.data == "Processing task1"
        
        # Second call with different data
        empty_context.set("item_data", {"item": "task2"})
        result2 = await processor.process(empty_context)
        assert_result_success(result2)
        assert result2.data == "Processing task2"
        
        # Verify context was updated correctly
        assert empty_context.get("prompt_output") == "Processing task2"

    def test_processor_repr(self):
        """Test string representation of PromptProcessor."""
        # Test with minimal parameters
        processor = PromptProcessor("test prompt")
        repr_str = repr(processor)
        assert "PromptProcessor" in repr_str
        assert "name='prompt'" in repr_str
        assert "input_key='prompt_input'" in repr_str
        assert "output_key='prompt_output'" in repr_str
        
        # Test with custom parameters
        processor = PromptProcessor(
            "test",
            name="custom",
            input_key="in",
            output_key="out"
        )
        repr_str = repr(processor)
        assert "name='custom'" in repr_str
        assert "input_key='in'" in repr_str
        assert "output_key='out'" in repr_str

    @pytest.mark.asyncio
    async def test_template_with_list_data(self, empty_context):
        """Test template with list data structures."""
        template = """
        Items: {{ items|join(', ') }}
        Count: {{ items|length }}
        """.strip()
        
        processor = PromptProcessor(
            prompt=template,
            input_key="list_data"
        )
        
        empty_context.set("list_data", {"items": ["apple", "banana", "cherry"]})
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert "Items: apple, banana, cherry" in result.data
        assert "Count: 3" in result.data

    @pytest.mark.asyncio
    async def test_template_with_conditional_rendering(self, empty_context):
        """Test template with conditional rendering logic."""
        template = """
        {% if user.is_premium %}
        Welcome, premium user {{ user.name }}!
        {% else %}
        Hello, {{ user.name }}. Consider upgrading to premium.
        {% endif %}
        """.strip()
        
        processor = PromptProcessor(
            prompt=template,
            input_key="user_info"
        )
        
        # Test premium user
        empty_context.set("user_info", {
            "user": {"name": "Alice", "is_premium": True}
        })
        result = await processor.process(empty_context)
        assert_result_success(result)
        assert "Welcome, premium user Alice!" in result.data
        
        # Test regular user
        empty_context.set("user_info", {
            "user": {"name": "Bob", "is_premium": False}
        })
        result = await processor.process(empty_context)
        assert_result_success(result)
        assert "Hello, Bob. Consider upgrading" in result.data

    @pytest.mark.asyncio
    async def test_exception_handling(self, empty_context):
        """Test handling of unexpected exceptions during processing."""
        # This test simulates an unexpected error by using a template
        # that would cause an error during rendering (accessing undefined attribute)
        template = "{{ undefined_var.some_attribute }}"
        processor = PromptProcessor(
            prompt=template,
            input_key="empty_data"
        )
        
        empty_context.set("empty_data", {})
        
        result = await processor.process(empty_context)
        
        # The processor should handle the UndefinedError gracefully
        # Jinja2 raises UndefinedError for undefined variables
        assert_result_failed(result)
        assert "undefined" in str(result.error).lower()
