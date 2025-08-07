from typing import Optional, Callable, Any

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class DataTransformProcessor(Processor):
    """
    A generic processor that transforms data from one key to another.

    Useful for data type conversion, formatting, or simple transformations.
    """

    def __init__(
        self,
        input_key: str,
        output_key: str,
        transform_func: Optional[Callable[[Any], Any]] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize data transform processor.

        Args:
            input_key: The key to read input data from context
            output_key: The key to store transformed data in context
            transform_func: Optional function to transform the data. If None, data is copied as-is
            name: Optional name for the processor
        """
        super().__init__(name)
        self.input_key = input_key
        self.output_key = output_key
        self.transform_func = transform_func or (lambda x: x)

    async def process(self, context: Context) -> ProcessingResult:
        """
        Transform data from input_key to output_key.

        Args:
            context: The processing context

        Returns:
            ProcessingResult: Result of the transformation
        """
        try:
            input_data = context.get(self.input_key)
            if input_data is None:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(f"No data found for input key '{self.input_key}' in context"),
                )

            # Apply transformation
            transformed_data = self.transform_func(input_data)

            # Store in context
            context.set(self.output_key, transformed_data)

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=transformed_data,
                metadata={
                    "processor_type": "data_transform",
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "input_type": type(input_data).__name__,
                    "output_type": type(transformed_data).__name__,
                },
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e,
            )

    def validate_input(self, context: Context) -> bool:
        """Validate that the required input key exists in context."""
        return context.has(self.input_key)
