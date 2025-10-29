# -*- coding: utf-8 -*-
"""
企业微信智能机器人消息处理
支持文本、图片、图文混排、流式消息刷新等消息类型
"""
import os
import requests
from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir


class WechatComAIBotMessage(ChatMessage):
    """
    企业微信智能机器人消息类
    
    支持的消息类型：
    - text: 文本消息
    - image: 图片消息（加密）
    - mixed: 图文混排消息
    - stream: 流式消息刷新
    """
    
    def __init__(self, msg_dict, client=None, aes_key=None):
        """
        初始化消息对象
        
        Args:
            msg_dict: 解密后的消息字典
            client: WechatComAIBotClient 实例
            aes_key: AES密钥，用于解密图片
        """
        # 智能机器人消息没有传统的 msg 对象，直接使用字典
        super().__init__(None)
        
        self.msg_dict = msg_dict
        self.client = client
        self.aes_key = aes_key
        
        # 基础字段
        self.msg_id = msg_dict.get("msgid")
        self.aibot_id = msg_dict.get("aibotid")
        self.chat_id = msg_dict.get("chatid")
        self.chat_type = msg_dict.get("chattype")  # single/group
        self.from_user_info = msg_dict.get("from", {})
        self.from_user_id = self.from_user_info.get("userid")
        self.corp_id = self.from_user_info.get("corpid", "")
        
        # 消息类型
        self.msg_type = msg_dict.get("msgtype")

        if self.msg_type == "text":
            self._handle_text_message(msg_dict)
        elif self.msg_type == "image":
            self._handle_image_message(msg_dict)
        elif self.msg_type == "mixed":
            self._handle_mixed_message(msg_dict)
        elif self.msg_type == "stream":
            self._handle_stream_message(msg_dict)
        else:
            raise NotImplementedError(f"Unsupported message type: {self.msg_type}")
        
        # 判断是否群聊
        self.is_group = (self.chat_type == "group")

        # 设置接收者和发送者
        self.to_user_id = self.aibot_id

        if self.is_group:
            # 群聊场景
            self.other_user_id = self.chat_id  # 群ID
            self.other_user_nickname = self.chat_id  # 群名称（暂时使用群ID）
            self.actual_user_id = self.from_user_id  # 实际发送者ID
            self.actual_user_nickname = self.from_user_id  # 实际发送者昵称（暂时使用ID）
        else:
            # 单聊场景
            self.other_user_id = self.from_user_id
            self.other_user_nickname = self.from_user_id
            self.actual_user_id = self.from_user_id
            self.actual_user_nickname = self.from_user_id
    
    def _handle_text_message(self, msg_dict):
        """处理文本消息"""
        self.ctype = ContextType.TEXT
        text_content = msg_dict.get("text", {}).get("content", "")

        # 检查是否是 @ 消息
        self.is_at = text_content.startswith("@")

        # 移除 @机器人 的部分
        # 例如: "@RobotA hello robot" -> "hello robot"
        if self.is_at:
            # 找到第一个空格，移除 @机器人名称
            space_index = text_content.find(" ")
            if space_index > 0:
                text_content = text_content[space_index + 1:].strip()
            else:
                # 如果没有空格，说明只有 @，内容为空
                text_content = ""

        self.content = text_content
        logger.info(f"[wechatcom_aibot] Received text message: {self.content}, is_at={self.is_at}")
    
    def _handle_image_message(self, msg_dict):
        """处理图片消息（加密）"""
        self.ctype = ContextType.IMAGE
        image_info = msg_dict.get("image", {})
        image_url = image_info.get("url")
        
        if not image_url:
            raise ValueError("Image URL is empty")
        
        # 生成临时文件路径
        self.content = TmpDir().path() + self.msg_id + ".png"
        
        def download_and_decrypt_image():
            """下载并解密图片"""
            try:
                # 下载加密图片
                logger.info(f"[wechatcom_aibot] Downloading encrypted image from: {image_url}")
                response = requests.get(image_url, timeout=30)
                
                if response.status_code == 200:
                    encrypted_data = response.content
                    logger.info(f"[wechatcom_aibot] Downloaded encrypted image, size: {len(encrypted_data)} bytes")
                    
                    # 解密图片（使用 WXBizMsgCrypt 方法）
                    # 企业微信图片加密方式：和消息加密类似，但不需要去除随机字符串和长度信息
                    decrypted = False
                    if self.aes_key:
                        try:
                            from Crypto.Cipher import AES
                            import base64
                            import struct
                            import socket

                            logger.info(f"[wechatcom_aibot] Attempting image decryption using WXBizMsgCrypt method")

                            # 1. 解码 Base64 密钥
                            key = base64.b64decode(self.aes_key + "=")
                            logger.info(f"[wechatcom_aibot] Decoded key length: {len(key)} bytes")

                            # 2. AES-CBC 解密（IV = key 的前 16 字节）
                            iv = key[:16]
                            cipher = AES.new(key, AES.MODE_CBC, iv)
                            plain_text = cipher.decrypt(encrypted_data)

                            # 3. 去除 PKCS7 填充
                            pad = plain_text[-1]
                            logger.info(f"[wechatcom_aibot] PKCS7 padding: {pad}")

                            # 4. 去除前 16 字节随机字符串
                            content = plain_text[16:-pad]

                            # 5. 读取 4 字节长度信息
                            img_len = socket.ntohl(struct.unpack("I", content[:4])[0])
                            logger.info(f"[wechatcom_aibot] Image length from header: {img_len} bytes")

                            # 6. 提取实际图片数据
                            decrypted_data = content[4:4+img_len]

                            # 检查图片文件头
                            file_header = decrypted_data[:16]
                            logger.info(f"[wechatcom_aibot] Decrypted file header (hex): {file_header.hex()}")

                            # 保存解密后的图片
                            with open(self.content, "wb") as f:
                                f.write(decrypted_data)
                            logger.info(f"[wechatcom_aibot] ✅ Image decrypted successfully and saved: {self.content}, size: {len(decrypted_data)} bytes")
                            decrypted = True
                        except Exception as e:
                            logger.warning(f"[wechatcom_aibot] ⚠️ Decryption failed: {e}, trying to save as unencrypted image")

                    # 如果解密失败或没有密钥，尝试直接保存（可能本身就是未加密的图片）
                    if not decrypted:
                        try:
                            with open(self.content, "wb") as f:
                                f.write(encrypted_data)
                            logger.info(f"[wechatcom_aibot] ✅ Image saved (unencrypted): {self.content}, size: {len(encrypted_data)} bytes")
                        except Exception as e:
                            logger.error(f"[wechatcom_aibot] ❌ Failed to save image: {e}")
                else:
                    logger.error(f"[wechatcom_aibot] Failed to download image: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"[wechatcom_aibot] Exception when downloading image: {e}")
        
        self._prepare_fn = download_and_decrypt_image
    
    def _handle_mixed_message(self, msg_dict):
        """
        处理图文混排消息

        策略：
        1. 提取文本内容作为主要内容
        2. 下载并解密第一张图片（如果有）
        3. 将图片路径保存到 image_path 属性，供后续处理
        """
        self.ctype = ContextType.TEXT  # 作为文本处理，但会附带图片
        mixed_info = msg_dict.get("mixed", {})
        msg_items = mixed_info.get("msg_item", [])

        # 提取所有文本内容
        text_parts = []
        image_urls = []
        has_at = False  # 标记是否包含 @ 消息

        for item in msg_items:
            item_type = item.get("msgtype")
            if item_type == "text":
                text_content = item.get("text", {}).get("content", "")
                # 检查是否是 @ 消息
                if text_content.startswith("@"):
                    has_at = True
                    # 移除 @机器人 的部分
                    space_index = text_content.find(" ")
                    if space_index > 0:
                        text_content = text_content[space_index + 1:].strip()
                    else:
                        text_content = ""
                text_parts.append(text_content)
            elif item_type == "image":
                image_url = item.get("image", {}).get("url", "")
                if image_url:
                    image_urls.append(image_url)

        # 设置 is_at 属性（重要！用于群聊消息过滤）
        self.is_at = has_at

        # 组合文本内容
        self.content = "\n".join(text_parts)

        # 保存图片URL列表
        self.image_urls = image_urls

        # 如果有图片，下载并解密第一张图片
        self.image_path = None
        if image_urls:
            first_image_url = image_urls[0]
            # 生成临时文件路径
            self.image_path = TmpDir().path() + self.msg_id + "_mixed_0.png"

            def download_and_decrypt_first_image():
                """下载并解密第一张图片"""
                try:
                    logger.info(f"[wechatcom_aibot] Downloading encrypted image from mixed message: {first_image_url}")
                    response = requests.get(first_image_url, timeout=30)

                    if response.status_code == 200:
                        encrypted_data = response.content
                        logger.info(f"[wechatcom_aibot] Downloaded encrypted image, size: {len(encrypted_data)} bytes")

                        # 尝试解密图片
                        # 企业微信图片加密方式：和消息加密类似，但不需要去除随机字符串和长度信息
                        decrypted = False
                        if self.aes_key:
                            try:
                                from Crypto.Cipher import AES
                                import base64
                                import struct
                                import socket

                                logger.info(f"[wechatcom_aibot] Attempting image decryption using WXBizMsgCrypt method")

                                # 1. 解码 Base64 密钥
                                key = base64.b64decode(self.aes_key + "=")
                                logger.info(f"[wechatcom_aibot] Decoded key length: {len(key)} bytes")

                                # 2. AES-CBC 解密（IV = key 的前 16 字节）
                                iv = key[:16]
                                cipher = AES.new(key, AES.MODE_CBC, iv)
                                plain_text = cipher.decrypt(encrypted_data)

                                # 3. 去除 PKCS7 填充
                                pad = plain_text[-1]
                                logger.info(f"[wechatcom_aibot] PKCS7 padding: {pad}")
                                logger.info(f"[wechatcom_aibot] Plain text length after decryption: {len(plain_text)} bytes")

                                # 图片加密格式可能不同于消息加密格式
                                # 尝试方法1：直接使用去除填充后的数据（不去除随机字符串和长度信息）
                                decrypted_data = plain_text[:-pad]
                                logger.info(f"[wechatcom_aibot] Trying method 1: direct decryption without removing header")
                                logger.info(f"[wechatcom_aibot] Decrypted data length: {len(decrypted_data)} bytes")

                                # 检查图片文件头
                                file_header = decrypted_data[:16]
                                logger.info(f"[wechatcom_aibot] Decrypted file header (hex): {file_header.hex()}")

                                # 保存解密后的图片
                                with open(self.image_path, "wb") as f:
                                    f.write(decrypted_data)
                                logger.info(f"[wechatcom_aibot] ✅ Mixed message image decrypted successfully and saved: {self.image_path}, size: {len(decrypted_data)} bytes")
                                decrypted = True
                            except Exception as e:
                                logger.warning(f"[wechatcom_aibot] ⚠️ Decryption failed: {e}, trying to save as unencrypted image")

                        # 如果解密失败或没有密钥，尝试直接保存（可能本身就是未加密的图片）
                        if not decrypted:
                            # 先检查原始数据的文件头
                            file_header = encrypted_data[:16]
                            logger.info(f"[wechatcom_aibot] Original file header (hex): {file_header.hex()}")

                            # PNG 文件头: 89 50 4E 47 0D 0A 1A 0A
                            # JPEG 文件头: FF D8 FF
                            if file_header[:8] == b'\x89PNG\r\n\x1a\n':
                                logger.info(f"[wechatcom_aibot] ✅ Valid PNG image detected (unencrypted)")
                                try:
                                    with open(self.image_path, "wb") as f:
                                        f.write(encrypted_data)
                                    logger.info(f"[wechatcom_aibot] ✅ Mixed message image saved (unencrypted): {self.image_path}, size: {len(encrypted_data)} bytes")
                                    decrypted = True
                                except Exception as e:
                                    logger.error(f"[wechatcom_aibot] ❌ Failed to save image: {e}")
                                    self.image_path = None
                            elif file_header[:3] == b'\xff\xd8\xff':
                                logger.info(f"[wechatcom_aibot] ✅ Valid JPEG image detected (unencrypted)")
                                try:
                                    with open(self.image_path, "wb") as f:
                                        f.write(encrypted_data)
                                    logger.info(f"[wechatcom_aibot] ✅ Mixed message image saved (unencrypted): {self.image_path}, size: {len(encrypted_data)} bytes")
                                    decrypted = True
                                except Exception as e:
                                    logger.error(f"[wechatcom_aibot] ❌ Failed to save image: {e}")
                                    self.image_path = None
                            else:
                                logger.error(f"[wechatcom_aibot] ❌ Image is encrypted but decryption failed, and it's not a valid unencrypted image")
                                self.image_path = None
                    else:
                        logger.error(f"[wechatcom_aibot] Failed to download mixed message image: {response.status_code}")
                        self.image_path = None

                except Exception as e:
                    logger.error(f"[wechatcom_aibot] Exception when downloading mixed message image: {e}")
                    self.image_path = None

            # 设置准备函数
            self._prepare_fn = download_and_decrypt_first_image

        logger.info(f"[wechatcom_aibot] Received mixed message: text={self.content}, images={len(image_urls)}, is_at={self.is_at}")
    
    def _handle_stream_message(self, msg_dict):
        """处理流式消息刷新"""
        self.ctype = ContextType.TEXT  # 特殊类型，用于触发流式消息回复
        stream_info = msg_dict.get("stream", {})
        self.stream_id = stream_info.get("id")
        
        # 流式消息刷新不包含用户输入内容，使用特殊标记
        self.content = f"[STREAM_REFRESH:{self.stream_id}]"
        
        logger.info(f"[wechatcom_aibot] Received stream refresh for stream_id: {self.stream_id}")

