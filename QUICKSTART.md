# 快速开始指南

## 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

## 步骤 2: 配置API密钥

### 方式一：使用 .env 文件（推荐）

1. 复制环境变量模板：
```bash
copy .env.example .env
```

2. 编辑 `.env` 文件，填入你的API密钥：
```env
DEEPSEEK_API_KEY=sk-your-key-here
```

### 方式二：直接编辑配置文件

编辑 `config/default_config.yaml`，找到对应模型的 `api_key` 字段并填入。

## 步骤 3: 运行程序

### Windows用户

双击运行 `run.bat`

### 或使用命令行

```bash
python -m src.main --text-mode
```

## 步骤 4: 开始对话

程序启动后，直接输入文本即可与AI对话：

```
你: 你好
AI: 你好！我是一个友好、专业的AI助手...
```

## 常用命令

- `/quit` - 退出程序
- `/clear` - 清空对话历史
- `/model` - 切换模型
- `/help` - 显示帮助

## 支持的模型

确保你至少配置了一个模型的API密钥：

### 免费/便宜的选项

- **DeepSeek** (推荐新手) - 价格低廉，性能不错
  - 官网: https://platform.deepseek.com/
  - 模型: deepseek-chat

- **Ollama** (本地运行，完全免费)
  - 需先安装: https://ollama.ai/
  - 运行: `ollama pull llama3:8b`

### 商业选项

- **OpenAI** - GPT-4, GPT-3.5
  - 官网: https://platform.openai.com/

- **智谱AI** - GLM-4
  - 官网: https://open.bigmodel.cn/

## 故障排除

### 问题1: "未找到模块"错误

```bash
# 确保在项目根目录
cd rt-voicechat-cli

# 重新安装依赖
pip install -r requirements.txt
```

### 问题2: "API Key错误"

检查：
1. `.env` 文件是否存在并包含正确的API密钥
2. `config/default_config.yaml` 中的 `active` 字段是否指向正确的模型
3. API密钥是否有效（可在对应平台查看）

### 问题3: 网络连接错误

- 检查网络连接
- 如果使用代理，配置环境变量:
  ```bash
  set HTTP_PROXY=http://your-proxy:port
  set HTTPS_PROXY=http://your-proxy:port
  ```

## 下一步

- 尝试切换不同的模型（使用 `/model` 命令）
- 修改 `config/default_config.yaml` 中的系统提示词，定制AI性格
- 调整 `temperature` 参数来改变AI回复的创造性

## 获取帮助

查看完整文档: `README.md`
