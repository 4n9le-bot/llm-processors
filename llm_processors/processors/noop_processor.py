from typing import Optional

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class NoOpProcessor(Processor):
    """
    A processor that does nothing but logs its execution.

    Useful for testing and debugging pipelines. Can optionally pass through
    data from input_key to output_key.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
    ):
        """
        Initialize no-op processor.

        Args:
            name: Optional name for the processor
            input_key: Optional input key to read from context
            output_key: Optional output key to write to context
        """
        super().__init__(name, input_key, output_key)

    async def process(self, context: Context) -> ProcessingResult:
        """
        Do nothing but return success, optionally with passthrough.

        Args:
            context: The processing context

        Returns:
            ProcessingResult: Success result with metadata
        """
        try:
            if self.input_key and self.output_key and context.has(self.input_key):
                input_data = context.get(self.input_key)
                context.set(self.output_key, input_data)

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                metadata={
                    "context_keys": list(context.get_all().keys()),
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                },
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e,
            )
