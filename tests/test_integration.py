"""
Integration tests for the llm-processors framework.
"""

import pytest

from core import Pipeline, PromptProcessor, LLMProcessor, NoOpProcessor, Context


class TestPipelineIntegration:
    """Integration tests for complete pipeline workflows."""
    
    def test_simple_prompt_llm_pipeline(self):
        """Test a simple pipeline with prompt and LLM processors."""
        # Create processors
        prompt_processor = PromptProcessor(
            prompt="请用简单的语言解释一下，编程中的 'API' 是什么？"
        )
        llm_processor = LLMProcessor(model="gpt-3.5-turbo")
        
        # Create pipeline
        pipeline = Pipeline(processors=[prompt_processor, llm_processor])
        
        # Run pipeline
        final_context = pipeline.run()
        
        # Verify results
        assert "prompt" in final_context
        assert "llm_response" in final_context
        assert final_context["prompt"] == prompt_processor.prompt
        assert "API" in final_context["llm_response"]
        assert "应用程序编程接口" in final_context["llm_response"]
        
        # Verify execution history
        history = final_context.get_history()
        assert history == ["PromptProcessor", "LLMProcessor"]
    
    def test_pipeline_with_initial_data(self):
        """Test pipeline with initial context data."""
        llm_processor = LLMProcessor()
        pipeline = Pipeline(processors=[llm_processor])
        
        initial_data = {
            "prompt": "What is Python programming language?",
            "user_id": "test_user"
        }
        
        final_context = pipeline.run(initial_data)
        
        # Verify initial data is preserved
        assert final_context["user_id"] == "test_user"
        assert final_context["prompt"] == initial_data["prompt"]
        
        # Verify LLM response is generated
        assert "llm_response" in final_context
        assert "模拟回答" in final_context["llm_response"]
    
    def test_multi_processor_pipeline(self):
        """Test pipeline with multiple processors."""
        prompt_processor = PromptProcessor(prompt="Test prompt")
        llm_processor = LLMProcessor()
        noop_processor = NoOpProcessor(name="Logger")
        
        pipeline = Pipeline(processors=[
            prompt_processor,
            llm_processor,
            noop_processor
        ])
        
        final_context = pipeline.run()
        
        # Verify all processors executed
        history = final_context.get_history()
        assert len(history) == 3
        assert "PromptProcessor" in history
        assert "LLMProcessor" in history
        assert "Logger" in history
        
        # Verify data flow
        assert final_context["prompt"] == "Test prompt"
        assert "llm_response" in final_context
    
    def test_pipeline_validation_success(self):
        """Test pipeline validation with compatible processors."""
        prompt_processor = PromptProcessor(prompt="Test")
        llm_processor = LLMProcessor()
        
        pipeline = Pipeline(processors=[prompt_processor, llm_processor])
        
        # Validate pipeline
        errors = pipeline.validate_pipeline()
        assert len(errors) == 0
    
    def test_pipeline_validation_failure(self):
        """Test pipeline validation with incompatible processors."""
        # LLMProcessor requires "prompt" but no processor provides it
        llm_processor = LLMProcessor()
        
        pipeline = Pipeline(processors=[llm_processor])
        
        # Validate pipeline
        errors = pipeline.validate_pipeline()
        assert len(errors) > 0
        assert "prompt" in errors[0]

    @pytest.mark.asyncio
    async def test_async_pipeline_execution(self):
        """Test async pipeline execution."""
        prompt_processor = PromptProcessor(prompt="Async test")
        llm_processor = LLMProcessor()
        
        pipeline = Pipeline(processors=[prompt_processor, llm_processor])
        context = Context()
        
        # Execute pipeline asynchronously
        results = await pipeline.execute(context)
        
        assert len(results) == 2
        assert all(r.status.value == "completed" for r in results)
        assert context["prompt"] == "Async test"
        assert "llm_response" in context
    
    def test_empty_pipeline(self):
        """Test behavior with empty pipeline."""
        pipeline = Pipeline()
        
        final_context = pipeline.run()
        
        # Should return empty context with no errors
        assert isinstance(final_context, Context)
        assert len(final_context.get_all()) == 0
        assert len(final_context.get_history()) == 0
    
    def test_pipeline_with_custom_timeout(self):
        """Test pipeline with custom timeout settings."""
        prompt_processor = PromptProcessor(prompt="Test")
        llm_processor = LLMProcessor()
        
        pipeline = Pipeline(
            processors=[prompt_processor, llm_processor],
            default_timeout=30.0
        )
        
        # Set specific timeout for LLM processor
        pipeline.set_processor_timeout("LLMProcessor", 60.0)
        
        final_context = pipeline.run()
        
        # Should succeed normally
        assert "llm_response" in final_context
    
    def test_context_data_flow(self):
        """Test data flow through context in pipeline."""
        # Custom processor that modifies context
        from core.base import Processor, ProcessingResult, ProcessingStatus
        
        class DataProcessor(Processor):
            def __init__(self, name="DataProcessor"):
                super().__init__(name)
            
            async def process(self, context):
                # Add some data to context
                context.set("processed_data", "modified")
                context.set("step_counter", context.get("step_counter", 0) + 1)
                
                return ProcessingResult(status=ProcessingStatus.COMPLETED)
            
            def validate_input(self, context):
                return True
            
            def get_required_inputs(self):
                return []
            
            def get_output_keys(self):
                return ["processed_data", "step_counter"]
        
        prompt_processor = PromptProcessor(prompt="Test")
        data_processor = DataProcessor()
        
        pipeline = Pipeline(processors=[prompt_processor, data_processor])
        
        final_context = pipeline.run({"initial_value": "test"})
        
        # Verify data flow
        assert final_context["initial_value"] == "test"  # Initial data preserved
        assert final_context["prompt"] == "Test"  # Added by PromptProcessor
        assert final_context["processed_data"] == "modified"  # Added by DataProcessor
        assert final_context["step_counter"] == 1  # Modified by DataProcessor


class TestEndToEndScenarios:
    """End-to-end scenario tests."""
    
    def test_ai_question_answering_workflow(self):
        """Test complete AI question-answering workflow."""
        # Setup: Create a question-answering pipeline
        question = "请解释什么是机器学习？"
        
        prompt_processor = PromptProcessor(prompt=question)
        llm_processor = LLMProcessor(model="gpt-4")
        
        pipeline = Pipeline(
            name="QAPipeline",
            processors=[prompt_processor, llm_processor]
        )
        
        # Execute: Run the pipeline
        result_context = pipeline.run()
        
        # Verify: Check the complete workflow
        assert result_context["prompt"] == question
        assert "llm_response" in result_context
        
        # Verify the response makes sense (contains expected keywords)
        response = result_context["llm_response"]
        assert len(response) > 0
        
        # Verify execution metadata
        history = result_context.get_history()
        assert len(history) == 2
        assert history == ["PromptProcessor", "LLMProcessor"]
    
    def test_multi_step_data_processing(self):
        """Test multi-step data processing scenario."""
        # Step 1: Prepare data
        prompt_processor = PromptProcessor(prompt="Analyze this data")
        
        # Step 2: Process with AI
        llm_processor = LLMProcessor()
        
        # Step 3: Log the process
        logger = NoOpProcessor(
            name="ProcessLogger",
            metadata={"step": "final_logging"}
        )
        
        pipeline = Pipeline(processors=[
            prompt_processor,
            llm_processor,
            logger
        ])
        
        # Execute with initial metadata
        initial_data = {
            "session_id": "session_123",
            "timestamp": "2025-08-06T10:00:00Z"
        }
        
        final_context = pipeline.run(initial_data)
        
        # Verify complete data processing
        assert final_context["session_id"] == "session_123"
        assert final_context["timestamp"] == "2025-08-06T10:00:00Z"
        assert final_context["prompt"] == "Analyze this data"
        assert "llm_response" in final_context
        
        # Verify all steps executed
        history = final_context.get_history()
        assert len(history) == 3
        assert "ProcessLogger" in history
