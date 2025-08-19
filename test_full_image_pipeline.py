#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试完整的图片处理流程
"""

import sys
import os
import io
import requests
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.utils import parse_markdown_text
from bridge.reply import Reply, ReplyType

def test_full_pipeline():
    """测试完整的图片处理流程"""
    
    # 模拟Dify返回的不同格式
    test_cases = [
        {
            "name": "格式1 - 带前缀文字",
            "content": "已为您生成柱状图，请查看：![](https://mdn.alipayobjects.com/one_clip/afts/img/-pV6QoJrMPMAAAAARQAAAAgAoEACAQFr/original)"
        },
        {
            "name": "格式2 - 多行带图片",
            "content": "我已经为您生成了柱状图，请查看以下图片:\n\n![](https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQ6AAAAgAoEACAQFr/original)"
        },
        {
            "name": "格式3 - 纯图片",
            "content": "![](https://mdn.alipayobjects.com/one_clip/afts/img/-pV6QoJrMPMAAAAARQAAAAgAoEACAQFr/original)"
        }
    ]
    
    print("🧪 测试完整的图片处理流程")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 测试用例 {i}: {test_case['name']}")
        print(f"内容: {repr(test_case['content'])}")
        print()
        
        # 步骤1: 解析markdown
        print("🔍 步骤1: 解析Markdown")
        try:
            parsed_content = parse_markdown_text(test_case['content'])
            print(f"   解析结果: {parsed_content}")
            
            # 查找图片项
            image_items = [item for item in parsed_content if item.get('type') == 'image']
            if image_items:
                print(f"   找到 {len(image_items)} 个图片项")
                for j, img_item in enumerate(image_items):
                    print(f"   图片 {j+1}: {img_item['content']}")
            else:
                print("   ❌ 没有找到图片项")
                continue
                
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
            continue
        
        # 步骤2: 测试图片下载
        print("\n🔍 步骤2: 测试图片下载")
        for j, img_item in enumerate(image_items):
            url = img_item['content']
            print(f"   图片 {j+1}: {url}")
            
            success = test_image_download_with_strategies(url)
            if success:
                print(f"   ✅ 图片 {j+1} 下载成功")
            else:
                print(f"   ❌ 图片 {j+1} 下载失败")
        
        print("\n" + "-" * 60)

def test_image_download_with_strategies(url):
    """使用多种策略测试图片下载"""
    
    # 不同的请求头策略
    strategies = [
        {
            "name": "Chrome浏览器",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            }
        },
        {
            "name": "Safari浏览器",
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.alipay.com/',
                'Accept': 'image/*,*/*;q=0.8',
            }
        },
        {
            "name": "简单请求",
            "headers": {
                'User-Agent': 'curl/7.68.0',
                'Accept': '*/*',
            }
        }
    ]
    
    for strategy in strategies:
        try:
            print(f"     尝试策略: {strategy['name']}")
            response = requests.get(url, headers=strategy['headers'], stream=True, timeout=30)
            response.raise_for_status()
            
            # 下载数据
            image_storage = io.BytesIO()
            size = 0
            for block in response.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            
            print(f"     ✅ 成功! 状态码: {response.status_code}, 大小: {size} bytes")
            
            # 验证数据
            image_storage.seek(0)
            data = image_storage.getvalue()
            
            if data.startswith(b'\x89PNG'):
                print("     📸 PNG格式")
            elif data.startswith(b'\xff\xd8\xff'):
                print("     📸 JPEG格式")
            elif data.startswith(b'GIF'):
                print("     📸 GIF格式")
            elif data.startswith(b'RIFF') and b'WEBP' in data[:20]:
                print("     📸 WebP格式")
            else:
                print(f"     ⚠️ 未知格式，前16字节: {data[:16]}")
            
            return True
            
        except Exception as e:
            print(f"     ❌ 失败: {e}")
            continue
    
    return False

def test_reply_creation():
    """测试Reply对象创建"""
    print("\n🧪 测试Reply对象创建")
    print("=" * 80)
    
    # 模拟成功下载的图片数据
    test_image_data = io.BytesIO(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00')  # JPEG头
    
    try:
        # 创建IMAGE类型的Reply
        reply = Reply(ReplyType.IMAGE, test_image_data)
        print(f"✅ IMAGE Reply创建成功: {reply}")
        print(f"   类型: {reply.type}")
        print(f"   内容类型: {type(reply.content)}")
        
        # 创建TEXT类型的Reply（回退方案）
        fallback_reply = Reply(ReplyType.TEXT, "https://example.com/image.jpg")
        print(f"✅ TEXT Reply创建成功: {fallback_reply}")
        print(f"   类型: {fallback_reply.type}")
        print(f"   内容: {fallback_reply.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Reply创建失败: {e}")
        return False

if __name__ == "__main__":
    print("开始完整流程测试...\n")
    
    # 测试完整流程
    test_full_pipeline()
    
    # 测试Reply创建
    test_reply_creation()
    
    print("\n" + "=" * 80)
    print("🎯 测试完成!")
    print("💡 如果所有步骤都成功，问题可能在代码的其他部分")
    print("💡 如果某个步骤失败，我们就找到了问题所在")
