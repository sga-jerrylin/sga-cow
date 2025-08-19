#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dify连接测试脚本
用于测试Dify服务的连接性和API端点
"""

import requests
import json
import os
from config import conf

def test_dify_connection():
    """测试Dify服务连接"""
    
    # 从配置读取参数
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    if not api_key:
        print("❌ 错误: 未配置dify_api_key")
        return False
    
    print(f"🔧 测试配置:")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   API Base: {api_base}")
    
    # 测试基本连接
    print(f"\n🌐 测试基本连接...")
    
    # 移除/v1后缀测试根路径
    base_url = api_base.replace('/v1', '').rstrip('/')
    test_urls = [
        base_url,
        f"{base_url}/health",
        f"{base_url}/ping", 
        f"{base_url}/status",
        api_base,
        f"{api_base}/health"
    ]
    
    for url in test_urls:
        try:
            print(f"   测试: {url}")
            response = requests.get(url, timeout=5)
            print(f"   状态码: {response.status_code}")
            if response.status_code < 500:
                print(f"   ✅ 连接成功")
                print(f"   响应: {response.text[:100]}...")
                return True
            else:
                print(f"   ❌ 服务错误")
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
    
    return False

def test_dify_chat():
    """测试Dify聊天API"""
    
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    print(f"\n💬 测试Dify聊天API...")
    
    url = f"{api_base}/chat-messages"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'inputs': {},
        'query': '你好',
        'response_mode': 'blocking',
        'conversation_id': '',
        'user': 'test_user'
    }
    
    try:
        print(f"   请求URL: {url}")
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ 聊天API正常")
            result = response.json()
            print(f"   响应: {result.get('answer', 'No answer')[:100]}...")
            return True
        else:
            print(f"   ❌ 聊天API失败")
            print(f"   错误: {response.text}")
            
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
    
    return False

def test_file_upload_endpoints():
    """测试文件上传端点"""
    
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    print(f"\n📁 测试文件上传端点...")
    
    # 创建测试图片
    test_image_path = "tmp/test_image.png"
    os.makedirs("tmp", exist_ok=True)
    
    # 1x1像素PNG
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with open(test_image_path, 'wb') as f:
        f.write(png_data)
    
    endpoints = [
        "/files/upload",
        "/file/upload",
        "/upload"
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    data = {'user': 'test_user'}
    
    for endpoint in endpoints:
        url = f"{api_base}{endpoint}"
        print(f"   测试端点: {url}")
        
        try:
            with open(test_image_path, 'rb') as f:
                files = {
                    'file': ('test.png', f, 'image/png')
                }
                
                response = requests.post(url, headers=headers, data=data, files=files, timeout=10)
                print(f"   状态码: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print("   ✅ 上传成功!")
                    try:
                        result = response.json()
                        print(f"   文件ID: {result.get('id', 'Unknown')}")
                        return True
                    except:
                        print(f"   响应: {response.text}")
                        return True
                else:
                    print(f"   ❌ 上传失败: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")
    
    # 清理
    try:
        os.remove(test_image_path)
    except:
        pass
    
    return False

if __name__ == "__main__":
    print("🚀 开始Dify服务测试")
    print("=" * 50)
    
    # 1. 测试基本连接
    connection_ok = test_dify_connection()
    
    if connection_ok:
        # 2. 测试聊天API
        chat_ok = test_dify_chat()
        
        # 3. 测试文件上传
        upload_ok = test_file_upload_endpoints()
        
        print(f"\n📊 测试结果:")
        print(f"   连接测试: {'✅' if connection_ok else '❌'}")
        print(f"   聊天API: {'✅' if chat_ok else '❌'}")
        print(f"   文件上传: {'✅' if upload_ok else '❌'}")
        
        if chat_ok and upload_ok:
            print(f"\n🎉 Dify服务完全正常!")
        elif chat_ok:
            print(f"\n⚠️ 聊天功能正常，但图像识别可能有问题")
        else:
            print(f"\n❌ Dify服务存在问题")
    else:
        print(f"\n❌ 无法连接到Dify服务，请检查配置和网络")
