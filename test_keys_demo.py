#!/usr/bin/env python3
"""
Test script to demonstrate input_key/output_key functionality.
"""

import asyncio
from core import (
    SequentialPipeline, 
    PromptProcessor, 
    LLMProcessor, 
    DataTransformProcessor,
    NoOpProcessor,
    Context
)


async def test_input_output_keys():
    """Test the input_key/output_key data flow."""
    print("=== Testing Input/Output Key Data Flow ===\n")
    
    # Create a pipeline with custom key mappings
    pipeline = SequentialPipeline(name="DataFlowDemo")
    
    # 1. PromptProcessor outputs to "user_query" instead of default "prompt"
    prompt_proc = PromptProcessor(
        prompt="What is machine learning?",
        output_key="user_query",
        name="UserQueryProcessor"
    )
    
    # 2. LLMProcessor reads from "user_query" and outputs to "ai_response"
    llm_proc = LLMProcessor(
        model="gpt-4",
        input_key="user_query",
        output_key="ai_response",
        name="AIProcessor"
    )
    
    # 3. Transform processor converts response to uppercase
    transform_proc = DataTransformProcessor(
        input_key="ai_response",
        output_key="formatted_response",
        transform_func=lambda x: x.upper(),
        name="UppercaseFormatter"
    )
    
    # 4. NoOp processor with passthrough from formatted_response to final_output
    noop_proc = NoOpProcessor(
        input_key="formatted_response",
        output_key="final_output",
        passthrough=True,
        name="FinalProcessor"
    )
    
    # Add processors to pipeline
    pipeline.add_processors([prompt_proc, llm_proc, transform_proc, noop_proc])
    
    # Validate pipeline
    errors = pipeline.validate_pipeline()
    if errors:
        print("Pipeline validation errors:")
        for error in errors:
            print(f"  - {error}")
        return
    
    print("✅ Pipeline validation passed!")
    print(f"Pipeline: {pipeline}")
    print()
    
    # Execute pipeline
    context = Context()
    print("📝 Initial context:", context.get_all())
    
    results = await pipeline.execute(context)
    
    print(f"\n📊 Execution completed with {len(results)} results:")
    for i, result in enumerate(results):
        processor_name = pipeline.get_processors()[i].name
        print(f"  {i+1}. {processor_name}: {result.status.value}")
        if result.error:
            print(f"     ❌ Error: {result.error}")
        elif result.metadata:
            print(f"     📋 Metadata: {result.metadata}")
    
    print(f"\n🎯 Final context:")
    for key, value in context.get_all().items():
        print(f"  {key}: {value[:100]}..." if len(str(value)) > 100 else f"  {key}: {value}")
    
    print(f"\n📜 Execution history: {context.get_history()}")
    
    # Demonstrate key mapping
    print(f"\n🔗 Data Flow Demonstration:")
    print(f"  user_query (from PromptProcessor): {context.get('user_query')}")
    print(f"  ai_response (from LLMProcessor): {context.get('ai_response')[:50]}...")
    print(f"  formatted_response (from DataTransformProcessor): {context.get('formatted_response')[:50]}...")
    print(f"  final_output (from NoOpProcessor): {context.get('final_output')[:50]}...")


async def test_pipeline_with_different_keys():
    """Test pipeline with non-standard key names."""
    print("\n\n=== Testing Custom Key Names ===\n")
    
    pipeline = SequentialPipeline(name="CustomKeysDemo")
    
    # Use completely different key names
    pipeline.add_processors([
        PromptProcessor("Explain APIs", output_key="question", name="QuestionSetter"),
        LLMProcessor(input_key="question", output_key="answer", name="Answerer"),
        DataTransformProcessor(
            input_key="answer",
            output_key="summary",
            transform_func=lambda x: f"Summary: {x[:100]}...",
            name="Summarizer"
        )
    ])
    
    context = Context()
    results = await pipeline.execute(context)
    
    print("✅ Custom keys pipeline executed successfully!")
    print(f"🎯 Final context keys: {list(context.get_all().keys())}")
    
    # Show the data flow
    print(f"\n🔗 Custom Key Data Flow:")
    print(f"  question: {context.get('question')}")
    print(f"  answer: {context.get('answer')[:50]}...")
    print(f"  summary: {context.get('summary')}")


if __name__ == "__main__":
    asyncio.run(test_input_output_keys())
    asyncio.run(test_pipeline_with_different_keys())
