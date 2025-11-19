# 使用示例

## 基础使用

### 1. 文本对话（基础模式）

```bash
# 启动程序
python -m src.main --text-mode

# 开始对话
你: 你好
AI: 你好！我是一个友好、专业的AI助手。有什么我可以帮助你的吗？

你: 用Python写一个快速排序
AI: 好的，这是一个Python快速排序的实现...

你: /quit
再见！
```

### 2. 指定模型运行

```bash
# 使用 DeepSeek
python -m src.main --model deepseek --text-mode

# 使用 OpenAI
python -m src.main --model openai --text-mode

# 使用本地 Ollama
python -m src.main --model ollama --text-mode
```

### 3. 使用自定义配置

```bash
# 指定配置文件
python -m src.main --config my_config.yaml --text-mode

# 使用环境变量
set DEEPSEEK_API_KEY=sk-xxxxx
python -m src.main --text-mode
```

## 高级功能

### 1. 运行中切换模型

```
你: 你好
AI: (使用 DeepSeek 回复)

你: /model
可用模型:
  [✓] 1. deepseek
  [ ] 2. openai
  [ ] 3. zhipu

选择模型: 2
已切换到模型: openai

你: 继续对话
AI: (使用 OpenAI 回复)
```

### 2. 管理对话历史

```bash
你: 今天天气怎么样？
AI: 抱歉，我无法获取实时天气信息...

你: /clear
对话历史已清空

你: 你好
AI: 你好！... (新的对话，不记得之前的内容)
```

### 3. 自定义系统提示词

编辑 `config/default_config.yaml`:

```yaml
conversation:
  system_prompt: "你是一个专业的Python编程助手，擅长解答编程问题。"
```

或者在代码中动态修改:

```python
from src.core import ConversationManager

conv = ConversationManager()
conv.update_system_prompt("你是一个幽默风趣的AI助手。")
```

## 配置示例

### 1. 多模型配置

**场景**: 主要使用 DeepSeek，OpenAI 作为备用

`config/default_config.yaml`:
```yaml
models:
  active: "deepseek"
  
  deepseek:
    api_key: "${DEEPSEEK_API_KEY}"
    model: "deepseek-chat"
    temperature: 0.7
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4o-mini"
    temperature: 0.7
```

`.env`:
```env
DEEPSEEK_API_KEY=sk-your-deepseek-key
OPENAI_API_KEY=sk-your-openai-key
```

### 2. 本地模型配置（Ollama）

**前提**: 已安装并运行 Ollama

```bash
# 1. 安装 Ollama (https://ollama.ai/)
# 2. 拉取模型
ollama pull llama3:8b

# 3. 启动 Ollama 服务（默认端口 11434）
ollama serve
```

`config/default_config.yaml`:
```yaml
models:
  active: "ollama"
  
  ollama:
    base_url: "http://localhost:11434"
    model: "llama3:8b"
    temperature: 0.7
```

运行:
```bash
python -m src.main --text-mode
```

### 3. 调整模型参数

**高创造性模式** (适合创意写作):
```yaml
deepseek:
  temperature: 1.2  # 更高的随机性
  max_tokens: 3000  # 更长的回复
```

**低创造性模式** (适合代码/数学):
```yaml
deepseek:
  temperature: 0.3  # 更确定的输出
  max_tokens: 1500
```

## 编程接口示例

### 1. 作为库使用

```python
from src.core import ConfigManager, ConversationManager
from src.llm import LLMManager

# 初始化
config = ConfigManager()
conversation = ConversationManager(
    system_prompt="你是编程助手"
)

# 创建LLM
llm_manager = LLMManager(config.get('models'))
llm_manager.switch_model('deepseek')
llm = llm_manager.get_current_llm()

# 对话
conversation.add_user_message("解释Python装饰器")
messages = conversation.get_messages()

# 生成回复
response = ""
for token in llm.generate(messages):
    print(token, end="")
    response += token

conversation.add_assistant_message(response)
```

### 2. 批量处理

```python
questions = [
    "什么是机器学习？",
    "解释深度学习",
    "什么是神经网络？"
]

for q in questions:
    conversation.add_user_message(q)
    messages = conversation.get_messages()
    
    response = ""
    for token in llm.generate(messages):
        response += token
    
    conversation.add_assistant_message(response)
    print(f"Q: {q}")
    print(f"A: {response}\n")
```

### 3. 自定义LLM实现

```python
# 创建自定义LLM类
from src.llm import BaseLLM

class CustomLLM(BaseLLM):
    def generate(self, messages, stream=True):
        # 你的实现
        yield "自定义响应"
    
    def check_connection(self):
        return True

# 使用
custom_llm = CustomLLM(api_key="", model="custom")
```

## 常见场景

### 场景1: 代码助手

```yaml
conversation:
  system_prompt: |
    你是一个专业的编程助手。
    - 提供清晰的代码示例
    - 解释最佳实践
    - 指出潜在问题
```

### 场景2: 学习伙伴

```yaml
conversation:
  system_prompt: |
    你是一个耐心的老师。
    - 用简单的语言解释复杂概念
    - 多用类比和例子
    - 鼓励提问
```

### 场景3: 创意写作

```yaml
models:
  deepseek:
    temperature: 1.0  # 更有创意
    
conversation:
  system_prompt: |
    你是一个创意写作助手。
    - 提供富有想象力的内容
    - 使用生动的描述
    - 保持故事连贯性
```

## 故障排除示例

### 问题: 响应太慢

**解决方案1**: 使用更小的模型
```yaml
models:
  active: "deepseek"  # 而不是 gpt-4
```

**解决方案2**: 减少max_tokens
```yaml
models:
  deepseek:
    max_tokens: 1000  # 而不是 4000
```

### 问题: API配额超限

**解决方案**: 切换到备用模型
```
你: /model
选择模型: ollama  # 本地模型，无配额限制
```

### 问题: 回复质量不佳

**解决方案**: 优化系统提示词
```yaml
conversation:
  system_prompt: |
    你是XXX领域的专家。
    请提供详细、准确的回答。
    包含具体例子和实践建议。
```

## 性能优化

### 1. 减少延迟

```yaml
# 使用流式输出
models:
  deepseek:
    stream: true  # 立即显示第一个token

# 减小上下文
conversation:
  max_history: 5  # 只保留最近5轮对话
```

### 2. 降低成本

```yaml
# 使用更便宜的模型
models:
  active: "deepseek"  # 相比OpenAI更便宜

# 限制输出长度
models:
  deepseek:
    max_tokens: 1000
```

## 下一步

- 查看 `README.md` 了解完整功能
- 查看 `PROJECT_SUMMARY.md` 了解项目状态
- 修改配置文件自定义你的AI助手
- 等待语音功能完善，体验完整的语音对话
