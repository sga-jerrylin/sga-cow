# -*- coding=utf-8 -*-
import io
import os
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
        print(self.corp_id, self.secret, self.agent_id, self.token, self.aes_key)
        logger.info(
            "[wechatcom] init: corp_id: {}, secret: {}, agent_id: {}, token: {}, aes_key: {}".format(self.corp_id, self.secret, self.agent_id, self.token, self.aes_key)
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
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = remove_markdown_symbol(reply.content)
            texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
            if len(texts) > 1:
                logger.info("[wechatcom] text too long, split into {} parts".format(len(texts)))
                # 使用顺序发送机制
                self._send_texts_in_order(receiver, texts)
            else:
                self.client.message.send_text(self.agent_id, receiver, texts[0])
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
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[wechatcom] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[wechatcom] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            try:
                response = self.client.media.upload("image", image_storage)
                logger.debug("[wechatcom] upload image response: {}".format(response))
            except WeChatClientException as e:
                logger.error("[wechatcom] upload image failed: {}".format(e))
                return
            self.client.message.send_image(self.agent_id, receiver, response["media_id"])
            logger.info("[wechatcom] sendImage, receiver={}".format(receiver))

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
