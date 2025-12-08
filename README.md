# llm-processors

Build **asynchronous** and **composable** AI pipelines for generative AI applications.

A lightweight Python library that enables efficient, parallel content processing with elegant operator overloading for chaining and composing AI processors.

## Features

- 🔄 **Async Streaming**: Built on `AsyncIterable` for efficient streaming processing
- ⚡ **Composable**: Chain processors with `+` or run in parallel with `//`
- 🎯 **Type-Safe**: Full type hints throughout
- 🧩 **Multi-Modal**: Support for text, bytes, and images (PIL)
- 🚀 **Production-Ready**: SOLID principles, immutable data structures
- 🤖 **LLM-Integrated**: Built-in OpenAI ChatProcessor

## Installation

```bash
pip install llm-processors
```

### Requirements

- Python 3.10+
- OpenAI API key (for ChatProcessor)

## Quick Start

### Basic Pipeline

```python
import asyncio
from llm_processors import (
    FromIterableProcessor,
    PromptProcessor,
    ChatProcessor,
    collect
)

async def main():
    # Create processors
    source = FromIterableProcessor(["Python", "Rust"])
    prompt = PromptProcessor("Explain ${input} in one sentence.")
    chat = ChatProcessor(model="gpt-4o-mini")

    # Compose pipeline with + operator
    pipeline = source + prompt + chat

    # Execute and collect results
    results = await collect(pipeline())

    for result in results:
        print(result.content)

asyncio.run(main())
```

### Parallel Processing

```python
# Run two models in parallel
model1 = ChatProcessor(model="gpt-4o-mini")
model2 = ChatProcessor(model="gpt-4o")

# Use // operator for parallel execution
pipeline = source + prompt + (model1 // model2)

results = await collect(pipeline())

# Results tagged with substream_name metadata
for result in results:
    print(f"Model: {result.metadata['model']}")
    print(f"Response: {result.content}")
```

## Core Concepts

### Packet

The standard data object representing content of a specific modality:

```python
from llm_processors import Packet

# Text packet
packet = Packet.from_text("Hello, world!")

# Bytes packet
packet = Packet.from_bytes(b"data", mimetype="application/pdf")

# Image packet (requires PIL/Pillow)
from PIL import Image
img = Image.open("photo.jpg")
packet = Packet.from_image(img)

# Metadata
packet = packet.with_metadata(author="Alice", priority=1)
```

### Processor

A processing unit that transforms async streams of Packets:

```python
from llm_processors import BaseProcessor, Packet
from typing import AsyncIterator

class UppercaseProcessor(BaseProcessor):
    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        if packet.is_text():
            yield Packet.from_text(packet.content.upper())
        else:
            yield packet
```

### Composition Operators

#### Sequential (`+`)

Chain processors - output of first flows into second:

```python
pipeline = proc1 + proc2 + proc3
# stream -> proc1 -> proc2 -> proc3
```

#### Parallel (`//`)

Run processors concurrently - input duplicated, outputs merged:

```python
parallel = proc1 // proc2 // proc3
# stream duplicated to all, outputs merged with substream tags
```

## Built-in Processors

### FromIterableProcessor

Entry point - converts Python iterable to async Packet stream:

```python
source = FromIterableProcessor(["item1", "item2", "item3"])
```

### PromptProcessor

Template-based prompt rendering with `${variable}` substitution:

```python
prompt = PromptProcessor(
    template="As a ${role}, explain ${input}.",
    context={"role": "teacher"}
)
```

### ChatProcessor

OpenAI API integration:

```python
chat = ChatProcessor(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000
)

# Uses environment variables:
# - OPENAI_API_KEY
# - OPENAI_BASE_URL (optional)
```

### Utility Functions

```python
from llm_processors import collect, collect_text

# Collect all packets
results = await collect(pipeline())

# Collect only text content
texts = await collect_text(pipeline())
```

## Advanced Usage

### Custom Processor

```python
from llm_processors import BaseProcessor, Packet, processor
from typing import AsyncIterator

# Class-based
class FilterLongText(BaseProcessor):
    def __init__(self, min_length: int = 100):
        super().__init__()
        self.min_length = min_length

    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        if packet.is_text() and len(packet.content) >= self.min_length:
            yield packet

# Function-based with decorator
@processor
async def uppercase(stream):
    async for packet in stream:
        if packet.is_text():
            yield Packet.from_text(packet.content.upper())
        else:
            yield packet
```

### Error Handling

```python
class SafeProcessor(BaseProcessor):
    async def process(self, packet: Packet) -> AsyncIterator[Packet]:
        try:
            # Processing logic
            result = await some_operation(packet)
            yield result
        except Exception as e:
            # Yield error packet
            yield Packet.from_text(
                f"Error: {str(e)}",
                error=True,
                original_content=packet.content
            )
```

### Complex Pipelines

```python
# Mixed composition
pipeline = (
    source
    + prompt
    + (fast_model // slow_model // creative_model)
    + aggregator
    + formatter
)
```

## Configuration

Set environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
```

Or in code:

```python
import os
os.environ['OPENAI_API_KEY'] = 'your-api-key'
```

## Examples

See the `examples/` directory:

- [`basic_chat.py`](examples/basic_chat.py) - Simple pipeline with chaining
- [`parallel_processing.py`](examples/parallel_processing.py) - Parallel execution with `//`

Run examples:

```bash
python examples/basic_chat.py
python examples/parallel_processing.py
```

## Architecture

- **Immutable Packets**: Thread-safe for async contexts
- **Protocol-based**: Duck typing for flexibility
- **Streaming-first**: No materialization until `collect()`
- **SOLID principles**: Clean, extensible design

## Development

### Setup

```bash
git clone https://github.com/yourusername/llm-processors.git
cd llm-processors

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests
pytest

# Unit tests only (fast, no API calls)
pytest -m unit

# Integration tests (requires API key)
pytest -m integration
```

### Code Quality

```bash
# Format code
black llm_processors tests examples

# Lint
ruff check llm_processors tests

# Type check
mypy llm_processors
```

## Roadmap

- [ ] Streaming LLM responses (token-by-token)
- [ ] Advanced routing based on metadata
- [ ] Retry logic and fallback processors
- [ ] Observability (logging, metrics, tracing)
- [ ] More processors (embeddings, vision, audio)
- [ ] YAML pipeline configuration

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- **Documentation**: [Coming soon]
- **Examples**: [`examples/`](examples/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/llm-processors/issues)

---

Built with ❤️ for the AI community
