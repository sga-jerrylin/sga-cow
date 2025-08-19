#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试文件类型检测功能
"""

import sys
import os
from urllib.parse import urlparse, unquote

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def is_downloadable_file(url):
    """判断文件是否应该下载（图片和音频文件）"""
    try:
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path).lower()
        
        # 支持下载的文件扩展名
        downloadable_extensions = {
            # 图片格式
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
            # 音频格式  
            '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma'
        }
        
        for ext in downloadable_extensions:
            if url_path.endswith(ext):
                return True
        return False
    except Exception as e:
        print(f"Error checking file type for {url}: {e}")
        return False

def test_file_type_detection():
    """测试文件类型检测"""
    
    test_urls = [
        # 应该下载的文件（图片）
        "https://example.com/image.jpg",
        "https://example.com/photo.png", 
        "https://example.com/avatar.gif",
        "https://example.com/icon.webp",
        "https://example.com/logo.svg",
        
        # 应该下载的文件（音频）
        "https://example.com/song.mp3",
        "https://example.com/audio.wav",
        "https://example.com/music.m4a",
        "https://example.com/sound.ogg",
        
        # 不应该下载的文件（其他格式）
        "https://example.com/document.pdf",
        "https://example.com/report.docx",
        "https://example.com/data.xlsx",
        "https://example.com/presentation.pptx",
        "https://example.com/archive.zip",
        "https://example.com/video.mp4",
        "https://example.com/movie.avi",
        "https://example.com/code.py",
        "https://example.com/config.json",
        "https://example.com/readme.txt",
        
        # 带参数的URL
        "https://example.com/image.jpg?v=123&t=456",
        "https://example.com/document.pdf?download=true",
        
        # 复杂路径
        "https://files.example.com/uploads/2024/08/photo.PNG",
        "https://cdn.example.com/assets/docs/manual.PDF",
    ]
    
    print("🧪 测试文件类型检测功能")
    print("=" * 60)
    
    downloadable_count = 0
    non_downloadable_count = 0
    
    for url in test_urls:
        is_downloadable = is_downloadable_file(url)
        status = "✅ 下载" if is_downloadable else "🔗 链接"
        print(f"{status} | {url}")
        
        if is_downloadable:
            downloadable_count += 1
        else:
            non_downloadable_count += 1
    
    print("=" * 60)
    print(f"📊 统计结果:")
    print(f"   可下载文件: {downloadable_count} 个")
    print(f"   链接文件: {non_downloadable_count} 个")
    print(f"   总计: {len(test_urls)} 个")
    
    # 验证预期结果
    expected_downloadable = 11  # 5个图片 + 4个音频 + 1个带参数的图片 + 1个大写扩展名的图片
    expected_non_downloadable = len(test_urls) - expected_downloadable
    
    if downloadable_count == expected_downloadable and non_downloadable_count == expected_non_downloadable:
        print("🎉 测试通过！文件类型检测功能正常")
        return True
    else:
        print(f"❌ 测试失败！预期可下载: {expected_downloadable}, 实际: {downloadable_count}")
        print(f"❌ 测试失败！预期链接: {expected_non_downloadable}, 实际: {non_downloadable_count}")
        return False

if __name__ == "__main__":
    test_file_type_detection()
