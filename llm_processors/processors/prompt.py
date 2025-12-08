"""
PromptProcessor: Template-based prompt rendering.

This processor renders prompts using Python's string.Template for
simple ${variable} substitution.
"""

from typing import Optional, Dict, Any, AsyncIterator
from string import Template

from llm_processors.core import Packet, BaseProcessor


class PromptProcessor(BaseProcessor):
    """
    Renders prompt templates with context variables.

    Uses Python's string.Template for simple ${variable} substitution.
    The input packet's content is available as ${input}.

    Examples:
        >>> prompt = PromptProcessor("Explain ${input} in one sentence.")
        >>> pipeline = source + prompt + chat

        >>> # With additional context
        >>> prompt = PromptProcessor(
        ...     "As a ${role}, explain ${input}.",
        ...     context={"role": "teacher"}
        ... )
    """

    def __init__(
        self,
        template: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize prompt processor.

        Args:
            template: Template string with ${variable} placeholders
            context: Variables for template substitution
        """
        super().__init__()
        self.template = Template(template)
        self.context = context or {}

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        """
        Render template with packet content as 'input' variable.

        Args:
            packet: Input packet (content available as ${input})

        Yields:
            Packet with rendered prompt as text
        """
        # Build context with packet content
        render_context = {
            'input': packet.content,
            **self.context
        }

        # Render template
        rendered = self.template.safe_substitute(render_context)

        # Preserve some original metadata
        metadata = {
            'source_mimetype': packet.mimetype,
            'template': self.template.template,
        }

        # Yield text packet
        yield Packet.from_text(rendered, **metadata)

    def __repr__(self) -> str:
        """String representation."""
        preview = self.template.template[:50]
        if len(self.template.template) > 50:
            preview += "..."
        return f"PromptProcessor('{preview}')"
