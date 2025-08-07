# Error Handler 移除重构总结

## 完成的重构工作

### 1. 移除集中式错误处理器
- 从 `SequentialPipeline` 和 `ParallelPipeline` 中移除了 `_error_handlers` 属性
- 移除了 `add_error_handler` 方法
- 从执行逻辑中移除了错误处理器调用
- 每个 processor 现在负责自己的异常处理

### 2. 类型安全改进
- 将 `processors` 参数类型从 `Optional[List[Processor]]` 改为 `Optional[Sequence[Processor]]`
- 将 `add_processors` 方法参数类型从 `List[Processor]` 改为 `Sequence[Processor]`
- 解决了类型检查中的协变性问题

### 3. 设计理念变更
**之前**: 集中式错误处理
- Pipeline 负责处理所有 processor 的错误
- 通过 `add_error_handler` 为特定 processor 注册错误处理函数
- 错误处理逻辑与 pipeline 执行逻辑耦合

**现在**: 分散式错误处理
- 每个 processor 负责自己的异常处理
- 遵循单一职责原则
- Pipeline 只负责编排和流程控制
- 更清晰的职责分离

### 4. 关于 processors 参数的设计决策

**问题**: `SequentialPipeline.__init__` 中 `processors` 参数可以为 `None` 有意义吗？

**答案**: 是的，非常有意义，原因包括：

1. **建造者模式支持**: 
   ```python
   pipeline = SequentialPipeline()
   pipeline.add_processor(processor1)
   pipeline.add_processor(processor2)
   ```

2. **动态配置**: 
   ```python
   pipeline = SequentialPipeline()
   if condition:
       pipeline.add_processor(conditional_processor)
   ```

3. **测试友好**: 测试中可以创建空 pipeline 然后添加 mock processors

4. **配置分离**: Pipeline 创建和配置可以分开进行

## 修改的文件

### 核心文件
- `core/pipeline.py` - 移除错误处理器，改进类型声明

### 测试文件
- `tests/test_pipeline.py` - 移除错误处理器相关测试
- `tests/test_integration.py` - 移除错误处理器集成测试

## 测试结果
- 所有 79 个测试都通过 ✅
- 类型检查错误已解决
- 代码结构更清晰，职责更明确

## 好处

1. **简化设计**: 移除了复杂的错误处理器机制
2. **更好的封装**: 每个 processor 管理自己的错误
3. **类型安全**: 使用 `Sequence` 支持协变性
4. **易于理解**: 更直观的错误处理流程
5. **遵循 SOLID 原则**: 单一职责和开闭原则

## 使用示例

```python
# 创建空 pipeline 然后添加 processors
pipeline = SequentialPipeline()
pipeline.add_processor(MyProcessor())

# 或者在初始化时传入 processors
processors = [Processor1(), Processor2()]
pipeline = SequentialPipeline(processors=processors)

# Processors 现在需要自己处理异常
class MyProcessor(Processor):
    async def process(self, context):
        try:
            # 处理逻辑
            result = do_something()
            return ProcessingResult(
                status=ProcessingStatus.COMPLETED,
                data=result
            )
        except Exception as e:
            # 自己处理异常
            return ProcessingResult(
                status=ProcessingStatus.FAILED,
                error=e
            )
```
