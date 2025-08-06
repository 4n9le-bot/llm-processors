"""
Tests for pipeline implementations.
"""

import pytest
from unittest.mock import AsyncMock

from core.pipeline import SequentialPipeline, ParallelPipeline, Pipeline
from core.base import Context, ProcessingStatus, ProcessingResult
from tests.conftest import assert_result_success, assert_result_failed
from tests.test_base import MockProcessor


class TestSequentialPipeline:
    """Test cases for SequentialPipeline."""
    
    def test_sequential_pipeline_initialization(self):
        """Test SequentialPipeline initialization."""
        pipeline = SequentialPipeline()
        assert pipeline.name.startswith("SequentialPipeline_")
        assert pipeline._processors == []
        assert pipeline.default_timeout is None
        
        # Test with custom parameters
        processors = [MockProcessor()]
        pipeline_custom = SequentialPipeline(
            name="CustomPipeline",
            default_timeout=30.0,
            processors=processors
        )
        assert pipeline_custom.name == "CustomPipeline"
        assert pipeline_custom.default_timeout == 30.0
        assert len(pipeline_custom._processors) == 1
    
    def test_sequential_pipeline_add_processor(self):
        """Test adding processors to pipeline."""
        pipeline = SequentialPipeline()
        processor1 = MockProcessor("Processor1")
        processor2 = MockProcessor("Processor2")
        
        # Test method chaining
        result = pipeline.add_processor(processor1).add_processor(processor2)
        assert result is pipeline
        assert len(pipeline._processors) == 2
        assert pipeline._processors[0].name == "Processor1"
        assert pipeline._processors[1].name == "Processor2"
    
    def test_sequential_pipeline_add_processors(self):
        """Test adding multiple processors at once."""
        pipeline = SequentialPipeline()
        processors = [MockProcessor("P1"), MockProcessor("P2")]
        
        pipeline.add_processors(processors)
        assert len(pipeline._processors) == 2
    
    def test_sequential_pipeline_remove_processor(self):
        """Test removing processors from pipeline."""
        pipeline = SequentialPipeline()
        processor = MockProcessor("TestProcessor")
        pipeline.add_processor(processor)
        
        # Test successful removal
        assert pipeline.remove_processor("TestProcessor") is True
        assert len(pipeline._processors) == 0
        
        # Test removing non-existent processor
        assert pipeline.remove_processor("NonExistent") is False
    
    def test_sequential_pipeline_get_processors(self):
        """Test getting processors from pipeline."""
        pipeline = SequentialPipeline()
        processor = MockProcessor()
        pipeline.add_processor(processor)
        
        processors = pipeline.get_processors()
        assert len(processors) == 1
        assert processors[0] is processor
        
        # Ensure returned list is a copy
        processors.clear()
        assert len(pipeline._processors) == 1
    
    def test_sequential_pipeline_error_handler(self):
        """Test adding error handlers."""
        pipeline = SequentialPipeline()
        
        def mock_handler(error, context):
            context.set("handled_error", str(error))
        
        result = pipeline.add_error_handler("TestProcessor", mock_handler)
        assert result is pipeline
        assert "TestProcessor" in pipeline._error_handlers
    
    def test_sequential_pipeline_timeout_setting(self):
        """Test setting processor timeouts."""
        pipeline = SequentialPipeline(default_timeout=10.0)
        
        result = pipeline.set_processor_timeout("TestProcessor", 20.0)
        assert result is pipeline
        assert pipeline._processor_timeouts["TestProcessor"] == 20.0
    
    @pytest.mark.asyncio
    async def test_sequential_pipeline_execute_success(self):
        """Test successful pipeline execution."""
        pipeline = SequentialPipeline()
        processor1 = MockProcessor("P1")
        processor2 = MockProcessor("P2")
        pipeline.add_processors([processor1, processor2])
        
        context = Context({"initial": "data"})
        results = await pipeline.execute(context)
        
        assert len(results) == 2
        assert_result_success(results[0])
        assert_result_success(results[1])
        assert processor1.process_called
        assert processor2.process_called
        assert context.get_history() == ["P1", "P2"]
    
    @pytest.mark.asyncio
    async def test_sequential_pipeline_execute_with_validation_failure(self):
        """Test pipeline execution with validation failure."""
        pipeline = SequentialPipeline()
        processor = MockProcessor(should_fail=True)  # This will fail validation
        pipeline.add_processor(processor)
        
        context = Context()
        results = await pipeline.execute(context)
        
        assert len(results) == 1
        assert_result_failed(results[0], ValueError)
        assert not processor.process_called  # Should not be called due to validation failure
    
    @pytest.mark.asyncio
    async def test_sequential_pipeline_execute_with_processor_failure(self):
        """Test pipeline execution with processor failure."""
        pipeline = SequentialPipeline()
        
        # Create a processor that passes validation but fails processing
        class FailingProcessor(MockProcessor):
            def validate_input(self, context):
                return True  # Pass validation
            
            async def process(self, context):
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=RuntimeError("Processing failed")
                )
        
        processor = FailingProcessor()
        pipeline.add_processor(processor)
        
        context = Context()
        results = await pipeline.execute(context, stop_on_error=True)
        
        assert len(results) == 1
        assert_result_failed(results[0], RuntimeError)
    
    @pytest.mark.asyncio
    async def test_sequential_pipeline_execute_continue_on_error(self):
        """Test pipeline execution continuing after error."""
        pipeline = SequentialPipeline()
        processor1 = MockProcessor(should_fail=True)
        processor2 = MockProcessor("P2")
        pipeline.add_processors([processor1, processor2])
        
        context = Context()
        results = await pipeline.execute(context, stop_on_error=False)
        
        assert len(results) == 2
        assert_result_failed(results[0])  # First processor failed validation
        assert_result_success(results[1])  # Second processor succeeded
    
    @pytest.mark.asyncio
    async def test_sequential_pipeline_execute_with_error_handler(self):
        """Test pipeline execution with error handler."""
        pipeline = SequentialPipeline()
        
        # Mock error handler
        def error_handler(error, context):
            context.set("error_handled", True)
            context.set("error_message", str(error))
        
        processor = MockProcessor(should_fail=True)
        pipeline.add_processor(processor)
        pipeline.add_error_handler(processor.name, error_handler)
        
        context = Context()
        await pipeline.execute(context)
        
        assert context.get("error_handled") is True
        assert "error_message" in context.get_all()
    
    def test_sequential_pipeline_validate_pipeline_empty(self):
        """Test pipeline validation with empty pipeline."""
        pipeline = SequentialPipeline()
        errors = pipeline.validate_pipeline()
        assert len(errors) == 1
        assert "no processors" in errors[0]
    
    def test_sequential_pipeline_validate_pipeline_success(self):
        """Test successful pipeline validation."""
        pipeline = SequentialPipeline()
        
        # Create processors with compatible inputs/outputs
        class ProducerProcessor(MockProcessor):
            def get_output_keys(self):
                return ["data"]
        
        class ConsumerProcessor(MockProcessor):
            def get_required_inputs(self):
                return ["data"]
            
            def get_output_keys(self):
                return ["result"]
        
        pipeline.add_processors([ProducerProcessor(), ConsumerProcessor()])
        errors = pipeline.validate_pipeline()
        assert len(errors) == 0
    
    def test_sequential_pipeline_validate_pipeline_missing_input(self):
        """Test pipeline validation with missing required input."""
        pipeline = SequentialPipeline()
        
        class ConsumerProcessor(MockProcessor):
            def get_required_inputs(self):
                return ["missing_data"]
        
        pipeline.add_processor(ConsumerProcessor())
        errors = pipeline.validate_pipeline()
        assert len(errors) == 1
        assert "missing_data" in errors[0]
    
    def test_sequential_pipeline_run_method(self):
        """Test the convenience run() method."""
        pipeline = SequentialPipeline()
        processor = MockProcessor()
        pipeline.add_processor(processor)
        
        context = pipeline.run({"initial": "data"})
        
        assert isinstance(context, Context)
        assert context.get("initial") == "data"
        assert context.get("mock_output") == "processed"
        assert processor.process_called
    
    def test_sequential_pipeline_run_method_with_failure(self):
        """Test run() method with processor failure."""
        pipeline = SequentialPipeline()
        
        class FailingProcessor(MockProcessor):
            def validate_input(self, context):
                return True
            
            async def process(self, context):
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=RuntimeError("Test failure")
                )
        
        pipeline.add_processor(FailingProcessor())
        
        with pytest.raises(RuntimeError, match="Pipeline execution failed"):
            pipeline.run()
    
    def test_sequential_pipeline_string_representation(self):
        """Test pipeline string representation."""
        pipeline = SequentialPipeline(name="TestPipeline")
        pipeline.add_processor(MockProcessor())
        
        repr_str = repr(pipeline)
        assert "SequentialPipeline" in repr_str
        assert "TestPipeline" in repr_str
        assert "processors=1" in repr_str


class TestParallelPipeline:
    """Test cases for ParallelPipeline."""
    
    def test_parallel_pipeline_initialization(self):
        """Test ParallelPipeline initialization."""
        pipeline = ParallelPipeline()
        assert pipeline.name.startswith("ParallelPipeline_")
        assert pipeline._processors == []
    
    @pytest.mark.asyncio
    async def test_parallel_pipeline_execute_success(self):
        """Test successful parallel execution."""
        pipeline = ParallelPipeline()
        processor1 = MockProcessor("P1")
        processor2 = MockProcessor("P2")
        pipeline.add_processors([processor1, processor2])
        
        context = Context({"initial": "data"})
        results = await pipeline.execute(context)
        
        assert len(results) == 2
        assert_result_success(results[0])
        assert_result_success(results[1])
        # Both processors should have been called
        assert processor1.process_called
        assert processor2.process_called
    
    @pytest.mark.asyncio
    async def test_parallel_pipeline_execute_with_failure(self):
        """Test parallel execution with one processor failing."""
        pipeline = ParallelPipeline()
        processor_success = MockProcessor("Success")
        processor_fail = MockProcessor("Fail", should_fail=True)
        pipeline.add_processors([processor_success, processor_fail])
        
        context = Context()
        results = await pipeline.execute(context, stop_on_error=False)
        
        assert len(results) == 2
        # One should succeed, one should fail validation
        success_results = [r for r in results if r.status == ProcessingStatus.COMPLETED]
        failed_results = [r for r in results if r.status == ProcessingStatus.FAILED]
        assert len(success_results) == 1
        assert len(failed_results) == 1
    
    def test_parallel_pipeline_validate_conflicting_outputs(self):
        """Test validation with conflicting processor outputs."""
        pipeline = ParallelPipeline()
        
        class ConflictingProcessor1(MockProcessor):
            def get_output_keys(self):
                return ["same_key"]
        
        class ConflictingProcessor2(MockProcessor):
            def get_output_keys(self):
                return ["same_key"]
        
        pipeline.add_processors([ConflictingProcessor1(), ConflictingProcessor2()])
        errors = pipeline.validate_pipeline()
        assert len(errors) > 0
        assert "conflict" in errors[0]


class TestPipelineAlias:
    """Test the Pipeline alias."""
    
    def test_pipeline_alias_is_sequential(self):
        """Test that Pipeline is an alias for SequentialPipeline."""
        assert Pipeline is SequentialPipeline
        
        pipeline = Pipeline()
        assert isinstance(pipeline, SequentialPipeline)
