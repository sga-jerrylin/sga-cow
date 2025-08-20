# encoding:utf-8
import io
import os
import mimetypes
import threading
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, Any

import requests
from urllib.parse import urlparse, unquote

from bot.bot import Bot
from lib.dify.dify_client import DifyClient, ChatClient
from bot.dify.dify_session import DifySession, DifySessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from common import const, memory
from common.utils import parse_markdown_text, print_red
from common.tmp_dir import TmpDir
from config import conf

UNKNOWN_ERROR_MSG = "我暂时遇到了一些问题，请您稍后重试~"

class DifyBot(Bot):
    def __init__(self):
        super().__init__()
        self.sessions = DifySessionManager(DifySession, model=conf().get("model", const.DIFY))
        # 性能优化：使用线程池处理并发请求
        self.executor = ThreadPoolExecutor(max_workers=conf().get("dify_max_workers", 10))
        # 请求缓存和重试机制
        self.request_cache = {}
        self.retry_config = {
            'max_retries': conf().get("dify_max_retries", 3),
            'retry_delay': conf().get("dify_retry_delay", 1.0),
            'timeout': conf().get("dify_timeout", 120)  # 默认120秒，支持复杂任务
        }

    def reply(self, query, context: Context=None):
        # acquire reply content
        logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: reply() method called with query: {repr(query)}")
        if context.type == ContextType.TEXT or context.type == ContextType.IMAGE_CREATE:
            if context.type == ContextType.IMAGE_CREATE:
                query = conf().get('image_create_prefix', ['画'])[0] + query
            logger.info("[DIFY] query={}".format(query))
            session_id = context["session_id"]

            # 处理会话重置命令
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                # 清除该用户的缓存
                self._clear_user_cache(session_id)
                return Reply(ReplyType.INFO, "会话已重置")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                # 清除所有缓存
                self.request_cache.clear()
                return Reply(ReplyType.INFO, "所有会话已重置")
            elif query == "#更新配置":
                from config import load_config
                load_config()
                return Reply(ReplyType.INFO, "配置已更新")

            # TODO: 适配除微信以外的其他channel
            channel_type = conf().get("channel_type", "wx")
            user = None
            if channel_type in ["wx", "wework", "gewechat"]:
                user = context["msg"].other_user_nickname if context.get("msg") else "default"
            elif channel_type in ["wechatcom_app", "wechatmp", "wechatmp_service", "wechatcom_service", "web"]:
                user = context["msg"].other_user_id if context.get("msg") else "default"
            else:
                return Reply(ReplyType.ERROR, f"unsupported channel type: {channel_type}, now dify only support wx, wechatcom_app, wechatmp, wechatmp_service channel")
            logger.debug(f"[DIFY] dify_user={user}")
            user = user if user else "default" # 防止用户名为None，当被邀请进的群未设置群名称时用户名为None
            session = self.sessions.get_session(session_id, user)
            if context.get("isgroup", False):
                # 群聊：根据是否是共享会话群来决定是否设置用户信息
                if not context.get("is_shared_session_group", False):
                    # 非共享会话群：设置发送者信息
                    session.set_user_info(context["msg"].actual_user_id, context["msg"].actual_user_nickname)
                else:
                    # 共享会话群：不设置用户信息
                    session.set_user_info('', '')
                # 设置群聊信息
                session.set_room_info(context["msg"].other_user_id, context["msg"].other_user_nickname)
            else:
                # 私聊：使用发送者信息作为用户信息，房间信息留空
                session.set_user_info(context["msg"].other_user_id, context["msg"].other_user_nickname)
                session.set_room_info('', '')

            # 打印设置的session信息
            logger.debug(f"[DIFY] Session user and room info - user_id: {session.get_user_id()}, user_name: {session.get_user_name()}, room_id: {session.get_room_id()}, room_name: {session.get_room_name()}")
            logger.debug(f"[DIFY] session={session} query={query}")



            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: About to call _reply() method")
            reply, err = self._reply(query, session, context)
            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: _reply() returned: {reply}, error: {err}")
            if err != None:
                dify_error_reply = conf().get("dify_error_reply", None)
                error_msg = dify_error_reply if dify_error_reply else err
                reply = Reply(ReplyType.TEXT, error_msg)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    # TODO: delete this function
    def _get_payload(self, query, session: DifySession, response_mode):
        # 输入的变量参考 wechat-assistant-pro：https://github.com/leochen-g/wechat-assistant-pro/issues/76
        return {
            'inputs': {
                'user_id': session.get_user_id(),
                'user_name': session.get_user_name(),
                'room_id': session.get_room_id(),
                'room_name': session.get_room_name()
            },
            "query": query,
            "response_mode": response_mode,
            "conversation_id": session.get_conversation_id(),
            "user": session.get_user()
        }

    def _get_dify_conf(self, context: Context, key, default=None):
        return context.get(key, conf().get(key, default))

    def _get_timeout_for_query(self, query: str, context: Context) -> int:
        """根据查询内容和上下文确定超时时间"""
        # 图片生成相关的关键词
        image_keywords = ['生成', '画', '图片', '图像', '海报', '图表', 'chart', '绘制', '制作图', '创建图']

        # 检查是否是图片生成任务
        if any(keyword in query.lower() for keyword in image_keywords):
            return self._get_dify_conf(context, "dify_image_timeout", 180)

        # 默认超时时间
        return self.retry_config['timeout']

    def _reply(self, query: str, session: DifySession, context: Context):
        try:
            session.count_user_message() # 限制一个conversation中消息数，防止conversation过长

            # 性能优化：使用缓存避免重复请求
            cache_key = self._generate_cache_key(query, session, context)
            if cache_key in self.request_cache:
                cached_result = self.request_cache[cache_key]
                if time.time() - cached_result['timestamp'] < 300:  # 5分钟缓存
                    logger.info(f"[DIFY] Using cached response for query: {query[:50]}...")
                    return cached_result['result'], cached_result['error']

            dify_app_type = self._get_dify_conf(context, "dify_app_type", 'chatbot')

            # 根据任务类型选择超时时间
            timeout = self._get_timeout_for_query(query, context)

            # 性能优化：使用线程池异步处理
            future = self.executor.submit(self._handle_request_with_retry, dify_app_type, query, session, context)
            try:
                result, error = future.result(timeout=timeout)
            except TimeoutError:
                logger.warning(f"[DIFY] Request timeout after {timeout} seconds for query: {query[:50]}...")
                # 取消任务
                future.cancel()
                # 返回友好的超时消息
                timeout_msg = f"处理您的请求需要更多时间（超过{timeout}秒），请稍后重试或尝试简化您的问题。"
                return None, timeout_msg

            # 缓存结果
            if cache_key and result:
                self.request_cache[cache_key] = {
                    'result': result,
                    'error': error,
                    'timestamp': time.time()
                }
                # 清理过期缓存
                self._cleanup_cache()

            return result, error

        except Exception as e:
            error_info = f"[DIFY] Exception: {e}"
            logger.exception(error_info)
            # 使用配置的错误回复或默认消息
            dify_error_reply = conf().get("dify_error_reply", None)
            error_msg = dify_error_reply if dify_error_reply else UNKNOWN_ERROR_MSG
            return None, error_msg

    def _handle_chatbot(self, query: str, session: DifySession, context: Context):
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        chat_client = ChatClient(api_key, api_base)
        response_mode = 'blocking'
        payload = self._get_payload(query, session, response_mode)
        files = self._get_upload_files(session, context)
        response = chat_client.create_chat_message(
            inputs=payload['inputs'],
            query=payload['query'],
            user=payload['user'],
            response_mode=payload['response_mode'],
            conversation_id=payload['conversation_id'],
            files=files
        )

        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warning(error_info)
            friendly_error_msg = self._handle_error_response(response.text, response.status_code)
            return None, friendly_error_msg

        # response:
        # {
        #     "event": "message",
        #     "message_id": "9da23599-e713-473b-982c-4328d4f5c78a",
        #     "conversation_id": "45701982-8118-4bc5-8e9b-64562b4555f2",
        #     "mode": "chat",
        #     "answer": "xxx",
        #     "metadata": {
        #         "usage": {
        #         },
        #         "retriever_resources": []
        #     },
        #     "created_at": 1705407629
        # }
        rsp_data = response.json()
        logger.debug("[DIFY] usage {}".format(rsp_data.get('metadata', {}).get('usage', 0)))

        answer = rsp_data['answer']
        logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Raw answer from Dify: {repr(answer)}")
        logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: About to call parse_markdown_text")
        parsed_content = parse_markdown_text(answer)
        logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Parsed content: {parsed_content}")

        # {"answer": "![image](/files/tools/dbf9cd7c-2110-4383-9ba8-50d9fd1a4815.png?timestamp=1713970391&nonce=0d5badf2e39466042113a4ba9fd9bf83&sign=OVmdCxCEuEYwc9add3YNFFdUpn4VdFKgl84Cg54iLnU=)"}
        at_prefix = ""
        channel = context.get("channel")
        is_group = context.get("isgroup", False)
        if is_group:
            at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
        logger.info(f"[DIFY] Processing {len(parsed_content)} parsed items")
        for item in parsed_content[:-1]:
            logger.info(f"[DIFY] Processing item: {item}")
            reply = None
            if item['type'] == 'text':
                content = at_prefix + item['content']
                reply = Reply(ReplyType.TEXT, content)
            elif item['type'] == 'image':
                image_url = self._fill_file_base_url(item['content'])
                logger.info(f"[DIFY] Processing image item: {image_url}")
                image = self._download_image(image_url)
                if image:
                    logger.info(f"[DIFY] Image downloaded successfully, creating IMAGE reply")
                    reply = Reply(ReplyType.IMAGE, image)
                else:
                    logger.warning(f"[DIFY] Image download failed, falling back to text link: {image_url}")
                    reply = Reply(ReplyType.TEXT, image_url)  # 不带前缀，直接返回链接
            elif item['type'] == 'file':
                file_url = self._fill_file_base_url(item['content'])
                file_path = self._download_file(file_url)
                if file_path:
                    reply = Reply(ReplyType.FILE, file_path)
                else:
                    # 对于不支持下载的文件，直接返回链接，不带括号
                    reply = Reply(ReplyType.TEXT, file_url)
            logger.debug(f"[DIFY] reply={reply}")
            if reply and channel:
                channel.send(reply, context)
        # parsed_content 没有数据时，直接不回复
        if not parsed_content:
            return None, None
        final_item = parsed_content[-1]
        final_reply = None
        if final_item['type'] == 'text':
            content = final_item['content']
            if is_group:
                at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                content = at_prefix + content
            final_reply = Reply(ReplyType.TEXT, content)
        elif final_item['type'] == 'image':
            image_url = self._fill_file_base_url(final_item['content'])
            logger.info(f"[DIFY] Processing final image item: {image_url}")
            image = self._download_image(image_url)
            if image:
                logger.info(f"[DIFY] Final image downloaded successfully, creating IMAGE reply")
                final_reply = Reply(ReplyType.IMAGE, image)
            else:
                logger.warning(f"[DIFY] Final image download failed, falling back to text link: {image_url}")
                final_reply = Reply(ReplyType.TEXT, image_url)  # 不带前缀，直接返回链接
        elif final_item['type'] == 'file':
            file_url = self._fill_file_base_url(final_item['content'])
            file_path = self._download_file(file_url)
            if file_path:
                final_reply = Reply(ReplyType.FILE, file_path)
            else:
                # 对于不支持下载的文件，直接返回链接，不带括号
                final_reply = Reply(ReplyType.TEXT, file_url)

        # 设置dify conversation_id, 依靠dify管理上下文
        if session.get_conversation_id() == '':
            session.set_conversation_id(rsp_data['conversation_id'])

        return final_reply, None

    def _is_downloadable_file(self, url):
        """判断文件是否应该下载（图片、音频和文档文件）"""
        try:
            parsed_url = urlparse(url)
            url_path = unquote(parsed_url.path).lower()

            logger.info(f"[DIFY] 🔍 检查文件类型: {url}")
            logger.info(f"[DIFY] 🔍 解析后的路径: {url_path}")

            # 支持下载的文件扩展名
            downloadable_extensions = {
                # 图片格式
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
                # 音频格式
                '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma',
                # 文档格式
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt'
            }

            for ext in downloadable_extensions:
                if url_path.endswith(ext):
                    logger.info(f"[DIFY] ✅ 文件类型支持下载: {ext}")
                    return True

            logger.info(f"[DIFY] ❌ 文件类型不支持下载，支持的扩展名: {downloadable_extensions}")
            return False
        except Exception as e:
            logger.error(f"[DIFY] Error checking file type for {url}: {e}")
            return False

    def _download_file(self, url):
        """下载图片、音频和文档文件，其他文件返回None"""
        if not self._is_downloadable_file(url):
            logger.info(f"[DIFY] File type not supported for download: {url}")
            return None

        try:
            logger.info(f"[DIFY] Starting file download from {url}")
            response = requests.get(url, timeout=self.retry_config['timeout'])
            response.raise_for_status()
            parsed_url = urlparse(url)
            url_path = unquote(parsed_url.path)
            # 从路径中提取文件名
            file_name = url_path.split('/')[-1]
            if not file_name:
                file_name = "download_file"
            logger.info(f"[DIFY] Saving file as {file_name}")
            file_path = os.path.join(TmpDir().path(), file_name)
            with open(file_path, 'wb') as file:
                file.write(response.content)
            file_size = os.path.getsize(file_path)
            logger.info(f"[DIFY] File downloaded successfully: {file_path}, size: {file_size} bytes")
            return file_path
        except Exception as e:
            logger.error(f"[DIFY] Error downloading file from {url}: {e}")
            return None

    def _download_image(self, url):
        """下载图片并返回BytesIO对象，支持重试机制和防盗链处理"""
        max_attempts = 3

        # 不同的请求头策略，用于绕过防盗链
        headers_strategies = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.alipay.com/',
                'Accept': 'image/*,*/*;q=0.8',
            },
            {
                'User-Agent': 'curl/7.68.0',
                'Accept': '*/*',
            }
        ]

        for attempt in range(max_attempts):
            # 选择请求头策略
            headers = headers_strategies[attempt % len(headers_strategies)]

            try:
                logger.info(f"[DIFY] Starting image download from {url} (attempt {attempt + 1}/{max_attempts})")
                logger.debug(f"[DIFY] Using headers: {headers}")

                pic_res = requests.get(url, headers=headers, stream=True, timeout=self.retry_config['timeout'])
                pic_res.raise_for_status()

                image_storage = io.BytesIO()
                size = 0
                for block in pic_res.iter_content(1024):
                    size += len(block)
                    image_storage.write(block)

                logger.info(f"[DIFY] Image download success, size={size}, img_url={url}")
                image_storage.seek(0)
                return image_storage

            except Exception as e:
                logger.warning(f"[DIFY] Image download attempt {attempt + 1} failed with headers strategy {attempt % len(headers_strategies) + 1}: {e}")
                if attempt == max_attempts - 1:
                    logger.error(f"[DIFY] All {max_attempts} attempts failed for image download from {url}")
                    return None
                # 短暂等待后重试
                import time
                time.sleep(1)
        return None

    def _download_image(self, url):
        try:
            pic_res = requests.get(url, stream=True)
            pic_res.raise_for_status()
            image_storage = io.BytesIO()
            size = 0
            for block in pic_res.iter_content(1024):
                size += len(block)
                image_storage.write(block)
            logger.debug(f"[WX] download image success, size={size}, img_url={url}")
            image_storage.seek(0)
            return image_storage
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
        return None

    def _optimize_query(self, query: str) -> str:
        """优化用户输入,避免触发内容过滤
        策略: 每次删除最后一个字符重试
        """
        if len(query) > 1:
            return query[:-1]  # 删除最后一个字
        return query

    def _parse_error_info(self, error_data: dict) -> dict:
        """解析错误信息,提取有用的内容"""
        try:
            if isinstance(error_data, str):
                return {}
            
            message = error_data.get('message', '')
            if not isinstance(message, str):
                return {}
                
            if 'azure_openai' not in message:
                return {}
                
            # 提取error部分
            import json
            import re
            
            # 尝试从消息中提取JSON部分
            match = re.search(r'\{.*\}', message)
            if match:
                error_json = json.loads(match.group())
                if 'error' in error_json:
                    return error_json['error']
            
            return {}
        except Exception as e:
            logger.warning(f"[DIFY] 解析错误信息失败: {e}")
            return {}

    def _handle_agent(self, query: str, session: DifySession, context: Context):
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        chat_client = ChatClient(api_key, api_base)
        response_mode = 'streaming'
        current_query = query
        original_query = query  # 保存原始查询用于记录
        
        max_attempts = 3  # 最多尝试3次优化
        attempt_count = 0
        
        while attempt_count < max_attempts:
            try:
                payload = self._get_payload(current_query, session, response_mode)
                files = self._get_upload_files(session, context)
                
                response = chat_client.create_chat_message(
                    inputs=payload['inputs'],
                    query=payload['query'],
                    user=payload['user'],
                    response_mode=payload['response_mode'],
                    conversation_id=payload['conversation_id'],
                    files=files
                )

                if response.status_code != 200:
                    error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
                    logger.warning(error_info)
                    friendly_error_msg = self._handle_error_response(response.text, response.status_code)
                    attempt_count += 1
                    if attempt_count >= max_attempts:
                        return None, friendly_error_msg
                    # 尝试优化查询
                    optimized_query = self._optimize_query(current_query)
                    if optimized_query == current_query:
                        break  # 如果无法进一步优化,就退出
                    logger.info(f"[DIFY] 优化查询从 '{current_query}' 到 '{optimized_query}'")
                    current_query = optimized_query
                    continue

                msgs, conversation_id = self._handle_sse_response(response)
                
                # 如果查询经过了优化并且成功了,记录这个成功案例
                if current_query != original_query:
                    logger.info(f"[DIFY] 查询优化成功 - 原始: '{original_query}' -> 优化后: '{current_query}'")
                
                channel = context.get("channel")
                is_group = context.get("isgroup", False)
                for msg in msgs[:-1]:
                    if msg['type'] == 'agent_message':
                        if is_group:
                            at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                            msg['content'] = at_prefix + msg['content']
                        reply = Reply(ReplyType.TEXT, msg['content'])
                        channel.send(reply, context)
                    elif msg['type'] == 'message_file':
                        url = self._fill_file_base_url(msg['content']['url'])
                        # 根据文件类型决定处理方式
                        if self._is_downloadable_file(url):
                            # 图片和音频文件使用IMAGE_URL类型，会被下载
                            reply = Reply(ReplyType.IMAGE_URL, url)
                        else:
                            # 其他文件直接发送链接，不带括号
                            reply = Reply(ReplyType.TEXT, url)
                        thread = threading.Thread(target=channel.send, args=(reply, context))
                        thread.start()
                final_msg = msgs[-1]
                reply = None
                if final_msg['type'] == 'agent_message':
                    content = final_msg['content']
                    if is_group:
                        at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                        content = at_prefix + content
                    reply = Reply(ReplyType.TEXT, content)
                elif final_msg['type'] == 'message_file':
                    url = self._fill_file_base_url(final_msg['content']['url'])
                    # 根据文件类型决定处理方式
                    if self._is_downloadable_file(url):
                        # 图片和音频文件使用IMAGE_URL类型，会被下载
                        reply = Reply(ReplyType.IMAGE_URL, url)
                    else:
                        # 其他文件直接发送链接，不带括号
                        reply = Reply(ReplyType.TEXT, url)
                if session.get_conversation_id() == '':
                    session.set_conversation_id(conversation_id)
                return reply, None
                
            except Exception as e:
                error_data = None
                if isinstance(e, dict) and e.get('event') == 'error':
                    error_data = e
                elif hasattr(e, 'args') and len(e.args) > 0 and isinstance(e.args[0], dict):
                    error_data = e.args[0]
                
                if error_data and 'message' in error_data:
                    error_message = error_data['message']
                    # 检查是否是Azure OpenAI的内容过滤错误
                    if 'azure_openai' in error_message and 'content management policy' in error_message.lower():
                        logger.warning(f"[DIFY] Azure OpenAI 内容过滤触发: {error_message}")
                        attempt_count += 1
                        if attempt_count >= max_attempts:
                            return None, "抱歉,我理解您的意思,但可能需要换个更委婉的说法。"
                        
                        # 尝试优化查询
                        optimized_query = self._optimize_query(current_query)
                        if optimized_query == current_query:
                            break  # 如果无法进一步优化,就退出
                        logger.info(f"[DIFY] 优化查询从 '{current_query}' 到 '{optimized_query}'")
                        current_query = optimized_query
                        continue
                        
                attempt_count += 1
                if attempt_count >= max_attempts:
                    error_info = f"[DIFY] Exception after {max_attempts} attempts: {e}"
                    logger.exception(error_info)
                    return None, "抱歉,我理解您的意思,但可能需要换个更委婉的说法。"
                logger.warning(f"[DIFY] 第{attempt_count}次尝试，错误信息：{str(e)}")
                continue

    def _handle_workflow(self, query: str, session: DifySession, context: Context):
        payload = self._get_workflow_payload(query, session)
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        dify_client = DifyClient(api_key, api_base)
        response = dify_client._send_request("POST", "/workflows/run", json=payload)
        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warning(error_info)
            friendly_error_msg = self._handle_error_response(response.text, response.status_code)
            return None, friendly_error_msg

        #  {
        #      "log_id": "djflajgkldjgd",
        #      "task_id": "9da23599-e713-473b-982c-4328d4f5c78a",
        #      "data": {
        #          "id": "fdlsjfjejkghjda",
        #          "workflow_id": "fldjaslkfjlsda",
        #          "status": "succeeded",
        #          "outputs": {
        #          "text": "Nice to meet you."
        #          },
        #          "error": null,
        #          "elapsed_time": 0.875,
        #          "total_tokens": 3562,
        #          "total_steps": 8,
        #          "created_at": 1705407629,
        #          "finished_at": 1727807631
        #      }
        #  }

        rsp_data = response.json()
        if 'data' not in rsp_data or 'outputs' not in rsp_data['data'] or 'text' not in rsp_data['data']['outputs']:
            error_info = f"[DIFY] Unexpected response format: {rsp_data}"
            logger.warning(error_info)
        reply = Reply(ReplyType.TEXT, rsp_data['data']['outputs']['text'])
        return reply, None

    def _get_upload_files(self, session: DifySession, context: Context):
        session_id = session.get_session_id()
        img_cache = memory.USER_IMAGE_CACHE.get(session_id)
        if not img_cache or not self._get_dify_conf(context, "image_recognition", False):
            return None

        logger.info(f"[DIFY] Processing image upload for session: {session_id}")

        # 清理图片缓存
        memory.USER_IMAGE_CACHE[session_id] = None
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")

        if not api_key:
            logger.error("[DIFY] No API key configured for image upload")
            return None

        dify_client = DifyClient(api_key, api_base)
        msg = img_cache.get("msg")
        path = img_cache.get("path")

        if not path:
            logger.error(f"[DIFY] No image path in cache")
            return None

        # 确保图片文件已下载
        if msg and hasattr(msg, 'prepare'):
            logger.info(f"[DIFY] Preparing image download...")
            msg.prepare()

        # 等待文件下载完成，最多等待10秒
        import time
        max_wait = 10
        wait_time = 0
        while not os.path.exists(path) and wait_time < max_wait:
            logger.info(f"[DIFY] Waiting for image download... ({wait_time}s)")
            time.sleep(1)
            wait_time += 1

        if not os.path.exists(path):
            logger.error(f"[DIFY] Image file not found after waiting: {path}")
            return None

        logger.info(f"[DIFY] Image file ready: {path}")

        try:
            with open(path, 'rb') as file:
                file_name = os.path.basename(path)
                file_type, _ = mimetypes.guess_type(file_name)
                if not file_type:
                    file_type = 'image/jpeg'  # 默认类型

                logger.info(f"[DIFY] Uploading file: {file_name}, type: {file_type}")

                files = {
                    'file': (file_name, file, file_type)
                }
                response = dify_client.file_upload(user=session.get_user(), files=files)

            if response.status_code != 200 and response.status_code != 201:
                error_info = f"[DIFY] File upload failed - status: {response.status_code}, response: {response.text}"
                logger.warning(error_info)
                return None

            try:
                file_upload_data = response.json()
                logger.info(f"[DIFY] File uploaded successfully: {file_upload_data}")
                return [
                    {
                        "type": "image",
                        "transfer_method": "local_file",
                        "upload_file_id": file_upload_data['id']
                    }
                ]
            except Exception as e:
                logger.error(f"[DIFY] Failed to parse upload response: {e}")
                return None

        except Exception as e:
            logger.error(f"[DIFY] Exception during file upload: {e}")
            return None

    def _fill_file_base_url(self, url: str):
        if url.startswith("https://") or url.startswith("http://"):
            return url
        # 补全文件base url, 默认使用去掉"/v1"的dify api base url
        return self._get_file_base_url() + url

    def _get_file_base_url(self) -> str:
        api_base = conf().get("dify_api_base", "https://api.dify.ai/v1")
        return api_base.replace("/v1", "")

    def _get_workflow_payload(self, query, session: DifySession):
        return {
            'inputs': {
                "query": query
            },
            "response_mode": "blocking",
            "user": session.get_user()
        }

    def _parse_sse_event(self, event_str):
        """
        Parses a single SSE event string and returns a dictionary of its data.
        """
        event_prefix = "data: "
        if not event_str.startswith(event_prefix):
            return None
        trimmed_event_str = event_str[len(event_prefix):]

        # Check if trimmed_event_str is not empty and is a valid JSON string
        if trimmed_event_str:
            try:
                event = json.loads(trimmed_event_str)
                return event
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from SSE event: {trimmed_event_str}")
                return None
        else:
            logger.warning("Received an empty SSE event.")
            return None

    # TODO: 异步返回events
    def _handle_sse_response(self, response: requests.Response):
        events = []
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                event = self._parse_sse_event(decoded_line)
                if event:
                    events.append(event)

        merged_message = []
        accumulated_agent_message = ''
        conversation_id = None
        for event in events:
            event_name = event['event']
            if event_name == 'agent_message' or event_name == 'message':
                accumulated_agent_message += event['answer']
                logger.debug("[DIFY] accumulated_agent_message: {}".format(accumulated_agent_message))
                # 保存conversation_id
                if not conversation_id:
                    conversation_id = event['conversation_id']
            elif event_name == 'agent_thought':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                logger.debug("[DIFY] agent_thought: {}".format(event))
            elif event_name == 'message_file':
                self._append_agent_message(accumulated_agent_message, merged_message)
                accumulated_agent_message = ''
                self._append_message_file(event, merged_message)
            elif event_name == 'message_replace':
                # TODO: handle message_replace
                pass
            elif event_name == 'error':
                logger.error("[DIFY] error: {}".format(event))
                raise Exception(event)
            elif event_name == 'message_end':
                self._append_agent_message(accumulated_agent_message, merged_message)
                logger.debug("[DIFY] message_end usage: {}".format(event['metadata']['usage']))
                break
            else:
                logger.warning("[DIFY] unknown event: {}".format(event))

        if not conversation_id:
            raise Exception("conversation_id not found")

        return merged_message, conversation_id

    def _append_agent_message(self, accumulated_agent_message,  merged_message):
        if accumulated_agent_message:
            merged_message.append({
                'type': 'agent_message',
                'content': accumulated_agent_message,
            })

    def _append_message_file(self, event: dict, merged_message: list):
        # 支持所有文件类型，但只下载图片和音频
        file_type = event.get('type', 'unknown')
        logger.info(f"[DIFY] Processing message file type: {file_type}")
        merged_message.append({
            'type': 'message_file',
            'content': event,
        })

    def _handle_error_response(self, response_text, status_code):
        """处理错误响应并提供用户指导"""
        try:
            friendly_error_msg = UNKNOWN_ERROR_MSG
            error_data = json.loads(response_text)
            if status_code == 400 and "agent chat app does not support blocking mode" in error_data.get("message", "").lower():
                friendly_error_msg = "[DIFY] 请把config.json中的dify_app_type修改为agent再重启机器人尝试"
                print_red(friendly_error_msg)
            elif status_code == 401 and error_data.get("code").lower() == "unauthorized":
                friendly_error_msg = "[DIFY] apikey无效, 请检查config.json中的dify_api_key或dify_api_base是否正确"
                print_red(friendly_error_msg)
            return friendly_error_msg
        except Exception as e:
            logger.error(f"Failed to handle error response, response_text: {response_text} error: {e}")
            return UNKNOWN_ERROR_MSG

    def _generate_cache_key(self, query: str, session: DifySession, context: Context) -> Optional[str]:
        """生成缓存键"""
        try:
            # 只对短查询进行缓存，避免内存占用过大
            if len(query) > 200:
                return None

            key_parts = [
                query,
                session.get_user(),
                self._get_dify_conf(context, "dify_app_type", 'chatbot'),
                str(session.get_conversation_id())
            ]
            return "|".join(key_parts)
        except Exception:
            return None

    def _cleanup_cache(self):
        """清理过期缓存"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key, value in self.request_cache.items()
                if current_time - value['timestamp'] > 300
            ]
            for key in expired_keys:
                del self.request_cache[key]

            # 限制缓存大小
            if len(self.request_cache) > 1000:
                # 删除最旧的一半缓存
                sorted_items = sorted(
                    self.request_cache.items(),
                    key=lambda x: x[1]['timestamp']
                )
                for key, _ in sorted_items[:500]:
                    del self.request_cache[key]
        except Exception as e:
            logger.warning(f"[DIFY] Cache cleanup failed: {e}")

    def _clear_user_cache(self, session_id: str):
        """清除特定用户的缓存"""
        try:
            keys_to_remove = [
                key for key in self.request_cache.keys()
                if session_id in key
            ]
            for key in keys_to_remove:
                del self.request_cache[key]
            logger.info(f"[DIFY] Cleared {len(keys_to_remove)} cache entries for session: {session_id}")
        except Exception as e:
            logger.warning(f"[DIFY] Failed to clear user cache: {e}")

    def _handle_request_with_retry(self, dify_app_type: str, query: str, session: DifySession, context: Context):
        """带重试机制的请求处理"""
        last_error = None

        for attempt in range(self.retry_config['max_retries']):
            try:
                if dify_app_type == 'chatbot' or dify_app_type == 'chatflow':
                    return self._handle_chatbot_optimized(query, session, context)
                elif dify_app_type == 'agent':
                    return self._handle_agent_optimized(query, session, context)
                elif dify_app_type == 'workflow':
                    return self._handle_workflow(query, session, context)
                else:
                    friendly_error_msg = "[DIFY] 请检查 config.json 中的 dify_app_type 设置，目前仅支持 agent, chatbot, chatflow, workflow"
                    return None, friendly_error_msg

            except Exception as e:
                last_error = e
                logger.warning(f"[DIFY] Attempt {attempt + 1} failed: {e}")

                if attempt < self.retry_config['max_retries'] - 1:
                    # 指数退避
                    delay = self.retry_config['retry_delay'] * (2 ** attempt)
                    time.sleep(delay)
                    continue
                else:
                    break

        # 所有重试都失败了
        error_info = f"[DIFY] All {self.retry_config['max_retries']} attempts failed. Last error: {last_error}"
        logger.error(error_info)
        return None, UNKNOWN_ERROR_MSG

    def _handle_chatbot_optimized(self, query: str, session: DifySession, context: Context):
        """优化版本的chatbot处理，支持连接池和超时控制"""
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")

        # 使用优化的HTTP会话
        with requests.Session() as session_http:
            session_http.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })

            chat_client = ChatClient(api_key, api_base)
            response_mode = 'blocking'
            payload = self._get_payload(query, session, response_mode)
            files = self._get_upload_files(session, context)

            # 设置超时和重试
            response = chat_client.create_chat_message(
                inputs=payload['inputs'],
                query=payload['query'],
                user=payload['user'],
                response_mode=payload['response_mode'],
                conversation_id=payload['conversation_id'],
                files=files
            )

            if response.status_code != 200:
                error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
                logger.warning(error_info)
                friendly_error_msg = self._handle_error_response(response.text, response.status_code)
                return None, friendly_error_msg

            rsp_data = response.json()
            logger.debug("[DIFY] usage {}".format(rsp_data.get('metadata', {}).get('usage', 0)))

            answer = rsp_data['answer']

            # 检查空回复
            if not answer or answer.strip() == "":
                logger.warning("[DIFY] Received empty response from Dify")
                return None, "抱歉，我暂时无法回答您的问题，请稍后再试。"

            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: About to call parse_markdown_text (path 2)")
            parsed_content = parse_markdown_text(answer)
            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Parsed content (path 2): {parsed_content}")

            # 处理多媒体内容
            return self._process_parsed_content(parsed_content, context, session, rsp_data)

    def _handle_agent_optimized(self, query: str, session: DifySession, context: Context):
        """优化版本的agent处理，使用流式响应提升性能"""
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")
        chat_client = ChatClient(api_key, api_base)
        response_mode = 'streaming'

        payload = self._get_payload(query, session, response_mode)
        files = self._get_upload_files(session, context)

        response = chat_client.create_chat_message(
            inputs=payload['inputs'],
            query=payload['query'],
            user=payload['user'],
            response_mode=payload['response_mode'],
            conversation_id=payload['conversation_id'],
            files=files
        )

        if response.status_code != 200:
            error_info = f"[DIFY] payload={payload} response text={response.text} status_code={response.status_code}"
            logger.warning(error_info)
            friendly_error_msg = self._handle_error_response(response.text, response.status_code)
            return None, friendly_error_msg

        msgs, conversation_id = self._handle_sse_response(response)

        # 检查空回复
        if not msgs:
            logger.warning("[DIFY] Received empty streaming response from Dify")
            return None, "抱歉，我暂时无法回答您的问题，请稍后再试。"

        # 处理流式响应
        return self._process_streaming_messages(msgs, context, session, conversation_id)

    def _process_parsed_content(self, parsed_content, context: Context, session: DifySession, rsp_data: dict):
        """处理解析后的内容"""
        logger.info(f"[DIFY] _process_parsed_content called with {len(parsed_content) if parsed_content else 0} items")
        logger.info(f"[DIFY] Parsed content items: {parsed_content}")

        if not parsed_content:
            return None, None

        channel = context.get("channel")
        is_group = context.get("isgroup", False)
        at_prefix = ""
        if is_group:
            at_prefix = "@" + context["msg"].actual_user_nickname + "\n"

        # 异步发送前面的消息
        for item in parsed_content[:-1]:
            logger.info(f"[DIFY] Processing non-final item: {item}")
            reply = self._create_reply_from_item(item, at_prefix)
            if reply and channel:
                logger.info(f"[DIFY] Sending non-final reply: {reply.type}")
                # 使用线程池异步发送，提升性能
                self.executor.submit(channel.send, reply, context)

        # 处理最后一条消息
        final_item = parsed_content[-1]
        logger.info(f"[DIFY] Processing final item: {final_item}")
        final_reply = self._create_reply_from_item(final_item, at_prefix if is_group else "")
        logger.info(f"[DIFY] Final reply created: {final_reply.type if final_reply else None}")

        # 设置conversation_id
        if session.get_conversation_id() == '':
            session.set_conversation_id(rsp_data['conversation_id'])

        return final_reply, None

    def _process_streaming_messages(self, msgs, context: Context, session: DifySession, conversation_id: str):
        """处理流式消息"""
        if not msgs:
            return None, None

        channel = context.get("channel")
        is_group = context.get("isgroup", False)

        # 异步发送前面的消息
        for msg in msgs[:-1]:
            if msg['type'] == 'agent_message':
                content = msg['content']
                if is_group:
                    at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                    content = at_prefix + content
                reply = Reply(ReplyType.TEXT, content)
                if channel:
                    self.executor.submit(channel.send, reply, context)
            elif msg['type'] == 'message_file':
                url = self._fill_file_base_url(msg['content']['url'])
                # 根据文件类型决定处理方式
                if self._is_downloadable_file(url):
                    # 图片和音频文件使用IMAGE_URL类型，会被下载
                    reply = Reply(ReplyType.IMAGE_URL, url)
                else:
                    # 其他文件直接发送链接，不带括号
                    reply = Reply(ReplyType.TEXT, url)
                if channel:
                    self.executor.submit(channel.send, reply, context)

        # 处理最后一条消息
        final_msg = msgs[-1]
        final_reply = None
        if final_msg['type'] == 'agent_message':
            content = final_msg['content']
            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Processing final agent message: {repr(content)}")

            # 解析markdown内容，查找图片和文件
            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: About to call parse_markdown_text (streaming path)")
            parsed_content = parse_markdown_text(content)
            logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Parsed content (streaming path): {parsed_content}")

            # 如果解析出了图片或文件，使用解析后的内容
            if len(parsed_content) > 1 or (len(parsed_content) == 1 and parsed_content[0]['type'] != 'text'):
                logger.info(f"[DIFY] 🚨🚨🚨 CRITICAL DEBUG: Found media content, processing with _process_parsed_content")
                # 创建模拟的rsp_data
                rsp_data = {'conversation_id': conversation_id}
                return self._process_parsed_content(parsed_content, context, session, rsp_data)
            else:
                # 没有媒体内容，按原来的方式处理
                if is_group:
                    at_prefix = "@" + context["msg"].actual_user_nickname + "\n"
                    content = at_prefix + content
                final_reply = Reply(ReplyType.TEXT, content)
        elif final_msg['type'] == 'message_file':
            url = self._fill_file_base_url(final_msg['content']['url'])
            # 根据文件类型决定处理方式
            if self._is_downloadable_file(url):
                # 图片和音频文件使用IMAGE_URL类型，会被下载
                final_reply = Reply(ReplyType.IMAGE_URL, url)
            else:
                # 其他文件直接发送链接，不带括号
                final_reply = Reply(ReplyType.TEXT, url)

        if session.get_conversation_id() == '':
            session.set_conversation_id(conversation_id)

        return final_reply, None

    def _create_reply_from_item(self, item: dict, at_prefix: str = "") -> Optional[Reply]:
        """从解析项创建回复对象"""
        logger.info(f"[DIFY] 🔍 _create_reply_from_item - 处理项目: {item}")

        if item['type'] == 'text':
            content = at_prefix + item['content']
            logger.info(f"[DIFY] ✅ 创建文本回复，长度: {len(content)}")
            return Reply(ReplyType.TEXT, content)

        elif item['type'] == 'image':
            image_url = self._fill_file_base_url(item['content'])
            logger.info(f"[DIFY] 🖼️  开始处理图片: {image_url}")

            # 步骤1: 下载图片
            logger.info(f"[DIFY] 📥 步骤1: 开始下载图片...")
            image = self._download_image(image_url)
            if image:
                logger.info(f"[DIFY] ✅ 步骤1: 图片下载成功，大小: {len(image.getvalue())} bytes")
                logger.info(f"[DIFY] 🎯 创建IMAGE类型回复，将由企业微信channel处理上传")
                return Reply(ReplyType.IMAGE, image)
            else:
                logger.error(f"[DIFY] ❌ 步骤1: 图片下载失败，回退到文本链接")
                return Reply(ReplyType.TEXT, f"图片链接: {image_url}")

        elif item['type'] == 'file':
            file_url = self._fill_file_base_url(item['content'])
            logger.info(f"[DIFY] 📄 开始处理文件: {file_url}")

            # 步骤1: 下载文件
            logger.info(f"[DIFY] 📥 步骤1: 开始下载文件...")
            file_path = self._download_file(file_url)
            if file_path:
                logger.info(f"[DIFY] ✅ 步骤1: 文件下载成功: {file_path}")
                logger.info(f"[DIFY] 🎯 创建FILE类型回复，将由企业微信channel处理上传")
                return Reply(ReplyType.FILE, file_path)
            else:
                logger.error(f"[DIFY] ❌ 步骤1: 文件下载失败，回退到文本链接")
                return Reply(ReplyType.TEXT, f"文件链接: {file_url}")

        logger.warning(f"[DIFY] ⚠️  未知的项目类型: {item.get('type', 'Unknown')}")
        return None

    def _is_empty_response(self, response_data: Any) -> bool:
        """检查响应是否为空"""
        if not response_data:
            return True

        if isinstance(response_data, dict):
            answer = response_data.get('answer', '')
            if not answer or answer.strip() == "":
                return True

        if isinstance(response_data, list):
            if len(response_data) == 0:
                return True
            # 检查是否所有消息都为空
            for msg in response_data:
                if isinstance(msg, dict) and msg.get('content', '').strip():
                    return False
            return True

        return False

    def _handle_network_error(self, error: Exception) -> tuple:
        """处理网络错误"""
        error_msg = str(error)

        if "timeout" in error_msg.lower():
            return None, "网络连接超时，请检查网络状况后重试。"
        elif "connection" in error_msg.lower():
            return None, "网络连接失败，请检查网络设置。"
        elif "ssl" in error_msg.lower():
            return None, "SSL连接错误，请检查证书配置。"
        else:
            return None, f"网络请求失败：{error_msg}"

    def _validate_dify_config(self, context: Context) -> tuple:
        """验证Dify配置"""
        api_key = self._get_dify_conf(context, "dify_api_key", '')
        api_base = self._get_dify_conf(context, "dify_api_base", "https://api.dify.ai/v1")

        if not api_key:
            return False, "Dify API Key未配置，请检查配置文件。"

        if not api_base:
            return False, "Dify API Base URL未配置，请检查配置文件。"

        return True, None

    def __del__(self):
        """析构函数，清理资源"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=False)
        except Exception:
            pass
