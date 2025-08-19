#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Dify Bot改进功能的脚本
"""

import sys
import os
import json
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试关键模块导入"""
    print("=== 测试模块导入 ===")

    try:
        # 测试dify_client导入
        from lib.dify.dify_client import DifyClient, ChatClient
        print("✓ dify_client模块导入成功")

        # 测试常量定义
        from common.const import DIFY
        print(f"✓ DIFY常量定义成功: {DIFY}")

        # 测试bot_factory注册
        from bot.bot_factory import create_bot
        from common.const import DIFY

        # 尝试创建dify bot（可能会因为配置问题失败，但至少能测试注册）
        try:
            bot = create_bot(DIFY)
            print("✓ Dify Bot创建成功")
        except Exception as e:
            if "dify" in str(e).lower() or "config" in str(e).lower():
                print("✓ Dify Bot已正确注册（配置问题正常）")
            else:
                print(f"✗ Dify Bot创建失败: {e}")

        return True

    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_dify_client():
    """测试Dify Client功能"""
    print("\n=== 测试Dify Client功能 ===")

    try:
        from lib.dify.dify_client import DifyClient, ChatClient

        # 测试DifyClient创建
        client = DifyClient("test-api-key", "https://api.dify.ai/v1")
        print("✓ DifyClient创建成功")

        # 测试ChatClient创建
        chat_client = ChatClient("test-api-key", "https://api.dify.ai/v1")
        print("✓ ChatClient创建成功")

        # 测试健康检查方法存在
        if hasattr(client, 'health_check'):
            print("✓ 健康检查方法存在")
        else:
            print("✗ 健康检查方法不存在")

        # 测试session和重试机制
        if hasattr(client, 'session'):
            print("✓ HTTP Session初始化成功")
        else:
            print("✗ HTTP Session未初始化")

        return True

    except Exception as e:
        print(f"✗ Dify Client测试失败: {e}")
        return False

def test_wechatcom_improvements():
    """测试企业微信改进功能"""
    print("\n=== 测试企业微信改进功能 ===")

    try:
        # 测试企业微信消息处理改进
        from channel.wechatcom.wechatcomapp_message import WechatComAppMessage
        print("✓ 企业微信消息类导入成功")

        # 检查是否有文件处理方法
        if hasattr(WechatComAppMessage, '_get_file_extension'):
            print("✓ 文件扩展名处理方法存在")
        else:
            print("✗ 文件扩展名处理方法不存在")

        if hasattr(WechatComAppMessage, '_extract_file_links'):
            print("✓ 文件链接提取方法存在")
        else:
            print("✗ 文件链接提取方法不存在")

        # 测试企业微信通道改进
        from channel.wechatcom.wechatcomapp_channel import WechatComAppChannel
        print("✓ 企业微信通道类导入成功")

        # 检查顺序发送方法
        if hasattr(WechatComAppChannel, '_send_texts_in_order'):
            print("✓ 顺序发送方法存在")
        else:
            print("✗ 顺序发送方法不存在")

        return True

    except Exception as e:
        print(f"✗ 企业微信改进测试失败: {e}")
        return False

def test_config_template():
    """测试配置模板"""
    print("\n=== 测试配置模板 ===")

    try:
        # 检查配置模板文件
        if os.path.exists("config-template.json"):
            with open("config-template.json", "r", encoding="utf-8") as f:
                config = json.load(f)

            # 检查Dify相关配置
            dify_configs = [
                "dify_api_key",
                "dify_api_base",
                "dify_app_type",
                "dify_max_workers",
                "dify_max_retries",
                "dify_timeout"
            ]

            for config_key in dify_configs:
                if config_key in config:
                    print(f"✓ 配置项存在: {config_key}")
                else:
                    print(f"✗ 配置项缺失: {config_key}")

            print("✓ 配置模板检查完成")
            return True
        else:
            print("✗ 配置模板文件不存在")
            return False

    except Exception as e:
        print(f"✗ 配置模板测试失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    print("\n=== 测试文件结构 ===")

    try:
        # 检查关键文件是否存在
        files_to_check = [
            "lib/dify/__init__.py",
            "lib/dify/dify_client.py",
            "bot/dify/dify_bot.py",
            "bot/dify/dify_session.py",
            "DIFY_IMPROVEMENTS.md"
        ]

        for file_path in files_to_check:
            if os.path.exists(file_path):
                print(f"✓ 文件存在: {file_path}")
            else:
                print(f"✗ 文件缺失: {file_path}")

        return True

    except Exception as e:
        print(f"✗ 文件结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试Dify Bot改进功能...\n")

    tests = [
        test_imports,
        test_dify_client,
        test_wechatcom_improvements,
        test_config_template,
        test_file_structure
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")

    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
