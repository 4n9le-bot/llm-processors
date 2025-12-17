"""
llm-processors: Build asynchronous and composable AI pipelines for generative AI.

This package provides a lightweight framework for creating composable AI pipelines
with async streaming support and elegant operator overloading.
"""

__version__ = "2.0.0"

# Core exports
from llm_processors.core import (
    Packet,
    BaseProcessor,
)

# Processor exports
from llm_processors.processors import (
    collect,
    collect_text,
    PromptProcessor,
    ChatProcessor,
    FilterProcessor,
)

# Utility exports
from llm_processors.utils import (
    PacketConverter,
    StreamAdapter,
)

__all__ = [
    # Core
    'Packet',
    'BaseProcessor',
    # Processors
    'collect',
    'collect_text',
    'PromptProcessor',
    'ChatProcessor',
    'FilterProcessor',
    # Utils
    'PacketConverter',
    'StreamAdapter',
]
