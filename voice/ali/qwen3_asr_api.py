# -*- coding: utf-8 -*-
"""
Author: SGA Team
Description: Qwen3-ASR 语音识别 API 实现
基于阿里云百炼平台的 Qwen3-ASR 模型
"""

import os
from common.log import logger
from config import conf

try:
    import dashscope
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    logger.warning("[Qwen3-ASR] dashscope module not installed. Please install it with: pip install dashscope")


def speech_to_text_qwen3(voice_file, api_key=None, model="qwen3-asr-flash", language=None, enable_lid=True, enable_itn=False, stream=False):
    """
    使用 Qwen3-ASR 模型进行语音识别
    
    参数:
    - voice_file (str): 语音文件的本地路径
    - api_key (str): DashScope API Key，如果为None则从环境变量或配置中获取
    - model (str): 使用的模型，默认为 "qwen3-asr-flash"
    - language (str): 指定音频语种，如 "zh"、"en" 等，None 表示自动检测
    - enable_lid (bool): 是否启用语种识别，默认 True
    - enable_itn (bool): 是否启用逆文本归一化，默认 False
    - stream (bool): 是否使用流式输出，默认 False
    
    返回值:
    - str: 识别到的文本，失败返回 None
    """
    if not DASHSCOPE_AVAILABLE:
        logger.error("[Qwen3-ASR] dashscope module is not available")
        return None
    
    try:
        # 获取 API Key
        if api_key is None:
            api_key = conf().get("dashscope_api_key") or os.getenv("DASHSCOPE_API_KEY")
        
        if not api_key:
            logger.error("[Qwen3-ASR] API Key not found. Please set dashscope_api_key in config or DASHSCOPE_API_KEY environment variable")
            return None
        
        # 构建文件路径 (DashScope 需要 file:// 前缀)
        if not voice_file.startswith("file://"):
            # 获取绝对路径
            abs_path = os.path.abspath(voice_file)
            # Windows 系统路径处理
            if os.name == 'nt':
                # Windows: file://D:/path/to/file.wav
                file_url = f"file://{abs_path}"
            else:
                # Linux/macOS: file:///path/to/file.wav
                file_url = f"file://{abs_path}"
        else:
            file_url = voice_file
        
        logger.debug(f"[Qwen3-ASR] Processing file: {file_url}")
        
        # 构建消息
        messages = [
            {
                "role": "system",
                "content": [
                    {"text": ""},  # 可用于配置定制化识别的 Context
                ]
            },
            {
                "role": "user",
                "content": [
                    {"audio": file_url},
                ]
            }
        ]
        
        # 构建 ASR 选项
        asr_options = {
            "enable_lid": enable_lid,
            "enable_itn": enable_itn
        }
        
        # 如果指定了语种，添加到选项中
        if language:
            asr_options["language"] = language
        
        # 调用 API
        if stream:
            # 流式输出
            logger.debug("[Qwen3-ASR] Using streaming mode")
            response = dashscope.MultiModalConversation.call(
                api_key=api_key,
                model=model,
                messages=messages,
                result_format="message",
                asr_options=asr_options,
                stream=True
            )
            
            # 收集流式输出的文本
            full_text = ""
            for chunk in response:
                try:
                    text_chunk = chunk["output"]["choices"][0]["message"].content[0]["text"]
                    full_text += text_chunk
                    logger.debug(f"[Qwen3-ASR] Stream chunk: {text_chunk}")
                except (KeyError, IndexError, TypeError):
                    pass
            
            if full_text:
                logger.info(f"[Qwen3-ASR] Recognition result (streaming): {full_text}")
                return full_text
            else:
                logger.error("[Qwen3-ASR] No text recognized in streaming mode")
                return None
        else:
            # 非流式输出
            logger.debug("[Qwen3-ASR] Using non-streaming mode")
            response = dashscope.MultiModalConversation.call(
                api_key=api_key,
                model=model,
                messages=messages,
                result_format="message",
                asr_options=asr_options
            )
            
            # 解析响应
            if response.status_code == 200:
                try:
                    text = response["output"]["choices"][0]["message"].content[0]["text"]
                    logger.info(f"[Qwen3-ASR] Recognition result: {text}")
                    return text
                except (KeyError, IndexError, TypeError) as e:
                    logger.error(f"[Qwen3-ASR] Failed to parse response: {e}")
                    logger.debug(f"[Qwen3-ASR] Response: {response}")
                    return None
            else:
                logger.error(f"[Qwen3-ASR] API call failed with status code: {response.status_code}")
                logger.debug(f"[Qwen3-ASR] Response: {response}")
                return None
                
    except Exception as e:
        logger.error(f"[Qwen3-ASR] Exception occurred: {e}")
        import traceback
        logger.debug(f"[Qwen3-ASR] Traceback: {traceback.format_exc()}")
        return None


def test_qwen3_asr():
    """
    测试函数，用于验证 Qwen3-ASR 功能
    """
    # 测试音频文件 URL
    test_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"
    
    print("Testing Qwen3-ASR with online audio...")
    result = speech_to_text_qwen3(test_url)
    print(f"Result: {result}")


if __name__ == "__main__":
    test_qwen3_asr()

