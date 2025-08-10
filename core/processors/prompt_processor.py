from typing import Optional, Dict, Any

from jinja2 import Template, TemplateSyntaxError

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class PromptProcessor(Processor):
    """
    A processor that sets up prompts for LLM processing with Jinja2 template support.

    This processor takes a prompt template (plain text or Jinja2 template) and prepares
    it for LLM consumption by rendering it with context data.
    """

    def __init__(
        self,
        prompt: str,
        output_key: str = "prompt",
        input_key: Optional[str] = None,
        name: str = "PromptProcessor",
    ):
        """
        Initialize prompt processor.

        Args:
            prompt: The prompt text or Jinja2 template to use
            output_key: The key to store the rendered prompt in context
            input_key: The key to get template variables from context (optional)
            name: Optional name for the processor
        """
        super().__init__(name, input_key, output_key)
        self.prompt = prompt

    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt template and add rendered result to context.

        Args:
            context: The processing context

        Returns:
            ProcessingResult: Result of the prompt processing
        """
        try:
            template = Template(self.prompt)
            template_vars = {}
            if self.input_key and context.has(self.input_key):
                template_vars = context.get(self.input_key)

            rendered_prompt = template.render(**template_vars)
            context.set(self.output_key, rendered_prompt)

            metadata = {
                "processor_type": "prompt",
                "prompt_length": len(rendered_prompt),
                "output_key": self.output_key,
            }

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=rendered_prompt,
                metadata=metadata,
            )

        except TemplateSyntaxError as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=ValueError(f"Template rendering error: {e}"),
            )
        except Exception as e:
            return ProcessingResult(status=ProcessingStatus.FAILED, error=e)

    def __repr__(self) -> str:
        """String representation of the processor."""
        parts = [f"name='{self.name}'"]

        if self.input_key:
            parts.append(f"input_key='{self.input_key}'")
        if self.output_key:
            parts.append(f"output_key='{self.output_key}'")

        return f"PromptProcessor({', '.join(parts)})"
