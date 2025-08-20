# 配置文件设置指南

## 🔧 配置文件创建

1. **复制模板文件**：
   ```bash
   cp config.json.template config.json
   ```

2. **填写您的配置信息**：
   编辑 `config.json` 文件，将所有 `YOUR_*` 占位符替换为实际值。

## 🔑 必需的配置项

### 企业微信配置
- `wechatcom_corp_id`: 企业微信的企业ID
- `wechatcomapp_secret`: 应用的Secret
- `wechatcomapp_agent_id`: 应用的AgentID
- `wechatcomapp_token`: 应用的Token
- `wechatcomapp_aes_key`: 应用的EncodingAESKey

### Dify配置
- `dify_api_base`: Dify API基础URL
- `dify_api_key`: Dify应用的API密钥
- `dify_app_type`: 应用类型 (`agent` 或 `chatbot`)

### Azure语音服务（可选）
- `azure_voice_api_key`: Azure语音服务API密钥
- `azure_voice_region`: Azure服务区域

### LinkAI配置（可选）
- `linkai_api_key`: LinkAI API密钥

## ⚠️ 安全提醒

- **绝不要**将包含真实API密钥的 `config.json` 文件提交到版本控制系统
- `config.json` 已被添加到 `.gitignore` 中，确保不会被意外提交
- 定期轮换您的API密钥以提高安全性

## 🚀 推荐配置

### 超时设置
```json
{
  "dify_timeout": 300,        // 5分钟，给AI充足思考时间
  "dify_image_timeout": 600   // 10分钟，图片生成需要更长时间
}
```

### 应用类型选择
- **Agent模式**: 适合智能代理，支持工具调用和流式响应
- **ChatBot模式**: 适合聊天机器人和工作流应用

## 📝 配置示例

参考 `config.json.template` 文件中的完整配置示例。
