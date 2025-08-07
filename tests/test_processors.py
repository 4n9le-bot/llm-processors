"""
Tests for specialized processors.
"""

import pytest

from core.processors import PromptProcessor, LLMProcessor, NoOpProcessor, DataTransformProcessor
from core.base import ProcessingStatus
from tests.conftest import assert_result_success, assert_result_failed


class TestPromptProcessor:
    """Test cases for PromptProcessor."""
    
    def test_prompt_processor_initialization(self):
        """Test PromptProcessor initialization."""
        prompt = "Test prompt"
        processor = PromptProcessor(prompt=prompt)
        
        assert processor.prompt == prompt
        assert processor.name == "PromptProcessor"
        assert processor.input_key is None
        assert processor.template_vars == {}
        
        # Test with custom name and input_key
        processor_named = PromptProcessor(
            prompt=prompt, 
            name="CustomPrompt",
            input_key="template_data"
        )
        assert processor_named.name == "CustomPrompt"
        assert processor_named.input_key == "template_data"
    
    @pytest.mark.asyncio
    async def test_prompt_processor_process_success(self, empty_context):
        """Test successful prompt processing."""
        prompt = "What is machine learning?"
        processor = PromptProcessor(prompt=prompt)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result, prompt)
        assert empty_context.get("prompt") == prompt
        assert result.metadata["processor_type"] == "prompt"
        assert result.metadata["prompt_length"] == len(prompt)
        assert result.metadata["is_template"] is False
    
    def test_prompt_processor_validate_input(self, empty_context):
        """Test prompt processor input validation."""
        processor = PromptProcessor(prompt="test")
        assert processor.validate_input(empty_context) is True


class TestPromptProcessorJinja2:
    """Test cases for PromptProcessor with Jinja2 template functionality."""
    
    @pytest.mark.asyncio
    async def test_simple_template_rendering(self, empty_context):
        """Test simple Jinja2 template rendering."""
        template = "Hello {{name}}! Welcome to {{service}}."
        processor = PromptProcessor(
            prompt=template,
            template_vars={"name": "Alice", "service": "AI Assistant"}
        )
        
        result = await processor.process(empty_context)
        
        expected = "Hello Alice! Welcome to AI Assistant."
        assert_result_success(result, expected)
        assert empty_context.get("prompt") == expected
        assert result.metadata["is_template"] is True
        # Check that required variables are present (order may vary)
        assert set(result.metadata["template_vars_needed"]) == {"name", "service"}
    
    @pytest.mark.asyncio
    async def test_input_key_template_vars(self, empty_context):
        """Test getting template variables from context via input_key."""
        template = "User {{user_name}} asked about {{topic}} with difficulty {{level}}."
        processor = PromptProcessor(
            prompt=template,
            input_key="template_data"
        )
        
        # Set template data in context
        empty_context.set("template_data", {
            "user_name": "Bob",
            "topic": "machine learning", 
            "level": "intermediate"
        })
        
        result = await processor.process(empty_context)
        
        expected = "User Bob asked about machine learning with difficulty intermediate."
        assert_result_success(result, expected)
        assert result.metadata["is_template"] is True
    
    @pytest.mark.asyncio
    async def test_mixed_template_variables(self, empty_context):
        """Test mixing static template_vars and input_key variables."""
        template = "{{greeting}}, {{user_name}}! Today's topic is {{topic}} at {{time}}."
        processor = PromptProcessor(
            prompt=template,
            input_key="dynamic_vars",
            template_vars={"greeting": "Hello", "time": "2:00 PM"}
        )
        
        empty_context.set("dynamic_vars", {
            "user_name": "Charlie",
            "topic": "deep learning"
        })
        
        result = await processor.process(empty_context)
        
        expected = "Hello, Charlie! Today's topic is deep learning at 2:00 PM."
        assert_result_success(result, expected)
    
    @pytest.mark.asyncio
    async def test_variable_priority(self, empty_context):
        """Test variable priority: static > input_key > context."""
        template = "Message: {{message}}, Source: {{source}}"
        processor = PromptProcessor(
            prompt=template,
            input_key="vars_from_context",
            template_vars={"message": "from static vars"}  # Highest priority
        )
        
        # Set up context with all priority levels
        empty_context.update({
            "message": "from context direct",  # Lowest priority
            "source": "context direct source",
            "vars_from_context": {
                "message": "from input_key",  # Medium priority  
                "source": "input_key source"
            }
        })
        
        result = await processor.process(empty_context)
        
        # message should come from static vars, source from input_key
        expected = "Message: from static vars, Source: input_key source"
        assert_result_success(result, expected)
    
    @pytest.mark.asyncio
    async def test_validation_with_input_key_success(self, empty_context):
        """Test validation passes when all required variables are available."""
        template = "Analyze {{data_type}} data: {{data_content}}"
        processor = PromptProcessor(
            prompt=template,
            input_key="analysis_vars",
            strict_mode=True
        )
        
        empty_context.set("analysis_vars", {
            "data_type": "sales",
            "data_content": "Q1 2024 sales data"
        })
        
        assert processor.validate_input(empty_context) is True
        
        result = await processor.process(empty_context)
        expected = "Analyze sales data: Q1 2024 sales data"
        assert_result_success(result, expected)
    
    @pytest.mark.asyncio
    async def test_validation_with_input_key_failure(self, empty_context):
        """Test validation fails when required variables are missing."""
        template = "Process {{task}} with {{priority}} priority"
        processor = PromptProcessor(
            prompt=template,
            input_key="task_vars",
            strict_mode=True
        )
        
        # Missing 'priority' variable
        empty_context.set("task_vars", {
            "task": "data processing"
        })
        
        assert processor.validate_input(empty_context) is False
        
        # Processing should fail with missing variables
        result = await processor.process(empty_context)
        assert result.status == ProcessingStatus.FAILED
        assert "Missing required template variables" in str(result.error)
    
    @pytest.mark.asyncio
    async def test_non_strict_mode(self, empty_context):
        """Test non-strict mode handles missing variables gracefully."""
        template = "User: {{user_name}}, Task: {{undefined_var}}"
        processor = PromptProcessor(
            prompt=template,
            template_vars={"user_name": "Alice"},
            strict_mode=False
        )
        
        result = await processor.process(empty_context)
        
        # Should succeed even with undefined variable
        assert result.status == ProcessingStatus.COMPLETED
        # undefined_var should be rendered as empty or undefined representation
        assert "Alice" in result.data
    
    @pytest.mark.asyncio
    async def test_non_dict_input_key_value(self, empty_context):
        """Test handling when input_key points to non-dict value."""
        template = "Process {{task}} task"
        processor = PromptProcessor(
            prompt=template,
            input_key="task_info",
            template_vars={"task": "default"}
        )
        
        # Set input_key to non-dict value
        empty_context.set("task_info", "not a dictionary")
        
        result = await processor.process(empty_context)
        
        # Should use static template_vars since input_key value is not a dict
        expected = "Process default task"
        assert_result_success(result, expected)
    
    @pytest.mark.asyncio
    async def test_complex_template_with_loops_and_conditions(self, empty_context):
        """Test complex Jinja2 template with loops and conditions."""
        template = """
{%- for item in items %}
{{loop.index}}. {{item.name}}: {{item.status}}
{%- if item.get('description') %}
   Description: {{item.description}}
{%- endif %}
{%- endfor %}

{%- if summary %}
Total items: {{items|length}}
{%- endif %}
""".strip()
        
        processor = PromptProcessor(
            prompt=template,
            input_key="report_data"
        )
        
        empty_context.set("report_data", {
            "items": [
                {"name": "Task A", "status": "Complete", "description": "First task"},
                {"name": "Task B", "status": "In Progress"},
                {"name": "Task C", "status": "Pending", "description": "Third task"}
            ],
            "summary": True
        })
        
        result = await processor.process(empty_context)
        
        assert result.status == ProcessingStatus.COMPLETED
        assert "1. Task A: Complete" in result.data
        assert "Description: First task" in result.data
        assert "2. Task B: In Progress" in result.data
        assert "Description: Third task" in result.data
        assert "Total items: 3" in result.data
    
    def test_preview_render_functionality(self):
        """Test template preview functionality."""
        template = "Report: {{title}}\nContent: {{content}}\nAuthor: {{author}}"
        processor = PromptProcessor(
            prompt=template,
            template_vars={"author": "System Generated"}
        )
        
        # Test preview with input_key_data
        preview = processor.preview_render(
            input_key_data={
                "title": "Monthly Report",
                "content": "All systems operational"
            }
        )
        
        expected = "Report: Monthly Report\nContent: All systems operational\nAuthor: System Generated"
        assert preview == expected
    
    def test_template_variable_management(self):
        """Test dynamic template variable management."""
        template = "{{var1}} - {{var2}} - {{var3}}"
        processor = PromptProcessor(prompt=template)
        
        # Test adding variables
        processor.add_template_var("var1", "value1")
        processor.add_template_var("var2", "value2")
        assert processor.template_vars["var1"] == "value1"
        assert processor.template_vars["var2"] == "value2"
        
        # Test removing variables
        removed = processor.remove_template_var("var1")
        assert removed == "value1"
        assert "var1" not in processor.template_vars
        assert processor.remove_template_var("nonexistent") is None
    
    def test_get_required_variables(self):
        """Test getting required template variables."""
        template = "Hello {{name}}! Your {{item_type}} is {{status}}."
        processor = PromptProcessor(prompt=template)
        
        required_vars = processor.get_required_variables()
        expected_vars = {"name", "item_type", "status"}
        assert required_vars == expected_vars
    
    def test_processor_string_representation(self):
        """Test processor string representation."""
        # Test basic processor
        processor1 = PromptProcessor(prompt="Hello world")
        repr1 = repr(processor1)
        assert "PromptProcessor" in repr1
        assert "is_template=False" in repr1
        
        # Test processor with template and input_key
        processor2 = PromptProcessor(
            prompt="Hello {{name}}",
            input_key="vars",
            template_vars={"greeting": "Hi"},
            name="CustomProcessor"
        )
        repr2 = repr(processor2)
        assert "CustomProcessor" in repr2
        assert "is_template=True" in repr2
        assert "input_key='vars'" in repr2
        assert "template_vars=1" in repr2
    

class TestLLMProcessor:
    """Test cases for LLMProcessor."""
    
    def test_llm_processor_initialization(self):
        """Test LLMProcessor initialization."""
        processor = LLMProcessor()
        assert processor.model == "gpt-3.5-turbo"
        assert processor.name == "LLMProcessor"
        
        # Test with custom model and name
        processor_custom = LLMProcessor(model="gpt-4", name="CustomLLM")
        assert processor_custom.model == "gpt-4"
        assert processor_custom.name == "CustomLLM"
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_success_api_prompt(self, context_with_prompt):
        """Test LLM processor with API-related prompt."""
        context_with_prompt.set("prompt", "What is an API?")
        processor = LLMProcessor()
        
        result = await processor.process(context_with_prompt)
        
        assert_result_success(result)
        response = context_with_prompt.get("llm_response")
        assert response is not None
        assert "API" in response
        assert "应用程序编程接口" in response
        assert result.metadata["processor_type"] == "llm"
        assert result.metadata["model"] == "gpt-3.5-turbo"
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_success_generic_prompt(self, context_with_prompt):
        """Test LLM processor with generic prompt."""
        generic_prompt = "Tell me about Python programming"
        context_with_prompt.set("prompt", generic_prompt)
        processor = LLMProcessor()
        
        result = await processor.process(context_with_prompt)
        
        assert_result_success(result)
        response = context_with_prompt.get("llm_response")
        assert response is not None
        assert "模拟回答" in response
        assert generic_prompt[:20] in response
    
    @pytest.mark.asyncio
    async def test_llm_processor_process_no_prompt(self, empty_context):
        """Test LLM processor when no prompt is provided."""
        processor = LLMProcessor()
        
        result = await processor.process(empty_context)
        
        assert_result_failed(result, ValueError)
        assert "No data found for input key 'prompt'" in str(result.error)
    
    def test_llm_processor_validate_input_success(self, context_with_prompt):
        """Test LLM processor input validation with valid input."""
        processor = LLMProcessor()
        assert processor.validate_input(context_with_prompt) is True
    
    def test_llm_processor_validate_input_failure(self, empty_context):
        """Test LLM processor input validation with missing prompt."""
        processor = LLMProcessor()
        assert processor.validate_input(empty_context) is False
    
    def test_llm_processor_mock_response_generation(self):
        """Test the mock response generation logic."""
        processor = LLMProcessor()
        
        # Test API prompt
        api_response = processor._generate_mock_response("What is an API?")
        assert "API" in api_response
        assert "应用程序编程接口" in api_response
        
        # Test generic prompt
        generic_response = processor._generate_mock_response("Random question")
        assert "模拟回答" in generic_response
        assert "Random question" in generic_response


class TestNoOpProcessor:
    """Test cases for NoOpProcessor."""
    
    def test_noop_processor_initialization(self):
        """Test NoOpProcessor initialization."""
        processor = NoOpProcessor()
        assert processor.name == "NoOpProcessor"
        assert processor._metadata == {}
        
        # Test with custom name and metadata
        custom_metadata = {"test": "value"}
        processor_custom = NoOpProcessor(name="CustomNoOp", metadata=custom_metadata)
        assert processor_custom.name == "CustomNoOp"
        assert processor_custom._metadata == custom_metadata
    
    @pytest.mark.asyncio
    async def test_noop_processor_process(self, sample_context):
        """Test NoOpProcessor processing."""
        processor = NoOpProcessor()
        
        result = await processor.process(sample_context)
        
        assert_result_success(result)
        assert result.metadata["processor_type"] == "noop"
        assert "context_keys" in result.metadata
        assert set(result.metadata["context_keys"]) == {"query", "user_id", "data"}
    
    @pytest.mark.asyncio
    async def test_noop_processor_with_custom_metadata(self, empty_context):
        """Test NoOpProcessor with custom metadata."""
        custom_metadata = {"custom_key": "custom_value"}
        processor = NoOpProcessor(metadata=custom_metadata)
        
        result = await processor.process(empty_context)
        
        assert_result_success(result)
        assert result.metadata["processor_type"] == "noop"
        assert result.metadata["custom_key"] == "custom_value"
    
    def test_noop_processor_validate_input(self, empty_context, sample_context):
        """Test NoOpProcessor input validation."""
        processor = NoOpProcessor()
        assert processor.validate_input(empty_context) is True
        assert processor.validate_input(sample_context) is True


class TestDataTransformProcessor:
    """Test cases for DataTransformProcessor."""
    
    def test_data_transform_processor_initialization(self):
        """Test DataTransformProcessor initialization."""
        processor = DataTransformProcessor(
            input_key="input", 
            output_key="output"
        )
        assert processor.input_key == "input"
        assert processor.output_key == "output"
        assert processor.name == "DataTransformProcessor"
        
        # Test with custom name and transform function
        def transform_func(x):
            return x.upper()
            
        processor_custom = DataTransformProcessor(
            input_key="input",
            output_key="output", 
            transform_func=transform_func,
            name="CustomTransform"
        )
        assert processor_custom.name == "CustomTransform"
        assert processor_custom.transform_func == transform_func
    
    @pytest.mark.asyncio
    async def test_data_transform_processor_process_success(self, empty_context):
        """Test successful data transformation."""
        # Set up input data
        empty_context.set("input_data", "hello world")
        
        # Create processor with uppercase transform
        def uppercase_transform(x):
            return x.upper()
            
        processor = DataTransformProcessor(
            input_key="input_data",
            output_key="output_data", 
            transform_func=uppercase_transform
        )
        
        result = await processor.process(empty_context)
        
        assert_result_success(result, "HELLO WORLD")
        assert empty_context.get("output_data") == "HELLO WORLD"
        assert result.metadata["processor_type"] == "data_transform"
        assert result.metadata["input_key"] == "input_data"
        assert result.metadata["output_key"] == "output_data"
        assert result.metadata["input_type"] == "str"
        assert result.metadata["output_type"] == "str"
    
    @pytest.mark.asyncio
    async def test_data_transform_processor_no_transform_func(self, empty_context):
        """Test data transform processor without transform function (passthrough)."""
        # Set up input data
        test_data = {"key": "value"}
        empty_context.set("input", test_data)
        
        # Create processor without transform function
        processor = DataTransformProcessor(
            input_key="input",
            output_key="output"
        )
        
        result = await processor.process(empty_context)
        
        assert_result_success(result, test_data)
        assert empty_context.get("output") == test_data
    
    @pytest.mark.asyncio
    async def test_data_transform_processor_missing_input(self, empty_context):
        """Test data transform processor when input key is missing."""
        processor = DataTransformProcessor(
            input_key="missing_key",
            output_key="output"
        )
        
        result = await processor.process(empty_context)
        
        assert_result_failed(result, ValueError)
        assert "No data found for input key 'missing_key'" in str(result.error)
    
    @pytest.mark.asyncio
    async def test_data_transform_processor_complex_transform(self, empty_context):
        """Test data transform processor with complex transformation."""
        # Set up input data
        input_data = [1, 2, 3, 4, 5]
        empty_context.set("numbers", input_data)
        
        # Create processor that squares numbers and filters even results
        def square_and_filter(numbers):
            squared = [x * x for x in numbers]
            return [x for x in squared if x % 2 == 0]
        
        processor = DataTransformProcessor(
            input_key="numbers",
            output_key="even_squares",
            transform_func=square_and_filter
        )
        
        result = await processor.process(empty_context)
        
        expected_result = [4, 16]  # squares of 2 and 4
        assert_result_success(result, expected_result)
        assert empty_context.get("even_squares") == expected_result
        assert result.metadata["input_type"] == "list"
        assert result.metadata["output_type"] == "list"
    
    def test_data_transform_processor_validate_input_success(self, sample_context):
        """Test data transform processor input validation with valid input."""
        processor = DataTransformProcessor(input_key="query", output_key="output")
        assert processor.validate_input(sample_context) is True
    
    def test_data_transform_processor_validate_input_failure(self, empty_context):
        """Test data transform processor input validation with missing input."""
        processor = DataTransformProcessor(input_key="missing", output_key="output")
        assert processor.validate_input(empty_context) is False
    