#!/usr/bin/env python3
"""
测试验证逻辑是否正常工作
"""

import asyncio
from core.context import Context
from core.processors import PromptProcessor, LLMProcessor
from core.pipeline import SequentialPipeline


async def test_pipeline_validation():
    """测试 pipeline 验证逻辑是否还能正常工作"""
    
    # 1. 测试正常情况 - input_key 和 output_key 匹配
    print("=== 测试正常情况 ===")
    pipeline = SequentialPipeline()
    
    prompt_proc = PromptProcessor(prompt="Test", output_key="user_prompt")
    llm_proc = LLMProcessor(input_key="user_prompt", output_key="response")
    
    pipeline.add_processor(prompt_proc)
    pipeline.add_processor(llm_proc)
    
    errors = pipeline.validate_pipeline()
    print(f"验证错误: {errors}")
    assert len(errors) == 0, "正常情况不应该有验证错误"
    
    # 2. 测试错误情况 - input_key 不匹配
    print("\n=== 测试错误情况 ===")
    pipeline2 = SequentialPipeline()
    
    prompt_proc2 = PromptProcessor(prompt="Test", output_key="user_prompt")
    llm_proc2 = LLMProcessor(input_key="wrong_key", output_key="response")  # 错误的 input_key
    
    pipeline2.add_processor(prompt_proc2)
    pipeline2.add_processor(llm_proc2)
    
    errors2 = pipeline2.validate_pipeline()
    print(f"验证错误: {errors2}")
    assert len(errors2) == 1, "应该有一个验证错误"
    assert "wrong_key" in errors2[0], "错误信息应该包含错误的key"
    
    # 3. 测试并行 pipeline 的冲突检测
    print("\n=== 测试并行 pipeline 冲突检测 ===")
    from core.pipeline import ParallelPipeline
    
    parallel_pipeline = ParallelPipeline()
    
    proc1 = PromptProcessor(prompt="Test1", output_key="same_key")
    proc2 = PromptProcessor(prompt="Test2", output_key="same_key")  # 相同的 output_key
    
    parallel_pipeline.add_processor(proc1)
    parallel_pipeline.add_processor(proc2)
    
    errors3 = parallel_pipeline.validate_pipeline()
    print(f"验证错误: {errors3}")
    assert len(errors3) == 1, "应该检测到冲突"
    assert "conflict" in errors3[0], "错误信息应该包含冲突信息"
    
    print("\n✅ 所有验证逻辑测试通过！")


async def test_actual_execution():
    """测试实际执行是否正常"""
    print("\n=== 测试实际执行 ===")
    
    context = Context()
    
    # 创建简单的 pipeline
    pipeline = SequentialPipeline()
    prompt_proc = PromptProcessor(prompt="What is AI?", output_key="prompt")
    llm_proc = LLMProcessor(input_key="prompt", output_key="response")
    
    pipeline.add_processor(prompt_proc)
    pipeline.add_processor(llm_proc)
    
    # 执行
    results = await pipeline.execute(context)
    
    print(f"执行结果数量: {len(results)}")
    print(f"Context 内容: {dict(context._data)}")
    
    assert len(results) == 2, "应该有两个处理结果"
    assert "prompt" in context, "Context 应该包含 prompt"
    assert "response" in context, "Context 应该包含 response"
    
    print("✅ 实际执行测试通过！")


if __name__ == "__main__":
    asyncio.run(test_pipeline_validation())
    asyncio.run(test_actual_execution())
