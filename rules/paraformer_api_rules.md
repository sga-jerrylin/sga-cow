================================================================================
                    Paraformer API 调用规则文档
================================================================================

【服务信息】
  服务名称：Paraformer-Large 高精度中文语音识别服务
  服务端口：10096
  连接地址：ws://localhost:10096
  协议类型：WebSocket
  模型特性：高精度中文识别 + VAD + 标点恢复 + ITN + 语言模型

【性能指标】
  字错误率（CER）：1.95%
  适用场景：会议记录、文件转写、高精度转录

================================================================================
【调用流程】
================================================================================

1. 建立 WebSocket 连接
   ws://localhost:10096

2. 发送配置消息（JSON 格式）
   {
     "mode": "offline",           // 识别模式：offline（离线）或 online（在线）
     "wav_name": "meeting_001",   // 音频文件名（任意字符串）
     "wav_format": "wav",         // 音频格式：wav, pcm 等
     "audio_fs": 16000,           // 采样率：16000 Hz（推荐）
     "is_speaking": true,         // 是否正在说话：true
     "itn": true,                 // 是否启用逆文本归一化：true/false
     "hotwords": ""               // 热词（可选）：用空格分隔的词语
   }

3. 发送音频数据（Binary 格式）
   - 直接发送音频文件的二进制数据
   - 支持格式：WAV, PCM
   - 推荐采样率：16000 Hz
   - 推荐声道：单声道

4. 发送结束标志（JSON 格式）
   {
     "is_speaking": false         // 标记音频发送完毕
   }

5. 接收识别结果（JSON 格式）
   {
     "text": "这是识别的文本内容，包含标点符号。",
     "timestamp": "...",
     "mode": "offline"
   }

================================================================================
【参数说明】
================================================================================

【请求参数】
  mode          识别模式
                - offline: 离线模式，等待完整音频后识别（推荐）
                - online: 在线模式，实时流式识别
                
  wav_name      音频标识符
                - 任意字符串，用于标识本次识别
                - 建议格式：meeting_timestamp 或 filename
                
  wav_format    音频格式
                - wav: WAV 格式（推荐）
                - pcm: 原始 PCM 数据
                
  audio_fs      采样率（Hz）
                - 16000: 16kHz（推荐，模型训练采样率）
                - 8000: 8kHz（电话音质，识别率可能下降）
                
  is_speaking   说话状态
                - true: 开始发送音频
                - false: 音频发送完毕
                
  itn           逆文本归一化
                - true: 启用（"一千二百三十四" → "1234"）
                - false: 禁用（保持文字形式）
                
  hotwords      热词（可选）
                - 用空格分隔的词语，如 "人工智能 深度学习 神经网络"
                - 提高特定词汇的识别准确率
                - 适用于专业术语、人名、地名等

【响应字段】
  text          识别文本
                - 自动添加标点符号（逗号、句号、问号等）
                - 如果启用 ITN，数字会转换为阿拉伯数字
                - 纯中文文本，无额外标签
                
  timestamp     时间戳（如果有）
  mode          识别模式

【VAD（语音活动检测）】
  - 自动检测音频中的语音段
  - 过滤静音和噪音
  - 提高识别效率和准确率

【标点恢复】
  - 自动添加标点符号
  - 支持：逗号、句号、问号、感叹号等
  - 基于 CT-Transformer 模型

【ITN（逆文本归一化）】
  - 数字转换：一千二百三十四 → 1234
  - 日期转换：二零二三年十月二十八日 → 2023年10月28日
  - 时间转换：下午三点半 → 15:30
  - 货币转换：一百二十三元 → 123元

【语言模型】
  - N-gram 语言模型
  - 提升识别准确率
  - 优化词序和语法

================================================================================
【代码示例】
================================================================================

【Python 示例】
---
import asyncio
import websockets
import json

async def recognize_audio(audio_file_path, hotwords=None):
    uri = "ws://localhost:10096"
    
    async with websockets.connect(uri) as websocket:
        # 1. 发送配置
        config = {
            "mode": "offline",
            "wav_name": "meeting_audio",
            "wav_format": "wav",
            "audio_fs": 16000,
            "is_speaking": True,
            "itn": True,
            "hotwords": hotwords or ""
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
        
        # 5. 获取文本
        text = data.get('text', '')
        print(f"识别结果: {text}")
        
        return text

# 运行示例
asyncio.run(recognize_audio("meeting.wav"))

# 使用热词
asyncio.run(recognize_audio("meeting.wav", hotwords="人工智能 深度学习"))
---

【JavaScript 示例】
---
const ws = new WebSocket('ws://localhost:10096');

ws.onopen = () => {
    console.log('连接成功');
    
    // 1. 发送配置
    const config = {
        mode: 'offline',
        wav_name: 'meeting_audio',
        wav_format: 'wav',
        audio_fs: 16000,
        is_speaking: true,
        itn: true,
        hotwords: '人工智能 深度学习 神经网络'
    };
    ws.send(JSON.stringify(config));
    
    // 2. 发送音频数据
    fetch('meeting.wav')
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
    const text = data.text || '';
    console.log('识别结果:', text);
};

ws.onerror = (error) => {
    console.error('连接错误:', error);
};
---

【批量识别示例（Python）】
---
import asyncio
import websockets
import json
import os

async def batch_recognize(audio_files):
    uri = "ws://localhost:10096"
    results = []
    
    for audio_file in audio_files:
        async with websockets.connect(uri) as websocket:
            # 配置
            config = {
                "mode": "offline",
                "wav_name": os.path.basename(audio_file),
                "wav_format": "wav",
                "audio_fs": 16000,
                "is_speaking": True,
                "itn": True
            }
            await websocket.send(json.dumps(config))
            
            # 音频数据
            with open(audio_file, 'rb') as f:
                await websocket.send(f.read())
            
            # 结束标志
            await websocket.send(json.dumps({"is_speaking": False}))
            
            # 接收结果
            result = await websocket.recv()
            data = json.loads(result)
            results.append({
                'file': audio_file,
                'text': data.get('text', '')
            })
            
            print(f"[{audio_file}] {data.get('text', '')}")
    
    return results

# 批量识别
files = ['meeting1.wav', 'meeting2.wav', 'meeting3.wav']
asyncio.run(batch_recognize(files))
---

================================================================================
【高级功能】
================================================================================

【热词使用技巧】
  1. 专业术语
     hotwords: "人工智能 机器学习 深度学习 神经网络"
     
  2. 人名地名
     hotwords: "张三 李四 北京 上海"
     
  3. 公司产品
     hotwords: "阿里巴巴 腾讯 华为 小米"
     
  4. 注意事项
     - 热词之间用空格分隔
     - 不要添加过多热词（建议 10-20 个）
     - 热词应该是完整的词语，不是字符

【流式识别（Online 模式）】
  - 设置 mode 为 "online"
  - 分段发送音频数据（每段 1-2 秒）
  - 每段发送后会返回中间结果
  - 最后发送 is_speaking: false 获取最终结果

【长音频处理】
  - 建议将长音频切分为多段（每段 30-60 秒）
  - 分别识别后拼接结果
  - 避免单次识别超过 5 分钟

================================================================================
【注意事项】
================================================================================

1. 音频格式要求
   - 必须使用 16kHz 采样率（8kHz 会降低准确率）
   - 单声道音频效果最佳
   - WAV 格式推荐使用 PCM 编码

2. 识别准确率优化
   - 使用高质量音频（清晰、无噪音）
   - 合理使用热词功能
   - 启用 ITN 可以提高数字识别准确率

3. 连接管理
   - 每次识别建议使用新的连接
   - 批量识别时可以复用连接
   - 识别完成后及时关闭连接

4. 错误处理
   - 连接失败：检查服务是否运行在 10096 端口
   - 识别超时：检查音频是否过长
   - 无结果：检查音频格式和采样率

5. 性能考虑
   - 服务占用约 4.8GB 内存
   - 单次识别时间取决于音频长度
   - 并发识别受限于 decoder-thread-num（当前为 10）

================================================================================
【与 SenseVoice 的区别】
================================================================================

【Paraformer】
  ✓ 高精度中文识别（CER 1.95%）
  ✓ 自动标点恢复
  ✓ ITN 数字转换
  ✓ 热词支持
  ✓ 语言模型优化
  ✓ 适合会议、转写等高精度场景
  ✗ 仅支持中文
  ✗ 无情感识别

【SenseVoice】
  ✓ 多语言支持（中英日韩粤）
  ✓ 情感识别
  ✓ 自动语言检测
  ✓ 适合实时交互场景
  ✗ 准确率略低于 Paraformer
  ✗ 无热词支持

【选择建议】
  - 高精度中文转写 → Paraformer
  - 多语言场景 → SenseVoice
  - 需要情感分析 → SenseVoice
  - 会议记录 → Paraformer
  - 实时对话 → SenseVoice

================================================================================
【常见问题】
================================================================================

Q: 为什么识别结果没有标点符号？
A: 检查是否启用了标点恢复功能（PUNC 模型已加载）。

Q: 数字识别不准确怎么办？
A: 启用 ITN 功能（itn: true），并确保音频清晰。

Q: 如何提高专业术语的识别率？
A: 使用 hotwords 参数添加专业术语。

Q: 支持英文识别吗？
A: Paraformer 主要针对中文优化，英文识别效果一般。建议使用 SenseVoice。

Q: 可以识别方言吗？
A: Paraformer 针对普通话优化，方言识别效果不佳。

Q: 识别速度如何？
A: 取决于音频长度和服务器性能。通常 1 分钟音频需要 5-10 秒处理。

================================================================================
【技术支持】
================================================================================

服务端口：10096
测试页面：test_paraformer.html
日志位置：/workspace/models/paraformer_v3.log（容器内）

模型组件：
  - ASR: Paraformer-Large (843MB)
  - VAD: FSMN-VAD (495KB)
  - PUNC: CT-Transformer (965MB)
  - ITN: FST (868KB)
  - LM: N-gram (915MB)

================================================================================

