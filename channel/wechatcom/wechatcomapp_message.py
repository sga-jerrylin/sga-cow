from wechatpy.enterprise import WeChatClient
import re
import os
import mimetypes

from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir


class WechatComAppMessage(ChatMessage):
    def __init__(self, msg, client: WeChatClient, is_group=False):
        super().__init__(msg)
        self.msg_id = msg.id
        self.create_time = msg.time
        self.is_group = is_group

        if msg.type == "text":
            self.ctype = ContextType.TEXT
            self.content = msg.content
        elif msg.type == "voice":
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + msg.media_id + "." + msg.format  # content直接存临时目录路径

            def download_voice():
                # 如果响应状态码是200，则将响应内容写入本地文件
                response = client.media.download(msg.media_id)
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    logger.info(f"[wechatcom] Failed to download voice file, {response.content}")

            self._prepare_fn = download_voice
        elif msg.type == "image":
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + msg.media_id + ".png"  # content直接存临时目录路径

            def download_image():
                # 如果响应状态码是200，则将响应内容写入本地文件
                response = client.media.download(msg.media_id)
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                else:
                    logger.info(f"[wechatcom] Failed to download image file, {response.content}")

            self._prepare_fn = download_image
        elif msg.type == "file":
            self.ctype = ContextType.FILE
            # 获取文件扩展名
            file_ext = self._get_file_extension(msg)
            self.content = TmpDir().path() + msg.media_id + file_ext

            def download_file():
                # 下载文件
                response = client.media.download(msg.media_id)
                if response.status_code == 200:
                    with open(self.content, "wb") as f:
                        f.write(response.content)
                    logger.info(f"[wechatcom] Downloaded file: {self.content}")
                else:
                    logger.info(f"[wechatcom] Failed to download file, {response.content}")

            self._prepare_fn = download_file
        elif msg.type == "link":
            # 处理链接消息，可能包含文件下载链接
            self.ctype = ContextType.TEXT
            self.content = self._extract_file_links(msg.content) or msg.content
        else:
            raise NotImplementedError("Unsupported message type: Type:{} ".format(msg.type))

        self.from_user_id = msg.source
        self.to_user_id = msg.target
        self.other_user_id = msg.source

    def _get_file_extension(self, msg):
        """根据消息获取文件扩展名"""
        # 如果消息中有文件名信息，尝试从中提取扩展名
        if hasattr(msg, 'title') and msg.title:
            _, ext = os.path.splitext(msg.title)
            if ext:
                return ext

        # 如果有媒体类型信息，根据MIME类型推断扩展名
        if hasattr(msg, 'media_type') and msg.media_type:
            ext = mimetypes.guess_extension(msg.media_type)
            if ext:
                return ext

        # 默认返回通用文件扩展名
        return ".file"

    def _extract_file_links(self, content):
        """从消息内容中提取文件下载链接"""
        if not content:
            return None

        # 定义支持的文件类型的正则表达式
        file_patterns = [
            # 直接的文件链接
            r'https?://[^\s]+\.(?:pdf|doc|docx|xlsx?|pptx?|txt|html?|png|jpe?g|gif|bmp|svg|zip|rar|7z|tar|gz)(?:\?[^\s]*)?',
            # 企业微信文件分享链接
            r'https?://[^\s]*(?:work\.weixin\.qq\.com|qyapi\.weixin\.qq\.com)[^\s]*(?:file|media)[^\s]*',
            # 通用下载链接模式
            r'https?://[^\s]*(?:download|file|attachment|media)[^\s]*',
        ]

        extracted_links = []
        for pattern in file_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            extracted_links.extend(matches)

        if extracted_links:
            # 返回提取到的链接信息
            links_text = "检测到文件链接:\n" + "\n".join(extracted_links)
            return links_text

        return None
