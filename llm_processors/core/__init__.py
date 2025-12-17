"""Core abstractions for llm-processors."""

from llm_processors.core.packet import Packet
from llm_processors.core.processor import BaseProcessor
from llm_processors.core.operators import SequentialProcessor, ParallelProcessor

__all__ = [
    'Packet',
    'BaseProcessor',
    'SequentialProcessor',
    'ParallelProcessor',
]
