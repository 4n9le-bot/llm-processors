"""
ChatProcessor: LLM integration via OpenAI API.

This processor sends text packets to OpenAI's chat completion API
and yields responses as packets.
"""

import os
from typing import Optional, AsyncIterator, AsyncIterable, Any

from openai import AsyncOpenAI

from llm_processors.core import Packet, BaseProcessor


class ChatProcessor(BaseProcessor):
    """
    Processes text packets through OpenAI Chat API.

    Converts text packets to chat messages and returns LLM responses.
    Only processes text packets; other packet types are passed through unchanged.

    Examples:
        >>> chat = ChatProcessor(model="gpt-4o-mini")
        >>> pipeline = source + prompt + chat

        >>> # With custom parameters
        >>> chat = ChatProcessor(
        ...     model="gpt-4o",
        ...     temperature=0.7,
        ...     max_tokens=1000
        ... )
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ):
        """
        Initialize chat processor.

        Args:
            model: OpenAI model name (default: gpt-4o-mini)
            api_key: API key (defaults to os.getenv('OPENAI_API_KEY'))
            base_url: Custom base URL (defaults to os.getenv('OPENAI_BASE_URL'))
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Max completion tokens
            **kwargs: Additional OpenAI API parameters
        """
        super().__init__()
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

        # Initialize async client with env var fallbacks
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            base_url=base_url or os.getenv('OPENAI_BASE_URL')
        )

    async def _process_stream(
        self,
        stream: AsyncIterable[Packet]
    ) -> AsyncIterator[Packet]:
        """
        Process text packets through OpenAI API.

        Args:
            stream: Input packet stream

        Yields:
            Packets with LLM responses and metadata (usage, model, etc.)

        Note:
            Non-text packets are passed through unchanged
        """
        async for packet in stream:
            if not packet.is_text():
                # Pass through non-text packets
                yield packet
                continue

            # Build messages
            messages = [
                {"role": "user", "content": packet.content}
            ]

            # Prepare API parameters
            api_params: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                **self.extra_params
            }

            if self.max_tokens:
                api_params["max_tokens"] = self.max_tokens

            # Call API
            response = await self.client.chat.completions.create(**api_params)

            # Extract response
            if response.choices:
                content = response.choices[0].message.content

                # Build metadata
                metadata: dict[str, Any] = {
                    'model': self.model,
                    'finish_reason': response.choices[0].finish_reason
                }

                # Add usage stats if available
                if response.usage:
                    metadata['usage'] = {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    }

                # Preserve original packet metadata
                if packet.metadata:
                    metadata['source_metadata'] = packet.metadata

                yield Packet.from_text(content or "", **metadata)

    def __repr__(self) -> str:
        """String representation."""
        return f"ChatProcessor(model='{self.model}')"
