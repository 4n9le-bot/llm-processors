# PromptProcessor Jinja2模板功能使用指南

PromptProcessor现在支持Jinja2模板功能，可以通过`input_key`从Context中动态获取模板变量。

## 主要功能

### 1. 基本模板支持

```python
from core.processors import PromptProcessor
from core.context import Context

# 简单模板
template = "你好，{{name}}！欢迎使用{{service}}。"
processor = PromptProcessor(
    prompt=template,
    template_vars={"name": "张三", "service": "AI助手"}
)

context = Context()
result = await processor.process(context)
# 输出: "你好，张三！欢迎使用AI助手。"
```

### 2. 通过input_key获取模板变量

```python
# 从Context中动态获取模板变量
template = "用户{{user_name}}询问关于{{topic}}的问题。"
processor = PromptProcessor(
    prompt=template,
    input_key="template_data"  # 从context中的此键获取变量
)

context = Context({
    "template_data": {
        "user_name": "李四",
        "topic": "机器学习"
    }
})

result = await processor.process(context)
# 输出: "用户李四询问关于机器学习的问题。"
```

### 3. 混合使用静态和动态变量

```python
template = "{{greeting}}，{{user_name}}！时间：{{time}}"
processor = PromptProcessor(
    prompt=template,
    input_key="dynamic_vars",
    template_vars={"greeting": "你好", "time": "下午2点"}  # 静态变量
)

context = Context({
    "dynamic_vars": {
        "user_name": "王五"
    }
})

result = await processor.process(context)
# 输出: "你好，王五！时间：下午2点"
```

### 4. 变量优先级

变量的优先级从高到低为：
1. `template_vars`（静态变量）
2. `input_key`指向的字典变量
3. Context中的直接变量

```python
template = "消息：{{message}}"
processor = PromptProcessor(
    prompt=template,
    input_key="vars_from_input",
    template_vars={"message": "来自静态变量"}  # 最高优先级
)

context = Context({
    "message": "来自Context直接变量",  # 最低优先级
    "vars_from_input": {
        "message": "来自input_key"  # 中等优先级
    }
})

# 结果将使用静态变量的值
```

### 5. 复杂模板（循环和条件）

```python
template = '''
{% for task in tasks %}
{{loop.index}}. {{task.name}}: {{task.status}}
{% if task.get('description') %}
   描述: {{task.description}}
{% endif %}
{% endfor %}

{% if summary %}
总计: {{tasks|length}} 个任务
{% endif %}
'''

processor = PromptProcessor(
    prompt=template,
    input_key="report_data"
)

context = Context({
    "report_data": {
        "tasks": [
            {"name": "任务A", "status": "完成", "description": "第一个任务"},
            {"name": "任务B", "status": "进行中"},
        ],
        "summary": True
    }
})
```

### 6. 验证和错误处理

```python
# 严格模式（默认）
processor = PromptProcessor(
    prompt="处理{{undefined_var}}",
    strict_mode=True
)

# 验证输入
is_valid = processor.validate_input(context)

# 非严格模式
processor_lenient = PromptProcessor(
    prompt="处理{{undefined_var}}",
    strict_mode=False
)
```

### 7. 预览功能

```python
processor = PromptProcessor(
    prompt="报告：{{title}}\\n内容：{{content}}",
    template_vars={"title": "默认标题"}
)

# 预览模板渲染结果
preview = processor.preview_render(
    input_key_data={"content": "测试内容"}
)
```

## 构造函数参数

- `prompt`: 提示词模板字符串
- `output_key`: 存储渲染结果的Context键名（默认: "prompt"）
- `input_key`: 从Context获取模板变量的键名（可选）
- `template_vars`: 静态模板变量字典（可选）
- `strict_mode`: 严格模式，缺少变量时报错（默认: True）
- `name`: 处理器名称（可选）

## 实用方法

- `validate_input(context)`: 验证Context是否包含所需变量
- `get_required_variables()`: 获取模板需要的变量名集合
- `add_template_var(key, value)`: 动态添加模板变量
- `remove_template_var(key)`: 移除模板变量
- `preview_render(context_data, input_key_data)`: 预览模板渲染结果

## 最佳实践

1. **使用input_key获取动态数据**：将经常变化的数据通过input_key从Context获取
2. **静态变量用于配置**：将不常变化的配置信息设置为template_vars
3. **启用严格模式**：在开发阶段使用strict_mode=True来捕获模板错误
4. **验证输入**：在处理前调用validate_input()确保数据完整性
5. **使用预览功能**：在生产环境前使用preview_render()测试模板
