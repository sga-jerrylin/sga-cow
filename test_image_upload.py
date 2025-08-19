#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试图像上传功能
按照Dify官方API文档格式测试
"""

import requests
import json
import os
from config import load_config, conf

# 加载配置
load_config()

def test_image_upload():
    """测试图像上传功能"""
    
    # 从配置读取参数
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    if not api_key:
        print("❌ 错误: 未配置dify_api_key")
        return False
    
    print(f"🔧 测试配置:")
    print(f"   API Key: {api_key[:10]}...")
    print(f"   API Base: {api_base}")
    
    # 创建测试图片
    test_image_path = "tmp/test_upload.png"
    os.makedirs("tmp", exist_ok=True)
    
    # 创建一个简单的PNG图片 (1x1像素)
    png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
    
    with open(test_image_path, 'wb') as f:
        f.write(png_data)
    
    print(f"📁 创建测试图片: {test_image_path} ({len(png_data)} bytes)")
    
    # 按照官方文档格式测试
    url = f"{api_base}/files/upload"
    print(f"🌐 上传URL: {url}")
    
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    # 按照文档格式准备数据
    data = {
        'user': 'test_user_123'
    }
    
    try:
        with open(test_image_path, 'rb') as f:
            files = {
                'file': ('test_upload.png', f, 'image/png')
            }
            
            print(f"📤 开始上传...")
            print(f"   Headers: {headers}")
            print(f"   Data: {data}")
            print(f"   Files: test_upload.png (image/png)")
            
            response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
            
            print(f"📥 响应结果:")
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            if response.status_code in [200, 201]:
                print("   ✅ 上传成功!")
                try:
                    result = response.json()
                    print(f"   响应数据:")
                    print(f"     ID: {result.get('id')}")
                    print(f"     名称: {result.get('name')}")
                    print(f"     大小: {result.get('size')} bytes")
                    print(f"     扩展名: {result.get('extension')}")
                    print(f"     MIME类型: {result.get('mime_type')}")
                    print(f"     创建时间: {result.get('created_at')}")
                    return True
                except Exception as e:
                    print(f"   ⚠️ 解析响应失败: {e}")
                    print(f"   原始响应: {response.text}")
                    return True
            else:
                print(f"   ❌ 上传失败")
                print(f"   错误内容: {response.text}")
                
                # 分析常见错误
                if response.status_code == 400:
                    print(f"   💡 可能原因: 请求参数错误")
                elif response.status_code == 401:
                    print(f"   💡 可能原因: API Key无效")
                elif response.status_code == 413:
                    print(f"   💡 可能原因: 文件太大")
                elif response.status_code == 415:
                    print(f"   💡 可能原因: 不支持的文件类型")
                elif response.status_code >= 500:
                    print(f"   💡 可能原因: Dify服务器错误")
                    
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ 连接错误: {e}")
        print(f"   💡 请检查Dify服务是否正常运行")
    except requests.exceptions.Timeout as e:
        print(f"   ❌ 超时错误: {e}")
    except Exception as e:
        print(f"   ❌ 其他错误: {e}")
    
    finally:
        # 清理测试文件
        try:
            os.remove(test_image_path)
            print(f"🗑️ 清理测试文件")
        except:
            pass
    
    return False

def test_chat_with_image():
    """测试带图片的聊天"""
    
    api_key = conf().get("dify_api_key", "")
    api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
    
    print(f"\n💬 测试带图片的聊天...")
    
    # 先上传图片
    print(f"1. 上传测试图片...")
    if not test_image_upload():
        print(f"   ❌ 图片上传失败，跳过聊天测试")
        return False
    
    # 这里应该使用上传成功的文件ID进行聊天测试
    # 但由于我们的测试是独立的，这里只是演示流程
    print(f"2. 发送带图片的消息...")
    print(f"   💡 需要先成功上传图片获取file_id")
    
    return True

if __name__ == "__main__":
    print("🚀 开始图像上传测试")
    print("=" * 50)
    
    # 测试图像上传
    upload_ok = test_image_upload()
    
    if upload_ok:
        print(f"\n🎉 图像上传测试成功!")
        print(f"💡 现在可以在企业微信中发送图片测试图像识别功能")
    else:
        print(f"\n❌ 图像上传测试失败")
        print(f"💡 请检查:")
        print(f"   1. Dify服务是否正常运行")
        print(f"   2. API Key是否正确")
        print(f"   3. API Base URL是否正确")
        print(f"   4. 网络连接是否正常")
