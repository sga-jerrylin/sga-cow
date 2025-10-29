# -*- coding: utf-8 -*-
"""
企业微信智能机器人 Channel
支持被动回复、流式消息、模板卡片等功能
"""
import io
import time
import threading
from collections import defaultdict

try:
    import web
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    import web_compat as web

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from common.log import logger
from common.singleton import singleton
from common.utils import remove_markdown_symbol
from config import conf


@singleton
class WechatComAIBotChannel(ChatChannel):
    """
    企业微信智能机器人 Channel
    
    特点：
    1. 被动回复模式（5秒内响应）
    2. 支持流式消息回复
    3. 支持模板卡片
    4. 支持图文混排
    """
    
    NOT_SUPPORT_REPLYTYPE = []
    
    def __init__(self):
        super().__init__()

        # 基础配置
        self.corp_id = conf().get("wechatcom_corp_id")
        self.token = conf().get("wechatcom_aibot_token")
        self.aes_key = conf().get("wechatcom_aibot_aes_key")
        self.enable_stream = conf().get("wechatcom_aibot_enable_stream", True)

        logger.info(
            "[wechatcom_aibot] Initializing: corp_id={}, token_len={}, aes_key_len={}, enable_stream={}".format(
                self.corp_id, len(self.token) if self.token else 0, len(self.aes_key) if self.aes_key else 0, self.enable_stream
            )
        )

        # 智能机器人不需要 client（不需要主动调用API）
        self.client = None
        
        # 被动回复相关
        # 缓存每个用户的回复内容
        self.cache_dict = defaultdict(list)
        # 记录正在处理的用户
        self.running = set()
        # 记录请求次数（用于处理微信重试）
        self.request_cnt = dict()

        # 流式消息相关
        # 存储每个 cache_key 对应的 stream_id {cache_key: stream_id}
        self.stream_ids = {}
        self.stream_lock = threading.Lock()

    def _compose_context(self, ctype, content, **kwargs):
        """
        重写 _compose_context 方法，实现企业微信智能机器人的特殊逻辑：
        1. 群聊时，session_id 使用群ID（保持上下文连续）
        2. 群聊时，content 添加发言人落款（让 agent 知道是谁在说话）

        这样设计的原因：
        - 从产品角度，agent 在群里应该像真人一样，能记住整个群的对话历史
        - 同时需要知道是谁在说话，所以添加 "from 用户名" 落款
        - 避免上下文割裂，提升用户体验
        """
        from bridge.context import ContextType

        # 调用父类方法获取基础 context
        context = super()._compose_context(ctype, content, **kwargs)

        if context is None:
            return None

        # 如果是群聊，修改 session_id 和 content
        if context.get("isgroup", False):
            cmsg = context["msg"]
            group_id = cmsg.other_user_id  # 群ID
            actual_user_id = cmsg.actual_user_id  # 实际发送者ID

            # 1. 强制使用群ID作为 session_id（保持群内上下文连续）
            # 这样 Dify 的 conversation_id 会基于群ID，所有人共享同一个对话线程
            context["session_id"] = group_id
            logger.info(f"[wechatcom_aibot] Group chat - Overriding session_id to group_id: {group_id}, actual_user: {actual_user_id}")

            # 2. 在 content 末尾添加发言人落款
            # 让 agent 知道是谁在说话，同时保持上下文连续
            original_content = context.content
            context.content = f"{original_content}\n\nfrom {actual_user_id}"
            logger.info(f"[wechatcom_aibot] Added user signature to content: 'from {actual_user_id}'")

        return context

    def startup(self):
        """启动 web 服务"""
        urls = ("/wxaibot/?", "channel.wechatcom_aibot.wechatcom_aibot_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("wechatcom_aibot_port", 9899)
        logger.info(f"[wechatcom_aibot] Starting web server on port {port}")
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))
    
    def send(self, reply: Reply, context: Context):
        """
        发送回复（被动回复模式）

        注意：智能机器人使用被动回复，不能主动发送消息
        回复内容会被缓存，等待微信服务器的请求时返回

        企业微信智能机器人支持的消息类型：
        - 文本消息（支持 Markdown）
        - 流式消息（支持 Markdown）
        - 模板卡片消息

        不支持直接发送文件，文件需要通过文本消息中的链接形式发送
        """
        receiver = context["receiver"]

        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = remove_markdown_symbol(reply.content)
            logger.info(f"[wechatcom_aibot] Text cached for {receiver}: {reply_text[:100]}...")
            self.cache_dict[receiver].append(("text", reply_text))

        elif reply.type == ReplyType.IMAGE_URL:
            # 图片URL
            img_url = reply.content
            logger.info(f"[wechatcom_aibot] Image URL cached for {receiver}: {img_url}")
            self.cache_dict[receiver].append(("image_url", img_url))

        elif reply.type == ReplyType.IMAGE:
            # 图片数据（BytesIO）
            image_storage = reply.content
            logger.info(f"[wechatcom_aibot] Image data cached for {receiver}")
            self.cache_dict[receiver].append(("image", image_storage))

        elif reply.type == ReplyType.FILE:
            # 文件：企业微信智能机器人不支持直接发送文件
            # 将文件路径或URL作为文本链接发送
            file_content = reply.content
            if isinstance(file_content, str):
                # 如果是文件路径，提取文件名
                if os.path.exists(file_content):
                    file_name = os.path.basename(file_content)
                    file_text = f"📎 文件已生成：{file_name}\n\n由于企业微信智能机器人不支持直接发送文件，请联系管理员获取文件。"
                    logger.info(f"[wechatcom_aibot] File converted to text for {receiver}: {file_name}")
                else:
                    # 如果是URL，直接发送链接
                    file_text = f"📎 文件下载链接：\n{file_content}"
                    logger.info(f"[wechatcom_aibot] File URL converted to text for {receiver}: {file_content}")

                self.cache_dict[receiver].append(("text", file_text))
            else:
                logger.warning(f"[wechatcom_aibot] Unsupported file content type: {type(file_content)}")

        else:
            logger.warning(f"[wechatcom_aibot] Unsupported reply type: {reply.type}")
    
    def _success_callback(self, session_id, context, **kwargs):
        """处理成功的回调"""
        # 对于智能机器人，使用 receiver 作为 key（群聊时是群ID，单聊时是用户ID）
        receiver = context.get("receiver", session_id)
        logger.info(f"[wechatcom_aibot] Success callback - session_id={session_id}, receiver={receiver}, msgId={context.get('msg').msg_id if context.get('msg') else 'unknown'}")
        logger.info(f"[wechatcom_aibot] Current running set: {self.running}")
        if receiver in self.running:
            self.running.remove(receiver)
            logger.info(f"[wechatcom_aibot] Removed {receiver} from running set")

    def _fail_callback(self, session_id, exception, context, **kwargs):
        """处理失败的回调"""
        # 对于智能机器人，使用 receiver 作为 key（群聊时是群ID，单聊时是用户ID）
        receiver = context.get("receiver", session_id)
        logger.exception(f"[wechatcom_aibot] Fail to generate reply, receiver={receiver}, exception={exception}")
        if receiver in self.running:
            self.running.remove(receiver)

    def _generate_stream_id(self):
        """生成唯一的 stream_id"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    def _create_stream_reply(self, stream_id, finish, content, msg_dict, nonce, timestamp):
        """
        创建流式消息回复

        Args:
            stream_id: 流式消息ID
            finish: 是否结束
            content: 消息内容
            msg_dict: 原始消息字典
            nonce: 随机数
            timestamp: 时间戳

        Returns:
            加密后的回复 JSON
        """
        import json
        from channel.wechatcom_aibot.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt

        reply_dict = {
            "msgtype": "stream",
            "stream": {
                "id": stream_id,
                "finish": finish,
                "content": content
            }
        }

        reply_json = json.dumps(reply_dict, ensure_ascii=False)

        # 使用官方的加密库
        # 智能机器人场景中，receiveid 为空字符串
        logger.info(f"[wechatcom_aibot] Encrypting with nonce={nonce}, timestamp={timestamp}")
        wxcpt = WXBizJsonMsgCrypt(self.token, self.aes_key, "")
        ret, encrypted_response = wxcpt.EncryptMsg(reply_json, nonce, timestamp)

        if ret != 0:
            logger.error(f"[wechatcom_aibot] Encrypt message failed, error code: {ret}")
            return "success"

        logger.info(f"[wechatcom_aibot] Sending stream reply - stream_id={stream_id}, finish={finish}, content_len={len(content)}")
        logger.info(f"[wechatcom_aibot] Reply JSON: {reply_json}")
        logger.info(f"[wechatcom_aibot] Encrypted response: {encrypted_response[:200]}...")

        # 设置正确的 Content-Type（参考官方示例）
        web.header('Content-Type', 'text/plain; charset=utf-8')

        return encrypted_response

    def _create_text_reply(self, text_content, msg_dict, nonce, timestamp):
        """创建文本回复（使用 stream 格式，finish=True）"""
        stream_id = self._generate_stream_id()
        return self._create_stream_reply(stream_id, True, text_content, msg_dict, nonce, timestamp)

    def _handle_stream_refresh(self, aibot_msg, crypto, nonce, timestamp):
        """
        处理流式消息刷新

        Args:
            aibot_msg: WechatComAIBotMessage 实例
            crypto: WeChatCrypto 实例
            nonce: 随机数
            timestamp: 时间戳

        Returns:
            加密后的流式消息回复
        """
        import json

        stream_id = aibot_msg.stream_id

        with self.stream_lock:
            session = self.stream_sessions.get(stream_id)

            if not session:
                # 流式会话不存在，返回空回复
                logger.warning(f"[wechatcom_aibot] Stream session not found: {stream_id}")
                return "success"

            # 构造流式消息回复
            reply_dict = {
                "msgtype": "stream",
                "stream": {
                    "id": stream_id,
                    "finish": session.get("finish", False),
                    "content": session.get("content", "")
                }
            }

            # 如果已完成，添加图片（如果有）
            if session.get("finish") and session.get("images"):
                reply_dict["stream"]["msg_item"] = session["images"]

            reply_json = json.dumps(reply_dict, ensure_ascii=False)
            encrypted_reply = crypto.encrypt_message(reply_json, nonce, timestamp)

            logger.info(f"[wechatcom_aibot] Stream refresh reply: stream_id={stream_id}, finish={session.get('finish')}")
            return encrypted_reply


class Query:
    """处理企业微信智能机器人的回调请求"""
    
    def GET(self):
        """验证 URL 有效性"""
        from channel.wechatcom_aibot.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt

        channel = WechatComAIBotChannel()
        params = web.input()

        logger.info(f"[wechatcom_aibot] Received GET request for URL verification: {params}")
        logger.info(f"[wechatcom_aibot] Config values - corp_id: {channel.corp_id}, token: {channel.token}, aes_key: {channel.aes_key}")

        # 检查必要参数
        if not channel.corp_id:
            logger.error("[wechatcom_aibot] corp_id is empty!")
            raise web.Forbidden()
        if not channel.token:
            logger.error("[wechatcom_aibot] token is empty!")
            raise web.Forbidden()
        if not channel.aes_key:
            logger.error("[wechatcom_aibot] aes_key is empty!")
            raise web.Forbidden()

        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce
            echostr = params.echostr

            # 使用官方的验证库
            # 智能机器人场景中，receiveid 为空字符串
            wxcpt = WXBizJsonMsgCrypt(channel.token, channel.aes_key, "")
            ret, reply_echostr = wxcpt.VerifyURL(signature, timestamp, nonce, echostr)

            if ret != 0:
                logger.error(f"[wechatcom_aibot] URL verification failed, error code: {ret}")
                raise web.Forbidden()

            logger.info("[wechatcom_aibot] URL verification successful")
            return reply_echostr

        except Exception as e:
            logger.error(f"[wechatcom_aibot] URL verification failed: {e}")
            raise web.Forbidden()
    
    def POST(self):
        """处理消息回调"""
        from channel.wechatcom_aibot.wechatcom_aibot_message import WechatComAIBotMessage
        from channel.wechatcom_aibot.WXBizJsonMsgCrypt import WXBizJsonMsgCrypt
        import json

        channel = WechatComAIBotChannel()
        params = web.input()
        request_time = time.time()

        logger.info(f"[wechatcom_aibot] Received POST request: {params}")

        try:
            signature = params.msg_signature
            timestamp = params.timestamp
            nonce = params.nonce

            # 获取加密的 JSON 数据
            encrypted_json_data = web.data().decode('utf-8')
            logger.info(f"[wechatcom_aibot] Encrypted JSON data: {encrypted_json_data}")

            # 使用官方的解密库
            # 智能机器人场景中，receiveid 为空字符串
            wxcpt = WXBizJsonMsgCrypt(channel.token, channel.aes_key, "")
            ret, decrypted_message = wxcpt.DecryptMsg(encrypted_json_data, signature, timestamp, nonce)

            if ret != 0:
                logger.error(f"[wechatcom_aibot] Decrypt message failed, error code: {ret}")
                raise web.Forbidden()

            logger.info(f"[wechatcom_aibot] Decrypted message: {decrypted_message}")

            # 解析 JSON
            msg_dict = json.loads(decrypted_message)
            logger.info(f"[wechatcom_aibot] Parsed message dict: {msg_dict}")
            
            # 创建消息对象
            try:
                aibot_msg = WechatComAIBotMessage(msg_dict, client=channel.client, aes_key=channel.aes_key)
            except NotImplementedError as e:
                logger.debug(f"[wechatcom_aibot] {e}")
                return "success"
            
            from_user = aibot_msg.from_user_id
            message_id = aibot_msg.msg_id
            content = aibot_msg.content

            # 确定缓存的 key
            # 单聊：使用用户ID
            # 群聊：使用群ID（与 _send 方法中的 receiver 保持一致）
            cache_key = aibot_msg.chat_id if aibot_msg.is_group else from_user

            logger.info(f"[wechatcom_aibot] Checking cache - cache_key={cache_key}, msgid={message_id}, has_cache={cache_key in channel.cache_dict}, in_running={cache_key in channel.running}")

            # 检查是否是重复的 msgid（用于去重）
            if not hasattr(channel, 'processed_msgids'):
                channel.processed_msgids = {}

            is_duplicate_msgid = message_id in channel.processed_msgids

            # 处理流式消息刷新（企业微信会不断推送这个请求，直到收到 finish=true）
            if aibot_msg.msg_type == "stream":
                logger.info(f"[wechatcom_aibot] Stream refresh request - stream_id={aibot_msg.stream_id}, cache_key={cache_key}")

                # 检查 Dify 是否已完成
                if cache_key in channel.cache_dict and len(channel.cache_dict[cache_key]) > 0:
                    logger.info(f"[wechatcom_aibot] Dify completed, returning final stream message")

                    # 合并所有缓存的文本消息
                    all_content = []
                    cached_items = channel.cache_dict[cache_key]
                    logger.info(f"[wechatcom_aibot] Found {len(cached_items)} cached items")

                    for reply_type, reply_content in cached_items:
                        if reply_type == "text":
                            all_content.append(reply_content)
                            logger.info(f"[wechatcom_aibot] Adding text content: {reply_content[:100]}...")
                        elif reply_type == "image":
                            # 图片暂时不支持在流式消息中发送
                            logger.warning(f"[wechatcom_aibot] Image in cache, but not supported in stream message")
                        elif reply_type == "image_url":
                            # 图片URL暂时不支持在流式消息中发送
                            logger.warning(f"[wechatcom_aibot] Image URL in cache, but not supported in stream message")

                    # 合并所有文本内容
                    final_content = "\n\n".join(all_content)
                    logger.info(f"[wechatcom_aibot] Final merged content length: {len(final_content)}")

                    # 清理缓存
                    del channel.cache_dict[cache_key]
                    if cache_key in channel.running:
                        channel.running.remove(cache_key)
                    if cache_key in channel.stream_ids:
                        del channel.stream_ids[cache_key]

                    # 返回完整内容，finish=true
                    return channel._create_stream_reply(aibot_msg.stream_id, True, final_content, msg_dict, nonce, timestamp)
                else:
                    # Dify 还在处理中，返回空内容，finish=false
                    logger.info(f"[wechatcom_aibot] Dify still processing, returning empty stream message")
                    return channel._create_stream_reply(aibot_msg.stream_id, False, "", msg_dict, nonce, timestamp)

            # 新请求（用户发送消息）
            # 判断条件：不是流式消息刷新 且 不是重复的msgid 且 不在处理中
            if aibot_msg.msg_type != "stream" and not is_duplicate_msgid and cache_key not in channel.running:
                # 第一次请求：立即开始异步处理，立即返回流式消息（finish=false）
                logger.info(f"[wechatcom_aibot] New request - Creating context - is_group={aibot_msg.is_group}, other_user_id={aibot_msg.other_user_id}, cache_key={cache_key}, msgid={message_id}")

                # 标记 msgid 为已处理
                channel.processed_msgids[message_id] = True

                context = channel._compose_context(
                    aibot_msg.ctype,
                    content,
                    isgroup=aibot_msg.is_group,
                    msg=aibot_msg,
                )

                if context:
                    # 处理图文混排消息中的图片
                    logger.info(f"[wechatcom_aibot] Checking for image - hasattr(image_path)={hasattr(aibot_msg, 'image_path')}, image_path={getattr(aibot_msg, 'image_path', None)}")

                    if hasattr(aibot_msg, 'image_path') and aibot_msg.image_path:
                        logger.info(f"[wechatcom_aibot] Mixed message contains image, preparing for upload to Dify")
                        # 下载并解密图片
                        if hasattr(aibot_msg, 'prepare'):
                            logger.info(f"[wechatcom_aibot] Calling aibot_msg.prepare() to download and decrypt image")
                            aibot_msg.prepare()
                            logger.info(f"[wechatcom_aibot] aibot_msg.prepare() completed")

                        # 将图片路径放入缓存，供 Dify bot 使用
                        import common.memory as memory
                        session_id = context.get("session_id")
                        memory.USER_IMAGE_CACHE[session_id] = {
                            "path": aibot_msg.image_path,
                            "msg": aibot_msg
                        }
                        logger.info(f"[wechatcom_aibot] Image cached for session {session_id}: {aibot_msg.image_path}")
                    else:
                        logger.info(f"[wechatcom_aibot] No image in this message")

                    # 智能机器人不需要在回复中添加 @用户名
                    context["no_need_at"] = True
                    channel.running.add(cache_key)
                    logger.info(f"[wechatcom_aibot] Added {cache_key} to running set, producing context...")
                    channel.produce(context)

                    # 生成并保存 stream_id
                    stream_id = channel._generate_stream_id()
                    channel.stream_ids[cache_key] = stream_id

                    # 立即返回流式消息（finish=false），让企业微信开始推送流式消息刷新请求
                    logger.info(f"[wechatcom_aibot] Returning initial stream message - stream_id={stream_id}, cache_key={cache_key}")
                    return channel._create_stream_reply(stream_id, False, "", msg_dict, nonce, timestamp)
                else:
                    logger.warning(f"[wechatcom_aibot] Context is None, skip processing. is_group={aibot_msg.is_group}, chat_id={aibot_msg.chat_id}")
                    return "success"

            # 重复请求（同一个 msgid 的重复请求，可能是网络问题导致的）
            if is_duplicate_msgid:
                logger.warning(f"[wechatcom_aibot] Duplicate msgid={message_id}, cache_key={cache_key}")
                logger.warning(f"[wechatcom_aibot] has_cache={cache_key in channel.cache_dict}, in_running={cache_key in channel.running}")

                # 如果有缓存，返回缓存的回复
                if cache_key in channel.cache_dict and len(channel.cache_dict[cache_key]) > 0:
                    logger.info(f"[wechatcom_aibot] Found cached reply for duplicate request, returning...")

                    # 合并所有缓存的文本消息
                    all_content = []
                    cached_items = channel.cache_dict[cache_key]
                    for reply_type, reply_content in cached_items:
                        if reply_type == "text":
                            all_content.append(reply_content)

                    final_content = "\n\n".join(all_content)

                    # 清理缓存
                    del channel.cache_dict[cache_key]
                    if cache_key in channel.running:
                        channel.running.remove(cache_key)

                    # 返回流式消息（finish=true）
                    stream_id = channel._generate_stream_id()
                    return channel._create_stream_reply(stream_id, True, final_content, msg_dict, nonce, timestamp)

                # 如果还在运行或已完成但没有缓存，返回成功
                logger.info(f"[wechatcom_aibot] No cache for duplicate request, returning success")
                return "success"

            # 未知情况（不应该到达这里）
            logger.warning(f"[wechatcom_aibot] Unknown situation - msgid={message_id}, cache_key={cache_key}, in_running={cache_key in channel.running}")
            return "success"
            
        except Exception as e:
            logger.exception(f"[wechatcom_aibot] Exception in POST handler: {e}")
            return "success"

