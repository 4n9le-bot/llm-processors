"""Built-in processors for common AI pipeline tasks."""

from llm_processors.processors.io import collect, collect_text
from llm_processors.processors.prompt import PromptProcessor
from llm_processors.processors.chat import ChatProcessor
from llm_processors.processors.filter import FilterProcessor

__all__ = [
    'collect',
    'collect_text',
    'PromptProcessor',
    'ChatProcessor',
    'FilterProcessor',
]
