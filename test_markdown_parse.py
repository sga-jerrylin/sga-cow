#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试Markdown解析功能
"""

from config import load_config
from common.utils import parse_markdown_text

# 加载配置
load_config()

def test_markdown_parsing():
    """测试Markdown解析功能"""
    
    print("🧪 测试Markdown解析功能")
    print("=" * 50)
    
    # 测试用例1：包含文件下载链接
    test_case_1 = """文档已生成成功！

[下载文件](https://difyfordoc-1323080521.cos.ap-guangzhou.myqcloud.com/documents/%E8%8A%B1%E6%9C%B5%E6%B5%B7%E6%A3%A0%E4%BD%A0%E5%A4%9A%E4%B9%85%E6%B2%A1%E5%BA%95%E4%BA%86%20202508019.docx)

如果你不需要调整或者添加内容，随时告诉我哦～ 😊"""

    print("测试用例1：文件下载链接")
    print(f"原文本：{test_case_1}")
    result_1 = parse_markdown_text(test_case_1)
    print(f"解析结果：")
    for i, item in enumerate(result_1):
        print(f"  {i+1}. 类型: {item['type']}, 内容: {item['content'][:100]}...")
    print()

    # 测试用例2：包含图片
    test_case_2 = """这是一张图片：

![示例图片](https://example.com/image.png)

图片很漂亮！"""

    print("测试用例2：图片链接")
    print(f"原文本：{test_case_2}")
    result_2 = parse_markdown_text(test_case_2)
    print(f"解析结果：")
    for i, item in enumerate(result_2):
        print(f"  {i+1}. 类型: {item['type']}, 内容: {item['content'][:100]}...")
    print()

    # 测试用例3：混合内容
    test_case_3 = """这里有多种内容：

![图片](https://example.com/pic.jpg)

[下载PDF](https://example.com/document.pdf)

还有一个[普通链接](https://example.com)

**粗体文本**和*斜体文本*"""

    print("测试用例3：混合内容")
    print(f"原文本：{test_case_3}")
    result_3 = parse_markdown_text(test_case_3)
    print(f"解析结果：")
    for i, item in enumerate(result_3):
        print(f"  {i+1}. 类型: {item['type']}, 内容: {item['content'][:100]}...")
    print()

    # 验证文件扩展名识别
    file_urls = [
        "https://example.com/doc.pdf",
        "https://example.com/sheet.xlsx", 
        "https://example.com/presentation.pptx",
        "https://example.com/archive.zip",
        "https://example.com/data.csv",
        "https://example.com/page.html",
        "https://example.com/normal-link"  # 不是文件
    ]
    
    print("测试文件扩展名识别：")
    for url in file_urls:
        test_text = f"[下载文件]({url})"
        result = parse_markdown_text(test_text)
        file_items = [item for item in result if item['type'] == 'file']
        is_file = len(file_items) > 0
        print(f"  {url} -> {'文件' if is_file else '普通链接'}")
    
    print("\n✅ Markdown解析测试完成！")

if __name__ == "__main__":
    test_markdown_parsing()
