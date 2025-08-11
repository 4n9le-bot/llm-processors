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
        model: str = "gpt-3.5-turbo",
        input_key: str = "prompt_output",
        output_key: str = "llm_output",
        name: str = "llm",
        temperature: float = 0.6,
        max_tokens: Optional[int] = None,
        system_message: Optional[str] = None,
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
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            system_message: System message to prepend to conversations
        """
        super().__init__(name, input_key, output_key)
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_message = system_message
        
        # Initialize OpenAI client
        client_kwargs = {}
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.client = OpenAI(**client_kwargs)

    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """
        Prepare messages for the chat completion API.
        
        Args:
            prompt: User prompt
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system message if provided
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        
        # Handle different input types
        if isinstance(prompt, str):
            messages.append({"role": "user", "content": prompt})
        elif isinstance(prompt, list):
            # Assume it's already a list of messages
            messages.extend(prompt)
        elif isinstance(prompt, dict) and "messages" in prompt:
            # Extract messages from dict
            messages.extend(prompt["messages"])
        else:
            # Convert to string
            messages.append({"role": "user", "content": str(prompt)})
            
        return messages

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
            messages = self._prepare_messages(prompt)
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
            }
            
            if self.max_tokens:
                api_params["max_tokens"] = self.max_tokens

            # Make the API call
            response = self.client.chat.completions.create(**api_params)
            
            # Extract the response content
            llm_response = response.choices[0].message.content
            
            # Prepare metadata
            metadata = {
                "processor_type": "llm",
                "model": self.model,
                "input_key": self.input_key,
                "output_key": self.output_key,
                "response_length": len(llm_response) if llm_response else 0,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
                "finish_reason": response.choices[0].finish_reason,
                "temperature": self.temperature,
            }
            
            if self.max_tokens:
                metadata["max_tokens"] = self.max_tokens

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
