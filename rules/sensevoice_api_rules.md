================================================================================
                    SenseVoice API 调用规则文档
================================================================================

【服务信息】
  服务名称：SenseVoice-Small 多语言语音识别服务
  服务端口：10095
  连接地址：ws://localhost:10095
  协议类型：WebSocket
  模型特性：多语言识别（中文、英文、日语、韩语、粤语）+ 情感识别

================================================================================
【调用流程】
================================================================================

1. 建立 WebSocket 连接
   ws://localhost:10095

2. 发送配置消息（JSON 格式）
   {
     "mode": "offline",           // 识别模式：offline（离线）或 online（在线）
     "wav_name": "audio_xxx",     // 音频文件名（任意字符串）
     "wav_format": "wav",         // 音频格式：wav, pcm, mp3 等
     "audio_fs": 16000,           // 采样率：16000 Hz（推荐）
     "is_speaking": true,         // 是否正在说话：true
     "itn": true                  // 是否启用逆文本归一化：true/false
   }

3. 发送音频数据（Binary 格式）
   - 直接发送音频文件的二进制数据
   - 支持格式：WAV, PCM, MP3 等
   - 推荐采样率：16000 Hz
   - 推荐声道：单声道

4. 发送结束标志（JSON 格式）
   {
     "is_speaking": false         // 标记音频发送完毕
   }

5. 接收识别结果（JSON 格式）
   {
     "text": "<|zh|><|NEUTRAL|>识别的文本内容",
     "timestamp": "...",
     "mode": "offline"
   }

================================================================================
【参数说明】
================================================================================

【请求参数】
  mode          识别模式
                - offline: 离线模式，等待完整音频后识别
                - online: 在线模式，实时流式识别
                
  wav_name      音频标识符
                - 任意字符串，用于标识本次识别
                - 建议格式：audio_timestamp 或 filename
                
  wav_format    音频格式
                - wav: WAV 格式（推荐）
                - pcm: 原始 PCM 数据
                - mp3: MP3 格式
                
  audio_fs      采样率（Hz）
                - 16000: 16kHz（推荐，模型训练采样率）
                - 8000: 8kHz（电话音质）
                
  is_speaking   说话状态
                - true: 开始发送音频
                - false: 音频发送完毕
                
  itn           逆文本归一化
                - true: 启用（"一千二百" → "1200"）
                - false: 禁用

【响应字段】
  text          识别文本
                - 包含语言标签：<|zh|>（中文）、<|en|>（英文）、<|ja|>（日语）
                - 包含情感标签：<|NEUTRAL|>（中性）、<|HAPPY|>（开心）、<|SAD|>（悲伤）
                - 实际文本内容
                
  timestamp     时间戳
  mode          识别模式

【语言标签】
  <|zh|>        中文（普通话）
  <|en|>        英文
  <|ja|>        日语
  <|ko|>        韩语
  <|yue|>       粤语

【情感标签】
  <|NEUTRAL|>   中性
  <|HAPPY|>     开心
  <|SAD|>       悲伤
  <|ANGRY|>     愤怒

================================================================================
【代码示例】
================================================================================

【Python 示例】
---
import asyncio
import websockets
import json

async def recognize_audio(audio_file_path):
    uri = "ws://localhost:10095"
    
    async with websockets.connect(uri) as websocket:
        # 1. 发送配置
        config = {
            "mode": "offline",
            "wav_name": "test_audio",
            "wav_format": "wav",
            "audio_fs": 16000,
            "is_speaking": True,
            "itn": True
        }
        await websocket.send(json.dumps(config))
        
        # 2. 发送音频数据
        with open(audio_file_path, 'rb') as f:
            audio_data = f.read()
            await websocket.send(audio_data)
        
        # 3. 发送结束标志
        end_msg = {"is_speaking": False}
        await websocket.send(json.dumps(end_msg))
        
        # 4. 接收结果
        result = await websocket.recv()
        data = json.loads(result)
        
        # 5. 解析文本（去除标签）
        text = data.get('text', '')
        # 移除语言和情感标签
        import re
        clean_text = re.sub(r'<\|[^|]+\|>', '', text)
        print(f"识别结果: {clean_text}")
        
        return clean_text

# 运行
asyncio.run(recognize_audio("test.wav"))
---

【JavaScript 示例】
---
const ws = new WebSocket('ws://localhost:10095');

ws.onopen = () => {
    console.log('连接成功');
    
    // 1. 发送配置
    const config = {
        mode: 'offline',
        wav_name: 'test_audio',
        wav_format: 'wav',
        audio_fs: 16000,
        is_speaking: true,
        itn: true
    };
    ws.send(JSON.stringify(config));
    
    // 2. 发送音频数据（假设已有 audioBlob）
    fetch('test.wav')
        .then(res => res.arrayBuffer())
        .then(buffer => {
            ws.send(buffer);
            
            // 3. 发送结束标志
            const endMsg = { is_speaking: false };
            ws.send(JSON.stringify(endMsg));
        });
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    let text = data.text || '';
    
    // 移除语言和情感标签
    text = text.replace(/<\|[^|]+\|>/g, '');
    console.log('识别结果:', text);
};

ws.onerror = (error) => {
    console.error('连接错误:', error);
};
---

【cURL 示例（不适用，WebSocket 需要专用客户端）】
注意：WebSocket 协议无法直接使用 cURL，需要使用 WebSocket 客户端库。

================================================================================
【注意事项】
================================================================================

1. 音频格式要求
   - 推荐使用 16kHz 采样率的 WAV 格式
   - 单声道音频效果最佳
   - 音频时长建议不超过 60 秒

2. 连接管理
   - 每次识别建议使用新的 WebSocket 连接
   - 识别完成后可以关闭连接或复用

3. 错误处理
   - 连接失败：检查服务是否运行在 10095 端口
   - 无识别结果：检查音频格式和采样率
   - 识别错误：查看服务日志

4. 性能优化
   - 批量识别时可以复用连接
   - 音频预处理：降噪、归一化可提升识别率

5. 标签处理
   - 语言标签和情感标签在文本开头
   - 使用正则表达式 `<\|[^|]+\|>` 可以移除所有标签
   - 保留标签可以获取语言和情感信息

================================================================================
【常见问题】
================================================================================

Q: 如何识别多语言混合的音频？
A: SenseVoice 自动检测语言，无需指定。结果中会包含语言标签。

Q: 如何获取情感信息？
A: 解析返回文本中的情感标签，如 <|HAPPY|>、<|SAD|> 等。

Q: 支持实时流式识别吗？
A: 支持，设置 mode 为 "online" 并分段发送音频数据。

Q: 识别准确率如何？
A: 中文场景下准确率较高，适合实时交互场景。

Q: 可以识别方言吗？
A: 支持粤语（<|yue|>），其他方言识别效果可能不佳。

================================================================================
【技术支持】
================================================================================

服务端口：10095
测试页面：test_sensevoice.html
日志位置：/workspace/models/sensevoice_noquant.log（容器内）

================================================================================

