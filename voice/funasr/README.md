# FunASR 语音识别模块

## 简介

FunASR 是阿里达摩院开源的语音识别工具包，支持多种高精度语音识别模型。本模块集成了 FunASR 的两个主要模型：

- **SenseVoice**: 多语言语音识别（中文、英文、日语、韩语、粤语）+ 情感识别
- **Paraformer**: 高精度中文语音识别 + 标点恢复 + ITN + 热词支持

## 配置说明

### ⚠️ 重要提示

**必须在 `config.json` 中设置 `"voice_to_text": "funasr"` 才能使用 FunASR！**

如果不设置，系统会使用默认的 OpenAI Whisper 引擎，而不是 FunASR。

### 1. 在主配置文件 `config.json` 中配置

```json
{
  "voice_to_text": "funasr",
  "speech_recognition": true,

  "funasr_url": "ws://localhost:10095",
  "funasr_model": "sensevoice",
  "funasr_enable_itn": true,
  "funasr_hotwords": "",
  "funasr_audio_fs": 16000
}
```

### 2. 配置参数说明

| 参数 | 是否必填 | 说明 | 默认值 | 可选值 |
|------|---------|------|--------|--------|
| `voice_to_text` | ✅ **必填** | 选择语音识别引擎 | `"openai"` | `"funasr"`, `"openai"`, `"ali"`, `"baidu"`, `"google"`, `"azure"`, `"xunfei"` |
| `speech_recognition` | ✅ **必填** | 是否开启语音识别 | `false` | `true` / `false` |
| `funasr_url` | ⚙️ 可选 | FunASR 服务地址 | `ws://localhost:10095` | SenseVoice: `ws://localhost:10095`<br>Paraformer: `ws://localhost:10096` |
| `funasr_model` | ⚙️ 可选 | 使用的模型 | `sensevoice` | `sensevoice` 或 `paraformer` |
| `funasr_enable_itn` | ⚙️ 可选 | 是否启用逆文本归一化 | `true` | `true` / `false` |
| `funasr_hotwords` | ⚙️ 可选 | 热词（仅 Paraformer） | `""` | 用空格分隔的词语 |
| `funasr_audio_fs` | ⚙️ 可选 | 音频采样率 | `16000` | `16000` / `8000` |

**说明：**
- ✅ **必填参数**：不填系统无法正常工作或不会使用 FunASR
- ⚙️ **可选参数**：有默认值，可以不填，但建议根据实际情况配置

### 3. 模型选择

#### SenseVoice（推荐用于多语言场景）

```json
{
  "voice_to_text": "funasr",
  "funasr_url": "ws://localhost:10095",
  "funasr_model": "sensevoice",
  "funasr_enable_itn": true
}
```

**特点：**
- ✅ 支持多语言（中英日韩粤）
- ✅ 自动语言检测
- ✅ 情感识别
- ✅ 适合实时对话场景
- ❌ 准确率略低于 Paraformer

#### Paraformer（推荐用于高精度中文场景）

```json
{
  "voice_to_text": "funasr",
  "funasr_url": "ws://localhost:10096",
  "funasr_model": "paraformer",
  "funasr_enable_itn": true,
  "funasr_hotwords": "人工智能 深度学习 神经网络"
}
```

**特点：**
- ✅ 高精度中文识别（CER 1.95%）
- ✅ 自动标点恢复
- ✅ ITN 数字转换
- ✅ 热词支持
- ✅ 适合会议记录、文件转写
- ❌ 仅支持中文

## 部署 FunASR 服务

### 方式一：Docker 部署（推荐）

#### 1. SenseVoice 服务

```bash
docker run -d \
  --name funasr-sensevoice \
  -p 10095:10095 \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.10 \
  bash -c "cd /workspace/FunASR/runtime && \
  nohup bash run_server.sh \
  --model-dir damo/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch \
  --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-pytorch \
  --punc-dir damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch \
  --port 10095 > log.txt 2>&1 &"
```

#### 2. Paraformer 服务

```bash
docker run -d \
  --name funasr-paraformer \
  -p 10096:10096 \
  registry.cn-hangzhou.aliyuncs.com/funasr_repo/funasr:funasr-runtime-sdk-online-cpu-0.1.10 \
  bash -c "cd /workspace/FunASR/runtime && \
  nohup bash run_server.sh \
  --model-dir damo/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch \
  --vad-dir damo/speech_fsmn_vad_zh-cn-16k-common-pytorch \
  --punc-dir damo/punc_ct-transformer_zh-cn-common-vocab272727-pytorch \
  --port 10096 > log.txt 2>&1 &"
```

### 方式二：本地部署

参考 FunASR 官方文档：https://github.com/alibaba/FunASR

## 使用示例

### 示例 1：使用 SenseVoice 进行多语言识别

```json
{
  "voice_to_text": "funasr",
  "speech_recognition": true,
  "funasr_url": "ws://localhost:10095",
  "funasr_model": "sensevoice",
  "funasr_enable_itn": true
}
```

### 示例 2：使用 Paraformer 进行高精度中文识别

```json
{
  "voice_to_text": "funasr",
  "speech_recognition": true,
  "funasr_url": "ws://localhost:10096",
  "funasr_model": "paraformer",
  "funasr_enable_itn": true,
  "funasr_hotwords": "企业微信 Dify 人工智能"
}
```

## 测试

### 测试 FunASR 连接

```bash
# 测试 SenseVoice
python voice/funasr/funasr_api.py test.wav sensevoice

# 测试 Paraformer
python voice/funasr/funasr_api.py test.wav paraformer
```

## 常见问题

### Q1: 为什么配置了 FunASR 但还是用的 OpenAI？

A: **必须在 `config.json` 中设置 `"voice_to_text": "funasr"`！**

如果不设置这个参数，系统会使用默认的 OpenAI Whisper 引擎。

```json
{
  "voice_to_text": "funasr",  // ← 这个必须填！
  "speech_recognition": true,
  "funasr_url": "ws://localhost:10095",
  "funasr_model": "sensevoice"
}
```

### Q2: 连接失败怎么办？

A: 检查 FunASR 服务是否正常运行：

```bash
# 检查 SenseVoice 服务
curl http://localhost:10095

# 检查 Paraformer 服务
curl http://localhost:10096
```

### Q3: 如何选择模型？

A:
- **多语言场景** → SenseVoice
- **高精度中文** → Paraformer
- **需要情感分析** → SenseVoice
- **会议记录** → Paraformer
- **实时对话** → SenseVoice

### Q4: 热词如何使用？

A: 热词仅 Paraformer 支持，用空格分隔：

```json
{
  "funasr_hotwords": "人工智能 深度学习 神经网络 企业微信"
}
```

**热词使用技巧：**

1. **专业术语场景**
   ```json
   "funasr_hotwords": "企业微信 Dify ChatGPT 大语言模型 API接口"
   ```

2. **会议记录场景**
   ```json
   "funasr_hotwords": "张三 李四 王五 项目A 季度报告 KPI OKR"
   ```

3. **客服场景**
   ```json
   "funasr_hotwords": "退款 发货 物流 订单号 售后服务 七天无理由"
   ```

**注意事项：**
- ✅ 用**空格**分隔，不要用逗号
- ✅ 热词应该是**完整词语**，不是单字
- ✅ 建议 **10-20 个**热词
- ❌ 不要添加标点符号

**效果对比：**

没有热词：
```
语音："我们使用 Dify 平台来构建大语言模型应用"
识别：我们使用低飞平台来构建大雨言模型应用 ❌
```

有热词：`"funasr_hotwords": "Dify 大语言模型"`
```
语音："我们使用 Dify 平台来构建大语言模型应用"
识别：我们使用Dify平台来构建大语言模型应用 ✅
```

### Q5: ITN 是什么？

A: ITN（Inverse Text Normalization）逆文本归一化，将文字数字转换为阿拉伯数字：
- "一千二百三十四" → "1234"
- "二零二三年十月二十八日" → "2023年10月28日"

## 依赖安装

```bash
pip install websockets
```

## 参考文档

- FunASR 官方仓库：https://github.com/alibaba/FunASR
- SenseVoice API 规则：`rules/sensevoice_api_rules.md`
- Paraformer API 规则：`rules/paraformer_api_rules.md`

