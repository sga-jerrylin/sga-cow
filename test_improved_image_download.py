#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试改进的图片下载功能
"""

import sys
import os
import io
import requests
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_improved_image_download():
    """测试改进的图片下载功能"""
    
    test_url = "https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQ6AAAAgAoEACAQFr/original"
    
    # 不同的请求头策略，用于绕过防盗链
    headers_strategies = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.alipay.com/',
            'Accept': 'image/*,*/*;q=0.8',
        },
        {
            'User-Agent': 'curl/7.68.0',
            'Accept': '*/*',
        }
    ]
    
    print("🧪 测试改进的图片下载功能")
    print("=" * 80)
    print(f"📸 测试链接: {test_url}")
    print()
    
    max_attempts = 3
    
    for attempt in range(max_attempts):
        # 选择请求头策略
        headers = headers_strategies[attempt % len(headers_strategies)]
        
        print(f"🔍 尝试 {attempt + 1}/{max_attempts}")
        print(f"   策略: {attempt % len(headers_strategies) + 1}")
        print(f"   User-Agent: {headers.get('User-Agent', 'None')}")
        print(f"   Referer: {headers.get('Referer', 'None')}")
        
        try:
            pic_res = requests.get(test_url, headers=headers, stream=True, timeout=30)
            pic_res.raise_for_status()
            
            image_storage = io.BytesIO()
            size = 0
            for block in pic_res.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            
            print(f"   ✅ 下载成功!")
            print(f"   状态码: {pic_res.status_code}")
            print(f"   Content-Type: {pic_res.headers.get('Content-Type', 'Unknown')}")
            print(f"   大小: {size} bytes")
            
            # 验证数据
            image_storage.seek(0)
            data = image_storage.getvalue()
            
            # 检查是否是有效的图片数据
            if data.startswith(b'\x89PNG'):
                print("   📸 检测到PNG格式")
            elif data.startswith(b'\xff\xd8\xff'):
                print("   📸 检测到JPEG格式")
            elif data.startswith(b'GIF'):
                print("   📸 检测到GIF格式")
            elif data.startswith(b'RIFF') and b'WEBP' in data[:20]:
                print("   📸 检测到WebP格式")
            else:
                print(f"   ⚠️  未识别的格式，前16字节: {data[:16]}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            if attempt < max_attempts - 1:
                print("   等待1秒后重试...")
                time.sleep(1)
    
    print("\n💥 所有尝试都失败了!")
    return False

if __name__ == "__main__":
    success = test_improved_image_download()
    
    print("\n" + "=" * 80)
    if success:
        print("🎉 改进的下载策略成功!")
        print("💡 现在应该可以正确下载和显示图片了")
    else:
        print("💥 改进的下载策略仍然失败!")
        print("💡 可能需要其他解决方案")
