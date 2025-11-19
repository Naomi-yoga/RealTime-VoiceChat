# RT-VoiceChat-CLI

实时语音聊天命令行工具，支持多家大模型API调用，具备强实时响应能力和语音包切换功能。

## 📋 功能特性

- ✅ **多模型支持**：支持 DeepSeek、OpenAI、智谱AI、Kimi、Ollama 等多家大模型
- ✅ **实时对话**：低延迟文本/语音交互体验
- ✅ **语音识别**：支持 Whisper、Azure Speech 等ASR引擎
- ✅ **语音合成**：支持 Edge TTS、Azure TTS、OpenAI TTS 等引擎
- ✅ **语音包切换**：可自由切换不同音色的语音包
- ✅ **对话管理**：自动保存对话历史，支持上下文记忆
- ✅ **灵活配置**：YAML配置文件 + 环境变量
- ✅ **命令行友好**：丰富的交互命令和状态显示

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆或下载项目
cd rt-voicechat-cli

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

方式一：使用环境变量（推荐）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# 例如:
# DEEPSEEK_API_KEY=sk-xxxxx
# OPENAI_API_KEY=sk-xxxxx
```

方式二：直接编辑配置文件

编辑 `config/default_config.yaml`，在对应模型的 `api_key` 字段填入密钥。

### 3. 运行程序

```bash
# 文本模式（测试）
python -m src.main --text-mode

# 指定配置文件
python -m src.main --config config/default_config.yaml --text-mode

# 指定使用的模型
python -m src.main --model deepseek --text-mode
```

## 📝 使用说明

### 文本模式命令

在文本模式下，可以使用以下命令：

- `/quit` 或 `/exit` - 退出程序
- `/clear` - 清空对话历史
- `/model` - 切换模型
- `/help` - 显示帮助信息

### 命令行参数

```bash
python -m src.main [OPTIONS]

Options:
  -c, --config PATH    配置文件路径
  -m, --model TEXT     使用的模型名称
  -v, --voice TEXT     语音包名称
  -t, --text-mode      文本模式（测试）
  --help               显示帮助信息
```

## ⚙️ 配置说明

### 模型配置

在 `config/default_config.yaml` 中配置：

```yaml
models:
  active: "deepseek"  # 默认使用的模型
  
  deepseek:
    api_key: ""  # API密钥
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
    temperature: 0.7
    max_tokens: 2000
```

### 语音识别配置

```yaml
asr:
  engine: "whisper"  # whisper, azure, baidu
  
  whisper:
    model: "base"  # tiny, base, small, medium, large
    language: "zh"  # zh, en, auto
    device: "cpu"   # cpu, cuda
```

### 语音合成配置

```yaml
tts:
  engine: "edge"  # edge, azure, openai
  active_voice: "female_gentle"
  
  voice_packs:
    female_gentle:
      engine: "edge"
      voice: "zh-CN-XiaoxiaoNeural"
      style: "gentle"
```

## 📦 项目结构

```
rt-voicechat-cli/
├── config/                 # 配置文件
│   └── default_config.yaml
├── src/                    # 源代码
│   ├── audio/             # 音频处理
│   ├── asr/               # 语音识别
│   ├── llm/               # 大模型
│   ├── tts/               # 语音合成
│   ├── core/              # 核心模块
│   ├── utils/             # 工具函数
│   └── main.py            # 主程序
├── requirements.txt        # 依赖列表
├── .env.example           # 环境变量示例
└── README.md              # 项目文档
```

## 🔧 开发计划

- [x] 基础架构搭建
- [x] 配置管理
- [x] LLM多模型支持
- [x] 对话管理
- [x] 文本模式
- [ ] 语音识别集成
- [ ] 语音合成集成
- [ ] 实时语音模式
- [ ] VAD优化
- [ ] 打包为exe

## 🤝 支持的模型

### LLM模型

- **DeepSeek** - deepseek-chat
- **OpenAI** - gpt-4, gpt-4o, gpt-3.5-turbo
- **智谱AI** - glm-4, glm-3-turbo
- **月之暗面** - moonshot-v1-8k
- **Ollama** - 本地模型

### ASR引擎

- **Whisper** (本地) - 开源，支持多语言
- **Azure Speech** - 微软云端服务
- **百度语音** - 国内服务

### TTS引擎

- **Edge TTS** - 免费，音质好
- **Azure TTS** - 微软云端服务
- **OpenAI TTS** - OpenAI语音合成

## 📄 许可证

MIT License

## 🙏 致谢

- OpenAI Whisper
- Edge TTS
- FastAPI
- Rich (终端UI)

---

**注意**: 当前版本为开发预览版，语音功能正在完善中。
