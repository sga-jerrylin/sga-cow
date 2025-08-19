#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试markdown解析功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.utils import parse_markdown_text

def test_markdown_parsing():
    """测试markdown解析功能"""
    
    # 从日志中看到的实际内容
    test_content = """我已经为您生成了柱状图，请查看以下图片:

![](https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQ6AAAAgAoEACAQFr/original)"""
    
    print("🧪 测试Markdown解析功能")
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

def test_simple_image_markdown():
    """测试简单的图片markdown"""
    
    print("🧪 测试简单图片Markdown")
    print("=" * 80)
    
    test_cases = [
        "![](https://example.com/image.jpg)",
        "![alt text](https://example.com/image.png)",
        "这是文本 ![](https://example.com/image.gif) 更多文本",
        "![image](https://mdn.alipayobjects.com/one_clip/afts/img/eCusSK57LBUAAAAAQ6AAAAgAoEACAQFr/original)",
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 测试用例 {i}: {repr(test_case)}")
        try:
            result = parse_markdown_text(test_case)
            print(f"   结果: {result}")
            print()
        except Exception as e:
            print(f"   ❌ 失败: {e}")
            print()

if __name__ == "__main__":
    print("开始测试...")
    result = test_markdown_parsing()
    print("\n" + "="*80 + "\n")
    test_simple_image_markdown()
    
    print("\n" + "="*80)
    if result:
        print("🎉 解析功能正常工作!")
    else:
        print("💥 解析功能有问题!")
