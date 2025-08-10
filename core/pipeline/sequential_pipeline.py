from typing import Dict, List, Optional, Any, Sequence
from ..base import Pipeline, Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class SequentialPipeline(Pipeline):
    """
    Pipeline that executes processors in sequence.

    The pipeline manages the flow of data through multiple processors,
    handling errors and maintaining execution state.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        processors: Optional[Sequence[Processor]] = None,
    ):
        """
        Initialize pipeline.

        Args:
            name: Optional name for the pipeline
            default_timeout: Default timeout for processors in seconds
            processors: Optional sequence of processors to add initially
        """
        self.name = name or f"SequentialPipeline_{id(self)}"
        self._processors: List[Processor] = list(processors) if processors else []

    async def execute(self, context: Context) -> List[ProcessingResult]:
        """
        Execute the pipeline with the given context.

        Args:
            context: The processing context
            stop_on_error: Whether to stop execution on first error

        Returns:
            List[ProcessingResult]: Results from each processor
        """
        results: List[ProcessingResult] = []

        for processor in self._processors:

            # Add processor to execution history
            context.add_to_history(processor.name)

            try:
                # Execute processor with timeout
                result = await processor.process(context)
                results.append(result)

            except Exception as e:
                result = ProcessingResult(status=ProcessingStatus.FAILED, error=e)
                results.append(result)

        return results

    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return f"SequentialPipeline(name='{self.name}', processors={len(self._processors)})"
