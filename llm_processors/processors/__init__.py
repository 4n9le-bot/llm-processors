"""Built-in processors for common AI pipeline tasks."""

from llm_processors.processors.io import FromIterableProcessor, collect, collect_text
from llm_processors.processors.prompt import PromptProcessor
from llm_processors.processors.chat import ChatProcessor

__all__ = [
    'FromIterableProcessor',
    'collect',
    'collect_text',
    'PromptProcessor',
    'ChatProcessor',
]
