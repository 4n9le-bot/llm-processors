"""
Run a pipeline defined in a YAML file.
"""

import os
import asyncio
import sys
from typing import Optional

from llm_processors import Context, ProcessingStatus, load_pipeline_from_yaml


async def main(yaml_path: str) -> None:
    # Optional: ensure API key present if ChatProcessor is used
    if not os.getenv("API_KEY"):
        print("[run_yaml_pipeline] Warning: API_KEY not set. LLM steps may fail.")

    pipeline = load_pipeline_from_yaml(yaml_path)
    ctx = Context()
    results = await pipeline.execute(ctx)

    # Dump result data and metadata
    for i, r in enumerate(results, start=1):
        print(f"Step {i}: {r.status.value}")
        if r.status == ProcessingStatus.COMPLETED:
            if r.data is not None:
                print(r.data)
            if r.metadata:
                print(r.metadata)
        else:
            print(f"Error: {r.error}")


if __name__ == "__main__":
    path: Optional[str] = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Usage: python examples/run_yaml_pipeline.py examples/pipeline.yaml")
        raise SystemExit(2)
    asyncio.run(main(path))
