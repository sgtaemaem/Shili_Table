"""
语音控制器模块

集成语音识别功能到视力系统，提供语音控制接口。

Author: Vision Test System
Version: 1.0.0
"""

from typing import Optional, Callable, Dict, Any
import logging
from PySide6.QtCore import QObject, Signal, QTimer

# 使用火山引擎语音识别，不再需要通用语音识别接口

logger = logging.getLogger(__name__)


class VoiceController(QObject):
    """
    语音控制器
    
    管理语音识别引擎，处理语音命令并转发给相应的处理器。
    """
    
    # 信号定义
    direction_command = Signal(str)  # 方向命令: up, down, left, right
    test_control_command = Signal(str)  # 测试控制命令: start_test, stop_test
    system_control_command = Signal(str)  # 系统控制命令: start_camera, stop_camera, open_settings, etc.
    voice_status_changed = Signal(str)  # 语音状态变化
    voice_error = Signal(str)  # 语音错误
    command_feedback = Signal(str, str)  # 命令反馈: 命令类型, 反馈消息
    
    def __init__(self):
        """初始化语音控制器"""
        super().__init__()
        
        # 语音识别引擎
        self.voice_engine: Optional[Any] = None
        
        # 控制状态
        self.is_enabled = False
        self.is_test_mode = False  # 是否在测试模式中
        
        # 命令处理器映射
        self.command_handlers: Dict[str, Callable] = {}
        
        # 反馈定时器
        self.feedback_timer = QTimer()
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(self._clear_feedback)
        
        # 初始化语音引擎
        self._init_voice_engine()
    
    def _init_voice_engine(self) -> None:
        """初始化语音识别引擎"""
        try:
            # 获取语音识别配置
            from config import get_voice_config
            voice_config = get_voice_config()

            # 检查是否启用语音识别
            if not voice_config.get("enabled", True):
                logger.info("语音识别功能已禁用")
                self.voice_engine = None
                return

            # 使用火山引擎语音识别
            from volcengine_speech_recognition import VolcengineVoiceRecognitionEngine

            # 获取火山引擎配置
            volcengine_config = voice_config.get("volcengine", {})

            # 检查配置完整性
            if not volcengine_config.get("app_id") or not volcengine_config.get("access_token"):
                logger.warning("火山引擎配置不完整，语音识别功能不可用")
                self.voice_engine = None
                return

            # 获取音频配置
            audio_config = voice_config.get("audio", {})

            # 合并配置
            engine_config = {
                **volcengine_config,
                **audio_config
            }

            # 创建火山引擎语音识别实例
            self.voice_engine = VolcengineVoiceRecognitionEngine(engine_config)
            logger.info(f"使用火山引擎语音识别引擎，麦克风设备: {audio_config.get('microphone_index', -1)}")

            # 连接信号
            self.voice_engine.command_recognized.connect(self._handle_voice_command)
            self.voice_engine.recognition_started.connect(
                lambda: self.voice_status_changed.emit("火山引擎语音识别已启动")
            )
            self.voice_engine.recognition_stopped.connect(
                lambda: self.voice_status_changed.emit("火山引擎语音识别已停止")
            )
            self.voice_engine.error_occurred.connect(self.voice_error.emit)

            # 连接状态变化信号
            if hasattr(self.voice_engine, 'status_changed'):
                self.voice_engine.status_changed.connect(self.voice_status_changed.emit)

            logger.info("火山引擎语音控制器初始化成功")

        except Exception as e:
            logger.error(f"初始化火山引擎语音控制器失败: {e}")
            self.voice_error.emit(f"火山引擎语音控制器初始化失败: {str(e)}")
            self.voice_engine = None
    
    def enable_voice_control(self) -> bool:
        """
        启用语音控制

        Returns:
            bool: 是否成功启用
        """
        if not self.voice_engine:
            self.voice_error.emit("火山引擎语音识别引擎不可用")
            return False

        if self.is_enabled:
            logger.warning("火山引擎语音控制已启用")
            return True

        try:
            success = self.voice_engine.start_listening()
            if success:
                self.is_enabled = True
                self.voice_status_changed.emit("火山引擎语音控制已启用")
                logger.info("火山引擎语音控制已启用")

            return success

        except Exception as e:
            logger.error(f"启用火山引擎语音控制失败: {e}")
            self.voice_error.emit(f"启用火山引擎语音控制失败: {str(e)}")
            return False
    
    def disable_voice_control(self) -> None:
        """禁用语音控制"""
        if not self.is_enabled:
            return

        try:
            if self.voice_engine:
                self.voice_engine.stop_listening()

            self.is_enabled = False
            self.voice_status_changed.emit("火山引擎语音控制已禁用")
            logger.info("火山引擎语音控制已禁用")

        except Exception as e:
            logger.error(f"禁用语音控制失败: {e}")
    
    def set_test_mode(self, enabled: bool) -> None:
        """
        设置测试模式

        Args:
            enabled: 是否启用测试模式
        """
        self.is_test_mode = enabled

        if enabled:
            self.voice_status_changed.emit("测试模式：可使用语音指向方向")
        else:
            self.voice_status_changed.emit("待机模式：可使用语音控制测试")
    
    def _handle_voice_command(self, command_type: str, original_text: str) -> None:
        """
        处理语音命令

        Args:
            command_type: 命令类型
            original_text: 原始识别文本
        """
        try:
            # 确保参数是字符串类型
            command_type = str(command_type) if command_type else ""
            original_text = str(original_text) if original_text else ""

            logger.info(f"处理语音命令: {command_type} (原文: {original_text})")

            # 根据命令类型分发处理
            if command_type in ["up", "down", "left", "right"]:
                self._handle_direction_command(command_type, original_text)
            elif command_type in ["start_test", "stop_test"]:
                self._handle_test_control_command(command_type, original_text)
            elif command_type in ["start_camera", "stop_camera", "open_settings", "save_results", "export_report"]:
                self._handle_system_control_command(command_type, original_text)
            else:
                logger.warning(f"未知命令类型: {command_type}")
                self.command_feedback.emit("error", f"未识别的命令: {original_text}")

        except Exception as e:
            logger.error(f"处理语音命令失败: {e}")
            try:
                self.voice_error.emit(f"处理语音命令失败: {str(e)}")
            except:
                print(f"语音错误信号发送失败: {e}")
    
    def _handle_direction_command(self, direction: str, original_text: str) -> None:
        """
        处理方向命令

        Args:
            direction: 方向 (up, down, left, right)
            original_text: 原始文本
        """
        # 发送方向命令信号（无论是否在测试模式）
        self.direction_command.emit(direction)

        # 提供反馈
        direction_names = {
            "up": "向上",
            "down": "向下",
            "left": "向左",
            "right": "向右"
        }

        # 🔥 只在测试模式下显示方向识别反馈
        if self.is_test_mode:
            feedback_msg = f"测试模式 - 识别到方向: {direction_names.get(direction, direction)}"
            self.command_feedback.emit("direction", feedback_msg)

            # 设置反馈清除定时器
            if self.feedback_timer.isActive():
                self.feedback_timer.stop()
            self.feedback_timer.start(2000)  # 2秒后清除反馈
        # 非测试模式下不显示方向识别反馈

        logger.info(f"处理方向命令: {direction} (测试模式: {self.is_test_mode})")
    
    def _handle_test_control_command(self, command: str, original_text: str) -> None:
        """
        处理测试控制命令

        Args:
            command: 控制命令 (start_test, stop_test)
            original_text: 原始文本
        """
        # 发送测试控制命令信号
        self.test_control_command.emit(command)

        # 提供反馈
        command_names = {
            "start_test": "开始测试",
            "stop_test": "停止测试"
        }

        feedback_msg = f"执行命令: {command_names.get(command, command)}"
        self.command_feedback.emit("control", feedback_msg)

        # 更新测试模式状态
        if command == "start_test":
            self.set_test_mode(True)
            # 通知语音引擎测试开始
            if hasattr(self.voice_engine, 'set_test_in_progress'):
                self.voice_engine.set_test_in_progress(True)
        elif command == "stop_test":
            self.set_test_mode(False)
            # 通知语音引擎测试完成
            if hasattr(self.voice_engine, 'set_test_in_progress'):
                self.voice_engine.set_test_in_progress(False)

        # 设置反馈清除定时器
        if self.feedback_timer.isActive():
            self.feedback_timer.stop()
        self.feedback_timer.start(3000)  # 3秒后清除反馈

        logger.info(f"处理测试控制命令: {command}")

    def _handle_system_control_command(self, command: str, original_text: str) -> None:
        """
        处理系统控制命令

        Args:
            command: 系统控制命令 (start_camera, stop_camera, open_settings, save_results, export_report)
            original_text: 原始文本
        """
        # 发送系统控制命令信号
        self.system_control_command.emit(command)

        # 提供反馈
        command_names = {
            "start_camera": "启动摄像头",
            "stop_camera": "关闭摄像头",
            "open_settings": "打开设置",
            "save_results": "保存结果",
            "export_report": "导出报告"
        }

        feedback_msg = f"执行命令: {command_names.get(command, command)}"
        self.command_feedback.emit("system", feedback_msg)

        # 设置反馈清除定时器
        if self.feedback_timer.isActive():
            self.feedback_timer.stop()
        self.feedback_timer.start(3000)  # 3秒后清除反馈

        logger.info(f"处理系统控制命令: {command}")

    def _clear_feedback(self) -> None:
        """清除命令反馈"""
        self.command_feedback.emit("clear", "")
    
    def register_command_handler(self, command_type: str, handler: Callable) -> None:
        """
        注册命令处理器
        
        Args:
            command_type: 命令类型
            handler: 处理器函数
        """
        self.command_handlers[command_type] = handler
        logger.debug(f"注册命令处理器: {command_type}")
    
    def unregister_command_handler(self, command_type: str) -> None:
        """
        注销命令处理器
        
        Args:
            command_type: 命令类型
        """
        if command_type in self.command_handlers:
            del self.command_handlers[command_type]
            logger.debug(f"注销命令处理器: {command_type}")
    
    def is_voice_available(self) -> bool:
        """
        检查语音功能是否可用
        
        Returns:
            bool: 是否可用
        """
        return (self.voice_engine is not None and 
                self.voice_engine.is_available())
    
    def get_voice_status(self) -> str:
        """
        获取语音状态
        
        Returns:
            str: 状态描述
        """
        if not self.is_voice_available():
            return "火山引擎语音功能不可用"
        elif not self.is_enabled:
            return "火山引擎语音控制已禁用"
        elif self.is_test_mode:
            return "测试模式 - 可使用语音指向"
        else:
            return "待机模式 - 可语音控制测试"
    
    def get_available_commands(self) -> Dict[str, list]:
        """
        获取可用命令列表

        Returns:
            Dict[str, list]: 命令分类和列表
        """
        return {
            "方向命令": [
                "向上 / 上 / 朝上 / up",
                "向下 / 下 / 朝下 / down",
                "向左 / 左 / 朝左 / left",
                "向右 / 右 / 朝右 / right"
            ],
            "测试控制": [
                "开始测试 / 开始 / start test",
                "停止测试 / 停止 / stop test"
            ],
            "系统控制": [
                "启动摄像头 / 打开摄像头 / start camera",
                "关闭摄像头 / 停止摄像头 / stop camera",
                "打开设置 / 设置 / open settings",
                "保存结果 / 保存 / save results",
                "导出报告 / 导出 / export report"
            ]
        }
    
    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.disable_voice_control()
            
            if self.feedback_timer.isActive():
                self.feedback_timer.stop()
            
            logger.info("语音控制器资源清理完成")
            
        except Exception as e:
            logger.error(f"清理语音控制器资源失败: {e}")
