# -*- coding: utf-8 -*-
"""
Author: SGA Team
Description: FunASR 语音识别服务
支持 SenseVoice 和 Paraformer 模型
"""

import json
import os
from bridge.reply import Reply, ReplyType
from common.log import logger
from voice.voice import Voice
from voice.funasr.funasr_api import speech_to_text_funasr
from config import conf


class FunASRVoice(Voice):
    def __init__(self):
        """
        初始化 FunASRVoice 类，从配置文件加载必要的配置。
        优先从主配置文件读取，如果没有则从本地配置文件读取。
        """
        try:
            # 尝试读取本地配置文件
            curdir = os.path.dirname(__file__)
            config_path = os.path.join(curdir, "config.json")
            local_config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as fr:
                    local_config = json.load(fr)

            # FunASR 服务地址（优先从主配置读取）
            # SenseVoice: ws://localhost:10095
            # Paraformer: ws://localhost:10096
            self.funasr_url = conf().get("funasr_url", local_config.get("funasr_url", "ws://localhost:10095"))

            # FunASR 模型选择：sensevoice 或 paraformer
            self.funasr_model = conf().get("funasr_model", local_config.get("funasr_model", "sensevoice"))

            # 是否启用逆文本归一化（ITN）
            # ITN: "一千二百" -> "1200"
            self.funasr_enable_itn = conf().get("funasr_enable_itn", local_config.get("funasr_enable_itn", True))

            # 热词（仅 Paraformer 支持）
            # 用空格分隔，例如："人工智能 深度学习 神经网络"
            self.funasr_hotwords = conf().get("funasr_hotwords", local_config.get("funasr_hotwords", ""))

            # 音频采样率
            self.funasr_audio_fs = conf().get("funasr_audio_fs", local_config.get("funasr_audio_fs", 16000))

            logger.info(f"[FunASR] Initialized with model={self.funasr_model}, url={self.funasr_url}")
            if self.funasr_model.lower() == "paraformer" and self.funasr_hotwords:
                logger.info(f"[FunASR] Hotwords enabled: {self.funasr_hotwords}")

        except Exception as e:
            logger.warning(f"[FunASR] Init failed: {e}, ignore")

    def voiceToText(self, voice_file):
        """
        将语音文件转换为文本。

        :param voice_file: 要转换的语音文件路径
        :return: 返回一个 Reply 对象，其中包含转换得到的文本或错误信息
        """
        logger.debug(f"[FunASR] voice file name={voice_file}")

        try:
            # 调用 FunASR API 进行语音识别
            text = speech_to_text_funasr(
                voice_file=voice_file,
                funasr_url=self.funasr_url,
                model=self.funasr_model,
                enable_itn=self.funasr_enable_itn,
                hotwords=self.funasr_hotwords,
                audio_fs=self.funasr_audio_fs
            )

            if text:
                logger.info(f"[FunASR] VoiceToText result: {text}")
                reply = Reply(ReplyType.TEXT, text)
            else:
                logger.error("[FunASR] Voice recognition failed")
                reply = Reply(ReplyType.ERROR, "抱歉，语音识别失败")

            return reply

        except Exception as e:
            logger.error(f"[FunASR] VoiceToText exception: {e}")
            return Reply(ReplyType.ERROR, "抱歉，语音识别出现异常")

    def textToVoice(self, text):
        """
        将文本转换为语音文件。
        FunASR 不支持 TTS，返回错误。

        :param text: 要转换的文本
        :return: 返回一个 Reply 对象，包含错误信息
        """
        logger.warning("[FunASR] textToVoice is not supported by FunASR")
        return Reply(ReplyType.ERROR, "FunASR 不支持文本转语音功能")

