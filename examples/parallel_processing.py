"""
Parallel processing example: Using the // operator for concurrent execution.

This example demonstrates:
- Running multiple processors in parallel
- Using the // operator
- Substream tagging for identifying results
- Comparing outputs from different models
"""

import asyncio
from llm_processors import (
    PromptProcessor,
    ChatProcessor,
    collect,
)
from llm_processors.utils import StreamAdapter


async def main():
    """Run parallel processing example."""
    print("=" * 60)
    print("Parallel Processing Example")
    print("=" * 60)
    print()

    # Create source data
    topics = ["machine learning"]

    # Create processors
    prompt = PromptProcessor("Explain ${input} in simple terms.")

    # Two different models for comparison
    model_mini = ChatProcessor(model="gpt-4o-mini", temperature=0.7)
    model_standard = ChatProcessor(model="gpt-4o", temperature=0.7)

    # Compose pipeline: prompt -> (model1 // model2)
    pipeline = prompt + (model_mini // model_standard)

    print("Pipeline:")
    print(f"  {prompt}")
    print(f"  + ({model_mini} // {model_standard})")
    print()
    print("This will send the same prompt to both models in parallel.")
    print()

    # Create input stream and execute pipeline
    print("Processing...")
    print()

    input_stream = StreamAdapter.from_items(topics)
    results = await collect(pipeline(input_stream))

    # Display results
    print(f"Received {len(results)} results:")
    print()

    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Substream: {result.metadata.get('substream_name')}")
        print(f"  Model: {result.metadata.get('model')}")
        print(f"  Content: {result.content[:100]}...")
        print(f"  Tokens: {result.metadata.get('usage', {}).get('total_tokens')}")
        print()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
