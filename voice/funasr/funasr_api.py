# -*- coding: utf-8 -*-
"""
Author: SGA Team
Description: FunASR 语音识别 API 实现
支持 SenseVoice 和 Paraformer 模型的 WebSocket 调用
"""

import asyncio
import json
import os
import re
from common.log import logger

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("[FunASR] websockets module not installed. Please install it with: pip install websockets")


def speech_to_text_funasr(voice_file, funasr_url="ws://localhost:10095", model="sensevoice", 
                          enable_itn=True, hotwords="", audio_fs=16000):
    """
    使用 FunASR 模型进行语音识别
    
    参数:
    - voice_file (str): 语音文件的本地路径
    - funasr_url (str): FunASR WebSocket 服务地址
      - SenseVoice: ws://localhost:10095
      - Paraformer: ws://localhost:10096
    - model (str): 使用的模型，"sensevoice" 或 "paraformer"
    - enable_itn (bool): 是否启用逆文本归一化（ITN），默认 True
    - hotwords (str): 热词，用空格分隔（仅 Paraformer 支持）
    - audio_fs (int): 音频采样率，默认 16000 Hz
    
    返回值:
    - str: 识别到的文本，失败返回 None
    """
    if not WEBSOCKETS_AVAILABLE:
        logger.error("[FunASR] websockets module is not available")
        return None
    
    try:
        # 检查文件是否存在
        if not os.path.exists(voice_file):
            logger.error(f"[FunASR] Voice file not found: {voice_file}")
            return None
        
        # 获取文件格式
        file_ext = os.path.splitext(voice_file)[1].lower()
        wav_format = file_ext[1:] if file_ext else "wav"  # 去掉点号
        
        # 读取音频文件
        with open(voice_file, 'rb') as f:
            audio_data = f.read()
        
        logger.info(f"[FunASR] Using model: {model}, URL: {funasr_url}")
        logger.debug(f"[FunASR] Audio file: {voice_file}, format: {wav_format}, size: {len(audio_data)} bytes")
        
        # 使用 asyncio 运行异步识别
        result = asyncio.run(_recognize_async(
            funasr_url=funasr_url,
            audio_data=audio_data,
            wav_format=wav_format,
            audio_fs=audio_fs,
            enable_itn=enable_itn,
            hotwords=hotwords,
            model=model
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"[FunASR] Exception occurred: {e}")
        import traceback
        logger.debug(f"[FunASR] Traceback: {traceback.format_exc()}")
        return None


async def _recognize_async(funasr_url, audio_data, wav_format, audio_fs, enable_itn, hotwords, model):
    """
    异步执行 FunASR 识别
    """
    try:
        # 建立 WebSocket 连接
        async with websockets.connect(funasr_url, ping_interval=None) as websocket:
            logger.debug(f"[FunASR] WebSocket connected to {funasr_url}")
            
            # 1. 发送配置消息
            config = {
                "mode": "offline",
                "wav_name": f"audio_{int(asyncio.get_event_loop().time())}",
                "wav_format": wav_format,
                "audio_fs": audio_fs,
                "is_speaking": True,
                "itn": enable_itn
            }
            
            # Paraformer 支持热词
            if model.lower() == "paraformer" and hotwords:
                config["hotwords"] = hotwords
            
            logger.debug(f"[FunASR] Sending config: {config}")
            await websocket.send(json.dumps(config))
            
            # 2. 发送音频数据
            logger.debug(f"[FunASR] Sending audio data: {len(audio_data)} bytes")
            await websocket.send(audio_data)
            
            # 3. 发送结束标志
            end_msg = {"is_speaking": False}
            logger.debug(f"[FunASR] Sending end message: {end_msg}")
            await websocket.send(json.dumps(end_msg))
            
            # 4. 接收识别结果
            logger.debug("[FunASR] Waiting for recognition result...")
            result = await websocket.recv()
            data = json.loads(result)
            
            logger.debug(f"[FunASR] Received result: {data}")
            
            # 5. 解析文本
            text = data.get('text', '')
            
            if not text:
                logger.error("[FunASR] No text in recognition result")
                return None
            
            # SenseVoice 需要移除语言和情感标签
            if model.lower() == "sensevoice":
                # 移除标签：<|zh|><|NEUTRAL|>识别的文本 -> 识别的文本
                clean_text = re.sub(r'<\|[^|]+\|>', '', text)
                logger.info(f"[FunASR-SenseVoice] Recognition result: {clean_text}")
                return clean_text
            else:
                # Paraformer 直接返回纯文本
                logger.info(f"[FunASR-Paraformer] Recognition result: {text}")
                return text
                
    except websockets.exceptions.WebSocketException as e:
        logger.error(f"[FunASR] WebSocket error: {e}")
        logger.error(f"[FunASR] Please check if FunASR service is running at {funasr_url}")
        return None
    except Exception as e:
        logger.error(f"[FunASR] Async recognition error: {e}")
        import traceback
        logger.debug(f"[FunASR] Traceback: {traceback.format_exc()}")
        return None


def test_funasr():
    """
    测试函数，用于验证 FunASR 功能
    需要先启动 FunASR 服务
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python funasr_api.py <audio_file> [model]")
        print("  model: sensevoice (default) or paraformer")
        return
    
    audio_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "sensevoice"
    
    # 根据模型选择 URL
    if model.lower() == "paraformer":
        url = "ws://localhost:10096"
    else:
        url = "ws://localhost:10095"
    
    print(f"Testing FunASR with model: {model}")
    print(f"Audio file: {audio_file}")
    print(f"Service URL: {url}")
    print("-" * 50)
    
    result = speech_to_text_funasr(
        voice_file=audio_file,
        funasr_url=url,
        model=model,
        enable_itn=True,
        hotwords="人工智能 深度学习" if model.lower() == "paraformer" else ""
    )
    
    if result:
        print(f"✓ Recognition successful!")
        print(f"Result: {result}")
    else:
        print(f"✗ Recognition failed!")


if __name__ == "__main__":
    test_funasr()

