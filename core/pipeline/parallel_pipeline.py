from typing import List, Optional, Sequence
import asyncio
from ..base import Pipeline, Processor, Context, ProcessingResult, ProcessingStatus


class ParallelPipeline(Pipeline):
    """
    Pipeline that executes processors in parallel.

    Useful when processors are independent and can run concurrently.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        processors: Optional[Sequence[Processor]] = None,
    ):
        """
        Initialize parallel pipeline.

        Args:
            name: Optional name for the pipeline
            default_timeout: Default timeout for processors in seconds
        """
        self.name = name or f"ParallelPipeline_{id(self)}"
        self._processors: List[Processor] = list(processors) if processors else []

    async def execute(self, context: Context) -> List[ProcessingResult]:
        """
        Execute processors in parallel.

        Args:
            context: The processing context
            stop_on_error: Whether to stop execution on first error

        Returns:
            List[ProcessingResult]: Results from each processor
        """

        tasks = [processor.process(context) for processor in self._processors]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to ProcessingResults
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    ProcessingResult(status=ProcessingStatus.FAILED, error=result)
                )
            else:
                processed_results.append(result)

            # Add to history
            context.add_to_history(self._processors[i].name)

        return processed_results

    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return (
            f"ParallelPipeline(name='{self.name}', processors={len(self._processors)})"
        )
