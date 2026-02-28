# Release Notes - v2.3.0

发布日期: 2026-02-28

## 版本摘要
- 融合母项目 CowAgent 2.0.2 能力到当前 fork 分支
- 保留并兼容本项目既有的 Dify 与企业微信定制
- 新增 Qwen3-ASR 本地/自定义接口接入能力

## 主要更新
- 上游能力融合:
  - Web 控制台能力增强（流式/工具调用可视化）
  - 多通道并行运行能力（飞书、钉钉、企微、Web）
  - 会话持久化与 Agent 相关能力
  - 新模型接入框架（如 Gemini/Claude/Qwen/MiniMax/GLM/Kimi/Doubao 等）

- 本项目兼容性保留:
  - 保留 Dify 路由与 `bot_factory` 兼容
  - 保留企业微信相关配置与既有行为
  - 保留并扩展本地语音识别链路

- 语音能力增强:
  - 新增 `voice/qwen3_asr/` 模块
  - 新增 `qwen3_asr_api_*` 配置项
  - 工厂注册更新，支持按配置路由到 Qwen3-ASR

## 升级说明
- 建议从 `config-template.json` 重新比对并合并自定义配置
- 如使用 Qwen3-ASR，请补充 `qwen3_asr_api_base` 等参数
- 如使用多通道/Agent，请检查 `channel_type` 与 `agent_*` 配置

## 关联提交
- `7b7eb137`: Merge upstream 2.0.2 into merge/upstream-2.0.2
- `bb207f34`: feat: merge upstream 2.0.2 and integrate qwen3 asr
