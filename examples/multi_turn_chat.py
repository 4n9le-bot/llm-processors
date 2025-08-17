"""
Multi-turn chat example using the llm-processors framework.

This example maintains a conversation history (messages) inside Context and
feeds it to ChatProcessor each turn.
"""

import os
import asyncio
from typing import List, Dict

from llm_processors import Context, Pipeline, ChatProcessor
from llm_processors.base import ProcessingStatus


async def main() -> None:
    # 0) Read config
    api_key = os.getenv("API_KEY")

    base_url = os.getenv("BASE_URL", "https://api.openai.com/v1")
    model = os.getenv("MODEL", "deepseek-chat")

    # 1) Initialize context with a system prompt and empty history
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Be concise.",
        }
    ]
    context = Context({"messages": messages})

    # 2) Build a pipeline that reads 'messages' and writes the assistant reply
    chat = ChatProcessor(
        base_url=base_url,
        api_key=api_key,
        model=model,
        input_key="messages",  # read conversation list
        output_key="assistant_message",  # store assistant reply text
    )

    pipeline = Pipeline(processors=[chat])

    # 3) Questions list (fill with your turns)
    question: List[str] = ["hi", "请用简单的语言解释一下，编程中的 'API' 是什么？", "你能帮我写一个 Python 函数吗？"]

    # If no API key is configured but there are questions to ask, exit early
    if not api_key and question:
        print("[multi_turn_chat] Missing API_KEY env var. Set it and re-run.")
        return

    # 4) Iterate over predefined questions (multi-turn)
    for user_text in question:
        text = user_text.strip()
        if not text:
            continue

        # Append user message into the running history in Context
        context.get("messages").append({"role": "user", "content": text})

        # Run the pipeline for this turn
        results = await pipeline.execute(context)

        # Pull the assistant reply and append it back to history
        last = results[-1] if results else None
        if last and last.status == ProcessingStatus.COMPLETED:
            assistant_text = context.get("assistant_message")
            print(f"You: {text}")
            print(f"Assistant: {assistant_text}\n")
            context.get("messages").append(
                {"role": "assistant", "content": assistant_text}
            )
        else:
            err = last.error if last else "Unknown error"
            print(f"[Error] {err}")


if __name__ == "__main__":
    asyncio.run(main())
