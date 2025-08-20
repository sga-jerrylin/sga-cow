import io
import os
import re
from urllib.parse import urlparse
from PIL import Image
from common.log import logger

def fsize(file):
    if isinstance(file, io.BytesIO):
        return file.getbuffer().nbytes
    elif isinstance(file, str):
        return os.path.getsize(file)
    elif hasattr(file, "seek") and hasattr(file, "tell"):
        pos = file.tell()
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(pos)
        return size
    else:
        raise TypeError("Unsupported type")


def compress_imgfile(file, max_size):
    if fsize(file) <= max_size:
        return file
    file.seek(0)
    img = Image.open(file)
    rgb_image = img.convert("RGB")
    quality = 95
    while True:
        out_buf = io.BytesIO()
        rgb_image.save(out_buf, "JPEG", quality=quality)
        if fsize(out_buf) <= max_size:
            return out_buf
        quality -= 5


def split_string_by_utf8_length(string, max_length, max_split=0):
    encoded = string.encode("utf-8")
    start, end = 0, 0
    result = []
    while end < len(encoded):
        if max_split > 0 and len(result) >= max_split:
            result.append(encoded[start:].decode("utf-8"))
            break
        end = min(start + max_length, len(encoded))
        # 如果当前字节不是 UTF-8 编码的开始字节，则向前查找直到找到开始字节为止
        while end < len(encoded) and (encoded[end] & 0b11000000) == 0b10000000:
            end -= 1
        result.append(encoded[start:end].decode("utf-8"))
        start = end
    return result


def get_path_suffix(path):
    path = urlparse(path).path
    return os.path.splitext(path)[-1].lstrip('.')


def convert_webp_to_png(webp_image):
    from PIL import Image
    try:
        webp_image.seek(0)
        img = Image.open(webp_image).convert("RGBA")
        png_image = io.BytesIO()
        img.save(png_image, format="PNG")
        png_image.seek(0)
        return png_image
    except Exception as e:
        logger.error(f"Failed to convert WEBP to PNG: {e}")
        raise


def remove_markdown_symbol(text: str):
    # 移除markdown格式，目前先移除**
    if not text:
        return text
    return re.sub(r'\*\*(.*?)\*\*', r'\1', text)


def parse_markdown_text(text: str):
    """
    解析Markdown文本和纯文本中的链接，提取文本、图片、文件等内容
    返回格式: [
        {'type': 'text', 'content': '文本内容'},
        {'type': 'image', 'content': '图片URL'},
        {'type': 'file', 'content': '文件URL'},
        ...
    ]
    """
    if not text:
        return [{'type': 'text', 'content': ''}]

    logger.info(f"[PARSE] 🔍 开始解析文本，长度: {len(text)}")
    logger.debug(f"[PARSE] 输入文本: {repr(text[:200])}...")

    result = []
    remaining_text = text

    # 定义文件扩展名模式（用于识别文件链接）
    file_extensions = r'\.(pdf|doc|docx|xlsx?|pptx?|txt|html?|zip|rar|7z|tar|gz|csv|json|xml)(\?[^\)]*)?$'

    # 1. 提取markdown图片 ![alt](url)
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    images = re.findall(image_pattern, remaining_text)
    if images:
        logger.info(f"[PARSE] 📸 找到 {len(images)} 个markdown图片")
        for alt, url in images:
            result.append({'type': 'image', 'content': url})
            logger.info(f"[PARSE] 提取markdown图片: {url}")
            # 从文本中移除已处理的图片
            remaining_text = remaining_text.replace(f'![{alt}]({url})', '', 1)

    # 2. 提取markdown链接 [text](url)
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_pattern, remaining_text)
    if links:
        logger.info(f"[PARSE] 🔗 找到 {len(links)} 个markdown链接")
        for link_text, url in links:
            # 检查是否为文件链接
            if re.search(file_extensions, url, re.IGNORECASE):
                result.append({'type': 'file', 'content': url})
                logger.info(f"[PARSE] 提取markdown文件: {url}")
                # 从文本中移除已处理的文件链接
                remaining_text = remaining_text.replace(f'[{link_text}]({url})', '', 1)
            else:
                # 普通链接保留在文本中，但移除Markdown格式
                remaining_text = remaining_text.replace(f'[{link_text}]({url})', link_text, 1)

    # 3. 如果没有找到markdown格式的媒体，查找纯文本中的链接
    if not any(item['type'] in ['image', 'file'] for item in result):
        logger.info("[PARSE] 🔍 没有找到markdown媒体，开始查找纯文本链接")

        # 图片链接模式 (阿里云、腾讯云等)
        image_url_patterns = [
            r'https://mdn\.alipayobjects\.com/[^\s]+',  # 阿里云图片
            r'https://[^/]*\.cos\.[^/]*\.myqcloud\.com/[^\s]+\.(?:jpg|jpeg|png|gif|webp)',  # 腾讯云图片
            r'https://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp)',  # 通用图片链接
        ]

        # 文件链接模式
        file_url_patterns = [
            r'https://[^/]*\.cos\.[^/]*\.myqcloud\.com/[^\s]+\.(?:docx?|pdf|xlsx?|pptx?)',  # 腾讯云文件
            r'https://[^\s]+\.(?:docx?|pdf|xlsx?|pptx?|txt|zip|rar)',  # 通用文件链接
        ]

        # 查找图片链接
        for pattern in image_url_patterns:
            matches = re.findall(pattern, remaining_text)
            if matches:
                logger.info(f"[PARSE] 📸 找到 {len(matches)} 个纯文本图片链接")
                for url in matches:
                    result.append({'type': 'image', 'content': url})
                    logger.info(f"[PARSE] 提取纯文本图片: {url}")
                    # 从文本中移除链接
                    remaining_text = remaining_text.replace(url, '', 1)
                break  # 找到图片链接后就不再查找其他模式

        # 如果没找到图片，查找文件链接
        if not any(item['type'] == 'image' for item in result):
            for pattern in file_url_patterns:
                matches = re.findall(pattern, remaining_text)
                if matches:
                    logger.info(f"[PARSE] 📄 找到 {len(matches)} 个纯文本文件链接")
                    for url in matches:
                        result.append({'type': 'file', 'content': url})
                        logger.info(f"[PARSE] 提取纯文本文件: {url}")
                        # 从文本中移除链接
                        remaining_text = remaining_text.replace(url, '', 1)
                    break  # 找到文件链接后就不再查找其他模式

    # 4. 处理剩余的文本内容
    if remaining_text.strip():
        # 移除其他Markdown格式
        clean_text = remaining_text
        # 移除粗体
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_text)
        # 移除斜体
        clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
        # 移除代码块
        clean_text = re.sub(r'```.*?```', '', clean_text, flags=re.DOTALL)
        # 移除行内代码
        clean_text = re.sub(r'`([^`]+)`', r'\1', clean_text)
        # 清理多余的空白
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text.strip())

        if clean_text.strip():
            result.insert(0, {'type': 'text', 'content': clean_text})
            logger.info(f"[PARSE] 📝 保留文本内容，长度: {len(clean_text)}")

    # 如果没有任何内容，返回空文本
    if not result:
        result = [{'type': 'text', 'content': ''}]
        logger.info("[PARSE] ⚠️  没有找到任何内容，返回空文本")

    logger.info(f"[PARSE] ✅ 解析完成，共 {len(result)} 个项目")
    for i, item in enumerate(result):
        logger.info(f"[PARSE] 项目 {i+1}: {item['type']} - {item['content'][:100]}...")

    return result


def print_red(text: str):
    """
    打印红色文本（用于错误信息）
    """
    # ANSI颜色代码：红色
    RED = '\033[91m'
    RESET = '\033[0m'

    # 同时输出到日志和控制台
    logger.error(text)
    print(f"{RED}{text}{RESET}")

    return text
