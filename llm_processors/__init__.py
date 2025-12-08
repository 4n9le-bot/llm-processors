"""
llm-processors: Build asynchronous and composable AI pipelines for generative AI.

This package provides a lightweight framework for creating composable AI pipelines
with async streaming support and elegant operator overloading.
"""

__version__ = "2.0.0"

# Core exports
from llm_processors.core import (
    Packet,
    PacketTypes,
    Processor,
    BaseProcessor,
    processor,
)

# Processor exports
from llm_processors.processors import (
    FromIterableProcessor,
    collect,
    collect_text,
    PromptProcessor,
    ChatProcessor,
)

__all__ = [
    # Core
    'Packet',
    'PacketTypes',
    'Processor',
    'BaseProcessor',
    'processor',
    # Processors
    'FromIterableProcessor',
    'collect',
    'collect_text',
    'PromptProcessor',
    'ChatProcessor',
]
