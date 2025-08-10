# Processor Input/Output Key 重构总结

## 重构概述

按照要求将 Context 设计为数据在 Pipeline 中流动的载体，通过 input_key 和 output_key 实现处理器之间的数据传递。

## 主要改进

### 1. PromptProcessor
**之前**: 固定输出到 "prompt" 键
```python
context.set("prompt", self.prompt)
```

**现在**: 可配置的输出键
```python
def __init__(self, prompt: str, output_key: str = "prompt", name: Optional[str] = None):
    self.output_key = output_key

async def process(self, context: Context):
    context.set(self.output_key, self.prompt)  # 使用可配置的输出键
```

### 2. LLMProcessor
**之前**: 固定从 "prompt" 读取，固定输出到 "llm_response"
```python
prompt = context.get("prompt")
context.set("llm_response", mock_response)
```

**现在**: 可配置的输入和输出键
```python
def __init__(self, model: str = "gpt-3.5-turbo", 
             input_key: str = "prompt", 
             output_key: str = "llm_response", 
             name: Optional[str] = None):
    self.input_key = input_key
    self.output_key = output_key

async def process(self, context: Context):
    prompt = context.get(self.input_key)       # 从配置的输入键读取
    context.set(self.output_key, response)     # 写入配置的输出键
```

### 3. NoOpProcessor 增强
- 添加了 input_key 和 output_key 支持
- 支持 passthrough 模式，可以将输入数据传递到输出
- 更灵活的调试和测试用途

### 4. 新增 DataTransformProcessor
全新的通用数据转换处理器：
```python
class DataTransformProcessor(Processor):
    def __init__(self, input_key: str, output_key: str, 
                 transform_func: Optional[Callable[[Any], Any]] = None):
        self.input_key = input_key
        self.output_key = output_key
        self.transform_func = transform_func or (lambda x: x)
```

## 数据流示例

### 传统固定键方式
```
PromptProcessor → "prompt" → LLMProcessor → "llm_response"
```

### 新的可配置键方式
```
PromptProcessor(output_key="user_query") 
  ↓ "user_query"
LLMProcessor(input_key="user_query", output_key="ai_response")
  ↓ "ai_response"  
DataTransformProcessor(input_key="ai_response", output_key="formatted_response")
  ↓ "formatted_response"
NoOpProcessor(input_key="formatted_response", output_key="final_output", passthrough=True)
```

## 实际运行效果

通过 `test_keys_demo.py` 演示了完整的数据流：

```
📝 Initial context: {}

🎯 Final context:
  user_query: What is machine learning?
  ai_response: 这是一个关于 'What is machine learning?...' 的模拟回答...
  formatted_response: 这是一个关于 'WHAT IS MACHINE LEARNING?...' 的模拟回答...
  final_output: 这是一个关于 'WHAT IS MACHINE LEARNING?...' 的模拟回答...

📜 Execution history: ['UserQueryProcessor', 'AIProcessor', 'UppercaseFormatter', 'FinalProcessor']
```

## 向后兼容性

所有现有的处理器都保持向后兼容：
- `PromptProcessor()` 默认仍输出到 "prompt"
- `LLMProcessor()` 默认仍从 "prompt" 读取，输出到 "llm_response"
- 现有测试和代码无需修改即可工作

## 好处

1. **灵活的数据流**: 处理器可以自定义输入/输出键名
2. **可组合性**: 更容易构建复杂的数据处理链
3. **调试友好**: 可以在 Context 中保留中间处理结果
4. **类型安全**: 通过键名明确数据流向
5. **测试便利**: 可以轻松模拟不同的数据流场景

## 使用案例

### 1. 多语言处理链
```python
pipeline = SequentialPipeline()
pipeline.add_processors([
    PromptProcessor("Hello", output_key="english_text"),
    TranslateProcessor(input_key="english_text", output_key="chinese_text"),
    LLMProcessor(input_key="chinese_text", output_key="ai_response")
])
```

### 2. 数据预处理链
```python
pipeline = SequentialPipeline()
pipeline.add_processors([
    DataTransformProcessor(input_key="raw_data", output_key="cleaned_data", transform_func=clean_data),
    DataTransformProcessor(input_key="cleaned_data", output_key="normalized_data", transform_func=normalize),
    AnalysisProcessor(input_key="normalized_data", output_key="results")
])
```

### 3. 调试和日志
```python
pipeline = SequentialPipeline()
pipeline.add_processors([
    BusinessProcessor(input_key="input", output_key="intermediate"),
    NoOpProcessor(input_key="intermediate", output_key="debug_copy", passthrough=True),  # 保留调试数据
    FinalProcessor(input_key="intermediate", output_key="final")
])
```

## 测试结果

- ✅ 所有 79 个现有测试通过
- ✅ 新功能测试通过
- ✅ 向后兼容性保持
- ✅ 数据流验证成功
