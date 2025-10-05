# Qwen3-ASR 语音识别集成说明

## 📖 概述

本项目已集成阿里云百炼平台的 **Qwen3-ASR** 语音识别模型，提供更高精度的语音识别能力。

Qwen3-ASR 是阿里云最新推出的语音识别模型，具有以下特点：
- ✅ 高精度识别
- ✅ 多语种支持（中文、英文等）
- ✅ 自动语种检测
- ✅ 支持流式和非流式输出
- ✅ 逆文本归一化（ITN）支持

## 🚀 快速开始

### 1. 安装依赖

首先需要安装 DashScope SDK：

```bash
pip install dashscope
```

### 2. 获取 API Key

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 登录并进入控制台
3. 在 API-KEY 管理页面创建新的 API Key
4. 复制生成的 API Key

### 3. 配置文件设置

编辑 `voice/ali/config.json` 文件（如果不存在，从 `config.json.template` 复制）：

```json
{
    "use_qwen3_asr": true,
    "qwen3_model": "qwen3-asr-flash",
    "qwen3_language": null,
    "qwen3_enable_lid": true,
    "qwen3_enable_itn": false,
    "qwen3_stream": false,
    "dashscope_api_key": "YOUR_DASHSCOPE_API_KEY",
    
    "api_url_text_to_voice": "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/tts",
    "api_url_voice_to_text": "https://nls-gateway.cn-shanghai.aliyuncs.com/stream/v1/asr",
    "app_key": "",
    "access_key_id": "",
    "access_key_secret": ""
}
```

或者在主配置文件 `config.json` 中添加：

```json
{
    "dashscope_api_key": "YOUR_DASHSCOPE_API_KEY"
}
```

### 4. 启用 Qwen3-ASR

在 `voice/ali/config.json` 中设置：

```json
{
    "use_qwen3_asr": true
}
```

## ⚙️ 配置参数说明

### 核心配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `use_qwen3_asr` | boolean | `false` | 是否启用 Qwen3-ASR（false 则使用传统 ASR） |
| `dashscope_api_key` | string | `""` | DashScope API Key |

### Qwen3-ASR 高级配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `qwen3_model` | string | `"qwen3-asr-flash"` | 使用的模型名称 |
| `qwen3_language` | string/null | `null` | 指定音频语种（null 表示自动检测） |
| `qwen3_enable_lid` | boolean | `true` | 是否启用语种识别 |
| `qwen3_enable_itn` | boolean | `false` | 是否启用逆文本归一化 |
| `qwen3_stream` | boolean | `false` | 是否使用流式输出 |

### 模型选择

目前支持的模型：
- `qwen3-asr-flash`: 快速模型，适合实时场景
- 其他模型请参考阿里云百炼平台文档

### 语种设置

`qwen3_language` 参数可选值：
- `null`: 自动检测语种（推荐）
- `"zh"`: 中文
- `"en"`: 英文
- 其他语种代码请参考官方文档

### 逆文本归一化（ITN）

`qwen3_enable_itn` 设置为 `true` 时，会将识别结果中的数字、日期等转换为规范格式。

例如：
- 关闭 ITN: "二零二五年一月十五日"
- 开启 ITN: "2025年1月15日"

### 流式输出

`qwen3_stream` 设置为 `true` 时，使用流式输出模式，可以更快地获得部分识别结果。

## 📝 使用示例

### 示例 1: 基础配置（自动语种检测）

```json
{
    "use_qwen3_asr": true,
    "qwen3_model": "qwen3-asr-flash",
    "qwen3_language": null,
    "qwen3_enable_lid": true,
    "qwen3_enable_itn": false,
    "qwen3_stream": false,
    "dashscope_api_key": "sk-xxxxxxxxxxxxx"
}
```

### 示例 2: 中文专用配置

```json
{
    "use_qwen3_asr": true,
    "qwen3_model": "qwen3-asr-flash",
    "qwen3_language": "zh",
    "qwen3_enable_lid": false,
    "qwen3_enable_itn": true,
    "qwen3_stream": false,
    "dashscope_api_key": "sk-xxxxxxxxxxxxx"
}
```

### 示例 3: 流式输出配置

```json
{
    "use_qwen3_asr": true,
    "qwen3_model": "qwen3-asr-flash",
    "qwen3_language": null,
    "qwen3_enable_lid": true,
    "qwen3_enable_itn": false,
    "qwen3_stream": true,
    "dashscope_api_key": "sk-xxxxxxxxxxxxx"
}
```

## 🔄 切换回传统 ASR

如果需要切换回传统的阿里云 ASR 服务，只需将 `use_qwen3_asr` 设置为 `false`：

```json
{
    "use_qwen3_asr": false
}
```

此时需要配置传统 ASR 的参数：
- `api_url_voice_to_text`
- `app_key`
- `access_key_id`
- `access_key_secret`

## 🐛 故障排查

### 问题 1: 提示 "dashscope module not installed"

**解决方案：**
```bash
pip install dashscope
```

### 问题 2: API Key 未找到

**错误信息：**
```
[Qwen3-ASR] API Key not found
```

**解决方案：**
1. 检查 `voice/ali/config.json` 中的 `dashscope_api_key` 是否正确填写
2. 或在主配置文件 `config.json` 中添加 `dashscope_api_key`
3. 或设置环境变量 `DASHSCOPE_API_KEY`

### 问题 3: 文件路径错误

**错误信息：**
```
[Qwen3-ASR] Failed to parse response
```

**解决方案：**
确保语音文件路径正确，系统会自动处理文件路径格式。

### 问题 4: 识别失败

**排查步骤：**
1. 检查 API Key 是否有效
2. 检查网络连接
3. 查看日志中的详细错误信息
4. 确认音频文件格式是否支持（支持 wav, mp3, m4a 等常见格式）

## 📊 性能对比

| 特性 | 传统 ASR | Qwen3-ASR |
|------|----------|-----------|
| 识别精度 | 较高 | 更高 |
| 多语种支持 | 有限 | 丰富 |
| 自动语种检测 | ❌ | ✅ |
| 流式输出 | ❌ | ✅ |
| ITN 支持 | ❌ | ✅ |
| 配置复杂度 | 较高 | 较低 |

## 🔗 相关链接

- [阿里云百炼平台](https://bailian.console.aliyun.com/)
- [DashScope SDK 文档](https://help.aliyun.com/zh/model-studio/developer-reference/sdk-overview)
- [Qwen3-ASR 官方文档](https://help.aliyun.com/zh/model-studio/developer-reference/qwen3-asr)

## 💡 最佳实践

1. **生产环境建议：**
   - 使用 `qwen3_enable_lid: true` 自动检测语种
   - 根据需求决定是否开启 ITN
   - 非实时场景可以关闭流式输出以获得更稳定的结果

2. **性能优化：**
   - 对于实时场景，可以开启 `qwen3_stream: true`
   - 如果明确知道语种，设置 `qwen3_language` 可以提高识别速度

3. **安全建议：**
   - 不要将 API Key 提交到版本控制系统
   - 使用环境变量或配置文件管理 API Key
   - 定期轮换 API Key

## 📞 技术支持

如有问题，请：
1. 查看日志文件获取详细错误信息
2. 参考本文档的故障排查部分
3. 提交 Issue 到项目仓库

