#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试图片下载功能
"""

import sys
import os
import io
import requests
from urllib.parse import urlparse, unquote

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def _download_image(url):
    """下载图片并返回BytesIO对象"""
    try:
        print(f"🔄 开始下载图片: {url}")
        pic_res = requests.get(url, stream=True, timeout=30)
        pic_res.raise_for_status()
        image_storage = io.BytesIO()
        size = 0
        for block in pic_res.iter_content(1024):
            size += len(block)
            image_storage.write(block)
        print(f"✅ 图片下载成功, 大小: {size} bytes")
        image_storage.seek(0)
        return image_storage
    except Exception as e:
        print(f"❌ 图片下载失败: {e}")
        return None

def test_image_download():
    """测试图片下载功能"""
    
    # 测试图片URL
    test_urls = [
        # 一个简单的测试图片
        "https://httpbin.org/image/png",
        "https://httpbin.org/image/jpeg",
        # 如果上面的不可用，可以用这个
        "https://via.placeholder.com/150x150.png",
    ]
    
    print("🧪 测试图片下载功能")
    print("=" * 50)
    
    success_count = 0
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📸 测试 {i}: {url}")
        
        image_data = _download_image(url)
        
        if image_data:
            # 检查数据是否有效
            data_size = len(image_data.getvalue())
            if data_size > 0:
                print(f"✅ 成功下载图片，数据大小: {data_size} bytes")
                print(f"   数据类型: {type(image_data)}")
                print(f"   是否为BytesIO: {isinstance(image_data, io.BytesIO)}")
                success_count += 1
            else:
                print("❌ 下载的图片数据为空")
        else:
            print("❌ 图片下载失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {success_count}/{len(test_urls)} 成功")
    
    if success_count > 0:
        print("🎉 图片下载功能正常！")
        return True
    else:
        print("💥 图片下载功能异常！")
        return False

if __name__ == "__main__":
    test_image_download()
