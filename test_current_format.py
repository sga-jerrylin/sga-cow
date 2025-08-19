#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试当前格式的markdown解析
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.utils import parse_markdown_text

def test_current_format():
    """测试当前格式的markdown解析"""
    
    # 从最新日志中看到的实际内容
    test_content = "已为您生成柱状图，请查看：![](https://mdn.alipayobjects.com/one_clip/afts/img/-pV6QoJrMPMAAAAARQAAAAgAoEACAQFr/original)"
    
    print("🧪 测试当前格式的Markdown解析")
    print("=" * 80)
    print("📝 输入内容:")
    print(repr(test_content))
    print()
    print("📝 输入内容（格式化）:")
    print(test_content)
    print()
    
    # 解析markdown
    print("🔍 解析结果:")
    try:
        parsed_result = parse_markdown_text(test_content)
        print(f"   类型: {type(parsed_result)}")
        print(f"   长度: {len(parsed_result) if isinstance(parsed_result, list) else 'N/A'}")
        print()
        
        if isinstance(parsed_result, list):
            for i, item in enumerate(parsed_result):
                print(f"   项目 {i+1}:")
                print(f"     类型: {item.get('type', 'Unknown')}")
                print(f"     内容: {repr(item.get('content', 'No content'))}")
                print()
        else:
            print(f"   结果: {parsed_result}")
            
        return parsed_result
        
    except Exception as e:
        print(f"   ❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_image_download():
    """测试新链接的下载"""
    import requests
    import io
    
    test_url = "https://mdn.alipayobjects.com/one_clip/afts/img/-pV6QoJrMPMAAAAARQAAAAgAoEACAQFr/original"
    
    print("🧪 测试新链接的下载")
    print("=" * 80)
    print(f"📸 测试链接: {test_url}")
    print()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    
    try:
        print("🔍 尝试下载...")
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
        print(f"   ❌ 下载失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试...")
    
    # 测试解析
    result = test_current_format()
    
    print("\n" + "="*80 + "\n")
    
    # 测试下载
    download_success = test_image_download()
    
    print("\n" + "="*80)
    
    if result and download_success:
        print("🎉 解析和下载都成功!")
        print("💡 问题可能在其他地方")
    elif result:
        print("🎉 解析成功，但下载失败!")
        print("💡 需要检查下载逻辑")
    elif download_success:
        print("🎉 下载成功，但解析失败!")
        print("💡 需要检查解析逻辑")
    else:
        print("💥 解析和下载都失败!")
        print("💡 需要全面检查")
