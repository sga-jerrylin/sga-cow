#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dify文件上传测试脚本
用于测试图像识别功能的文件上传API
"""

import requests
import json
import os
from config import conf, load_config

def test_dify_file_upload():
    """测试Dify文件上传功能"""

    # 加载配置
    load_config()

    # 从配置读取参数
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    if not api_key:
        print("❌ 错误: 未配置dify_api_key")
        return False
    
    print(f"🔧 测试配置:")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   API Base: {api_base}")
    
    # 创建测试图片文件
    test_image_path = "tmp/test_image.png"
    os.makedirs("tmp", exist_ok=True)
    
    # 创建一个简单的1x1像素PNG图片
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with open(test_image_path, 'wb') as f:
        f.write(png_data)
    
    print(f"📁 创建测试图片: {test_image_path}")
    
    # 测试不同的API端点
    endpoints_to_test = [
        "/files/upload",
        "/file/upload", 
        "/upload",
        "/api/files/upload"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🧪 测试端点: {endpoint}")
        
        url = f"{api_base.rstrip('/')}{endpoint}"
        print(f"   完整URL: {url}")
        
        headers = {
            'Authorization': f'Bearer {api_key}'
        }
        
        data = {'user': 'test_user'}
        
        try:
            with open(test_image_path, 'rb') as f:
                files = {
                    'file': ('test_image.png', f, 'image/png')
                }
                
                response = requests.post(url, headers=headers, data=data, files=files, timeout=10)
                
                print(f"   状态码: {response.status_code}")
                print(f"   响应头: {dict(response.headers)}")
                
                if response.status_code == 200 or response.status_code == 201:
                    print("   ✅ 上传成功!")
                    try:
                        result = response.json()
                        print(f"   响应数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return True
                    except:
                        print(f"   响应内容: {response.text}")
                        return True
                else:
                    print(f"   ❌ 上传失败")
                    print(f"   错误内容: {response.text}")
                    
        except requests.exceptions.ConnectionError as e:
            print(f"   ❌ 连接错误: {e}")
        except requests.exceptions.Timeout as e:
            print(f"   ❌ 超时错误: {e}")
        except Exception as e:
            print(f"   ❌ 其他错误: {e}")
    
    # 清理测试文件
    try:
        os.remove(test_image_path)
        print(f"\n🗑️ 清理测试文件: {test_image_path}")
    except:
        pass
    
    return False

def test_dify_health():
    """测试Dify服务健康状态"""
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    print(f"\n🏥 测试Dify服务健康状态")
    print(f"   API Base: {api_base}")
    
    # 测试不同的健康检查端点
    health_endpoints = [
        "",
        "/health",
        "/ping",
        "/status"
    ]
    
    for endpoint in health_endpoints:
        url = f"{api_base.rstrip('/')}{endpoint}"
        print(f"\n   测试: {url}")
        
        try:
            response = requests.get(url, timeout=5)
            print(f"   状态码: {response.status_code}")
            if response.status_code < 500:
                print(f"   ✅ 服务可访问")
                print(f"   响应: {response.text[:200]}...")
                return True
            else:
                print(f"   ❌ 服务错误: {response.text}")
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 开始Dify文件上传测试")
    print("=" * 50)
    
    # 测试服务健康状态
    health_ok = test_dify_health()
    
    if health_ok:
        # 测试文件上传
        upload_ok = test_dify_file_upload()
        
        if upload_ok:
            print("\n🎉 测试完成: 文件上传功能正常")
        else:
            print("\n❌ 测试完成: 文件上传功能异常")
    else:
        print("\n❌ 测试完成: Dify服务不可访问")
