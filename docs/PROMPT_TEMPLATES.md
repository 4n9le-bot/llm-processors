# Prompt Templates for PromptProcessor

This document contains various prompt templates that can be used with the `PromptProcessor` class. The templates demonstrate different use cases and Jinja2 template features.

## Basic Prompts

### Simple Question Answering
```python
simple_qa_prompt = """
Please answer the following question clearly and concisely:

Question: {{ question }}

Answer:
"""
```

### Text Summarization
```python
summarization_prompt = """
Please provide a concise summary of the following text:

Text: {{ text }}

Summary:
"""
```

### Translation
```python
translation_prompt = """
Translate the following text from {{ source_language }} to {{ target_language }}:

Original text: {{ text }}

Translation:
"""
```

## Advanced Prompts with Conditional Logic

### Code Review Assistant
```python
code_review_prompt = """
Please review the following {{ language }} code and provide feedback:

{% if file_path %}
File: {{ file_path }}
{% endif %}

Code:
```{{ language }}
{{ code }}
```

Please analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
{% if specific_concerns %}
4. Specific concerns: {{ specific_concerns }}
{% endif %}

Review:
"""
```

### Email Generator
```python
email_prompt = """
Compose a {{ tone | default('professional') }} email with the following details:

To: {{ recipient }}
Subject: {{ subject }}

{% if context %}
Context: {{ context }}
{% endif %}

Main points to cover:
{% for point in main_points %}
- {{ point }}
{% endfor %}

{% if call_to_action %}
Call to action: {{ call_to_action }}
{% endif %}

Email:
"""
```

### Data Analysis Report
```python
data_analysis_prompt = """
Generate a data analysis report based on the following information:

Dataset: {{ dataset_name }}
Analysis Type: {{ analysis_type }}

Key Findings:
{% for finding in key_findings %}
- {{ finding }}
{% endfor %}

{% if metrics %}
Metrics:
{% for metric, value in metrics.items() %}
- {{ metric }}: {{ value }}
{% endfor %}
{% endif %}

{% if recommendations %}
Recommendations:
{% for recommendation in recommendations %}
{{ loop.index }}. {{ recommendation }}
{% endfor %}
{% endif %}

Please provide:
1. Executive Summary
2. Detailed Analysis
3. Conclusions
{% if include_next_steps %}
4. Next Steps
{% endif %}

Report:
"""
```

## Domain-Specific Prompts

### Customer Support
```python
customer_support_prompt = """
You are a helpful customer support representative. Please assist with the following inquiry:

Customer: {{ customer_name }}
{% if customer_tier %}
Customer Tier: {{ customer_tier }}
{% endif %}

Issue Category: {{ issue_category }}
Priority: {{ priority | default('Medium') }}

Customer Message:
{{ customer_message }}

{% if previous_interactions %}
Previous Interactions:
{% for interaction in previous_interactions %}
- {{ interaction.date }}: {{ interaction.summary }}
{% endfor %}
{% endif %}

Please provide:
1. A sympathetic and professional response
2. Clear steps to resolve the issue
3. Any additional resources that might help

Response:
"""
```

### Educational Content
```python
educational_prompt = """
Create educational content for {{ subject }} at {{ level | default('intermediate') }} level:

Topic: {{ topic }}
{% if learning_objectives %}
Learning Objectives:
{% for objective in learning_objectives %}
- {{ objective }}
{% endfor %}
{% endif %}

Target Audience: {{ target_audience }}
Duration: {{ duration | default('30 minutes') }}

{% if prerequisites %}
Prerequisites:
{% for prereq in prerequisites %}
- {{ prereq }}
{% endfor %}
{% endif %}

Please include:
1. Introduction
2. Main concepts with examples
3. Practice exercises
{% if include_assessment %}
4. Assessment questions
{% endif %}
5. Summary and key takeaways

Content:
"""
```

### Creative Writing
```python
creative_writing_prompt = """
Write a {{ genre }} story with the following elements:

Setting: {{ setting }}
{% if time_period %}
Time Period: {{ time_period }}
{% endif %}

Main Character: {{ main_character }}
{% if supporting_characters %}
Supporting Characters:
{% for character in supporting_characters %}
- {{ character }}
{% endfor %}
{% endif %}

Plot Elements:
{% for element in plot_elements %}
- {{ element }}
{% endfor %}

{% if theme %}
Theme: {{ theme }}
{% endif %}

{% if tone %}
Tone: {{ tone }}
{% endif %}

Word Count: {{ word_count | default('500-1000') }} words

Story:
"""
```

## Technical Documentation Prompts

### API Documentation
```python
api_docs_prompt = """
Generate comprehensive API documentation for the following endpoint:

Method: {{ http_method }}
Endpoint: {{ endpoint }}
Description: {{ description }}

{% if parameters %}
Parameters:
{% for param in parameters %}
- {{ param.name }} ({{ param.type }}): {{ param.description }}{% if param.required %} [Required]{% endif %}
{% endfor %}
{% endif %}

{% if request_body %}
Request Body:
{{ request_body }}
{% endif %}

{% if response_format %}
Response Format:
{{ response_format }}
{% endif %}

{% if error_codes %}
Error Codes:
{% for error in error_codes %}
- {{ error.code }}: {{ error.description }}
{% endfor %}
{% endif %}

{% if examples %}
Examples:
{% for example in examples %}
{{ example.title }}:
Request: {{ example.request }}
Response: {{ example.response }}
{% endfor %}
{% endif %}

Documentation:
"""
```

### Code Documentation
```python
code_docs_prompt = """
Generate comprehensive documentation for the following {{ language }} code:

{% if module_name %}
Module: {{ module_name }}
{% endif %}

Code:
```{{ language }}
{{ code }}
```

Please provide:
1. Overview and purpose
2. Function/class descriptions
3. Parameter explanations
4. Return value descriptions
5. Usage examples
{% if include_edge_cases %}
6. Edge cases and error handling
{% endif %}

Documentation:
"""
```

## Usage Examples

### Basic Usage
```python
from core.processors.prompt_processor import PromptProcessor
from core.context import Context

# Simple template
processor = PromptProcessor(
    prompt="Hello {{ name }}, welcome to {{ platform }}!",
    output_key="greeting",
    name="greeting_processor"
)

context = Context({"name": "Alice", "platform": "AI Assistant"})
result = await processor.process(context)
# Result: "Hello Alice, welcome to AI Assistant!"
```

### Complex Template with Context Data
```python
# Email generation with template variables from context
email_processor = PromptProcessor(
    prompt=email_prompt,  # Use the email_prompt template from above
    input_key="email_data",
    output_key="generated_email",
    name="email_generator"
)

email_context = Context({
    "email_data": {
        "recipient": "john.doe@example.com",
        "subject": "Project Update",
        "tone": "professional",
        "main_points": [
            "Project is on schedule",
            "Budget is within limits",
            "Next milestone is next week"
        ],
        "call_to_action": "Please review and provide feedback"
    }
})

result = await email_processor.process(email_context)
```

### Conditional Logic Example
```python
# Code review with optional fields
review_processor = PromptProcessor(
    prompt=code_review_prompt,
    input_key="code_data",
    output_key="review_prompt",
    name="code_reviewer"
)

code_context = Context({
    "code_data": {
        "language": "python",
        "file_path": "src/utils.py",
        "code": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
        "specific_concerns": "Error handling for empty lists"
    }
})

result = await review_processor.process(code_context)
```

## Best Practices

1. **Use Clear Variable Names**: Make template variables descriptive and meaningful
2. **Provide Default Values**: Use Jinja2's `default` filter for optional variables
3. **Handle Missing Data**: Use conditional blocks to handle optional sections
4. **Structure Output**: Organize prompts with clear sections and numbered lists
5. **Include Context**: Provide sufficient context for the AI model to generate good responses
6. **Test Templates**: Always test your templates with sample data before deployment

## Template Debugging

When debugging templates, check the `metadata` in the processing result:
- `template_vars`: Shows what variables were passed to the template
- `prompt_length`: Indicates the length of the rendered prompt
- Any template syntax errors will be caught and returned as processing failures
