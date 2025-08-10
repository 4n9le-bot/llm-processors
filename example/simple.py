"""
Example usage of the llm-processors framework.
"""

from core import Context, Pipeline, PromptProcessor, LLMProcessor


def main():
    """
    通过 Python 代码构建并运行一个简单的 Pipeline。
    """
    # 1. 定义 Pipeline 中的各个处理器 (Processor)
    prompt_processor = PromptProcessor(
        # 模板中用 {{...}} 标记变量
        prompt="请用简单的语言解释一下，编程中的 'API' 是什么？",
    )

    llm_processor = LLMProcessor(
        # 指定要使用的模型
        model="gpt-3.5-turbo",
    )

    context = Context()

    # 2. 创建流水线 (Pipeline)，并将处理器按顺序添加进去
    pipeline = Pipeline(
        processors=[
            prompt_processor,
            llm_processor,
        ]
    )

    # 3. 运行流水线
    # process() 方法会返回最终的 Context 对象
    final_result = pipeline.execute(context)

    # 4. 从 Context 中获取并打印结果
    # LLMProcessor 默认会将结果写入 'llm_response' 这个 key
    print("AI 的回答是：")
    print(final_result["data"])

    # 也可以打印完整的 context，观察数据的流动
    print("\n--- 最终的 Context 内容 ---")
    print(final_context)


if __name__ == "__main__":
    main()
