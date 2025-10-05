#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qwen3-ASR 测试脚本

使用方法:
1. 确保已安装 dashscope: pip install dashscope
2. 配置 API Key 在 config.json 或环境变量中
3. 运行: python test_qwen3_asr.py
"""

import os
import sys

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from voice.ali.qwen3_asr_api import speech_to_text_qwen3
from common.log import logger


def test_online_audio():
    """
    测试在线音频文件
    """
    print("\n" + "="*60)
    print("测试 1: 在线音频文件识别")
    print("="*60)
    
    # 阿里云提供的测试音频
    test_url = "https://dashscope.oss-cn-beijing.aliyuncs.com/audios/welcome.mp3"
    
    print(f"音频 URL: {test_url}")
    print("开始识别...")
    
    result = speech_to_text_qwen3(test_url)
    
    if result:
        print(f"✅ 识别成功!")
        print(f"识别结果: {result}")
    else:
        print("❌ 识别失败")
    
    return result is not None


def test_local_audio(audio_file):
    """
    测试本地音频文件
    
    :param audio_file: 本地音频文件路径
    """
    print("\n" + "="*60)
    print("测试 2: 本地音频文件识别")
    print("="*60)
    
    if not os.path.exists(audio_file):
        print(f"❌ 文件不存在: {audio_file}")
        return False
    
    print(f"音频文件: {audio_file}")
    print("开始识别...")
    
    result = speech_to_text_qwen3(audio_file)
    
    if result:
        print(f"✅ 识别成功!")
        print(f"识别结果: {result}")
    else:
        print("❌ 识别失败")
    
    return result is not None


def test_with_language(audio_file, language):
    """
    测试指定语种识别
    
    :param audio_file: 音频文件路径
    :param language: 语种代码，如 "zh", "en"
    """
    print("\n" + "="*60)
    print(f"测试 3: 指定语种识别 (language={language})")
    print("="*60)
    
    print(f"音频文件: {audio_file}")
    print(f"指定语种: {language}")
    print("开始识别...")
    
    result = speech_to_text_qwen3(audio_file, language=language)
    
    if result:
        print(f"✅ 识别成功!")
        print(f"识别结果: {result}")
    else:
        print("❌ 识别失败")
    
    return result is not None


def test_with_itn(audio_file):
    """
    测试启用逆文本归一化（ITN）
    
    :param audio_file: 音频文件路径
    """
    print("\n" + "="*60)
    print("测试 4: 启用逆文本归一化 (ITN)")
    print("="*60)
    
    print(f"音频文件: {audio_file}")
    print("ITN: 启用")
    print("开始识别...")
    
    result = speech_to_text_qwen3(audio_file, enable_itn=True)
    
    if result:
        print(f"✅ 识别成功!")
        print(f"识别结果: {result}")
    else:
        print("❌ 识别失败")
    
    return result is not None


def test_streaming(audio_file):
    """
    测试流式输出
    
    :param audio_file: 音频文件路径
    """
    print("\n" + "="*60)
    print("测试 5: 流式输出")
    print("="*60)
    
    print(f"音频文件: {audio_file}")
    print("流式模式: 启用")
    print("开始识别...")
    
    result = speech_to_text_qwen3(audio_file, stream=True)
    
    if result:
        print(f"✅ 识别成功!")
        print(f"识别结果: {result}")
    else:
        print("❌ 识别失败")
    
    return result is not None


def check_environment():
    """
    检查运行环境
    """
    print("\n" + "="*60)
    print("环境检查")
    print("="*60)
    
    # 检查 dashscope 模块
    try:
        import dashscope
        print("✅ dashscope 模块已安装")
        print(f"   版本: {dashscope.__version__ if hasattr(dashscope, '__version__') else '未知'}")
    except ImportError:
        print("❌ dashscope 模块未安装")
        print("   请运行: pip install dashscope")
        return False
    
    # 检查 API Key
    from config import conf
    api_key = conf().get("dashscope_api_key") or os.getenv("DASHSCOPE_API_KEY")
    
    if api_key:
        print("✅ API Key 已配置")
        print(f"   Key: {api_key[:10]}...{api_key[-5:] if len(api_key) > 15 else ''}")
    else:
        print("❌ API Key 未配置")
        print("   请在 config.json 中设置 dashscope_api_key")
        print("   或设置环境变量 DASHSCOPE_API_KEY")
        return False
    
    return True


def main():
    """
    主测试函数
    """
    print("\n" + "="*60)
    print("Qwen3-ASR 语音识别测试")
    print("="*60)
    
    # 环境检查
    if not check_environment():
        print("\n❌ 环境检查失败，请先配置环境")
        return
    
    # 测试计数
    total_tests = 0
    passed_tests = 0
    
    # 测试 1: 在线音频
    total_tests += 1
    if test_online_audio():
        passed_tests += 1
    
    # 如果有本地测试文件，进行更多测试
    test_audio = "test_audio.wav"  # 可以替换为实际的测试文件路径
    
    if os.path.exists(test_audio):
        # 测试 2: 本地音频
        total_tests += 1
        if test_local_audio(test_audio):
            passed_tests += 1
        
        # 测试 3: 指定语种
        total_tests += 1
        if test_with_language(test_audio, "zh"):
            passed_tests += 1
        
        # 测试 4: ITN
        total_tests += 1
        if test_with_itn(test_audio):
            passed_tests += 1
        
        # 测试 5: 流式输出
        total_tests += 1
        if test_streaming(test_audio):
            passed_tests += 1
    else:
        print(f"\n💡 提示: 如需测试本地文件，请将音频文件命名为 {test_audio} 并放在当前目录")
    
    # 测试总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过!")
    else:
        print(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败")


if __name__ == "__main__":
    main()

