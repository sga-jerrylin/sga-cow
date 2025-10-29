# Release Notes - v2.2.0

## 🎉 重大更新：企业微信智能机器人完整实现

本次更新实现了完整的企业微信智能机器人（WeChat Work AI Bot）功能，支持流式消息、群聊上下文管理、图文混排等核心功能。

---

## ✨ 新增功能

### 1. 企业微信智能机器人（wechatcom_aibot）

完整实现企业微信智能机器人，支持：

- ✅ **流式消息协议**：解决 HTTP 超时问题，支持长时间 AI 响应
- ✅ **群聊和单聊**：完整支持企业微信群聊和单聊场景
- ✅ **多种消息类型**：
  - 文本消息（支持 Markdown 格式）
  - 图片消息（支持加密图片解密）
  - 图文混排消息（文本 + 图片）
  - 流式消息（实时响应）
- ✅ **消息加解密**：使用 WXBizJsonMsgCrypt 进行消息加解密
- ✅ **@ 消息识别**：支持群聊中 @ 机器人触发对话

### 2. 群聊上下文管理优化

解决了群聊中不同用户消息导致上下文分裂的问题：

- ✅ **统一群聊上下文**：群聊使用群 ID 作为 `session_id`，保持连续对话
- ✅ **用户身份识别**：自动添加用户签名（`from {user_id}`），AI 能识别发言人
- ✅ **Dify API 优化**：修复 `user` 参数传递，确保 Dify 正确管理对话线程

### 3. 图文混排消息支持

实现完整的图文混排消息处理流程：

- ✅ **图片下载**：从企业微信 COS 下载加密图片
- ✅ **AES-256-CBC 解密**：正确解密企业微信加密图片
- ✅ **上传到 Dify**：将图片上传到 Dify 进行多模态分析
- ✅ **图片格式识别**：自动识别 PNG、JPEG 等图片格式

### 4. 文件链接显示优化

修复 Dify 生成的文件链接不显示的问题：

- ✅ **文件链接解析**：从 Markdown 中提取文件下载链接
- ✅ **多种文件格式**：支持 Word、Excel、PDF、TXT、ZIP 等文件
- ✅ **流式消息合并**：正确合并所有缓存的文本消息（包括文件链接）

### 5. 消息去重机制

避免重复处理相同消息：

- ✅ **msgid 去重**：使用消息 ID 进行去重
- ✅ **缓存管理**：优化缓存逻辑，避免新消息被误判为重复

---

## 🔧 技术改进

### 核心技术实现

1. **流式消息协议**
   - 首次请求立即返回 `finish=false`
   - 企业微信持续发送刷新请求
   - Dify 完成后返回 `finish=true` 和完整内容

2. **图片解密算法**
   - Base64 解码密钥
   - AES-CBC 解密（IV = key 的前 16 字节）
   - 去除 PKCS7 填充
   - 直接使用解密后的数据（不去除随机字符串）

3. **群聊上下文管理**
   - `session_id` = 群 ID（群聊）或用户 ID（单聊）
   - `user` 参数 = 群 ID（群聊）或用户 ID（单聊）
   - 消息内容添加 `from {user_id}` 签名

4. **消息去重**
   - 使用 `channel.processed_msgids` 字典存储已处理的消息 ID
   - 避免重复处理相同消息

---

## 📦 文件变更

### 新增文件

- `channel/wechatcom_aibot/` - 企业微信智能机器人完整实现
  - `wechatcom_aibot_channel.py` - 主要的 channel 处理逻辑
  - `wechatcom_aibot_message.py` - 消息解析和处理
  - `WXBizJsonMsgCrypt.py` - 企业微信消息加解密库
  - `README.md` - 详细的使用文档
  - `config.json.template` - 配置模板
  - `快速配置指南.md` - 快速配置指南
  - `配置说明.md` - 详细配置说明
  - `实现总结.md` - 技术实现总结

### 修改文件

- `bot/dify/dify_bot.py` - 支持图片上传和文件处理
- `channel/chat_channel.py` - 优化群聊消息处理逻辑
- `common/utils.py` - 增强 Markdown 解析功能
- `config.py` - 添加 wechatcom_aibot 配置
- `requirements.txt` - 添加 pycryptodome 依赖

---

## 📚 配置说明

### 1. 安装依赖

```bash
pip install pycryptodome
```

### 2. 配置文件

在 `config.json` 中添加：

```json
{
  "channel_type": "wechatcom_aibot",
  "wechatcom_aibot_token": "your_token",
  "wechatcom_aibot_aes_key": "your_aes_key",
  "wechatcom_aibot_port": 9898,
  "wechatcom_aibot_corp_id": "your_corp_id"
}
```

### 3. 企业微信后台配置

1. 创建智能助手应用
2. 配置回调 URL：`http://your-domain:9898/wxaibot`
3. 获取 Token 和 EncodingAESKey
4. 配置可见范围

详细配置请参考：`channel/wechatcom_aibot/快速配置指南.md`

---

## 🐛 Bug 修复

1. ✅ 修复 HTTP 超时问题（通过流式消息协议）
2. ✅ 修复群聊上下文分裂问题（统一使用群 ID）
3. ✅ 修复图片无法显示问题（正确解密图片）
4. ✅ 修复文件链接不显示问题（合并所有缓存消息）
5. ✅ 修复消息去重问题（使用 msgid）

---

## 📖 文档

- [快速配置指南](channel/wechatcom_aibot/快速配置指南.md)
- [详细配置说明](channel/wechatcom_aibot/配置说明.md)
- [技术实现总结](channel/wechatcom_aibot/实现总结.md)
- [README](channel/wechatcom_aibot/README.md)

---

## 🙏 致谢

感谢所有参与测试和反馈的用户！

---

## 📝 下一步计划

- [ ] 支持更多消息类型（视频、文件等）
- [ ] 优化图片处理性能
- [ ] 添加更多配置选项
- [ ] 完善错误处理和日志

---

**完整更新日志**: https://github.com/sga-jerrylin/sga-cow/compare/v2.1.3...v2.2.0

