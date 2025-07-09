#!/usr/bin/env python3
"""
火山引擎流式语音识别

基于火山引擎大模型流式语音识别API的实现
"""

import asyncio
import websockets
import json
import struct
import gzip
import uuid
import time
import threading
import logging
from typing import Optional, Dict, Any, Callable
import numpy as np

# 检查 PyAudio 是否可用
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None

from PySide6.QtCore import QObject, Signal

# 设置日志
logger = logging.getLogger(__name__)

# 配置日志格式，确保能看到详细信息
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)  # 设置为INFO级别以显示更多信息

class VolcengineVoiceRecognitionEngine(QObject):
    """火山引擎语音识别引擎"""

    # 信号定义
    command_recognized = Signal(str, str)  # 命令类型, 原始文本
    recognition_started = Signal()
    recognition_stopped = Signal()
    error_occurred = Signal(str)
    status_changed = Signal(str)
    audio_level_changed = Signal(int)  # 音频电平变化 (0-100)

    def __init__(self, config: Dict[str, Any]):
        super().__init__()

        # 火山引擎配置
        self.app_id = config.get("app_id", "")
        self.access_token = config.get("access_token", "")
        self.secret_key = config.get("secret_key", "")

        # WebSocket配置 - 修正URL
        self.ws_url = "wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
        self.resource_id = "volc.bigasr.sauc.duration"  # 小时版

        # 音频参数 - 优化延迟
        self.sample_rate = config.get("sample_rate", 16000)
        self.chunk_size = config.get("chunk_size", 1024)  # 减小块大小降低延迟
        self.channels = config.get("channels", 1)
        self.microphone_index = config.get("microphone_index", -1)  # -1表示默认设备
        self.format = pyaudio.paInt16 if PYAUDIO_AVAILABLE else None
        self.low_latency_mode = config.get("low_latency_mode", True)  # 低延迟模式

        # 状态管理
        self.is_listening = False
        self.websocket = None
        self.audio_stream = None
        self.audio_thread = None
        self.current_audio_level = 0

        # 音频缓冲和序列号
        self.audio_buffer = []
        self.sequence_number = 1  # 从1开始

        # 指令去重机制 - 彻底阻止重复处理
        self.last_processed_text = ""  # 上次处理的文本
        self.last_command_time = 0     # 上次命令时间
        self.command_timeout = 3.0     # 命令超时时间（秒）
        self.processing_lock = False   # 处理锁，防止并发处理

        # 测试状态管理 - 防止测试完成后继续处理旧指令
        self.test_in_progress = False  # 是否正在测试
        self.test_completed_time = 0   # 测试完成时间
        self.test_timeout = 10.0       # 测试完成后的指令忽略时间（秒）

        # 重连机制
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 5  # 秒

        # 初始化音频系统
        self.audio = None
        self._init_audio_system()
    
    def _init_audio_system(self) -> None:
        """初始化音频系统"""
        if not PYAUDIO_AVAILABLE:
            logger.warning("PyAudio未安装，语音功能不可用")
            self.audio = None
            return

        try:
            if PYAUDIO_AVAILABLE:
                self.audio = pyaudio.PyAudio()
                logger.info("音频系统初始化成功")
            else:
                self.audio = None
                logger.warning("PyAudio不可用，语音功能将被禁用")
        except Exception as e:
            logger.error(f"音频系统初始化失败: {e}")
            self.error_occurred.emit(f"音频系统初始化失败: {str(e)}")
            self.audio = None
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return (self.audio is not None and 
                bool(self.app_id) and 
                bool(self.access_token))
    
    def get_status(self) -> str:
        """获取当前状态"""
        if not self.is_available():
            return "火山引擎语音识别不可用"
        elif self.is_listening:
            return "正在监听语音命令（火山引擎）"
        else:
            return "火山引擎语音识别已就绪"
    
    def _create_headers(self) -> Dict[str, str]:
        """创建WebSocket连接头"""
        connect_id = str(uuid.uuid4())
        
        headers = {
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": self.resource_id,
            "X-Api-Connect-Id": connect_id
        }
        
        return headers
    
    def _create_protocol_header(self, message_type: int, flags: int = 0, 
                               serialization: int = 1, compression: int = 0) -> bytes:
        """创建协议头"""
        # Protocol version (4 bits) + Header size (4 bits)
        byte0 = (0b0001 << 4) | 0b0001  # version 1, header size 1
        
        # Message type (4 bits) + Message type specific flags (4 bits)
        byte1 = (message_type << 4) | flags
        
        # Message serialization method (4 bits) + Message compression (4 bits)
        byte2 = (serialization << 4) | compression
        
        # Reserved (8 bits)
        byte3 = 0x00
        
        return struct.pack('>BBBB', byte0, byte1, byte2, byte3)
    
    def _create_full_client_request(self) -> bytes:
        """创建完整客户端请求"""
        request_data = {
            "user": {
                "uid": "python_client"
            },
            "audio": {
                "format": "pcm",  # 使用PCM格式，与Java示例一致
                "sample_rate": self.sample_rate,
                "bits": 16,
                "channel": self.channels,
                "codec": "raw"
            },
            "request": {
                "model_name": "bigmodel",
                "enable_punc": True
            }
        }

        # 序列化为JSON
        json_str = json.dumps(request_data, ensure_ascii=False)
        json_bytes = json_str.encode('utf-8')

        # 使用GZIP压缩，与Java示例一致
        compressed_payload = gzip.compress(json_bytes)

        # 创建协议头 - 包含sequence字段
        header = self._create_protocol_header(
            message_type=0b0001,  # full client request
            flags=0b0001,         # POS_SEQUENCE - 包含sequence字段
            serialization=0b0001, # JSON
            compression=0b0001    # GZIP压缩
        )

        # 创建完整消息: header + sequence + payload_size + payload
        sequence_bytes = struct.pack('>I', self.sequence_number)
        payload_size = struct.pack('>I', len(compressed_payload))

        return header + sequence_bytes + payload_size + compressed_payload
    
    def _create_audio_request(self, audio_data: bytes, is_last: bool = False) -> bytes:
        """创建音频请求"""
        # 增加序列号
        self.sequence_number += 1

        # 根据Java示例设置flags和序列号
        if is_last:
            # 最后一包：NEG_WITH_SEQUENCE (0b0011)
            flags = 0b0011
            sequence = -self.sequence_number  # 负序列号表示最后一包
        else:
            # 普通包：POS_SEQUENCE (0b0001)
            flags = 0b0001
            sequence = self.sequence_number

        # 使用GZIP压缩音频数据，与Java示例一致
        compressed_audio = gzip.compress(audio_data)

        # 创建协议头
        header = self._create_protocol_header(
            message_type=0b0010,  # audio only request
            flags=flags,
            serialization=0b0001, # JSON (与Java示例一致)
            compression=0b0001    # GZIP压缩
        )

        # 创建完整消息: header + sequence + payload_size + payload
        sequence_bytes = struct.pack('>I', sequence & 0xFFFFFFFF)  # 处理负数
        payload_size = struct.pack('>I', len(compressed_audio))

        return header + sequence_bytes + payload_size + compressed_audio
    
    async def _connect_websocket(self) -> bool:
        """连接WebSocket"""
        try:
            headers = self._create_headers()

            logger.info(f"连接火山引擎WebSocket: {self.ws_url}")
            logger.info(f"使用headers: {headers}")

            # 连接WebSocket
            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,  # 使用 extra_headers 而不是 additional_headers
                ping_interval=60,  # 增加心跳间隔
                ping_timeout=30,   # 增加心跳超时
                close_timeout=30   # 增加关闭超时
            )

            logger.info("WebSocket连接成功")
            return True

        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            self.error_occurred.emit(f"连接失败: {str(e)}")
            return False
    
    async def _send_full_request(self) -> bool:
        """发送完整请求"""
        try:
            request_data = self._create_full_client_request()
            logger.info(f"发送完整请求，数据长度: {len(request_data)}")
            await self.websocket.send(request_data)

            # 等待响应
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            logger.info(f"收到初始响应，长度: {len(response)}")

            # 处理初始响应
            await self._handle_response(response)
            return True

        except asyncio.TimeoutError:
            logger.error("发送完整请求超时")
            self.error_occurred.emit("发送请求超时")
            return False
        except Exception as e:
            logger.error(f"发送完整请求失败: {e}")
            self.error_occurred.emit(f"发送请求失败: {str(e)}")
            return False
    
    async def _handle_response(self, response: bytes) -> None:
        """处理服务器响应 - 根据Java示例实现"""
        try:
            if len(response) < 12:  # 最小长度：header(4) + sequence(4) + payload_size(4)
                logger.warning(f"响应数据太短: {len(response)} bytes")
                return

            # 解析协议头 - 与Java示例一致
            header = response[:4]
            protocol_version = (header[0] >> 4) & 0x0F
            header_size = header[0] & 0x0F
            message_type = (header[1] >> 4) & 0x0F
            message_type_specific_flags = header[1] & 0x0F
            serialization_method = (header[2] >> 4) & 0x0F
            message_compression = header[2] & 0x0F
            reserved = header[3]

            # 解析sequence字段 (4 bytes)
            sequence = struct.unpack('>I', response[4:8])[0]

            # 解析payload size (4 bytes)
            payload_size = struct.unpack('>I', response[8:12])[0]

            # 提取payload
            if len(response) < 12 + payload_size:
                logger.warning(f"payload数据不完整: 期望{payload_size}, 实际{len(response) - 12}")
                return

            payload = response[12:12 + payload_size]

            logger.debug(f"响应解析: 消息类型={message_type}, 序列号={sequence}, 负载大小={payload_size}")

            # 根据消息类型处理
            if message_type == 0b1001:  # FULL_SERVER_RESPONSE
                try:
                    # 根据压缩方式解压payload
                    if message_compression == 0b0001:  # GZIP
                        payload_str = gzip.decompress(payload).decode('utf-8')
                    else:
                        payload_str = payload.decode('utf-8')

                    logger.debug(f"payload内容: {payload_str}")

                    # 解析JSON响应
                    json_data = json.loads(payload_str)

                    if 'result' in json_data and json_data['result']:
                        result = json_data['result']
                        if 'text' in result and result['text']:
                            text = result['text'].strip()
                            if text:
                                # 彻底阻止重复处理 - 使用处理锁
                                if self.processing_lock:
                                    logger.debug(f"正在处理中，忽略: {text}")
                                    return

                                # 🔥 检查是否应该忽略旧指令（测试完成后）
                                if self._should_ignore_old_commands():
                                    # 只允许"开始测试"指令通过
                                    if "开始" not in text and "测试" not in text:
                                        logger.debug(f"测试已完成，忽略旧指令: {text}")
                                        return
                                    else:
                                        logger.info(f"检测到新的开始测试指令: {text}")
                                        # 重置测试状态，允许新测试
                                        self.set_test_in_progress(True)

                                # 检查是否是重复的指令
                                if self._is_duplicate_command(text):
                                    logger.debug(f"忽略重复指令: {text}")
                                    return

                                # 设置处理锁，防止并发处理
                                self.processing_lock = True

                                try:
                                    # 分析命令类型
                                    command_type = self._analyze_text(text)

                                    # 只有识别到有效命令才记录日志，不在这里发送信号
                                    if command_type != "speech_text":
                                        logger.info(f"识别结果: {text} -> {command_type}")
                                        # 更新最后处理的指令信息
                                        self._update_last_command(text)
                                    else:
                                        logger.debug(f"忽略无效命令: {text}")

                                finally:
                                    # 释放处理锁
                                    self.processing_lock = False

                    # 检查是否是最后一包
                    is_last_package = sequence < 0
                    if is_last_package:
                        logger.info("收到最后一包响应")

                except gzip.BadGzipFile as e:
                    logger.error(f"GZIP解压失败: {e}")
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}, 原始数据: {payload}")
                except UnicodeDecodeError as e:
                    logger.error(f"UTF-8解码失败: {e}")

            elif message_type == 0b1011:  # SERVER_ACK
                payload_str = payload.decode('utf-8')
                logger.debug(f"服务器ACK: {payload_str}")

            elif message_type == 0b1111:  # SERVER_ERROR_RESPONSE
                # 根据Java示例，此时sequence是错误码，payload是错误消息
                error_code = sequence
                error_msg = payload.decode('utf-8') if payload else f"错误码: {error_code}"
                logger.error(f"服务器错误: 代码={error_code}, 消息={error_msg}")
                self.error_occurred.emit(f"服务器错误: {error_msg}")

            else:
                logger.warning(f"未知消息类型: {message_type:04b}")

        except Exception as e:
            logger.error(f"处理响应失败: {e}")
            self.error_occurred.emit(f"处理响应失败: {str(e)}")
    
    def _analyze_text(self, text: str) -> str:
        """分析识别文本，确定命令类型（只处理最新指令）"""
        text_lower = text.lower().strip()

        # 🔥 关键修复：新指令来了，立即清空所有缓存和状态
        self._clear_audio_buffer()

        # 🔥 重置处理锁，确保不会被之前的处理阻塞
        self.processing_lock = False

        logger.info(f"🔥 新指令到达，清空所有缓存: {text}")

        # 检测所有可能的命令
        detected_commands = []

        # 系统命令检测
        if "摄像头" in text:
            if any(word in text for word in ["启动", "打开"]):
                detected_commands.append("start_camera")
            elif any(word in text for word in ["关闭", "停止", "结束"]):
                detected_commands.append("stop_camera")

        # 测试控制命令检测（独立于摄像头命令）
        if "测试" in text:
            if any(word in text for word in ["开始", "启动"]):
                detected_commands.append("start_test")
            elif any(word in text for word in ["停止", "结束"]):
                detected_commands.append("stop_test")

        # 方向命令检测 - 按出现顺序和次数检测所有方向命令
        import re

        # 定义方向词汇映射
        direction_patterns = {
            "up": ["上", "朝上", "向上"],
            "down": ["下", "朝下", "向下"],
            "left": ["左", "朝左", "向左"],
            "right": ["右", "朝右", "向右"]
        }

        # 按照在文本中出现的顺序检测所有方向命令
        direction_matches = []
        for direction, words in direction_patterns.items():
            for word in words:
                # 找到所有匹配位置
                start = 0
                while True:
                    pos = text.find(word, start)
                    if pos == -1:
                        break
                    direction_matches.append((pos, direction))
                    start = pos + 1

        # 按位置排序，确保按出现顺序添加命令
        direction_matches.sort(key=lambda x: x[0])

        # 添加所有检测到的方向命令
        for pos, direction in direction_matches:
            detected_commands.append(direction)

        # 如果检测到多个命令，立即发送所有命令
        if detected_commands:
            # 🔥 关键修复：不要去重，保持所有检测到的命令
            # 优先级：系统命令 > 测试控制命令 > 方向命令
            priority_order = ["start_camera", "stop_camera", "start_test", "stop_test", "up", "down", "left", "right"]

            # 按优先级排序命令，但保持所有出现的命令（不去重）
            sorted_commands = []

            # 先添加系统和测试命令（这些通常只出现一次）
            for cmd in ["start_camera", "stop_camera", "start_test", "stop_test"]:
                if cmd in detected_commands:
                    sorted_commands.append(cmd)

            # 然后按原始顺序添加所有方向命令（保持重复）
            for cmd in detected_commands:
                if cmd in ["up", "down", "left", "right"]:
                    sorted_commands.append(cmd)

            if sorted_commands:
                # 🔥 关键修复：只发送最后一个命令，不发送复合命令
                last_command = sorted_commands[-1]  # 取最后一个命令

                if len(sorted_commands) > 1:
                    logger.info(f"检测到复合命令: {sorted_commands}, 只发送最后一个: {last_command}")
                else:
                    logger.info(f"识别到单个命令: {last_command}")

                # 只发送最后一个命令
                self.command_recognized.emit(last_command, f"最后指令-{last_command}")
                return last_command

        # 其他系统命令
        elif any(word in text for word in ["设置", "打开设置", "配置"]):
            self._clear_audio_buffer()
            return "open_settings"
        elif any(word in text for word in ["保存", "保存结果"]):
            self._clear_audio_buffer()
            return "save_results"
        elif any(word in text for word in ["导出", "导出报告"]):
            self._clear_audio_buffer()
            return "export_report"

        # 默认返回文本类型
        return "speech_text"

    def _emit_all_commands_immediately(self, commands: list, original_text: str) -> None:
        """立即发送所有命令（包括第一个）"""
        try:
            # 为每个命令生成简化的原文描述
            command_names = {
                "start_camera": "启动摄像头",
                "stop_camera": "关闭摄像头",
                "start_test": "开始测试",
                "stop_test": "停止测试",
                "up": "向上",
                "down": "向下",
                "left": "向左",
                "right": "向右"
            }

            # 发送所有命令，包括第一个
            for i, cmd in enumerate(commands):
                # 使用简化的命令名称作为原文，避免重复显示完整原文
                simplified_text = command_names.get(cmd, cmd)
                logger.info(f"立即发送命令 {i+1}/{len(commands)}: {cmd} (简化原文: {simplified_text})")
                self.command_recognized.emit(cmd, f"复合命令-{simplified_text}")

            logger.info(f"已发送 {len(commands)} 个复合命令: {commands}")

        except Exception as e:
            logger.error(f"发送复合命令失败: {e}")

    def _emit_all_commands(self, commands: list, original_text: str) -> None:
        """立即发送所有命令（保留旧方法作为备用）"""
        try:
            # 为每个命令生成简化的原文描述
            command_names = {
                "start_camera": "启动摄像头",
                "stop_camera": "关闭摄像头",
                "start_test": "开始测试",
                "stop_test": "停止测试",
                "up": "向上",
                "down": "向下",
                "left": "向左",
                "right": "向右"
            }

            for i, cmd in enumerate(commands):
                if i == 0:
                    # 第一个命令已经通过返回值处理，这里只处理后续命令
                    continue

                # 使用简化的命令名称作为原文，避免重复显示完整原文
                simplified_text = command_names.get(cmd, cmd)
                logger.info(f"立即发送命令: {cmd} (简化原文: {simplified_text})")
                self.command_recognized.emit(cmd, f"复合命令-{simplified_text}")

            logger.info(f"已发送 {len(commands)} 个命令: {commands}")

        except Exception as e:
            logger.error(f"发送命令失败: {e}")

    def _queue_additional_commands(self, commands: list, original_text: str) -> None:
        """将额外的命令加入队列，延迟执行（保留作为备用方法）"""
        try:
            import threading
            import time

            def delayed_emit():
                for i, cmd in enumerate(commands):
                    # 延迟执行其他命令，避免冲突
                    delay = (i + 1) * 1.0  # 每个命令延迟1秒
                    time.sleep(delay)
                    logger.info(f"执行延迟命令: {cmd} (原文: {original_text})")
                    self.command_recognized.emit(cmd, original_text)

            # 在单独的线程中执行延迟命令
            thread = threading.Thread(target=delayed_emit, daemon=True)
            thread.start()

            logger.info(f"已安排延迟执行 {len(commands)} 个命令: {commands}")

        except Exception as e:
            logger.error(f"安排延迟命令失败: {e}")

    def _is_duplicate_command(self, text: str) -> bool:
        """检查是否是重复的指令 - 超严格去重"""
        import time
        current_time = time.time()

        # 🔥 超严格去重：如果文本完全相同，且在超时时间内，认为是重复指令
        if text == self.last_processed_text:
            if current_time - self.last_command_time < self.command_timeout:
                return True

        # 🔥 更严格：如果文本只是增加了标点符号，也认为是重复
        if self.last_processed_text:
            # 移除标点符号后比较
            import re
            clean_text = re.sub(r'[。，、！？\s]+', '', text)
            clean_last = re.sub(r'[。，、！？\s]+', '', self.last_processed_text)

            if clean_text == clean_last and current_time - self.last_command_time < self.command_timeout:
                return True

        # 🔥 最严格：如果在很短时间内（5秒），任何文本都认为是重复
        if self.last_processed_text and current_time - self.last_command_time < 5.0:
            return True

        # 🔥 终极严格：如果文本包含相同的核心内容，认为是重复
        if self.last_processed_text and len(text) > 10 and len(self.last_processed_text) > 10:
            # 提取核心内容（去除标点和空格）
            import re
            core_text = re.sub(r'[。，、！？\s\w]+', '', text)
            core_last = re.sub(r'[。，、！？\s\w]+', '', self.last_processed_text)

            # 如果核心内容相似度很高，认为是重复
            if len(core_text) > 5 and len(core_last) > 5:
                if core_text in core_last or core_last in core_text:
                    if current_time - self.last_command_time < 5.0:
                        return True

        return False

    def _update_last_command(self, text: str) -> None:
        """更新最后处理的指令信息"""
        import time
        self.last_processed_text = text
        self.last_command_time = time.time()
        logger.debug(f"更新最后指令: {text}")

    def set_test_in_progress(self, in_progress: bool) -> None:
        """设置测试状态"""
        import time
        self.test_in_progress = in_progress
        if not in_progress:
            self.test_completed_time = time.time()
            logger.info(f"测试已完成，将在 {self.test_timeout} 秒内忽略旧指令")
        else:
            logger.info("测试开始，开始接受新指令")

    def _should_ignore_old_commands(self) -> bool:
        """检查是否应该忽略旧指令（测试完成后）"""
        import time
        if not self.test_in_progress and self.test_completed_time > 0:
            elapsed = time.time() - self.test_completed_time
            if elapsed < self.test_timeout:
                return True
        return False

    def _clear_audio_buffer(self):
        """清空音频缓存区"""
        try:
            # 清空音频缓存区
            self.audio_buffer = []
            logger.debug("音频缓存区已清空")
        except Exception as e:
            logger.error(f"清空音频缓存区失败: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """音频回调函数"""
        try:
            if status:
                logger.warning(f"音频状态警告: {status}")

            if self.is_listening:
                # 将音频数据添加到缓冲区
                audio_data = np.frombuffer(in_data, dtype=np.int16)
                self.audio_buffer.extend(audio_data)

                # 限制缓冲区大小，防止内存溢出
                max_buffer_size = self.sample_rate * 10  # 10秒的音频数据
                if len(self.audio_buffer) > max_buffer_size:
                    self.audio_buffer = self.audio_buffer[-max_buffer_size:]
                    logger.debug(f"音频缓冲区已满，截断到 {max_buffer_size} 个样本")

                # 计算音频电平
                if len(audio_data) > 0:
                    # 计算RMS音量
                    rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
                    # 使用对数刻度转换为0-100的范围
                    max_amplitude = 32767.0
                    relative_volume = rms / max_amplitude
                    if relative_volume > 0:
                        level = min(100, max(0, int(np.log10(relative_volume * 1000 + 1) / 3 * 100)))
                    else:
                        level = 0
                    self.current_audio_level = level

            return (in_data, pyaudio.paContinue if PYAUDIO_AVAILABLE else None)

        except Exception as e:
            logger.error(f"音频回调函数错误: {e}")
            return (in_data, pyaudio.paAbort if PYAUDIO_AVAILABLE else None)
    
    def _emit_audio_level(self) -> None:
        """发送音频电平信号"""
        self.audio_level_changed.emit(self.current_audio_level)
    
    async def _audio_streaming_loop(self) -> None:
        """音频流处理循环"""
        last_send_time = time.time()
        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.is_listening and self.websocket:
                try:
                    # 检查是否有足够的音频数据
                    if len(self.audio_buffer) >= self.chunk_size:
                        # 获取音频块
                        audio_chunk = np.array(self.audio_buffer[:self.chunk_size], dtype=np.int16)
                        self.audio_buffer = self.audio_buffer[self.chunk_size:]

                        # 转换为字节
                        audio_bytes = audio_chunk.tobytes()

                        # 创建音频请求
                        audio_request = self._create_audio_request(audio_bytes)

                        # 发送音频数据
                        await asyncio.wait_for(self.websocket.send(audio_request), timeout=5.0)
                        last_send_time = time.time()
                        consecutive_errors = 0  # 重置错误计数

                        logger.debug(f"发送音频包: 序列号={self.sequence_number}, 大小={len(audio_bytes)}")

                    # 检查发送超时
                    if time.time() - last_send_time > 30:
                        logger.warning("音频发送超时，可能连接有问题")
                        break

                    # 根据低延迟模式调整延迟
                    if self.low_latency_mode:
                        await asyncio.sleep(0.05)  # 50ms延迟，低延迟模式
                    else:
                        await asyncio.sleep(0.1)   # 100ms延迟，标准模式

                except asyncio.TimeoutError:
                    consecutive_errors += 1
                    logger.warning(f"音频发送超时 ({consecutive_errors}/{max_consecutive_errors})")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("连续音频发送超时，停止发送")
                        break
                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket连接在音频发送时关闭")
                    break
                except Exception as e:
                    consecutive_errors += 1
                    logger.error(f"音频发送错误 ({consecutive_errors}/{max_consecutive_errors}): {e}")
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error("连续音频发送错误，停止发送")
                        break
                    await asyncio.sleep(1)  # 错误后等待1秒

        except Exception as e:
            logger.error(f"音频流处理循环错误: {e}")
            self.error_occurred.emit(f"音频处理错误: {str(e)}")

        logger.info("音频流处理循环结束")
    
    async def _websocket_loop(self) -> None:
        """WebSocket主循环"""
        audio_task = None
        connection_lost_count = 0
        max_connection_lost = 3

        try:
            # 连接WebSocket
            if not await self._connect_websocket():
                logger.error("WebSocket连接失败，退出循环")
                return

            # 发送完整请求
            if not await self._send_full_request():
                logger.error("发送完整请求失败，退出循环")
                return

            # 启动音频流处理
            audio_task = asyncio.create_task(self._audio_streaming_loop())
            logger.info("音频流处理任务已启动")

            # 监听响应
            try:
                while self.is_listening and self.websocket:
                    try:
                        # 设置接收超时
                        message = await asyncio.wait_for(self.websocket.recv(), timeout=30.0)
                        await self._handle_response(message)
                        connection_lost_count = 0  # 重置连接丢失计数

                    except asyncio.TimeoutError:
                        connection_lost_count += 1
                        logger.warning(f"接收响应超时 ({connection_lost_count}/{max_connection_lost})，发送心跳")

                        # 发送心跳包
                        try:
                            await self.websocket.ping()
                            logger.debug("心跳发送成功")
                        except Exception as ping_error:
                            logger.error(f"心跳发送失败: {ping_error}")
                            connection_lost_count += 1

                        # 如果连续超时太多次，断开连接
                        if connection_lost_count >= max_connection_lost:
                            logger.error("连续超时次数过多，断开连接")
                            break

                    except websockets.exceptions.ConnectionClosed as e:
                        logger.warning(f"WebSocket连接已关闭: {e}")
                        break
                    except Exception as e:
                        logger.error(f"接收消息时发生未知错误: {e}")
                        connection_lost_count += 1
                        if connection_lost_count >= max_connection_lost:
                            logger.error("连续错误次数过多，断开连接")
                            break

            except Exception as e:
                logger.error(f"消息接收循环错误: {e}")

        except Exception as e:
            logger.error(f"WebSocket循环错误: {e}")
            self.error_occurred.emit(f"连接错误: {str(e)}")

        finally:
            logger.info("WebSocket循环结束，清理资源")

            # 取消音频任务
            if audio_task:
                logger.info("取消音频流处理任务")
                audio_task.cancel()
                try:
                    await audio_task
                except asyncio.CancelledError:
                    logger.debug("音频任务已取消")

            # 关闭WebSocket连接
            if self.websocket:
                try:
                    logger.info("关闭WebSocket连接")
                    await self.websocket.close()
                except Exception as close_error:
                    logger.warning(f"关闭WebSocket时出错: {close_error}")
                self.websocket = None

            logger.info("WebSocket循环完全结束")
    
    def start_listening(self) -> bool:
        """开始监听"""
        if not self.is_available():
            self.error_occurred.emit("火山引擎配置不完整")
            return False
        
        if self.is_listening:
            return True
        
        try:
            # 初始化音频流 - 优化延迟
            audio_params = {
                'format': self.format,
                'channels': self.channels,
                'rate': self.sample_rate,
                'input': True,
                'frames_per_buffer': self.chunk_size,
                'stream_callback': self._audio_callback
            }

            # 低延迟模式配置
            if self.low_latency_mode and PYAUDIO_AVAILABLE:
                # 添加低延迟参数
                audio_params['input_host_api_specific_stream_info'] = None

            # 如果指定了麦克风设备，添加input_device_index参数
            if self.microphone_index >= 0:
                audio_params['input_device_index'] = self.microphone_index
                logger.info(f"使用指定麦克风设备: {self.microphone_index}")
            else:
                logger.info("使用系统默认麦克风设备")

            self.audio_stream = self.audio.open(**audio_params)
            
            self.is_listening = True
            self.audio_buffer = []
            self.sequence_number = 1  # 从1开始
            self.reconnect_attempts = 0  # 重置重连计数器
            
            # 启动音频流
            self.audio_stream.start_stream()
            
            # 启动WebSocket线程
            self.audio_thread = threading.Thread(
                target=self._run_websocket_loop,
                daemon=True
            )
            self.audio_thread.start()
            
            self.recognition_started.emit()
            self.status_changed.emit("火山引擎语音识别已启动")
            logger.info("火山引擎语音识别开始监听")
            
            return True
            
        except Exception as e:
            logger.error(f"启动监听失败: {e}")
            self.error_occurred.emit(f"启动失败: {str(e)}")
            return False
    
    def _run_websocket_loop(self) -> None:
        """运行WebSocket循环，带重连机制"""
        logger.info("WebSocket线程启动")

        while self.is_listening and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info(f"开始运行WebSocket循环 (尝试 {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
                loop.run_until_complete(self._websocket_loop())
                logger.info("WebSocket循环正常结束")
                break  # 正常结束，不需要重连

            except Exception as e:
                logger.error(f"WebSocket线程错误: {e}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")

                self.reconnect_attempts += 1

                if self.reconnect_attempts < self.max_reconnect_attempts and self.is_listening:
                    logger.info(f"将在 {self.reconnect_delay} 秒后尝试重连...")
                    self.status_changed.emit(f"连接断开，{self.reconnect_delay}秒后重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
                    time.sleep(self.reconnect_delay)
                else:
                    logger.error("达到最大重连次数或用户停止监听")
                    self.error_occurred.emit(f"连接失败，已尝试 {self.reconnect_attempts} 次")
                    break

            finally:
                try:
                    if 'loop' in locals():
                        logger.debug("关闭事件循环")
                        loop.close()
                except Exception as close_error:
                    logger.warning(f"关闭事件循环时出错: {close_error}")

        logger.info("WebSocket线程结束")
    
    def stop_listening(self) -> None:
        """停止监听"""
        self.is_listening = False
        
        try:
            # 停止音频流
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            
            # 等待线程结束
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2.0)
            
            self.recognition_stopped.emit()
            self.status_changed.emit("火山引擎语音识别已停止")
            logger.info("火山引擎语音识别停止监听")
            
        except Exception as e:
            logger.error(f"停止监听失败: {e}")
    
    def __del__(self):
        """析构函数"""
        if self.is_listening:
            self.stop_listening()
        
        if self.audio:
            self.audio.terminate()
