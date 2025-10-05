# Qwen3-ASR 快速配置

## 🚀 两步启用

### 1. 安装依赖
```bash
pip install dashscope
```

### 2. 修改 config.json（项目根目录）

```json
{
  "voice_to_text": "ali",
  "speech_recognition": true,
  "use_qwen3_asr": true,
  "dashscope_api_key": "sk-你的API密钥"
}
```

## 🔑 获取 API Key

访问：https://bailian.console.aliyun.com/ → API-KEY 管理 → 创建

## 📋 配置参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `use_qwen3_asr` | ✅ | `false` | 启用 Qwen3-ASR |
| `dashscope_api_key` | ✅ | - | API Key |
| `qwen3_language` | ❌ | `null` | 语种（`null`=自动，`"zh"`=中文） |
| `qwen3_enable_itn` | ❌ | `false` | 数字转换（"一千"→"1000"） |

## ✨ 完整示例

```json
{
  "channel_type": "wechatcom_app",
  "model": "dify",
  "voice_to_text": "ali",
  "speech_recognition": true,
  "group_speech_recognition": true,
  "use_qwen3_asr": true,
  "dashscope_api_key": "sk-xxxxxxxxxxxxxxxx"
}
```

**就这么简单！所有配置都在主 config.json 中完成！**

