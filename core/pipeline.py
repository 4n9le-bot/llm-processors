"""
Pipeline implementations for the llm-processors framework.

This module provides concrete implementations of pipelines for different execution patterns.
"""

from typing import Dict, List, Optional, Any, Sequence
import asyncio

from .base import Pipeline, Processor, ProcessingResult, ProcessingStatus
from .context import Context


class SequentialPipeline(Pipeline):
    """
    Pipeline that executes processors in sequence.
    
    The pipeline manages the flow of data through multiple processors,
    handling errors and maintaining execution state.
    """
    
    def __init__(
        self, 
        name: Optional[str] = None, 
        default_timeout: Optional[float] = None,
        processors: Optional[Sequence[Processor]] = None
    ):
        """
        Initialize pipeline.
        
        Args:
            name: Optional name for the pipeline
            default_timeout: Default timeout for processors in seconds
            processors: Optional sequence of processors to add initially
        """
        self.name = name or f"SequentialPipeline_{id(self)}"
        self.default_timeout = default_timeout
        self._processors: List[Processor] = list(processors) if processors else []
        self._processor_timeouts: Dict[str, float] = {}
    
    def add_processor(self, processor: Processor) -> 'SequentialPipeline':
        """
        Add a processor to the pipeline.
        
        Args:
            processor: The processor to add
            
        Returns:
            SequentialPipeline: Self for method chaining
        """
        self._processors.append(processor)
        return self
    
    def add_processors(self, processors: Sequence[Processor]) -> 'SequentialPipeline':
        """
        Add multiple processors to the pipeline.
        
        Args:
            processors: Sequence of processors to add
            
        Returns:
            SequentialPipeline: Self for method chaining
        """
        self._processors.extend(processors)
        return self
    
    def remove_processor(self, processor_name: str) -> bool:
        """
        Remove a processor by name.
        
        Args:
            processor_name: Name of the processor to remove
            
        Returns:
            bool: True if processor was found and removed
        """
        for i, processor in enumerate(self._processors):
            if processor.name == processor_name:
                del self._processors[i]
                return True
        return False
    
    def get_processors(self) -> List[Processor]:
        """Get list of all processors in the pipeline."""
        return self._processors.copy()

    def set_processor_timeout(self, processor_name: str, timeout: float) -> 'SequentialPipeline':
        """
        Set timeout for a specific processor.
        
        Args:
            processor_name: Name of the processor
            timeout: Timeout in seconds
            
        Returns:
            SequentialPipeline: Self for method chaining
        """
        self._processor_timeouts[processor_name] = timeout
        return self
    
    async def _execute_processor_with_timeout(
        self, 
        processor: Processor, 
        context: Context
    ) -> ProcessingResult:
        """
        Execute a processor with optional timeout.
        
        Args:
            processor: The processor to execute
            context: The processing context
            
        Returns:
            ProcessingResult: Result of the processing operation
        """
        # Determine timeout for this processor
        timeout = self._processor_timeouts.get(processor.name, self.default_timeout)
        
        if timeout is None:
            return await processor.process(context)
        
        try:
            return await asyncio.wait_for(processor.process(context), timeout=timeout)
        except asyncio.TimeoutError:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=asyncio.TimeoutError(f"Processor {processor.name} timed out after {timeout}s")
            )
    
    async def execute(
        self, 
        context: Context, 
        stop_on_error: bool = True
    ) -> List[ProcessingResult]:
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
            # Validate input before processing
            if not processor.validate_input(context):
                result = ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(f"Invalid input for processor {processor.name}")
                )
                results.append(result)
                
                if stop_on_error:
                    break
                continue
            
            # Add processor to execution history
            context.add_to_history(processor.name)
            
            try:
                # Execute processor with timeout
                result = await self._execute_processor_with_timeout(processor, context)
                results.append(result)
                
                # Stop on error if requested
                if result.status == ProcessingStatus.FAILED and stop_on_error:
                    break
                        
            except Exception as e:
                result = ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=e
                )
                results.append(result)
                
                if stop_on_error:
                    break
        
        return results
    
    def run(self, initial_data: Optional[Dict[str, Any]] = None) -> Context:
        """
        Convenient synchronous method to run the pipeline.
        
        Args:
            initial_data: Optional initial data for the context
            
        Returns:
            Context: The final context after all processors have run
        """
        context = Context(initial_data)
        
        # Run the pipeline synchronously
        results = asyncio.run(self.execute(context))
        
        # Check if any processor failed
        failed_results = [r for r in results if r.status == ProcessingStatus.FAILED]
        if failed_results:
            # Get the first error for simplicity
            first_error = failed_results[0].error
            raise RuntimeError(f"Pipeline execution failed: {first_error}")
        
        return context
    
    def validate_pipeline(self) -> List[str]:
        """
        Validate the pipeline configuration.
        
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors: List[str] = []
        
        if not self._processors:
            errors.append("Pipeline has no processors")
            return errors
        
        # Check for required inputs/outputs compatibility
        available_keys = set()
        
        for i, processor in enumerate(self._processors):
            # Get input key from processor attribute
            input_key = getattr(processor, 'input_key', None)
            
            # Check if required input is available
            if input_key and input_key not in available_keys:
                errors.append(
                    f"Processor {processor.name} at position {i} "
                    f"requires input '{input_key}' which is not available"
                )
            
            # Add output key to available keys
            output_key = getattr(processor, 'output_key', None)
            if output_key:
                available_keys.add(output_key)
        
        return errors
    
    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return f"SequentialPipeline(name='{self.name}', processors={len(self._processors)})"


class ParallelPipeline(Pipeline):
    """
    Pipeline that executes processors in parallel.
    
    Useful when processors are independent and can run concurrently.
    """
    
    def __init__(self, name: Optional[str] = None, default_timeout: Optional[float] = None):
        """
        Initialize parallel pipeline.
        
        Args:
            name: Optional name for the pipeline
            default_timeout: Default timeout for processors in seconds
        """
        self.name = name or f"ParallelPipeline_{id(self)}"
        self.default_timeout = default_timeout
        self._processors: List[Processor] = []
        self._processor_timeouts: Dict[str, float] = {}
    
    def add_processor(self, processor: Processor) -> 'ParallelPipeline':
        """Add a processor to the pipeline."""
        self._processors.append(processor)
        return self
    
    def add_processors(self, processors: Sequence[Processor]) -> 'ParallelPipeline':
        """Add multiple processors to the pipeline."""
        self._processors.extend(processors)
        return self
    
    def remove_processor(self, processor_name: str) -> bool:
        """Remove a processor by name."""
        for i, processor in enumerate(self._processors):
            if processor.name == processor_name:
                del self._processors[i]
                return True
        return False
    
    def get_processors(self) -> List[Processor]:
        """Get list of all processors in the pipeline."""
        return self._processors.copy()

    def set_processor_timeout(self, processor_name: str, timeout: float) -> 'ParallelPipeline':
        """Set timeout for a specific processor."""
        self._processor_timeouts[processor_name] = timeout
        return self
    
    async def _execute_processor_with_timeout(
        self, 
        processor: Processor, 
        context: Context
    ) -> ProcessingResult:
        """Execute a processor with optional timeout."""
        timeout = self._processor_timeouts.get(processor.name, self.default_timeout)
        
        if timeout is None:
            return await processor.process(context)
        
        try:
            return await asyncio.wait_for(processor.process(context), timeout=timeout)
        except asyncio.TimeoutError:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=asyncio.TimeoutError(f"Processor {processor.name} timed out after {timeout}s")
            )
    
    async def execute(
        self, 
        context: Context, 
        stop_on_error: bool = True
    ) -> List[ProcessingResult]:
        """
        Execute processors in parallel.
        
        Args:
            context: The processing context
            stop_on_error: Whether to stop execution on first error
            
        Returns:
            List[ProcessingResult]: Results from each processor
        """
        # Validate all processors first
        for processor in self._processors:
            if not processor.validate_input(context):
                if stop_on_error:
                    return [ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error=ValueError(f"Invalid input for processor {processor.name}")
                    )]
        
        # Create individual context copies for each processor
        tasks = [
            self._execute_processor_with_timeout(processor, context)
            for processor in self._processors
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Convert exceptions to ProcessingResults
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(ProcessingResult(
                        status=ProcessingStatus.FAILED,
                        error=result
                    ))
                else:
                    processed_results.append(result)
                
                # Add to history
                context.add_to_history(self._processors[i].name)
            
            return processed_results
            
        except Exception as e:
            return [ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )]
    
    def validate_pipeline(self) -> List[str]:
        """
        Validate the pipeline configuration for parallel execution.
        
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors: List[str] = []
        
        if not self._processors:
            errors.append("Pipeline has no processors")
            return errors
        
        # For parallel execution, all processors should be able to run with the initial context
        # Check that no processor depends on output from another processor in the same pipeline
        all_outputs = set()
        for processor in self._processors:
            output_key = getattr(processor, 'output_key', None)
            if output_key:
                if output_key in all_outputs:
                    errors.append(
                        f"Processor {processor.name} produces output '{output_key}' that conflicts with other processors"
                    )
                all_outputs.add(output_key)
        
        return errors
    
    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return f"ParallelPipeline(name='{self.name}', processors={len(self._processors)})"


# Convenience alias for the most common use case
Pipeline = SequentialPipeline
