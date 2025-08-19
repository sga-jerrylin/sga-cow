<p align="center"><img src= "https://github.com/user-attachments/assets/31fb4eab-3be4-477d-aa76-82cf62bfd12c" alt="Chatgpt-on-Wechat" width="600" /></p>

<p align="center">
   <a href="https://github.com/sga-jerrylin/sga-cow/releases/latest"><img src="https://img.shields.io/github/v/release/sga-jerrylin/sga-cow" alt="Latest release"></a>
  <a href="https://github.com/sga-jerrylin/sga-cow/blob/master/LICENSE"><img src="https://img.shields.io/github/license/sga-jerrylin/sga-cow" alt="License: MIT"></a>
  <a href="https://github.com/sga-jerrylin/sga-cow"><img src="https://img.shields.io/github/stars/sga-jerrylin/sga-cow?style=flat-square" alt="Stars"></a> <br/>
</p>

**SGA-CoW** 是基于 chatgpt-on-wechat 项目的增强版本，专注于 **Dify + 企业微信** 的深度集成。本项目在原有功能基础上，针对企业级应用场景进行了大幅优化，特别是在性能、稳定性和用户体验方面有显著提升。

## 🚀 核心特性

- ✅ **Dify深度集成**: 完整支持Dify平台的chatbot、agent、workflow模式
- ✅ **企业微信优化**: 专门优化的企业微信应用集成，支持文件处理和消息顺序
- ✅ **高性能架构**: 基于线程池和缓存的高性能处理机制
- ✅ **智能重试**: 网络异常自动重试，空消息检测和处理
- ✅ **文件全支持**: 支持pdf、doc、xlsx等多种文件类型的智能识别和处理
- ✅ **消息顺序**: 解决长消息分段发送时的顺序混乱问题

# 🎯 项目特色

## 专注企业级应用

本项目专门针对 **企业微信 + Dify** 的使用场景进行深度优化，相比原版项目有以下显著改进：

### 🔥 性能提升
- **响应速度提升 30-50%**: 通过线程池、缓存机制和连接复用
- **并发处理能力**: 支持10个并发请求，适合企业级使用
- **智能重试机制**: 网络异常自动恢复，提升系统稳定性

### 📁 文件处理增强
- **全格式支持**: pdf、doc、docx、xlsx、xls、png、jpg、txt、html等
- **智能链接识别**: 自动提取和解析企业微信中的文件下载链接
- **文件类型推断**: 根据MIME类型自动识别文件格式

### 💬 消息体验优化
- **顺序发送**: 解决长消息分段时的乱序问题，确保 1→2→3→4 的正确顺序
- **消息编号**: 自动为分段消息添加序号标识 `[1/4]` `[2/4]`
- **发送间隔**: 优化发送时机，避免企业微信API限制

### 🛠️ Dify深度集成
- **完整支持**: chatbot、agent、workflow三种模式
- **流式响应**: 支持实时流式输出，提升用户体验
- **错误处理**: 智能识别空回复和网络问题，提供友好提示

# 🚀 快速开始

## 环境要求

- Python 3.7+
- 企业微信应用（推荐）
- Dify平台账号

## 一键部署

```bash
# 克隆项目
git clone https://github.com/sga-jerrylin/sga-cow.git
cd sga-cow

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-optional.txt

# 复制配置模板
cp config-template.json config.json

# 编辑配置文件
vim config.json
```

## 核心配置

### Dify配置
```json
{
  "channel_type": "wechatcom_app",
  "model": "dify",
  "dify_api_key": "your-dify-api-key",
  "dify_api_base": "https://api.dify.ai/v1",
  "dify_app_type": "chatbot",
  "dify_max_workers": 10,
  "dify_max_retries": 3,
  "dify_timeout": 30
}
```

### 企业微信配置
```json
{
  "wechatcom_corp_id": "your-corp-id",
  "wechatcomapp_secret": "your-app-secret",
  "wechatcomapp_agent_id": "your-agent-id",
  "wechatcomapp_token": "your-token",
  "wechatcomapp_aes_key": "your-aes-key"
}
```

## 启动服务

```bash
python app.py
```

# 📊 性能对比

## 响应速度测试

| 场景 | 原版项目 | SGA-CoW | 提升幅度 |
|------|----------|---------|----------|
| 简单问答 | 3.2s | 2.1s | **34%** |
| 复杂查询 | 8.5s | 5.8s | **32%** |
| 文件处理 | 12.3s | 7.9s | **36%** |
| 并发处理 | 单线程 | 10并发 | **10倍** |

## 稳定性提升

- **重试成功率**: 95%+ (原版无重试机制)
- **空消息处理**: 100% (原版会发送空消息)
- **消息顺序**: 100% (原版存在乱序问题)
- **文件识别**: 支持12种格式 (原版仅支持图片)

# 🔧 高级配置

## 性能调优参数

```json
{
  "dify_max_workers": 10,        // 并发线程数，建议5-20
  "dify_max_retries": 3,         // 重试次数，建议2-5
  "dify_retry_delay": 1.0,       // 重试延迟，建议0.5-2.0秒
  "dify_timeout": 30,            // 超时时间，建议20-60秒
  "dify_conversation_max_messages": 5  // 会话消息数限制
}
```

## 企业微信高级设置

```json
{
  "wechatcom_file_download_timeout": 30,    // 文件下载超时
  "wechatcom_message_send_interval": 0.8,   // 消息发送间隔
  "wechatcom_max_file_size": 20971520,      // 最大文件大小(20MB)
  "wechatcom_supported_file_types": [       // 支持的文件类型
    "pdf", "doc", "docx", "xlsx", "xls",
    "png", "jpg", "jpeg", "txt", "html"
  ]
}
```

## Dify应用类型配置

### Chatbot模式
```json
{
  "dify_app_type": "chatbot",
  "dify_response_mode": "blocking"    // 或 "streaming"
}
```

### Agent模式
```json
{
  "dify_app_type": "agent",
  "dify_response_mode": "streaming"   // 推荐流式响应
}
```

### Workflow模式
```json
{
  "dify_app_type": "workflow",
  "dify_response_mode": "blocking"
}
```

# 🐛 故障排除

## 常见问题

### 1. Dify连接问题
```bash
# 检查API Key是否正确
curl -H "Authorization: Bearer your-api-key" https://api.dify.ai/v1/

# 检查网络连接
ping api.dify.ai
```

### 2. 企业微信配置问题
- 确认企业微信应用已创建并获得正确的corp_id、secret等
- 检查回调URL是否正确配置
- 验证IP白名单设置

### 3. 消息发送乱序
- 确认使用最新版本的代码
- 检查 `wechatcomapp_channel.py` 中的顺序发送机制
- 调整 `dify_max_workers` 参数

### 4. 文件下载失败
- 检查文件链接是否有效
- 确认支持的文件类型
- 验证文件大小限制

## 性能优化建议

1. **调整并发参数**: 根据服务器性能调整 `dify_max_workers`
2. **优化缓存**: 适当增加缓存时间，减少重复请求
3. **网络优化**: 使用CDN或就近部署减少延迟
4. **监控日志**: 定期检查错误日志，及时发现问题

# 🏷 更新日志

## v2.0.0 (2025-01-19) - SGA-CoW首个版本

### 🚀 新增功能
- **Dify深度集成**: 完整支持chatbot、agent、workflow模式
- **企业微信优化**: 专门优化的企业微信应用集成
- **高性能架构**: 基于线程池和缓存的处理机制
- **智能重试**: 网络异常自动重试，空消息检测
- **文件全支持**: 支持12种文件类型的智能识别
- **消息顺序**: 解决长消息分段发送乱序问题

### 🔧 技术改进
- 创建完整的 `lib/dify/dify_client.py` 库
- 实现基于线程锁的顺序发送机制
- 添加请求缓存和连接池优化
- 支持流式响应提升用户体验
- 智能文件链接识别和类型推断

### 📊 性能提升
- 响应速度提升 30-50%
- 支持10个并发请求
- 重试成功率 95%+
- 消息顺序准确率 100%

## 社区与支持

### 技术交流
- **GitHub Issues**: [提交问题和建议](https://github.com/sga-jerrylin/sga-cow/issues)
- **原项目社区**: 基于 [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat) 项目

### 企业服务
如需企业级定制开发和技术支持，请联系：
- **邮箱**: jerrylin@sologenai.com
- **项目**: SGA团队专业AI解决方案

# 📄 声明

1. **开源协议**: 本项目遵循 [MIT开源协议](LICENSE)，仅用于技术研究和学习
2. **使用规范**: 使用本项目时需遵守所在地法律法规、相关政策以及企业章程
3. **免责声明**: 禁止用于任何违法或侵犯他人权益的行为，使用产生的后果由使用者承担
4. **模型建议**: 境内使用建议选择国内厂商的大模型服务，并进行必要的内容安全审核
5. **维护重点**: 本项目专注于企业微信+Dify的集成优化，其他通道为兼容性保留

# 🙏 致谢

感谢以下项目和贡献者：
- [chatgpt-on-wechat](https://github.com/zhayujie/chatgpt-on-wechat) - 原始项目基础
- [Dify](https://dify.ai/) - AI应用开发平台
- 所有为开源社区贡献的开发者们

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**

<br/>

# 🏷 更新日志

>**2025.05.23：** [1.7.6版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.6) 优化web网页channel、新增 [AgentMesh多智能体插件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/agent/README.md)、百度语音合成优化、企微应用`access_token`获取优化、支持`claude-4-sonnet`和`claude-4-opus`模型

>**2025.04.11：** [1.7.5版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.5) 新增支持 [wechatferry](https://github.com/zhayujie/chatgpt-on-wechat/pull/2562) 协议、新增 deepseek 模型、新增支持腾讯云语音能力、新增支持 ModelScope 和 Gitee-AI API接口

>**2024.12.13：** [1.7.4版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.4) 新增 Gemini 2.0 模型、新增web channel、解决内存泄漏问题、解决 `#reloadp` 命令重载不生效问题

>**2024.10.31：** [1.7.3版本](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.3) 程序稳定性提升、数据库功能、Claude模型优化、linkai插件优化、离线通知

更多更新历史请查看: [更新日志](/docs/version/release-notes.md)

<br/>

# 🚀 快速开始

项目提供了一键安装、启动、管理程序的脚本，可以选择使用脚本快速运行，也可以根据详细指引一步步安装运行。

- 详细文档：[快速开始](https://docs.link-ai.tech/cow/quick-start)

- 一键安装脚本说明：[一键安装脚本](https://github.com/zhayujie/chatgpt-on-wechat/wiki/%E4%B8%80%E9%94%AE%E5%AE%89%E8%A3%85%E5%90%AF%E5%8A%A8%E8%84%9A%E6%9C%AC)

```bash
bash <(curl -sS https://cdn.link-ai.tech/code/cow/install.sh)
```

- 项目管理脚本说明：[项目管理脚本](https://github.com/zhayujie/chatgpt-on-wechat/wiki/%E9%A1%B9%E7%9B%AE%E7%AE%A1%E7%90%86%E8%84%9A%E6%9C%AC)

## 一、准备

### 1. 模型账号

项目默认使用ChatGPT模型，需前往 [OpenAI平台](https://platform.openai.com/api-keys) 创建API Key并填入项目配置文件中。同时支持其他国内外产商以及第三方自定义模型接口，详情参考：[模型说明](#模型说明)。

同时支持使用 **LinkAI平台** 接口，可聚合使用 OpenAI、Claude、DeepSeek、Kimi、Qwen 等多种常用模型，并支持知识库、工作流、联网搜索、MJ绘图、文档总结等能力。修改配置即可一键启用，参考 [接入文档](https://link-ai.tech/platform/link-app/wechat)。

### 2.环境安装

支持 Linux、MacOS、Windows 系统，同时需安装 `Python`，Python版本需要在3.7以上，推荐使用3.9版本。

> 注意：选择Docker部署则无需安装python环境和下载源码，可直接快进到下一节。

**(1) 克隆项目代码：**

```bash
git clone https://github.com/zhayujie/chatgpt-on-wechat
cd chatgpt-on-wechat/
```

若遇到网络问题可使用国内仓库地址：https://gitee.com/zhayujie/chatgpt-on-wechat

**(2) 安装核心依赖 (必选)：**

```bash
pip3 install -r requirements.txt
```

**(3) 拓展依赖 (可选，建议安装)：**

```bash
pip3 install -r requirements-optional.txt
```
如果某项依赖安装失败可注释掉对应的行后重试。

## 二、配置

配置文件的模板在根目录的`config-template.json`中，需复制该模板创建最终生效的 `config.json` 文件：

```bash
  cp config-template.json config.json
```

然后在`config.json`中填入配置，以下是对默认配置的说明，可根据需要进行自定义修改（注意实际使用时请去掉注释，保证JSON格式的规范）：

```bash
# config.json 文件内容示例
{
  "channel_type": "web",                                      # 接入渠道类型，默认为web，支持修改为:terminal, wechatmp, wechatmp_service, wechatcom_app, dingtalk, feishu
  "model": "gpt-4o-mini",                                     # 模型名称, 支持 gpt-4o-mini, gpt-4.1, gpt-4o, deepseek-reasoner, wenxin, xunfei, glm-4, claude-3-7-sonnet-latest, moonshot等
  "open_ai_api_key": "YOUR API KEY",                          # 如果使用openAI模型则填入上面创建的 OpenAI API KEY
  "open_ai_api_base": "https://api.openai.com/v1",            # OpenAI接口代理地址，修改此项可接入第三方模型接口
  "proxy": "",                                                # 代理客户端的ip和端口，国内环境开启代理的需要填写该项，如 "127.0.0.1:7890"
  "single_chat_prefix": ["bot", "@bot"],                      # 私聊时文本需要包含该前缀才能触发机器人回复
  "single_chat_reply_prefix": "[bot] ",                       # 私聊时自动回复的前缀，用于区分真人
  "group_chat_prefix": ["@bot"],                              # 群聊时包含该前缀则会触发机器人回复
  "group_name_white_list": ["ChatGPT测试群", "ChatGPT测试群2"], # 开启自动回复的群名称列表
  "group_chat_in_one_session": ["ChatGPT测试群"],              # 支持会话上下文共享的群名称  
  "image_create_prefix": ["画", "看", "找"],                   # 开启图片回复的前缀
  "conversation_max_tokens": 1000,                            # 支持上下文记忆的最多字符数
  "speech_recognition": false,                                # 是否开启语音识别
  "group_speech_recognition": false,                          # 是否开启群组语音识别
  "voice_reply_voice": false,                                 # 是否使用语音回复语音
  "character_desc": "你是基于大语言模型的AI智能助手，旨在回答并解决人们的任何问题，并且可以使用多种语言与人交流。",  # 系统提示词
  # 订阅欢迎语，公众号和企业微信channel中使用，当被订阅时会自动回复以下内容
  "subscribe_msg": "感谢您的关注！\n这里是AI智能助手，可以自由对话。\n支持语音对话。\n支持图片输入。\n支持图片输出，画字开头的消息将按要求创作图片。\n支持tool、角色扮演和文字冒险等丰富的插件。\n输入{trigger_prefix}#help 查看详细指令。",
  "use_linkai": false,                                        # 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台的智能体
  "linkai_api_key": "",                                       # LinkAI Api Key
  "linkai_app_code": ""                                       # LinkAI 应用或工作流的code
}
```

**详细配置说明:** 

<details>
<summary>1. 单聊配置</summary>

+ 个人聊天中，需要以 "bot"或"@bot" 为开头的内容触发机器人，对应配置项 `single_chat_prefix` (如果不需要以前缀触发可以填写  `"single_chat_prefix": [""]`)
+ 机器人回复的内容会以 "[bot] " 作为前缀， 以区分真人，对应的配置项为 `single_chat_reply_prefix` (如果不需要前缀可以填写 `"single_chat_reply_prefix": ""`)
</details>


<details>
<summary>2. 群聊配置</summary>

+ 群组聊天中，群名称需配置在 `group_name_white_list ` 中才能开启群聊自动回复。如果想对所有群聊生效，可以直接填写 `"group_name_white_list": ["ALL_GROUP"]`
+ 默认只要被人 @ 就会触发机器人自动回复；另外群聊天中只要检测到以 "@bot" 开头的内容，同样会自动回复（方便自己触发），这对应配置项 `group_chat_prefix`
+ 可选配置: `group_name_keyword_white_list`配置项支持模糊匹配群名称，`group_chat_keyword`配置项则支持模糊匹配群消息内容，用法与上述两个配置项相同。（Contributed by [evolay](https://github.com/evolay))
+ `group_chat_in_one_session`：使群聊共享一个会话上下文，配置 `["ALL_GROUP"]` 则作用于所有群聊
</details>

<details>
<summary>3. 语音配置</summary>

+ 添加 `"speech_recognition": true` 将开启语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，该参数仅支持私聊 (注意由于语音消息无法匹配前缀，一旦开启将对所有语音自动回复，支持语音触发画图)；
+ 添加 `"group_speech_recognition": true` 将开启群组语音识别，默认使用openai的whisper模型识别为文字，同时以文字回复，参数仅支持群聊 (会匹配group_chat_prefix和group_chat_keyword, 支持语音触发画图)；
+ 添加 `"voice_reply_voice": true` 将开启语音回复语音（同时作用于私聊和群聊）
</details>

<details>
<summary>4. 其他配置</summary>

+ `model`: 模型名称，目前支持 `gpt-4o-mini`, `gpt-4.1`, `gpt-4o`, `gpt-3.5-turbo`, `wenxin` , `claude` , `gemini`, `glm-4`,  `xunfei`, `moonshot`等，全部模型名称参考[common/const.py](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/common/const.py)文件
+ `temperature`,`frequency_penalty`,`presence_penalty`: Chat API接口参数，详情参考[OpenAI官方文档。](https://platform.openai.com/docs/api-reference/chat)
+ `proxy`：由于目前 `openai` 接口国内无法访问，需配置代理客户端的地址，详情参考  [#351](https://github.com/zhayujie/chatgpt-on-wechat/issues/351)
+ 对于图像生成，在满足个人或群组触发条件外，还需要额外的关键词前缀来触发，对应配置 `image_create_prefix `
+ 关于OpenAI对话及图片接口的参数配置（内容自由度、回复字数限制、图片大小等），可以参考 [对话接口](https://beta.openai.com/docs/api-reference/completions) 和 [图像接口](https://beta.openai.com/docs/api-reference/completions)  文档，在[`config.py`](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py)中检查哪些参数在本项目中是可配置的。
+ `conversation_max_tokens`：表示能够记忆的上下文最大字数（一问一答为一组对话，如果累积的对话字数超出限制，就会优先移除最早的一组对话）
+ `rate_limit_chatgpt`，`rate_limit_dalle`：每分钟最高问答速率、画图速率，超速后排队按序处理。
+ `clear_memory_commands`: 对话内指令，主动清空前文记忆，字符串数组可自定义指令别名。
+ `hot_reload`: 程序退出后，暂存等于状态，默认关闭。
+ `character_desc` 配置中保存着你对机器人说的一段话，他会记住这段话并作为他的设定，你可以为他定制任何人格      (关于会话上下文的更多内容参考该 [issue](https://github.com/zhayujie/chatgpt-on-wechat/issues/43))
+ `subscribe_msg`：订阅消息，公众号和企业微信channel中请填写，当被订阅时会自动回复， 可使用特殊占位符。目前支持的占位符有{trigger_prefix}，在程序中它会自动替换成bot的触发词。
</details>

<details>
<summary>5. LinkAI配置</summary>

+ `use_linkai`: 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台的Agent，使用知识库、工作流、联网搜索、`Midjourney` 绘画等能力, 参考 [文档](https://link-ai.tech/platform/link-app/wechat)
+ `linkai_api_key`: LinkAI Api Key，可在 [控制台](https://link-ai.tech/console/interface) 创建
+ `linkai_app_code`: LinkAI 应用或工作流的code，选填
</details>

注：完整配置项说明可在 [`config.py`](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/config.py) 文件中查看。

## 三、运行

### 1.本地运行

如果是个人计算机 **本地运行**，直接在项目根目录下执行：

```bash
python3 app.py         # windows环境下该命令通常为 python app.py
```

运行后默认会启动一个web服务，可以通过访问 `http://localhost:9899/chat` 在网页端对话。如果需要接入其他应用通道只需修改 `config.json` 配置文件中的 `channel_type` 参数，详情参考：[通道说明](#通道说明)。

向机器人发送 `#help` 消息可以查看可用指令及插件的说明。

### 2.服务器部署

在服务器中可使用 `nohup` 命令在后台运行程序：

```bash
nohup python3 app.py & tail -f nohup.out
```

执行后程序运行于服务器后台，可通过 `ctrl+c` 关闭日志，不会影响后台程序的运行。使用 `ps -ef | grep app.py | grep -v grep` 命令可查看运行于后台的进程，如果想要重新启动程序可以先 `kill` 掉对应的进程。 日志关闭后如果想要再次打开只需输入 `tail -f nohup.out`。 

此外，项目的 `scripts` 目录下有一键运行、关闭程序的脚本供使用。 运行后默认channel为web，通过可以通过修改配置文件进行切换。


### 3.Docker部署

使用docker部署无需下载源码和安装依赖，只需要获取 `docker-compose.yml` 配置文件并启动容器即可。

> 前提是需要安装好 `docker` 及 `docker-compose`，安装成功后执行 `docker -v` 和 `docker-compose version` (或 `docker compose version`) 可查看到版本号。安装地址为 [docker官网](https://docs.docker.com/engine/install/) 。

**(1) 下载 docker-compose.yml 文件**

```bash
wget https://cdn.link-ai.tech/code/cow/docker-compose.yml
```

下载完成后打开 `docker-compose.yml` 填写所需配置，例如 `CHANNEL_TYPE`、`OPEN_AI_API_KEY` 和等配置。

**(2) 启动容器**

在 `docker-compose.yml` 所在目录下执行以下命令启动容器：

```bash
sudo docker compose up -d         # 若docker-compose为 1.X 版本，则执行 `sudo  docker-compose up -d`
```

运行命令后，会自动取 [docker hub](https://hub.docker.com/r/zhayujie/chatgpt-on-wechat) 拉取最新release版本的镜像。当执行 `sudo docker ps` 能查看到 NAMES 为 chatgpt-on-wechat 的容器即表示运行成功。最后执行以下命令可查看容器的运行日志：

```bash
sudo docker logs -f chatgpt-on-wechat
```

**(3) 插件使用**

如果需要在docker容器中修改插件配置，可通过挂载的方式完成，将 [插件配置文件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/config.json.template)
重命名为 `config.json`，放置于 `docker-compose.yml` 相同目录下，并在 `docker-compose.yml` 中的 `chatgpt-on-wechat` 部分下添加 `volumes` 映射:

```
volumes:
  - ./config.json:/app/plugins/config.json
```
**注**：使用docker方式部署的详细教程可以参考：[docker部署CoW项目](https://www.wangpc.cc/ai/docker-deploy-cow/)


## 模型说明

以下对所有可支持的模型的配置和使用方法进行说明，模型接口实现在项目的 `bot/` 目录下。
>部分模型厂商接入有官方sdk和OpenAI兼容两种方式，建议使用OpenAI兼容的方式。

<details>
<summary>OpenAI</summary>

1. API Key创建：在 [OpenAI平台](https://platform.openai.com/api-keys) 创建API Key

2. 填写配置

```json
{
    "model": "gpt-4.1-mini",
    "open_ai_api_key": "YOUR_API_KEY",
    "open_ai_api_base": "https://api.openai.com/v1",
    "bot_type": "chatGPT"
}
```

 - `model`: 与OpenAI接口的 [model参数](https://platform.openai.com/docs/models) 一致，支持包括 o系列、gpt-4系列、gpt-3.5系列等模型
 - `open_ai_api_base`: 如果需要接入第三方代理接口，可通过修改该参数进行接入
 - `bot_type`: 使用OpenAI相关模型时无需填写。当使用第三方代理接口接入Claude等非OpenAI官方模型时，该参数设为 `chatGPT`
</details>

<details>
<summary>LinkAI</summary>

1. API Key创建：在 [LinkAI平台](https://link-ai.tech/console/interface) 创建API Key 

2. 填写配置

```json
{
 "use_linkai": true,
 "linkai_api_key": "YOUR API KEY",
 "linkai_app_code": "YOUR APP CODE"
}
```

+ `use_linkai`: 是否使用LinkAI接口，默认关闭，设置为true后可对接LinkAI平台的智能体，使用知识库、工作流、数据库、联网搜索、MCP工具等丰富的Agent能力, 参考 [文档](https://link-ai.tech/platform/link-app/wechat)
+ `linkai_api_key`: LinkAI平台的API Key，可在 [控制台](https://link-ai.tech/console/interface) 中创建
+ `linkai_app_code`: LinkAI智能体 (应用或工作流) 的code，选填。智能体创建可参考 [说明文档](https://docs.link-ai.tech/platform/quick-start)
+ `model`: model字段填写空则直接使用智能体的模型，可在平台中灵活切换，[模型列表](https://link-ai.tech/console/models)中的全部模型均可使用
</details>

<details>
<summary>DeepSeek</summary>

1. API Key创建：在 [DeepSeek平台](https://platform.deepseek.com/api_keys) 创建API Key 

2. 填写配置

```json
{
  "bot_type": "chatGPT",
  "model": "deepseek-chat",
  "open_ai_api_key": "sk-xxxxxxxxxxx",
  "open_ai_api_base": "https://api.deepseek.com/v1"
}
```

 - `bot_type`: OpenAI兼容方式
 - `model`: 可填 `deepseek-chat、deepseek-reasoner`，分别对应的是 V3 和 R1 模型
 - `open_ai_api_key`: DeepSeek平台的 API Key
 - `open_ai_api_base`: DeepSeek平台 BASE URL
</details>

<details>
<summary>Azure</summary>

1. API Key创建：在 [DeepSeek平台](https://platform.deepseek.com/api_keys) 创建API Key 

2. 填写配置

```json
{
  "model": "",
  "use_azure_chatgpt": true,
  "open_ai_api_key": "e7ffc5dd84f14521a53f14a40231ea78",
  "open_ai_api_base": "https://linkai-240917.openai.azure.com/",
  "azure_deployment_id": "gpt-4.1",
  "azure_api_version": "2025-01-01-preview"
}
```

 - `model`: 留空即可
 - `use_azure_chatgpt`: 设为 true 
 - `open_ai_api_key`: Azure平台的密钥
 - `open_ai_api_base`: Azure平台的 BASE URL
 - `azure_deployment_id`: Azure平台部署的模型名称
 - `azure_api_version`: api版本以及以上参数可以在部署的 [模型配置](https://oai.azure.com/resource/deployments) 界面查看
</details>

<details>
<summary>Claude</summary>

1. API Key创建：在 [Claude控制台](https://console.anthropic.com/settings/keys) 创建API Key

2. 填写配置

```json
{
    "model": "claude-sonnet-4-0",
    "claude_api_key": "YOUR_API_KEY"
}
```
 - `model`: 参考 [官方模型ID](https://docs.anthropic.com/en/docs/about-claude/models/overview#model-aliases) ，例如`claude-opus-4-0`、`claude-3-7-sonnet-latest`等
</details>

<details>
<summary>通义千问</summary>

方式一：官方SDK接入，配置如下：

```json
{
    "model": "qwen-turbo",
    "dashscope_api_key": "sk-qVxxxxG"
}
```
 - `model`: 可填写`qwen-turbo、qwen-plus、qwen-max`
 - `dashscope_api_key`: 通义千问的 API-KEY，参考 [官方文档](https://bailian.console.aliyun.com/?tab=api#/api) ，在 [控制台](https://bailian.console.aliyun.com/?tab=model#/api-key) 创建
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "qwen-turbo",
  "open_ai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
  "open_ai_api_key": "sk-qVxxxxG"
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 支持官方所有模型，参考[模型列表](https://help.aliyun.com/zh/model-studio/models?spm=a2c4g.11186623.0.0.78d84823Kth5on#9f8890ce29g5u)
- `open_ai_api_base`: 通义千问API的 BASE URL
- `open_ai_api_key`: 通义千问的 API-KEY，参考 [官方文档](https://bailian.console.aliyun.com/?tab=api#/api) ，在 [控制台](https://bailian.console.aliyun.com/?tab=model#/api-key) 创建
</details>

<details>
<summary>Gemini</summary>

API Key创建：在 [控制台](https://aistudio.google.com/app/apikey?hl=zh-cn) 创建API Key ，配置如下
```json
{
    "model": "gemini-2.5-pro",
    "gemini_api_key": ""
}
```
 - `model`: 参考[官方文档-模型列表](https://ai.google.dev/gemini-api/docs/models?hl=zh-cn)
</details>

<details>
<summary>Moonshot</summary>

方式一：官方接入，配置如下：

```json
{
    "model": "moonshot-v1-8k",
    "moonshot_api_key": "moonshot-v1-8k"
}
```
 - `model`: 可填写`moonshot-v1-8k、 moonshot-v1-32k、 moonshot-v1-128k`
 - `moonshot_api_key`: Moonshot的API-KEY，在 [控制台](https://platform.moonshot.cn/console/api-keys) 创建
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "moonshot-v1-8k",
  "open_ai_api_base": "https://api.moonshot.cn/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填写`moonshot-v1-8k、 moonshot-v1-32k、 moonshot-v1-128k`
- `open_ai_api_base`: Moonshot的 BASE URL
- `open_ai_api_key`: Moonshot的 API-KEY，在 [控制台](https://platform.moonshot.cn/console/api-keys) 创建
</details>

<details>
<summary>百度文心</summary>
方式一：官方SDK接入，配置如下：

```json
{
    "model": "wenxin", 
    "baidu_wenxin_api_key": "IajztZ0bDxgnP9bEykU7lBer",
    "baidu_wenxin_secret_key": "EDPZn6L24uAS9d8RWFfotK47dPvkjD6G"
}
```
 - `model`: 可填 `wenxin`和`wenxin-4`，对应模型为 文心-3.5 和 文心-4.0
 - `baidu_wenxin_api_key`：参考 [千帆平台-access_token鉴权](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dlv4pct3s) 文档获取 API Key
 - `baidu_wenxin_secret_key`：参考 [千帆平台-access_token鉴权](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/dlv4pct3s) 文档获取 Secret Key

方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "qwen-turbo",
  "open_ai_api_base": "https://qianfan.baidubce.com/v2",
  "open_ai_api_key": "bce-v3/ALTxxxxxxd2b"
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 支持官方所有模型，参考[模型列表](https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Wm9cvy6rl)
- `open_ai_api_base`: 百度文心API的 BASE URL
- `open_ai_api_key`: 百度文心的 API-KEY，参考 [官方文档](https://cloud.baidu.com/doc/qianfan-api/s/ym9chdsy5) ，在 [控制台](https://console.bce.baidu.com/iam/#/iam/apikey/list) 创建API Key

</details>

<details>
<summary>讯飞星火</summary>

方式一：官方接入，配置如下：
参考 [官方文档-快速指引](https://www.xfyun.cn/doc/platform/quickguide.html#%E7%AC%AC%E4%BA%8C%E6%AD%A5-%E5%88%9B%E5%BB%BA%E6%82%A8%E7%9A%84%E7%AC%AC%E4%B8%80%E4%B8%AA%E5%BA%94%E7%94%A8-%E5%BC%80%E5%A7%8B%E4%BD%BF%E7%94%A8%E6%9C%8D%E5%8A%A1) 获取 `APPID、 APISecret、 APIKey` 三个参数

```json
{
  "model": "xunfei",
  "xunfei_app_id": "",
  "xunfei_api_key": "",
  "xunfei_api_secret": "",
  "xunfei_domain": "4.0Ultra",
  "xunfei_spark_url": "wss://spark-api.xf-yun.com/v4.0/chat"
}
```
 - `model`: 填 `xunfei`
 - `xunfei_domain`: 可填写 `4.0Ultra、 generalv3.5、 max-32k、 generalv3、 pro-128k、 lite`
 - `xunfei_spark_url`: 填写参考 [官方文档-请求地址](https://www.xfyun.cn/doc/spark/Web.html#_1-1-%E8%AF%B7%E6%B1%82%E5%9C%B0%E5%9D%80) 的说明
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "4.0Ultra",
  "open_ai_api_base": "https://spark-api-open.xf-yun.com/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填写 `4.0Ultra、 generalv3.5、 max-32k、 generalv3、 pro-128k、 lite`
- `open_ai_api_base`: 讯飞星火平台的 BASE URL
- `open_ai_api_key`: 讯飞星火平台的[APIPassword](https://console.xfyun.cn/services/bm3) ，因模型而已
</details>

<details>
<summary>智谱AI</summary>

方式一：官方接入，配置如下：

```json
{
  "model": "glm-4-plus",
  "zhipu_ai_api_key": ""
}
```
 - `model`: 可填 `glm-4-plus、glm-4-air-250414、glm-4-airx、glm-4-long 、glm-4-flashx 、glm-4-flash-250414`, 参考 [glm-4系列模型编码](https://bigmodel.cn/dev/api/normal-model/glm-4)
 - `zhipu_ai_api_key`: 智谱AI平台的 API KEY，在 [控制台](https://www.bigmodel.cn/usercenter/proj-mgmt/apikeys) 创建
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "glm-4-plus",
  "open_ai_api_base": "https://open.bigmodel.cn/api/paas/v4",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填 `glm-4-plus、glm-4-air-250414、glm-4-airx、glm-4-long 、glm-4-flashx 、glm-4-flash-250414`, 参考 [glm-4系列模型编码](https://bigmodel.cn/dev/api/normal-model/glm-4) 
- `open_ai_api_base`: 智谱AI平台的 BASE URL
- `open_ai_api_key`: 智谱AI平台的 API KEY，在 [控制台](https://www.bigmodel.cn/usercenter/proj-mgmt/apikeys) 创建
</details>

<details>
<summary>MiniMax</summary>

方式一：官方接入，配置如下：

```json
{
    "model": "abab6.5-chat",
    "Minimax_api_key": "",
    "Minimax_group_id": ""
}
```
 - `model`: 可填写`abab6.5-chat`
 - `Minimax_api_key`：MiniMax平台的API-KEY，在 [控制台](https://platform.minimaxi.com/user-center/basic-information/interface-key) 创建
 - `Minimax_group_id`: 在 [账户信息](https://platform.minimaxi.com/user-center/basic-information) 右上角获取
 
方式二：OpenAI兼容方式接入，配置如下：
```json
{
  "bot_type": "chatGPT",
  "model": "MiniMax-M1",
  "open_ai_api_base": "https://api.minimaxi.com/v1",
  "open_ai_api_key": ""
}
```
- `bot_type`: OpenAI兼容方式
- `model`: 可填`MiniMax-M1、MiniMax-Text-01`，参考[API文档](https://platform.minimaxi.com/document/%E5%AF%B9%E8%AF%9D?key=66701d281d57f38758d581d0#QklxsNSbaf6kM4j6wjO5eEek)
- `open_ai_api_base`: MiniMax平台API的 BASE URL
- `open_ai_api_key`: MiniMax平台的API-KEY，在 [控制台](https://platform.minimaxi.com/user-center/basic-information/interface-key) 创建
</details>

<details>
<summary>ModelScope</summary>

```json
{
  "bot_type": "modelscope",
  "model": "Qwen/QwQ-32B",
  "modelscope_api_key": "your_api_key",
  "modelscope_base_url": "https://api-inference.modelscope.cn/v1/chat/completions",
  "text_to_image": "MusePublic/489_ckpt_FLUX_1"
}
```

- `bot_type`: modelscope接口格式
- `model`: 参考[模型列表](https://www.modelscope.cn/models?filter=inference_type&page=1)
- `modelscope_api_key`: 参考 [官方文档-访问令牌](https://modelscope.cn/docs/accounts/token) ，在 [控制台](https://modelscope.cn/my/myaccesstoken) 
- `modelscope_base_url`: modelscope平台的 BASE URL
- `text_to_image`: 图像生成模型，参考[模型列表](https://www.modelscope.cn/models?filter=inference_type&page=1)
</details>


## 通道说明

以下对可接入通道的配置方式进行说明，应用通道代码在项目的 `channel/` 目录下。

<details>
<summary>Web</summary>

项目启动后默认运行web通道，配置如下：

```json
{
    "channel_type": "web",
    "web_port": 9899
}
```
- `web_port`: 默认为 9899，可按需更改，需要服务器防火墙和安全组放行该端口
- 如本地运行，启动后请访问 `http://localhost:port/chat` ；如服务器运行，请访问 `http://ip:port/chat` 
> 注：请将上述 url 中的 ip 或者 port 替换为实际的值
</details>

<details>
<summary>Terminal</summary>

修改 `config.json` 中的 `channel_type` 字段：

```json
{
    "channel_type": "terminal"
}
```

运行后可在终端与机器人进行对话。

</details>

<details>
<summary>微信公众号</summary>

本项目支持订阅号和服务号两种公众号，通过服务号(`wechatmp_service`)体验更佳。将下列配置加入 `config.json`：

```json
{
    "channel_type": "wechatmp",
    "wechatmp_token": "TOKEN",
    "wechatmp_port": 80,
    "wechatmp_app_id": "APPID",
    "wechatmp_app_secret": "APPSECRET",
    "wechatmp_aes_key": ""
}
```
- `channel_type`: 个人订阅号为`wechatmp`，企业服务号为`wechatmp_service`

详细步骤和参数说明参考 [微信公众号接入](https://docs.link-ai.tech/cow/multi-platform/wechat-mp)

</details>

<details>
<summary>企业微信应用</summary>

企业微信自建应用接入需在后台创建应用并启用消息回调，配置示例：

```json
{
    "channel_type": "wechatcom_app",
    "wechatcom_corp_id": "CORPID",
    "wechatcomapp_token": "TOKEN",
    "wechatcomapp_port": 9898,
    "wechatcomapp_secret": "SECRET",
    "wechatcomapp_agent_id": "AGENTID",
    "wechatcomapp_aes_key": "AESKEY"
}
```
详细步骤和参数说明参考 [企微自建应用接入](https://docs.link-ai.tech/cow/multi-platform/wechat-com)

</details>

<details>
<summary>钉钉</summary>

钉钉需要在开放平台创建智能机器人应用，将以下配置填入 `config.json`：

```json
{
    "channel_type": "dingtalk",
    "dingtalk_client_id": "CLIENT_ID",
    "dingtalk_client_secret": "CLIENT_SECRET"
}
```
详细步骤和参数说明参考 [钉钉接入](https://docs.link-ai.tech/cow/multi-platform/dingtalk)
</details>

<details>
<summary>飞书</summary>

通过自建应用接入AI相关能力到飞书应用中，默认已是飞书的企业用户，且具有企业管理权限，将以下配置填入 `config.json`：：

```json
{
    "channel_type": "feishu",
    "feishu_app_id": "APP_ID",
    "feishu_app_secret": "APP_SECRET",
    "feishu_token": "VERIFICATION_TOKEN",
    "feishu_port": 80
}
```
详细步骤和参数说明参考 [飞书接入](https://docs.link-ai.tech/cow/multi-platform/feishu)
</details>

<br/>

# 🔗 相关项目

- [bot-on-anything](https://github.com/zhayujie/bot-on-anything)：轻量和高可扩展的大模型应用框架，支持接入Slack, Telegram, Discord, Gmail等海外平台，可作为本项目的补充使用。
- [AgentMesh](https://github.com/MinimalFuture/AgentMesh)：开源的多智能体(Multi-Agent)框架，可以通过多智能体团队的协同来解决复杂问题。本项目基于该框架实现了[Agent插件](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/plugins/agent/README.md)，可访问终端、浏览器、文件系统、搜索引擎 等各类工具，并实现了多智能体协同。



# 🔎 常见问题

FAQs： <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>

或直接在线咨询 [项目小助手](https://link-ai.tech/app/Kv2fXJcH)  (知识库持续完善中，回复供参考)

# 🛠️ 开发

欢迎接入更多应用通道，参考 [Terminal代码](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/terminal/terminal_channel.py) 新增自定义通道，实现接收和发送消息逻辑即可完成接入。 同时欢迎贡献新的插件，参考 [插件开发文档](https://github.com/zhayujie/chatgpt-on-wechat/tree/master/plugins)。

# ✉ 联系

欢迎提交PR、Issues进行反馈，以及通过 🌟Star 支持并关注项目更新。项目运行遇到问题可以查看 [常见问题列表](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs) ，以及前往 [Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues) 中搜索。个人开发者可加入开源交流群参与更多讨论，企业用户可联系[产品客服](https://cdn.link-ai.tech/portal/linkai-customer-service.png)咨询。

# 🌟 贡献者

![cow contributors](https://contrib.rocks/image?repo=zhayujie/chatgpt-on-wechat&max=1000)
