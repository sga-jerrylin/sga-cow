#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试特定图片链接的下载
"""

import sys
import os
import io
import requests
from urllib.parse import urlparse, unquote

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_specific_image_download():
    """测试特定的图片链接下载"""
    
    # 从截图中看到的实际链接
    test_url = "https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQGAAAAAgAoEACAQFr/original"
    
    print("🧪 测试特定图片链接下载")
    print("=" * 80)
    print(f"📸 测试链接: {test_url}")
    print()
    
    # 测试1: 基本连接测试
    print("🔍 步骤1: 测试基本连接")
    try:
        response = requests.head(test_url, timeout=30)
        print(f"   状态码: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'Unknown')}")
        print("   ✅ 基本连接成功")
    except Exception as e:
        print(f"   ❌ 基本连接失败: {e}")
        return False
    
    print()
    
    # 测试2: 完整下载测试
    print("🔍 步骤2: 测试完整下载")
    try:
        pic_res = requests.get(test_url, stream=True, timeout=30)
        pic_res.raise_for_status()
        
        image_storage = io.BytesIO()
        size = 0
        chunk_count = 0
        
        for block in pic_res.iter_content(1024):
            size += len(block)
            chunk_count += 1
            image_storage.write(block)
            
            # 显示进度（每100个chunk显示一次）
            if chunk_count % 100 == 0:
                print(f"   下载进度: {size} bytes ({chunk_count} chunks)")
        
        print(f"   ✅ 下载成功!")
        print(f"   总大小: {size} bytes")
        print(f"   总块数: {chunk_count}")
        
        # 验证数据
        image_storage.seek(0)
        data = image_storage.getvalue()
        print(f"   验证: BytesIO 大小 = {len(data)} bytes")
        
        # 检查是否是有效的图片数据
        if data.startswith(b'\x89PNG') or data.startswith(b'\xff\xd8\xff') or data.startswith(b'GIF'):
            print("   ✅ 检测到有效的图片格式")
        else:
            print(f"   ⚠️  未识别的文件格式，前16字节: {data[:16]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 下载失败: {e}")
        return False

def test_with_different_headers():
    """测试使用不同的请求头"""
    test_url = "https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQGAAAAAgAoEACAQFr/original"
    
    print("\n🔍 步骤3: 测试不同的请求头")
    
    headers_list = [
        {},  # 无特殊头
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
    ]
    
    for i, headers in enumerate(headers_list, 1):
        print(f"   测试 {i}: {headers}")
        try:
            response = requests.get(test_url, headers=headers, timeout=30)
            response.raise_for_status()
            print(f"   ✅ 成功 - 状态码: {response.status_code}, 大小: {len(response.content)} bytes")
            
            # 只测试第一个成功的就够了
            if response.status_code == 200:
                return True
                
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    return False

if __name__ == "__main__":
    success1 = test_specific_image_download()
    success2 = test_with_different_headers()
    
    print("\n" + "=" * 80)
    if success1 or success2:
        print("🎉 至少有一种方法可以成功下载图片!")
        print("💡 建议: 检查我们的代码实现是否有问题")
    else:
        print("💥 所有下载方法都失败了!")
        print("💡 建议: 可能是网络问题或者链接已失效")
