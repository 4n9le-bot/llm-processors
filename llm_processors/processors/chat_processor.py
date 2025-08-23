import json
from typing import Optional, List, Dict, Any
import openai
from openai import OpenAI

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class ChatProcessor(Processor):
    """
    A processor that handles LLM processing using OpenAI API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        input_key: str = "prompt_output",
        output_key: str = "llm_output",
        name: str = "llm",
        **kwargs,
    ):
        """
        Initialize LLM processor.

        Args:
            base_url: Custom OpenAI API base URL
            api_key: OpenAI API key
            model: The model name to use
            input_key: The key to read the prompt from context
            output_key: The key to store the LLM response in context
            name: Optional name for the processor
            **kwargs: Additional configuration options:
                temperature (float): Sampling temperature (default: 0.6)
                max_tokens (int): Maximum tokens in response (default: None)
                response_format (str): Response format, 'text' or 'json' (default: 'text')
        """
        super().__init__(name, input_key, output_key)

        self.model = model
        self.temperature = kwargs.get("temperature", 0.6)
        self.max_tokens = kwargs.get("max_tokens", None)
        self.response_format = kwargs.get("response_format", "text")

        # Initialize OpenAI client
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)


    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt using OpenAI LLM.

        Args:
            context: The processing context containing the prompt

        Returns:
            ProcessingResult: Result of the LLM processing
        """
        try:
            if not context.has(self.input_key):
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(
                        f"No data found for input key '{self.input_key}' in context"
                    ),
                )

            prompt = context.get(self.input_key)
            messages = [{"role": "user", "content": prompt}]

            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "response_format": {"type": self.response_format},
            }

            if self.max_tokens:
                api_params["max_tokens"] = self.max_tokens

            # Make the API call
            response = self.client.chat.completions.create(**api_params)

            llm_response = None
            if response.choices:
                llm_response = response.choices[0].message.content
                if self.response_format == "json":
                    llm_response = json.loads(llm_response)

            # Prepare metadata
            metadata = {
                "model": self.model,
                "input_key": self.input_key,
                "output_key": self.output_key,
                "response_length": len(llm_response) if llm_response else 0,
                "usage": (
                    {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                    if response.usage
                    else None
                ),
                "finish_reason": response.choices[0].finish_reason,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens if self.max_tokens else None,
            }

            # Add the response to context using the specified output key
            context.set(self.output_key, llm_response)

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=llm_response,
                metadata=metadata,
            )

        except openai.AuthenticationError as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=ValueError(f"OpenAI authentication failed: {str(e)}"),
            )
        except openai.RateLimitError as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=ValueError(f"OpenAI rate limit exceeded: {str(e)}"),
            )
        except openai.APIError as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=ValueError(f"OpenAI API error: {str(e)}"),
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e,
            )
