# -*- coding=utf-8 -*-
import io
import os
import sys
import time
import threading
import queue

import requests
try:
    import web
except ImportError:
    # 如果web.py不可用，使用兼容模块
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import web_compat as web
from wechatpy.enterprise import create_reply, parse_message
from wechatpy.enterprise.crypto import WeChatCrypto
from wechatpy.enterprise.exceptions import InvalidCorpIdException
from wechatpy.exceptions import InvalidSignatureException, WeChatClientException

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.wechatcom.wechatcomapp_client import WechatComAppClient
from channel.wechatcom.wechatcomapp_message import WechatComAppMessage
from common.log import logger
from common.singleton import singleton
from common.utils import compress_imgfile, fsize, split_string_by_utf8_length, convert_webp_to_png, remove_markdown_symbol
from config import conf, subscribe_msg
try:
    from voice.audio_convert import any_to_amr, split_audio
    AUDIO_SUPPORT = True
except ImportError as e:
    logger.warning(f"[wechatcom] Audio conversion not available: {e}")
    AUDIO_SUPPORT = False
    # 提供空的替代函数
    def any_to_amr(file_path):
        return file_path
    def split_audio(file_path, max_duration):
        return [file_path]

MAX_UTF8_LEN = 2048


@singleton
class WechatComAppChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.corp_id = conf().get("wechatcom_corp_id")
        self.secret = conf().get("wechatcomapp_secret")
        self.agent_id = conf().get("wechatcomapp_agent_id")
        self.token = conf().get("wechatcomapp_token")
        self.aes_key = conf().get("wechatcomapp_aes_key")
        self._http_server = None
        logger.info(
            "[wechatcom] Initializing WeCom app channel, corp_id: {}, agent_id: {}".format(self.corp_id, self.agent_id)
        )
        self.crypto = WeChatCrypto(self.token, self.aes_key, self.corp_id)
        self.client = WechatComAppClient(self.corp_id, self.secret)

        # 为每个接收者创建消息发送队列，确保顺序发送
        self.send_queues = {}
        self.send_locks = {}

    def startup(self):
        # start message listener
        urls = ("/wxcomapp/?", "channel.wechatcom.wechatcomapp_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatcomapp_port", 9898)
        logger.info("[wechatcom] ✅ WeCom app channel started successfully")
        logger.info("[wechatcom] 📡 Listening on http://0.0.0.0:{}/wxcomapp/".format(port))
        logger.info("[wechatcom] 🤖 Ready to receive messages")
        
        # Build WSGI app with middleware (same as runsimple but without print)
        func = web.httpserver.StaticMiddleware(app.wsgifunc())
        func = web.httpserver.LogMiddleware(func)
        server = web.httpserver.WSGIServer(("0.0.0.0", port), func)
        self._http_server = server
        try:
            server.start()
        except (KeyboardInterrupt, SystemExit):
            server.stop()

    def stop(self):
        if self._http_server:
            try:
                self._http_server.stop()
                logger.info("[wechatcom] HTTP server stopped")
            except Exception as e:
                logger.warning(f"[wechatcom] Error stopping HTTP server: {e}")
            self._http_server = None

    def _calculate_prefix_length(self, total_parts):
        """计算分段编号前缀的字节长度"""
        # 编号格式: "[1/3] " 或 "[99/99] "
        prefix = f"[{total_parts}/{total_parts}] "
        return len(prefix.encode("utf-8"))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = remove_markdown_symbol(reply.content)

            # 先用原始长度预估分段数
            temp_texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)

            if len(temp_texts) > 1:
                # 需要分段，计算编号前缀长度并重新分段
                prefix_len = self._calculate_prefix_length(len(temp_texts))
                adjusted_max_len = MAX_UTF8_LEN - prefix_len
                texts = split_string_by_utf8_length(reply_text, adjusted_max_len)

                # 如果重新分段后数量变化，再次调整
                if len(texts) != len(temp_texts):
                    prefix_len = self._calculate_prefix_length(len(texts))
                    adjusted_max_len = MAX_UTF8_LEN - prefix_len
                    texts = split_string_by_utf8_length(reply_text, adjusted_max_len)

                logger.info("[wechatcom] text too long, split into {} parts, prefix_len={}, adjusted_max_len={}".format(
                    len(texts), prefix_len, adjusted_max_len))
                # 使用顺序发送机制
                self._send_texts_in_order(receiver, texts)
            else:
                # 不需要分段，直接发送
                self.client.message.send_text(self.agent_id, receiver, temp_texts[0])
            logger.info("[wechatcom] Do send text to {}: {}".format(receiver, reply_text))
        elif reply.type == ReplyType.VOICE:
            try:
                media_ids = []
                file_path = reply.content
                amr_file = os.path.splitext(file_path)[0] + ".amr"
                any_to_amr(file_path, amr_file)
                duration, files = split_audio(amr_file, 60 * 1000)
                if len(files) > 1:
                    logger.info("[wechatcom] voice too long {}s > 60s , split into {} parts".format(duration / 1000.0, len(files)))
                for path in files:
                    response = self.client.media.upload("voice", open(path, "rb"))
                    logger.debug("[wechatcom] upload voice response: {}".format(response))
                    media_ids.append(response["media_id"])
            except ImportError as e:
                logger.error("[wechatcom] voice conversion failed: {}".format(e))
                logger.error("[wechatcom] please install pydub: pip install pydub")
                return
            except WeChatClientException as e:
                logger.error("[wechatcom] upload voice failed: {}".format(e))
                return
            try:
                os.remove(file_path)
                if amr_file != file_path:
                    os.remove(amr_file)
            except Exception:
                pass
            for media_id in media_ids:
                self.client.message.send_voice(self.agent_id, receiver, media_id)
                time.sleep(1)
            logger.info("[wechatcom] sendVoice={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:  # 从网络下载图片
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[wechatcom] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[wechatcom] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            if ".webp" in img_url:
                try:
                    image_storage = convert_webp_to_png(image_storage)
                except Exception as e:
                    logger.error(f"Failed to convert image: {e}")
                    return
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcom] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcom] upload image failed: {}".format(e))
                return

            self.client.message.send_image(self.agent_id, receiver, response["media_id"])
            logger.info("[wechatcom] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:  # 从文件读取图片
            image_storage = reply.content
            logger.info("[wechatcom] 🖼️  收到IMAGE类型回复，开始处理图片")
            logger.info("[wechatcom] 📊 图片数据类型: {}, 大小: {} bytes".format(type(image_storage), fsize(image_storage)))

            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[wechatcom] ⚠️  图片过大，开始压缩: {} bytes".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[wechatcom] ✅ 图片压缩完成: {} bytes".format(fsize(image_storage)))

            # 步骤2: 上传到企业微信临时素材库
            logger.info("[wechatcom] 📤 步骤2: 开始上传到企业微信临时素材库...")
            try:
                media_id = self._upload_temp_media_from_bytesio(image_storage, "image")
                logger.info("[wechatcom] ✅ 步骤2: 临时素材上传成功，media_id: {}".format(media_id))
            except Exception as e:
                logger.error("[wechatcom] ❌ 步骤2: 临时素材上传失败: {}".format(e))
                logger.error("[wechatcom] 🔄 回退到发送错误提示")
                self.client.message.send_text(self.agent_id, receiver, "图片上传失败，请稍后重试")
                return

            # 步骤3: 发送图片消息
            logger.info("[wechatcom] 📨 步骤3: 开始发送图片消息...")
            try:
                self.client.message.send_image(self.agent_id, receiver, media_id)
                logger.info("[wechatcom] ✅ 步骤3: 图片消息发送成功! 接收者: {}".format(receiver))
            except Exception as e:
                logger.error("[wechatcom] ❌ 步骤3: 图片消息发送失败: {}".format(e))
                self.client.message.send_text(self.agent_id, receiver, "图片发送失败，请稍后重试")

        elif reply.type == ReplyType.FILE:  # 处理文件
            file_path = reply.content
            logger.info("[wechatcom] 📄 收到FILE类型回复，开始处理文件")
            logger.info("[wechatcom] 📁 文件路径: {}".format(file_path))

            try:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    logger.error("[wechatcom] ❌ 文件不存在: {}".format(file_path))
                    self.client.message.send_text(self.agent_id, receiver, "文件不存在，无法发送")
                    return

                file_size = os.path.getsize(file_path)
                logger.info("[wechatcom] 📊 文件大小: {} bytes".format(file_size))

                # 步骤2: 上传到企业微信临时素材库
                logger.info("[wechatcom] 📤 步骤2: 开始上传文件到企业微信临时素材库...")
                with open(file_path, 'rb') as f:
                    file_data = io.BytesIO(f.read())
                    filename = os.path.basename(file_path)
                    media_id = self._upload_temp_media_from_bytesio(file_data, "file", filename)
                    logger.info("[wechatcom] ✅ 步骤2: 文件临时素材上传成功，media_id: {}".format(media_id))

                # 步骤3: 发送文件消息
                logger.info("[wechatcom] 📨 步骤3: 开始发送文件消息...")
                self.client.message.send_file(self.agent_id, receiver, media_id)
                logger.info("[wechatcom] ✅ 步骤3: 文件消息发送成功! 接收者: {}".format(receiver))

            except Exception as e:
                logger.error("[wechatcom] ❌ 文件处理失败: {}".format(e))
                self.client.message.send_text(self.agent_id, receiver, "文件发送失败，请稍后重试")

    def _send_texts_in_order(self, receiver, texts):
        """按顺序发送多条文本消息，确保不乱序"""
        # 为每个接收者创建独立的锁
        if receiver not in self.send_locks:
            self.send_locks[receiver] = threading.Lock()

        def send_worker():
            with self.send_locks[receiver]:
                for i, text in enumerate(texts):
                    try:
                        # 添加序号前缀，确保用户能看到正确顺序
                        if len(texts) > 1:
                            prefixed_text = f"[{i+1}/{len(texts)}] {text}"
                        else:
                            prefixed_text = text

                        self.client.message.send_text(self.agent_id, receiver, prefixed_text)
                        logger.info(f"[wechatcom] Sent part {i+1}/{len(texts)} to {receiver}")

                        # 发送间隔，防止过快
                        if i < len(texts) - 1:
                            time.sleep(0.8)  # 增加到0.8秒间隔
                    except Exception as e:
                        logger.error(f"[wechatcom] Failed to send part {i+1}/{len(texts)}: {e}")

        # 在新线程中执行发送，避免阻塞主线程
        thread = threading.Thread(target=send_worker, daemon=True)
        thread.start()

    def _upload_temp_media_from_bytesio(self, file_data, file_type, filename=None):
        """
        从BytesIO对象上传临时素材到企业微信，获取media_id
        参考您提供的app.py中的upload_temp_media方法
        """
        import requests
        import mimetypes

        logger.info("[wechatcom] 🚀 开始临时素材上传流程")

        if filename is None:
            if file_type == "image":
                filename = "image.jpg"
            elif file_type == "voice":
                filename = "voice.amr"
            else:
                filename = "file.bin"

        # 获取access_token
        access_token = self.client.access_token
        if not access_token:
            logger.error("[wechatcom] ❌ access_token为空，无法上传")
            raise Exception("access_token为空")

        logger.info("[wechatcom] 🔑 access_token: {}...".format(access_token[:10]))

        # 企业微信临时素材上传API
        WX_BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"
        url = f"{WX_BASE_URL}/media/upload?access_token={access_token}&type={file_type}"

        # 自动识别文件MIME类型
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type is None:
            mime_type = "application/octet-stream"

        logger.info("[wechatcom] 📋 上传参数: type={}, filename={}, mime_type={}".format(file_type, filename, mime_type))
        logger.info("[wechatcom] 🌐 API地址: {}".format(url))

        # 确保BytesIO指针在开始位置
        file_data.seek(0)
        data_size = len(file_data.getvalue())
        file_data.seek(0)  # 重置指针

        logger.info("[wechatcom] 📊 文件数据大小: {} bytes".format(data_size))

        # 准备multipart/form-data，字段名固定为"media"
        files = {"media": (filename, file_data, mime_type)}

        try:
            logger.info("[wechatcom] 📤 发送HTTP请求到企业微信API...")
            response = requests.post(url, files=files, timeout=30)
            logger.info("[wechatcom] 📥 收到HTTP响应: status_code={}".format(response.status_code))

            result = response.json()
            logger.info("[wechatcom] 📋 API响应内容: {}".format(result))

            if result.get("errcode") == 0:
                media_id = result.get("media_id")
                logger.info("[wechatcom] ✅ 临时素材上传成功! media_id: {}".format(media_id))
                return media_id
            else:
                error_msg = f"企业微信API返回错误: errcode={result.get('errcode')}, errmsg={result.get('errmsg')}"
                logger.error("[wechatcom] ❌ {}".format(error_msg))
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error("[wechatcom] ❌ HTTP请求失败: {}".format(e))
            raise Exception(f"HTTP请求失败: {e}")
        except Exception as e:
            logger.error("[wechatcom] ❌ 临时素材上传异常: {}".format(e))
            raise


class Query:
    def GET(self):
        channel = WechatComAppChannel()
        params = web.input()
        logger.info("[wechatcom] receive params: {}".format(params))
        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce
            echostr = params.echostr
            echostr = channel.crypto.check_signature(signature, timestamp, nonce, echostr)
        except InvalidSignatureException:
            raise web.Forbidden()
        return echostr

    def POST(self):
        channel = WechatComAppChannel()
        params = web.input()
        logger.info("[wechatcom] receive params: {}".format(params))
        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce
            message = channel.crypto.decrypt_message(web.data(), signature, timestamp, nonce)
        except (InvalidSignatureException, InvalidCorpIdException):
            raise web.Forbidden()
        msg = parse_message(message)
        logger.debug("[wechatcom] receive message: {}, msg= {}".format(message, msg))
        if msg.type == "event":
            if msg.event == "subscribe":
                pass
                # reply_content = subscribe_msg()
                # if reply_content:
                #     reply = create_reply(reply_content, msg).render()
                #     res = channel.crypto.encrypt_message(reply, nonce, timestamp)
                #     return res
        else:
            try:
                wechatcom_msg = WechatComAppMessage(msg, client=channel.client)
            except NotImplementedError as e:
                logger.debug("[wechatcom] " + str(e))
                return "success"
            context = channel._compose_context(
                wechatcom_msg.ctype,
                wechatcom_msg.content,
                isgroup=False,
                msg=wechatcom_msg,
            )
            if context:
                channel.produce(context)
        return "success"
