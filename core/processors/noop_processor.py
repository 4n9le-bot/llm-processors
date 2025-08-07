from typing import Optional, Dict, Any

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
        metadata: Optional[Dict[str, Any]] = None,
        input_key: Optional[str] = None,
        output_key: Optional[str] = None,
        passthrough: bool = False,
    ):
        """
        Initialize no-op processor.

        Args:
            name: Optional name for the processor
            metadata: Optional metadata to include in results
            input_key: Optional input key to read from context
            output_key: Optional output key to write to context
            passthrough: If True and both keys provided, copies input to output
        """
        super().__init__(name)
        self._metadata = metadata or {}
        self.input_key = input_key
        self.output_key = output_key
        self.passthrough = passthrough

    async def process(self, context: Context) -> ProcessingResult:
        """
        Do nothing but return success, optionally with passthrough.

        Args:
            context: The processing context

        Returns:
            ProcessingResult: Success result with metadata
        """
        try:
            # If passthrough is enabled and keys are provided, copy input to output
            if (
                self.passthrough
                and self.input_key
                and self.output_key
                and context.has(self.input_key)
            ):
                input_data = context.get(self.input_key)
                context.set(self.output_key, input_data)

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                metadata={
                    "processor_type": "noop",
                    "context_keys": list(context.get_all().keys()),
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "passthrough": self.passthrough,
                    **self._metadata,
                },
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e,
            )

    def validate_input(self, context: Context) -> bool:
        """
        Validate input if required.

        Returns True if no input required, or if required input exists.
        """
        if self.input_key:
            return context.has(self.input_key)
        return True
