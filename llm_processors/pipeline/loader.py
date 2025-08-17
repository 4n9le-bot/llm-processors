"""
YAML loader for building pipelines.

Supported YAML schema:

pipeline:
  type: sequential  # optional, default: sequential
  processors:
    - id: MyPrompt
      type: prompt
      config:
        prompt: "..."
        # optional: input_key, output_key, name
    - id: MyLLM
      type: llm
      config:
        model: "gpt-3.5-turbo"
        # optional: input_key, output_key, name, base_url, api_key, temperature, max_tokens
"""

from __future__ import annotations

from typing import Any, Dict, List

import yaml

from ..processors import PromptProcessor, ChatProcessor, NoOpProcessor
from .sequential_pipeline import SequentialPipeline


TYPE_TO_PROCESSOR = {
    "prompt": PromptProcessor,
    "llm": ChatProcessor,
    "noop": NoOpProcessor,
}


def load_pipeline_from_yaml(path: str) -> SequentialPipeline:
    with open(path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if not isinstance(spec, dict) or "pipeline" not in spec:
        raise ValueError("YAML must contain a top-level 'pipeline' mapping")

    p_spec: Dict[str, Any] = spec["pipeline"] or {}
    p_type = (p_spec.get("type") or "sequential").lower()
    if p_type != "sequential":
        raise ValueError(f"Unsupported pipeline type: {p_type}")

    processors_spec: List[Dict[str, Any]] = p_spec.get("processors") or []
    if not isinstance(processors_spec, list):
        raise ValueError("'pipeline.processors' must be a list")

    processors = []
    for entry in processors_spec:
        if not isinstance(entry, dict):
            raise ValueError("Each processor entry must be a mapping")

        pid = entry.get("id")
        ptype = (entry.get("type") or "").lower()
        config: Dict[str, Any] = entry.get("config") or {}

        if not ptype:
            raise ValueError("Processor 'type' is required")
        if ptype not in TYPE_TO_PROCESSOR:
            raise ValueError(f"Unknown processor type: {ptype}")

        cls = TYPE_TO_PROCESSOR[ptype]

        # Use id as name if provided; allow overrides in config
        if pid and "name" not in config:
            config["name"] = pid

        processor = cls(**config)  # type: ignore[arg-type]
        processors.append(processor)

    return SequentialPipeline(processors=processors)
