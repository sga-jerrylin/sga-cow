# Qwen3-ASR 使用示例

## 🎯 快速配置指南

### 步骤 1: 安装依赖

```bash
# 安装可选依赖（包含 dashscope）
pip install -r requirements-optional.txt

# 或单独安装 dashscope
pip install dashscope
```

### 步骤 2: 获取 API Key

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 登录后进入 **API-KEY 管理**
3. 点击 **创建新的 API Key**
4. 复制生成的 API Key（格式类似：`sk-xxxxxxxxxxxxxxxx`）

### 步骤 3: 配置文件

#### 方式 1: 使用 voice/ali/config.json（推荐）

复制模板文件：
```bash
cp voice/ali/config.json.template voice/ali/config.json
```

编辑 `voice/ali/config.json`：
```json
{
    "use_qwen3_asr": true,
    "dashscope_api_key": "sk-xxxxxxxxxxxxxxxx",
    
    "qwen3_model": "qwen3-asr-flash",
    "qwen3_language": null,
    "qwen3_enable_lid": true,
    "qwen3_enable_itn": false,
    "qwen3_stream": false,
    
    "api_url_text_to_voice": "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts",
    "api_url_voice_to_text": "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr",
    "app_key": "",
    "access_key_id": "",
    "access_key_secret": ""
}
```

#### 方式 2: 使用主配置文件 config.json

在项目根目录的 `config.json` 中添加：
```json
{
    "voice_to_text": "ali",
    "dashscope_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

然后在 `voice/ali/config.json` 中设置：
```json
{
    "use_qwen3_asr": true
}
```

### 步骤 4: 启用语音识别

在主配置文件 `config.json` 中启用语音识别：

```json
{
    "channel_type": "wechatcom_app",
    "voice_to_text": "ali",
    "speech_recognition": true,
    "group_speech_recognition": true,
    "dashscope_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

### 步骤 5: 启动项目

```bash
python app.py
```

## 📱 使用场景示例

### 场景 1: 企业微信语音消息识别

**配置：**
```json
{
    "channel_type": "wechatcom_app",
    "voice_to_text": "ali",
    "speech_recognition": true,
    "group_speech_recognition": true
}
```

**使用：**
1. 在企业微信中发送语音消息
2. 系统自动识别语音内容
3. AI 根据识别的文字进行回复

### 场景 2: 中文专用高精度识别

**配置 voice/ali/config.json：**
```json
{
    "use_qwen3_asr": true,
    "qwen3_language": "zh",
    "qwen3_enable_lid": false,
    "qwen3_enable_itn": true
}
```

**特点：**
- 指定中文识别，速度更快
- 启用 ITN，数字自动转换为阿拉伯数字
- 例如："二零二五年" → "2025年"

### 场景 3: 多语种自动检测

**配置 voice/ali/config.json：**
```json
{
    "use_qwen3_asr": true,
    "qwen3_language": null,
    "qwen3_enable_lid": true,
    "qwen3_enable_itn": false
}
```

**特点：**
- 自动检测语音语种
- 支持中文、英文等多种语言
- 适合国际化场景

### 场景 4: 实时流式识别

**配置 voice/ali/config.json：**
```json
{
    "use_qwen3_asr": true,
    "qwen3_stream": true
}
```

**特点：**
- 流式输出识别结果
- 更快的响应速度
- 适合实时对话场景

## 🔧 高级配置

### 配置项详解

```json
{
    // 核心开关
    "use_qwen3_asr": true,              // 启用 Qwen3-ASR
    "dashscope_api_key": "sk-xxx",      // API Key
    
    // 模型配置
    "qwen3_model": "qwen3-asr-flash",   // 模型名称
    
    // 语种配置
    "qwen3_language": null,             // null=自动检测, "zh"=中文, "en"=英文
    "qwen3_enable_lid": true,           // 启用语种识别
    
    // 文本处理
    "qwen3_enable_itn": false,          // 启用逆文本归一化
    
    // 输出模式
    "qwen3_stream": false               // 启用流式输出
}
```

### ITN（逆文本归一化）效果对比

| 原始识别 | ITN 关闭 | ITN 开启 |
|---------|---------|---------|
| 数字 | "一千二百三十四" | "1234" |
| 日期 | "二零二五年一月十五日" | "2025年1月15日" |
| 时间 | "下午三点半" | "15:30" |
| 金额 | "五百块钱" | "500元" |

### 性能优化建议

**1. 明确语种场景**
```json
{
    "qwen3_language": "zh",      // 明确指定中文
    "qwen3_enable_lid": false    // 关闭语种检测，提升速度
}
```

**2. 实时场景优化**
```json
{
    "qwen3_stream": true,        // 启用流式输出
    "qwen3_enable_itn": false    // 关闭 ITN，减少处理时间
}
```

**3. 高精度场景**
```json
{
    "qwen3_stream": false,       // 关闭流式，获得完整结果
    "qwen3_enable_itn": true,    // 启用 ITN，规范化输出
    "qwen3_enable_lid": true     // 启用语种检测
}
```

## 🧪 测试验证

### 运行测试脚本

```bash
cd voice/ali
python test_qwen3_asr.py
```

### 测试输出示例

```
============================================================
Qwen3-ASR 语音识别测试
============================================================

============================================================
环境检查
============================================================
✅ dashscope 模块已安装
   版本: 1.14.0
✅ API Key 已配置
   Key: sk-xxxxxxx...xxxxx

============================================================
测试 1: 在线音频文件识别
============================================================
音频 URL: https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3
开始识别...
✅ 识别成功!
识别结果: 欢迎使用阿里云语音服务

============================================================
测试总结
============================================================
总测试数: 1
通过测试: 1
失败测试: 0
通过率: 100.0%

🎉 所有测试通过!
```

## 🔍 日志查看

### 启用详细日志

在 `config.json` 中设置：
```json
{
    "debug": true
}
```

### 日志示例

```
[INFO] [AliVoice] Initialized with use_qwen3_asr=True
[INFO] [Ali] Using Qwen3-ASR model for speech recognition
[DEBUG] [Qwen3-ASR] Processing file: file:///path/to/audio.wav
[DEBUG] [Qwen3-ASR] Using non-streaming mode
[INFO] [Qwen3-ASR] Recognition result: 你好，这是一条测试语音
[INFO] [Ali] VoicetoText = 你好，这是一条测试语音
```

## ❓ 常见问题

### Q1: 如何切换回传统 ASR？

**A:** 在 `voice/ali/config.json` 中设置：
```json
{
    "use_qwen3_asr": false
}
```

### Q2: 支持哪些音频格式？

**A:** 支持常见格式：
- WAV
- MP3
- M4A
- AMR
- 其他 ffmpeg 支持的格式

### Q3: 识别速度慢怎么办？

**A:** 尝试以下优化：
1. 指定语种：`"qwen3_language": "zh"`
2. 关闭语种检测：`"qwen3_enable_lid": false`
3. 启用流式输出：`"qwen3_stream": true`

### Q4: API Key 在哪里配置？

**A:** 三种方式（优先级从高到低）：
1. `voice/ali/config.json` 中的 `dashscope_api_key`
2. 主配置 `config.json` 中的 `dashscope_api_key`
3. 环境变量 `DASHSCOPE_API_KEY`

## 📞 获取帮助

- 查看详细文档：[QWEN3_ASR_README.md](./QWEN3_ASR_README.md)
- 提交 Issue：项目 GitHub 仓库
- 阿里云官方文档：[Qwen3-ASR 文档](https://help.aliyun.com/zh/model-studio/developer-reference/qwen3-asr)

