"""
Example usage of the llm-processors framework.
"""

import os
import asyncio
from llm_processors import Context, Pipeline, PromptProcessor, ChatProcessor
from llm_processors.base import ProcessingStatus

async def main():
    """
    通过 Python 代码构建并运行一个简单的 Pipeline。
    """
    prompt_processor = PromptProcessor(
        prompt="请用简单的语言解释一下，编程中的 'API' 是什么？",
    )

    llm_processor = ChatProcessor(
        base_url=os.getenv("BASE_URL", "https://api.openai.com/v1"),
        api_key=os.getenv("API_KEY"),
        model="deepseek-chat",
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
    final_result = await pipeline.execute(context)

    # 4. 从 Context 中获取并打印结果
    print("AI 的回答是：")
    for result in final_result:
        if result.status == ProcessingStatus.COMPLETED:
            print(result.data)
            print(result.metadata)
        else:
            print(f"处理失败: {result.error}")  



if __name__ == "__main__":
    asyncio.run(main())
