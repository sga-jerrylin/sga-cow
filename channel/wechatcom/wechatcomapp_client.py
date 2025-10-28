# wechatcomapp_client.py
import threading
import time
import requests
from wechatpy.enterprise import WeChatClient
from common.log import logger

class WechatComAppClient(WeChatClient):
    def __init__(self, corp_id, secret, access_token=None, session=None, timeout=None, auto_retry=True):
        super(WechatComAppClient, self).__init__(corp_id, secret, access_token, session, timeout, auto_retry)
        self.fetch_access_token_lock = threading.Lock()
        self._active_refresh()
        
    def _active_refresh(self):
        """启动主动刷新的后台线程"""
        def refresh_loop():
            while True:
                now = time.time()
                expires_at = self.session.get(f"{self.corp_id}_expires_at", 0)
                
                # 提前10分钟刷新(600秒)
                if expires_at - now < 600:
                    with self.fetch_access_token_lock:
                        # 双重检查避免重复刷新
                        if self.session.get(f"{self.corp_id}_expires_at", 0) - time.time() < 600:
                            super(WechatComAppClient, self).fetch_access_token()
                # 每次检查间隔60秒
                time.sleep(60)
                
        # 启动守护线程
        refresh_thread = threading.Thread(
            target=refresh_loop,
            daemon=True,
            name="wechatcom_token_refresh_thread"
        )
        refresh_thread.start()

    def fetch_access_token(self):
        with self.fetch_access_token_lock:
            access_token = self.session.get(self.access_token_key)
            expires_at = self.session.get(f"{self.corp_id}_expires_at", 0)

            if access_token and expires_at > time.time() + 60:
                return access_token
            return super().fetch_access_token()

    def download_hd_voice(self, media_id):
        """
        下载高清语音素材（16K speex格式）

        使用 /cgi-bin/media/get/jssdk 接口获取高清语音
        相比普通接口（8K amr），高清语音（16K speex）更适合语音识别

        Args:
            media_id: 媒体文件ID

        Returns:
            requests.Response: 响应对象，包含 speex 格式的语音数据
        """
        try:
            access_token = self.access_token
            url = f"https://qyapi.weixin.qq.com/cgi-bin/media/get/jssdk?access_token={access_token}&media_id={media_id}"

            logger.info(f"[wechatcom] Downloading HD voice with media_id: {media_id}")
            response = requests.get(url, timeout=30)

            # 检查是否成功
            if response.status_code == 200:
                # 检查是否是错误响应（JSON格式）
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    # 可能是错误响应
                    try:
                        error_data = response.json()
                        logger.warning(f"[wechatcom] HD voice download failed: {error_data}")
                        return None
                    except:
                        pass

                logger.info(f"[wechatcom] HD voice downloaded successfully, size: {len(response.content)} bytes")
                return response
            else:
                logger.warning(f"[wechatcom] HD voice download failed with status code: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"[wechatcom] Exception when downloading HD voice: {e}")
            return None