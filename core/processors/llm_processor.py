from typing import Optional

from ..base import Processor, ProcessingResult, ProcessingStatus
from ..context import Context


class LLMProcessor(Processor):
    """
    A processor that simulates LLM processing.

    In a real implementation, this would call an actual LLM API.
    For now, it provides a mock response.
    """

    def __init__(
        self,
        model: str = "gpt-3.5-turbo",
        input_key: str = "prompt",
        output_key: str = "llm_response",
        name: Optional[str] = None,
    ):
        """
        Initialize LLM processor.

        Args:
            model: The model name to use (currently for documentation only)
            input_key: The key to read the prompt from context
            output_key: The key to store the LLM response in context
            name: Optional name for the processor
        """
        super().__init__(name)
        self.model = model
        self.input_key = input_key
        self.output_key = output_key

    async def process(self, context: Context) -> ProcessingResult:
        """
        Process the prompt using LLM (currently mocked).

        Args:
            context: The processing context containing the prompt

        Returns:
            ProcessingResult: Result of the LLM processing
        """
        try:
            prompt = context.get(self.input_key)
            if not prompt:
                return ProcessingResult(
                    status=ProcessingStatus.FAILED,
                    error=ValueError(f"No data found for input key '{self.input_key}' in context"),
                )

            # Mock LLM response - in real implementation, this would call an API
            mock_response = self._generate_mock_response(prompt)

            # Add the response to context using the specified output key
            context.set(self.output_key, mock_response)

            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=mock_response,
                metadata={
                    "processor_type": "llm",
                    "model": self.model,
                    "input_key": self.input_key,
                    "output_key": self.output_key,
                    "response_length": len(mock_response),
                },
            )
        except Exception as e:
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e,
            )

    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate a mock response for the given prompt.

        Args:
            prompt: The input prompt

        Returns:
            str: Mock response
        """
        if "API" in prompt:
            return (
                "API（Application Programming Interface，应用程序编程接口）是一组预定义的规则和协议，"
                "它允许不同的软件应用程序之间进行通信和数据交换。\n\n"
                "简单来说，API 就像是一个'翻译官'或'服务员'：\n"
                "- 当你在餐厅点菜时，服务员帮你把需求传达给厨房\n"
                "- API 就是帮助不同程序之间传递信息的'服务员'\n\n"
                "例如，当你在手机上查看天气时，天气应用通过调用天气服务的 API 来获取最新的天气数据。"
            )
        else:
            return f"这是一个关于 '{prompt[:50]}...' 的模拟回答。在实际应用中，这里会调用真正的 LLM API。"

    def validate_input(self, context: Context) -> bool:
        """Validate that the required input key exists in context."""
        return context.has(self.input_key)
