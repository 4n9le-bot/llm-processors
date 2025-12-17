"""
Basic chat example: Using operator chaining to create a simple AI pipeline.

This example demonstrates:
- Creating a packet stream from a list using StreamAdapter
- Chaining processors with the + operator
- Using PromptProcessor for template rendering
- Using ChatProcessor for LLM calls
- Collecting results
"""

import asyncio
from llm_processors import (
    PromptProcessor,
    ChatProcessor,
    collect,
)
from llm_processors.utils import StreamAdapter


async def main():
    """Run basic chat pipeline example."""
    print("=" * 60)
    print("Basic Chat Pipeline Example")
    print("=" * 60)
    print()

    # Create source data
    topics = ["Python", "Rust", "Go"]

    # Create processors
    prompt = PromptProcessor("Explain ${input} programming language in one sentence.")
    chat = ChatProcessor(model="gpt-4o-mini", temperature=0.7)

    # Compose pipeline using + operator
    pipeline = prompt + chat

    print("Pipeline:")
    print(f"  {prompt}")
    print(f"  + {chat}")
    print()

    # Create input stream and execute pipeline
    print("Processing...")
    print()

    input_stream = StreamAdapter.from_items(topics)
    results = await collect(pipeline(input_stream))

    # Display results
    for i, result in enumerate(results, 1):
        print(f"Result {i}:")
        print(f"  Content: {result.content}")
        print(f"  Model: {result.metadata.get('model')}")
        print(f"  Tokens: {result.metadata.get('usage', {}).get('total_tokens')}")
        print()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
