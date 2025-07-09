#!/usr/bin/env python3
"""
使用Qt Designer UI文件的主程序
集成实时手势识别显示 - 美化版本
"""
import sys
import os
import traceback
import random
import time

# 设置环境变量，解决SystemError
os.environ['PY_SSIZE_T_CLEAN'] = '1'

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QIcon

from ui_generated import Ui_MainWindow
from camera_with_gesture import CameraWithGestureHandler
from vision_calculator import VisionCalculator
from communication import MockCommunication
from ai_diagnosis import AIVisionDiagnosis
from config import (get_siliconflow_config, get_camera_config, get_voice_config,
                   is_api_key_configured, get_api_setup_instructions, is_volcengine_configured)
from settings_dialog import SettingsDialog
from resources_manager import resource_manager
from voice_controller import VoiceController

class AIDiagnosisThread(QThread):
    """AI诊断线程"""

    # 信号定义
    progress_updated = Signal(str)  # 进度更新
    stream_content = Signal(str)    # 流式内容
    stream_started = Signal()       # 流式开始
    stream_ended = Signal()         # 流式结束
    diagnosis_completed = Signal(str)  # 诊断完成
    diagnosis_failed = Signal(str)     # 诊断失败

    def __init__(self, ai_diagnosis, test_results):
        super().__init__()
        self.ai_diagnosis = ai_diagnosis
        self.test_results = test_results
        self.is_running = True

        # 设置流式回调
        if self.ai_diagnosis:
            self.ai_diagnosis.stream_callback = self.handle_stream_callback
            self.ai_diagnosis.progress_callback = self.handle_progress_callback

    def handle_stream_callback(self, content, is_start=False, is_chunk=False, is_end=False):
        """处理流式回调"""
        if is_start:
            self.stream_started.emit()
        elif is_chunk:
            self.stream_content.emit(content)
        elif is_end:
            self.stream_ended.emit()

    def handle_progress_callback(self, message):
        """处理进度回调"""
        self.progress_updated.emit(message)

    def run(self):
        """运行AI诊断"""
        try:
            if not self.is_running:
                return

            # 执行AI诊断
            diagnosis = self.ai_diagnosis.analyze_vision_results(self.test_results)

            if self.is_running:
                self.diagnosis_completed.emit(diagnosis)

        except Exception as e:
            if self.is_running:
                self.diagnosis_failed.emit(str(e))

    def stop(self):
        """停止线程"""
        self.is_running = False
        self.quit()
        self.wait()

class ELetterWidget(QLabel):
    """E字母显示控件"""
    
    def __init__(self):
        super().__init__()
        self.letter_size = 100
        self.direction = "Right"  # Up, Down, Left, Right
        self.background_color = "white"
        
    def set_letter_params(self, size, direction):
        """设置字母参数"""
        self.letter_size = size
        self.direction = direction
        self.update()
    
    def set_background_color(self, color):
        """设置背景颜色"""
        self.background_color = color
        self.update()
    
    def paintEvent(self, event):
        """绘制E字母"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 设置背景
        if self.background_color == "green":
            painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.green))
        elif self.background_color == "red":
            painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.red))
        else:
            painter.fillRect(self.rect(), QBrush(Qt.GlobalColor.white))
        
        # 计算E字母的绘制区域
        widget_width = self.width()
        widget_height = self.height()
        
        # E字母的实际大小
        e_width = min(self.letter_size, widget_width - 20)
        e_height = e_width  # 保持正方形
        
        # 居中位置
        start_x = (widget_width - e_width) // 2
        start_y = (widget_height - e_height) // 2
        
        # 设置画笔
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        
        # 根据方向绘制E字母
        self.draw_e_letter(painter, start_x, start_y, e_width, e_height)
    
    def draw_e_letter(self, painter, x, y, width, height):
        """绘制E字母"""
        stroke_width = max(width // 10, 2)  # 笔画宽度
        gap_width = width // 5  # 开口宽度
        
        if self.direction == "Right":
            # 开口向右的E
            painter.fillRect(x, y, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x, y + height//2 - stroke_width//2, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x, y + height - stroke_width, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x, y, stroke_width, height, Qt.GlobalColor.black)
            
        elif self.direction == "Left":
            # 开口向左的E
            painter.fillRect(x + gap_width, y, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x + gap_width, y + height//2 - stroke_width//2, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x + gap_width, y + height - stroke_width, width - gap_width, stroke_width, Qt.GlobalColor.black)
            painter.fillRect(x + width - stroke_width, y, stroke_width, height, Qt.GlobalColor.black)
            
        elif self.direction == "Up":
            # 开口向上的E（旋转90度）
            painter.fillRect(x, y + gap_width, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x + width//2 - stroke_width//2, y + gap_width, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x + width - stroke_width, y + gap_width, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x, y + height - stroke_width, width, stroke_width, Qt.GlobalColor.black)
            
        elif self.direction == "Down":
            # 开口向下的E（旋转90度）
            painter.fillRect(x, y, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x + width//2 - stroke_width//2, y, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x + width - stroke_width, y, stroke_width, height - gap_width, Qt.GlobalColor.black)
            painter.fillRect(x, y, width, stroke_width, Qt.GlobalColor.black)

class VisionMainWindow(QMainWindow):
    """视力系统主窗口 - 使用UI文件"""
    
    def __init__(self):
        super().__init__()

        # 设置UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # 添加缺失的按钮
        self.add_missing_buttons()

        # 设置窗口显示模式
        self.is_fullscreen = False

        # 检查是否启用自动全屏模式
        from config import get_system_config
        system_config = get_system_config()
        auto_fullscreen = system_config.get("auto_fullscreen", False)

        if auto_fullscreen:
            # 直接进入全屏模式
            self.showFullScreen()
            self.is_fullscreen = True
        else:
            # 最大化窗口（保留标题栏和任务栏）
            self.showMaximized()

        # 添加快捷键
        try:
            from PySide6.QtWidgets import QShortcut
            from PySide6.QtGui import QKeySequence
            # F11切换全屏
            self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
            self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)
            # Ctrl+Q退出程序
            self.exit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
            self.exit_shortcut.activated.connect(self.safe_exit)
        except ImportError:
            print("警告: 无法导入快捷键模块，快捷键功能不可用")

        # 应用医疗主题样式
        self.apply_medical_theme()

        # 设置退出按钮样式
        self.setup_exit_button_style()

        # 根据显示模式调整界面布局
        self.adjust_layout_for_display_mode()

        # 性能监控
        self.performance_metrics = {
            'startup_time': time.time(),
            'test_count': 0,
            'ai_diagnosis_count': 0,
            'error_count': 0
        }

        try:
            # 初始化组件
            self.vision_calculator = VisionCalculator()

            # 摄像头和通信模块
            self.camera_handler = None
            self.communication = None
            self.ai_diagnosis = None
            self.ai_diagnosis_thread = None

            # 语音控制器
            self.voice_controller = None
            self._last_voice_feedback_message = None  # 记录最后一条语音反馈消息
            self._init_voice_controller()

            # 替换E字母显示区域
            self.e_letter_widget = ELetterWidget()
            self.ui.verticalLayout_e_letter.removeWidget(self.ui.label_e_letter)
            self.ui.label_e_letter.deleteLater()
            self.ui.verticalLayout_e_letter.addWidget(self.e_letter_widget)
            
            # 系统状态
            self.current_distance = 100.0
            self.current_direction = "Right"

            # 测试状态
            self.current_vision = 5.0  # 从5.0开始测试
            self.consecutive_failures = 0
            self.test_results = []
            self.is_testing = False
            self.test_start_time = 0
            self.correct_start_time = 0

            # 定时器
            self.test_timer = QTimer()
            self.test_timer.timeout.connect(self.check_test_progress)

            self.flash_timer = QTimer()
            self.flash_timer.timeout.connect(self.reset_background)
            
            # 连接信号
            self.setup_connections()

            # 添加初始信息
            self.ui.textEdit_results.append("=== 电子视力表系统 ===")
            if self.is_fullscreen:
                self.ui.textEdit_results.append("🖥️ 程序已自动进入全屏模式")
                self.ui.textEdit_results.append("💡 按 F11 可切换到窗口模式")
            else:
                self.ui.textEdit_results.append("🖥️ 窗口已自动最大化显示")
                self.ui.textEdit_results.append("💡 按 F11 可切换到全屏模式")
            self.ui.textEdit_results.append("🎯 程序框图将自动覆盖满整个屏幕")
            self.ui.textEdit_results.append("🚪 点击右上角'❌ 退出'按钮或按 Ctrl+Q 可退出程序")
            self.ui.textEdit_results.append("点击'启动摄像头'按钮开始手势识别")

        except Exception as e:
            print(f"系统初始化失败: {e}")
            traceback.print_exc()

    def add_missing_buttons(self):
        """添加UI文件中缺失的按钮"""
        try:
            from PySide6.QtWidgets import QPushButton, QSizePolicy
            from PySide6.QtCore import QSize

            # 在控制按钮布局中添加缺失的按钮

            # 开始测试按钮
            self.ui.btn_start_test = QPushButton("开始测试")
            self.ui.btn_start_test.setMinimumSize(QSize(100, 40))
            self.ui.btn_start_test.setEnabled(False)  # 初始禁用
            self.ui.horizontalLayout_controls.insertWidget(1, self.ui.btn_start_test)

            # 停止测试按钮
            self.ui.btn_stop_test = QPushButton("停止测试")
            self.ui.btn_stop_test.setMinimumSize(QSize(100, 40))
            self.ui.btn_stop_test.setEnabled(False)  # 初始禁用
            self.ui.horizontalLayout_controls.insertWidget(2, self.ui.btn_stop_test)

            # 语音控制按钮
            self.ui.btn_voice_toggle = QPushButton("🎤 语音控制")
            self.ui.btn_voice_toggle.setMinimumSize(QSize(120, 40))
            self.ui.btn_voice_toggle.setCheckable(True)
            self.ui.btn_voice_toggle.setChecked(False)
            self.ui.horizontalLayout_controls.insertWidget(3, self.ui.btn_voice_toggle)

            # 退出按钮
            self.ui.btn_exit = QPushButton("❌ 退出")
            self.ui.btn_exit.setMinimumSize(QSize(100, 40))
            # 在spacer之后添加退出按钮
            spacer_index = -1
            for i in range(self.ui.horizontalLayout_controls.count()):
                item = self.ui.horizontalLayout_controls.itemAt(i)
                if item.spacerItem():
                    spacer_index = i
                    break

            if spacer_index >= 0:
                self.ui.horizontalLayout_controls.insertWidget(spacer_index + 1, self.ui.btn_exit)
            else:
                self.ui.horizontalLayout_controls.addWidget(self.ui.btn_exit)

            print("✅ 缺失的按钮已添加")

        except Exception as e:
            print(f"添加缺失按钮失败: {e}")
            traceback.print_exc()

    def toggle_fullscreen(self):
        """切换全屏模式（F11快捷键）"""
        try:
            if self.is_fullscreen:
                # 退出全屏，回到最大化窗口
                self.showMaximized()
                self.is_fullscreen = False
                self.ui.textEdit_results.append("🖥️ 已切换到最大化窗口模式（按F11可切换到全屏）")
                self.ui.textEdit_results.append("📐 程序框图已调整为窗口模式显示")
            else:
                # 进入全屏模式
                self.showFullScreen()
                self.is_fullscreen = True
                self.ui.textEdit_results.append("🖥️ 已切换到全屏模式（按F11可退出全屏）")
                self.ui.textEdit_results.append("📐 程序框图已自动覆盖满整个屏幕")

            # 触发界面重新布局以适应新的显示模式
            self.adjust_layout_for_display_mode()

        except Exception as e:
            print(f"切换全屏模式失败: {e}")
            self.ui.textEdit_results.append(f"❌ 切换显示模式失败: {str(e)}")

    def adjust_layout_for_display_mode(self):
        """根据显示模式调整界面布局"""
        try:
            # 获取当前屏幕尺寸
            screen = self.screen()
            screen_geometry = screen.geometry()
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()

            print(f"🖥️ 屏幕尺寸: {screen_width}x{screen_height}, 全屏模式: {self.is_fullscreen}")

            if self.is_fullscreen:
                # 全屏模式：更精确的布局计算
                # 为菜单栏、状态栏和控制区域预留空间
                control_area_height = 150  # 控制按钮和手势信息区域高度
                result_area_height = 200   # 结果显示区域高度
                margin = 60               # 边距

                available_height = screen_height - control_area_height - result_area_height - margin
                available_width = screen_width - margin

                # 计算合适的显示区域大小，确保两个区域能并排显示
                # 考虑到需要并排显示两个区域，每个区域最大宽度为可用宽度的48%
                max_frame_width = int(available_width * 0.48)
                max_frame_height = int(available_height * 0.9)  # 高度占可用高度的90%

                # 选择较小的值作为正方形边长，确保比例协调
                frame_size = min(max_frame_width, max_frame_height, 550)  # 最大不超过550像素
                frame_size = max(frame_size, 300)  # 最小不少于300像素

                print(f"📐 全屏布局计算: 屏幕{screen_width}x{screen_height}, 可用{available_width}x{available_height}, frame_size={frame_size}")

                # 设置E字母显示区域大小
                self.ui.frame_e_letter.setMinimumSize(frame_size, frame_size)
                self.ui.frame_e_letter.setMaximumSize(frame_size, frame_size)

                # 设置摄像头显示区域大小
                self.ui.frame_camera.setMinimumSize(frame_size, frame_size)
                self.ui.frame_camera.setMaximumSize(frame_size, frame_size)

                # 调整结果显示区域高度，使用固定高度避免布局问题
                result_height = min(280, int(screen_height * 0.25))  # 最大280像素或屏幕高度的25%
                self.ui.textEdit_results.setMinimumSize(0, result_height)
                self.ui.textEdit_results.setMaximumSize(16777215, result_height)

                # 调整控制按钮的大小，防止重叠
                button_height = 45  # 稍微增大按钮高度
                self.ui.btn_start_camera.setMinimumSize(130, button_height)
                self.ui.btn_start_test.setMinimumSize(110, button_height)
                self.ui.btn_stop_test.setMinimumSize(110, button_height)
                self.ui.btn_voice_toggle.setMinimumSize(130, button_height)

                # 在全屏模式下增大退出按钮
                self.ui.btn_exit.setMinimumSize(120, button_height)
                self.ui.btn_exit.setStyleSheet("""
                    QPushButton#btn_exit {
                        background-color: #dc3545;
                        color: white;
                        border: 3px solid #dc3545;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 16px;
                        padding: 8px 16px;
                        margin: 2px;
                    }
                    QPushButton#btn_exit:hover {
                        background-color: #c82333;
                        border-color: #c82333;
                    }
                """)

                # 设置布局间距和边距
                self.ui.verticalLayout_main.setSpacing(12)
                self.ui.verticalLayout_main.setContentsMargins(15, 15, 15, 15)
                self.ui.horizontalLayout_top.setSpacing(25)
                self.ui.horizontalLayout_controls.setSpacing(8)
                self.ui.horizontalLayout_gesture_info.setSpacing(15)

            else:
                # 窗口模式：恢复默认大小
                self.ui.frame_e_letter.setMinimumSize(400, 400)
                self.ui.frame_e_letter.setMaximumSize(400, 400)

                self.ui.frame_camera.setMinimumSize(400, 400)
                self.ui.frame_camera.setMaximumSize(400, 400)

                self.ui.textEdit_results.setMinimumSize(0, 300)
                self.ui.textEdit_results.setMaximumSize(16777215, 300)

                # 恢复按钮默认大小
                self.ui.btn_start_camera.setMinimumSize(120, 40)
                self.ui.btn_start_test.setMinimumSize(100, 40)
                self.ui.btn_stop_test.setMinimumSize(100, 40)
                self.ui.btn_voice_toggle.setMinimumSize(120, 40)
                self.ui.btn_exit.setMinimumSize(100, 40)

                # 重新应用默认样式
                self.setup_exit_button_style()

                # 恢复默认布局间距和边距
                self.ui.verticalLayout_main.setSpacing(6)
                self.ui.verticalLayout_main.setContentsMargins(9, 9, 9, 9)
                self.ui.horizontalLayout_top.setSpacing(6)
                self.ui.horizontalLayout_controls.setSpacing(6)
                self.ui.horizontalLayout_gesture_info.setSpacing(6)

            # 强制重新布局
            self.ui.centralwidget.updateGeometry()
            self.update()  # 使用update()而不是adjustSize()，更适合全屏模式

        except Exception as e:
            print(f"调整界面布局失败: {e}")

    def resizeEvent(self, event):
        """窗口大小变化事件处理"""
        super().resizeEvent(event)
        try:
            # 检查是否启用自适应布局
            from config import get_system_config
            system_config = get_system_config()
            if system_config.get("adaptive_layout", True):
                # 延迟调整布局，避免频繁调整
                if hasattr(self, '_resize_timer'):
                    self._resize_timer.stop()
                else:
                    from PySide6.QtCore import QTimer
                    self._resize_timer = QTimer()
                    self._resize_timer.setSingleShot(True)
                    self._resize_timer.timeout.connect(self.adjust_layout_for_display_mode)

                self._resize_timer.start(100)  # 100ms延迟
        except Exception as e:
            print(f"处理窗口大小变化失败: {e}")

    def _init_voice_controller(self):
        """初始化语音控制器"""
        try:
            # 获取语音配置
            voice_config = get_voice_config()

            # 检查是否启用语音功能
            if not voice_config.get("enabled", False):
                self.ui.textEdit_results.append("🎤 语音控制功能已禁用（可在设置中启用或点击语音按钮手动启用）")
                return

            self.voice_controller = VoiceController()

            # 连接语音控制信号
            self.voice_controller.direction_command.connect(self.handle_voice_direction)
            self.voice_controller.test_control_command.connect(self.handle_voice_test_control)
            self.voice_controller.system_control_command.connect(self.handle_voice_system_control)
            self.voice_controller.voice_status_changed.connect(self.update_voice_status)
            self.voice_controller.voice_error.connect(self.handle_voice_error)
            self.voice_controller.command_feedback.connect(self.show_voice_feedback)

            # 检查语音功能是否可用
            if self.voice_controller.is_voice_available():
                self.ui.textEdit_results.append("🌐 火山引擎语音控制功能已就绪")
                self.ui.textEdit_results.append("⚡ 在线识别，高精度，专业语音引擎")
                self.ui.textEdit_results.append("🎯 支持多种语音命令，实时流式识别")
                self.ui.textEdit_results.append("测试命令：开始测试、停止测试、向上/朝上、向下/朝下、向左/朝左、向右/朝右")
                self.ui.textEdit_results.append("系统命令：启动摄像头、关闭摄像头、打开设置、保存结果、导出报告")

                # 显示火山引擎语音识别状态
                self._show_volcengine_voice_status()

                # 根据配置决定是否自动启用语音控制（默认关闭）
                if voice_config.get("auto_start", False):
                    if self.voice_controller.enable_voice_control():
                        self.ui.textEdit_results.append("✅ 火山引擎语音控制已自动启用")
                        self.ui.btn_voice_toggle.setChecked(True)
                        self.ui.btn_voice_toggle.setText("�️ 语音识别 (开)")
                        self.ui.btn_voice_toggle.setStyleSheet("background-color: #4CAF50; color: white;")
                    else:
                        self.ui.textEdit_results.append("⚠️ 火山引擎语音控制启用失败")
                        self.ui.btn_voice_toggle.setChecked(False)
                        self.ui.btn_voice_toggle.setText("�️ 语音识别 (关)")
                        self.ui.btn_voice_toggle.setStyleSheet("background-color: #6c757d; color: white;")
                else:
                    self.ui.textEdit_results.append("💡 火山引擎语音控制已就绪，点击按钮手动启用")
                    self.ui.btn_voice_toggle.setChecked(False)
                    self.ui.btn_voice_toggle.setText("�️ 语音识别 (关)")
                    self.ui.btn_voice_toggle.setStyleSheet("background-color: #6c757d; color: white;")
            else:
                self.ui.textEdit_results.append("⚠️ 火山引擎语音控制功能不可用")
                self._show_voice_configuration_prompt()

        except Exception as e:
            print(f"语音控制器初始化失败: {e}")
            self.ui.textEdit_results.append(f"❌ 语音控制器初始化失败: {str(e)}")
            self.ui.textEdit_results.append("💡 请在设置中检查语音配置")
            # 禁用语音控制按钮
            self.ui.btn_voice_toggle.setEnabled(False)
            self.ui.btn_voice_toggle.setText("🎤 语音错误")
            self.ui.btn_voice_toggle.setStyleSheet("background-color: #cccccc; color: #666666;")

    def handle_voice_direction(self, direction):
        """处理语音方向命令"""
        try:
            # 将语音方向转换为系统方向格式
            direction_map = {
                "up": "Up",
                "down": "Down",
                "left": "Left",
                "right": "Right"
            }

            if direction in direction_map:
                system_direction = direction_map[direction]
                self.ui.textEdit_results.append(f"🎤 语音方向: {direction} → {system_direction}")

                # 如果正在测试，执行测试逻辑
                if self.is_testing:
                    self.handle_test_direction(system_direction)
                else:
                    # 如果没有在测试，只显示识别结果
                    self.ui.textEdit_results.append(f"✅ 方向识别成功: {system_direction} (当前未在测试模式)")
                    # 更新方向显示，让用户看到识别效果
                    self.ui.label_current_direction.setText(system_direction)
                    color_map = {"Up": "blue", "Down": "orange", "Left": "purple", "Right": "green"}
                    color = color_map.get(system_direction, "red")
                    self.ui.label_current_direction.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            else:
                self.ui.textEdit_results.append(f"❌ 未知方向命令: {direction}")

        except Exception as e:
            print(f"处理语音方向命令失败: {e}")

    def handle_voice_test_control(self, command):
        """处理语音测试控制命令"""
        try:
            if command == "start_test":
                self.ui.textEdit_results.append("🎤 语音命令: 开始测试")
                if not self.is_testing:
                    self.start_test()
                else:
                    self.ui.textEdit_results.append("⚠️ 测试已在进行中")

            elif command == "stop_test":
                self.ui.textEdit_results.append("🎤 语音命令: 停止测试")
                if self.is_testing:
                    self.stop_test()
                else:
                    self.ui.textEdit_results.append("⚠️ 当前没有进行测试")
            else:
                self.ui.textEdit_results.append(f"❌ 未知测试控制命令: {command}")

        except Exception as e:
            print(f"处理语音测试控制命令失败: {e}")

    def handle_voice_system_control(self, command):
        """处理语音系统控制命令"""
        try:
            if command == "start_camera":
                self.ui.textEdit_results.append("🎤 语音命令: 启动摄像头")

                # 检查摄像头状态
                camera_running = (hasattr(self, 'camera_handler') and
                                self.camera_handler and
                                hasattr(self.camera_handler, 'running') and
                                self.camera_handler.running)

                if not camera_running:
                    self.ui.textEdit_results.append("📷 正在启动摄像头...")
                    self.start_camera_and_gesture()
                else:
                    self.ui.textEdit_results.append("⚠️ 摄像头已经启动")

            elif command == "stop_camera":
                self.ui.textEdit_results.append("🎤 语音命令: 关闭摄像头")

                # 检查摄像头状态
                camera_running = (hasattr(self, 'camera_handler') and
                                self.camera_handler and
                                hasattr(self.camera_handler, 'running') and
                                self.camera_handler.running)

                if camera_running:
                    self.ui.textEdit_results.append("📷 正在关闭摄像头...")
                    self.stop_camera()
                else:
                    self.ui.textEdit_results.append("⚠️ 摄像头未启动")

            elif command == "open_settings":
                self.ui.textEdit_results.append("🎤 语音命令: 打开设置")
                self.show_settings()

            elif command == "save_results":
                self.ui.textEdit_results.append("🎤 语音命令: 保存结果")
                self.ui.textEdit_results.append("💡 保存功能已移除")

            elif command == "export_report":
                self.ui.textEdit_results.append("🎤 语音命令: 导出报告")
                self.ui.textEdit_results.append("💡 导出功能已移除")

            else:
                self.ui.textEdit_results.append(f"❌ 未知系统控制命令: {command}")

        except Exception as e:
            print(f"处理语音系统控制命令失败: {e}")

    def toggle_voice_control(self):
        """切换语音控制开关"""
        try:
            if not self.voice_controller or not self.voice_controller.is_voice_available():
                self.ui.textEdit_results.append("❌ 语音控制功能不可用")
                return

            if self.ui.btn_voice_toggle.isChecked():
                # 启用语音控制
                if self.voice_controller.enable_voice_control():
                    self.ui.textEdit_results.append("✅ 火山引擎语音控制已启用")
                    self.ui.btn_voice_toggle.setText("🌐 火山引擎 (开)")
                    self.ui.btn_voice_toggle.setStyleSheet("background-color: #4CAF50; color: white;")
                else:
                    self.ui.textEdit_results.append("❌ 火山引擎语音控制启用失败")
                    self.ui.btn_voice_toggle.setChecked(False)
                    self.ui.btn_voice_toggle.setText("🌐 火山引擎 (关)")
                    self.ui.btn_voice_toggle.setStyleSheet("background-color: #f44336; color: white;")
            else:
                # 禁用语音控制
                self.voice_controller.disable_voice_control()
                self.ui.textEdit_results.append("⏹️ 火山引擎语音控制已禁用")
                self.ui.btn_voice_toggle.setText("🌐 火山引擎 (关)")
                self.ui.btn_voice_toggle.setStyleSheet("background-color: #f44336; color: white;")

        except Exception as e:
            print(f"切换语音控制失败: {e}")
            self.ui.textEdit_results.append(f"❌ 切换语音控制失败: {str(e)}")

    def stop_camera(self):
        """停止摄像头"""
        try:
            if hasattr(self, 'camera_handler') and self.camera_handler:
                self.camera_handler.stop_camera()
                self.camera_handler = None

                # 恢复按钮状态
                self.ui.btn_start_camera.setEnabled(True)
                self.ui.btn_start_camera.setText("启动摄像头")
                self.ui.btn_start_camera.setStyleSheet("")

                # 禁用测试按钮
                self.ui.btn_start_test.setEnabled(False)

                # 更新显示
                self.ui.label_camera.setText("摄像头已关闭")
                self.ui.label_gesture_status.setText("未启动")
                self.ui.label_gesture_status.setStyleSheet("font-size: 14px; color: red;")
                self.ui.label_current_direction.setText("None")
                self.ui.label_current_direction.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")

                self.ui.textEdit_results.append("📷 摄像头已关闭")
            else:
                self.ui.textEdit_results.append("⚠️ 摄像头未启动")
        except Exception as e:
            print(f"停止摄像头失败: {e}")
            self.ui.textEdit_results.append(f"❌ 停止摄像头失败: {str(e)}")

    def show_settings(self):
        """显示设置对话框"""
        try:
            dialog = SettingsDialog(self)
            if dialog.exec() == dialog.DialogCode.Accepted:
                self.ui.textEdit_results.append("✅ 设置已更新")
                # 重新加载配置
                self.reload_configurations()
            else:
                self.ui.textEdit_results.append("⚠️ 设置已取消")
        except Exception as e:
            print(f"显示设置对话框失败: {e}")
            self.ui.textEdit_results.append(f"❌ 打开设置失败: {str(e)}")

    # 已移除测试结果保存和导出功能

    def reload_configurations(self):
        """重新加载配置"""
        try:
            # 重新加载语音配置
            if self.voice_controller:
                from config import get_voice_config
                voice_config = get_voice_config()
                self.voice_controller.voice_engine.update_config(voice_config)
                self.ui.textEdit_results.append("🔄 语音配置已重新加载")

            # 重新加载其他配置...
            self.ui.textEdit_results.append("🔄 配置重新加载完成")

        except Exception as e:
            print(f"重新加载配置失败: {e}")
            self.ui.textEdit_results.append(f"❌ 重新加载配置失败: {str(e)}")

    def _show_volcengine_voice_status(self):
        """显示火山引擎语音识别状态"""
        try:
            # 检查火山引擎配置
            from config import get_voice_config, is_volcengine_configured
            voice_config = get_voice_config()
            volcengine_config = voice_config.get("volcengine", {})

            if is_volcengine_configured():
                app_id = volcengine_config.get("app_id", "")
                self.ui.textEdit_results.append(f"📋 火山引擎语音识别: ✅ 已配置（APP ID: {app_id[:8]}...）")
                self.ui.textEdit_results.append("💡 特色: 在线识别 | 高精度 | 专业引擎 | 实时流式")
            else:
                self.ui.textEdit_results.append("📋 火山引擎语音识别: ⚠️ 未配置（需要APP ID和Access Token）")
                self.ui.textEdit_results.append("💡 请在设置中配置火山引擎参数")

        except Exception as e:
            print(f"显示火山引擎语音状态失败: {e}")

    def _show_voice_configuration_prompt(self):
        """显示火山引擎语音识别配置提示"""
        try:
            self.ui.textEdit_results.append("💡 火山引擎语音控制需要配置API参数")
            self.ui.textEdit_results.append("🔧 需要配置: APP ID、Access Token、Secret Key")
            self.ui.textEdit_results.append("⚙️ 请在 设置 → 🎤 语音设置 中配置火山引擎参数")
            self.ui.textEdit_results.append("🌐 配置后可享受高精度在线语音识别功能")
            self.ui.textEdit_results.append("🎯 特色: 在线识别 | 高精度 | 专业引擎 | 实时流式")

            # 禁用语音控制按钮
            self.ui.btn_voice_toggle.setEnabled(False)
            self.ui.btn_voice_toggle.setText("🌐 需要配置")
            self.ui.btn_voice_toggle.setStyleSheet("background-color: #cccccc; color: #666666;")

        except Exception as e:
            print(f"显示语音配置提示失败: {e}")

    # 已移除离线语音识别安装相关代码，现在使用火山引擎语音识别

    def update_voice_status(self, status):
        """更新语音状态显示"""
        try:
            # 在状态栏或结果区域显示语音状态
            self.ui.textEdit_results.append(f"🎤 {status}")
        except Exception as e:
            print(f"更新语音状态失败: {e}")

    def handle_voice_error(self, error_msg):
        """处理语音错误"""
        try:
            self.ui.textEdit_results.append(f"🎤 ❌ 语音错误: {error_msg}")
        except Exception as e:
            print(f"处理语音错误失败: {e}")

    def show_voice_feedback(self, feedback_type, message):
        """显示语音命令反馈"""
        try:
            if feedback_type == "clear":
                # 清除反馈：移除最后一条语音反馈消息
                self._clear_last_voice_feedback()
                return

            feedback_icons = {
                "direction": "🎯",
                "control": "🎮",
                "system": "⚙️",
                "warning": "⚠️",
                "error": "❌"
            }

            icon = feedback_icons.get(feedback_type, "🎤")

            # 🔥 修复：在AI诊断期间，使用更突出的显示方式
            if hasattr(self, 'ai_diagnosis_thread') and self.ai_diagnosis_thread and self.ai_diagnosis_thread.isRunning():
                # AI诊断进行中，使用更突出的格式
                feedback_message = f"\n>>> {icon} {message} <<<\n"
            else:
                # 正常情况
                feedback_message = f"{icon} {message}"

            # 记录这是一条语音反馈消息
            self._last_voice_feedback_message = feedback_message
            self.ui.textEdit_results.append(feedback_message)

            # 🔥 确保滚动到底部，让用户看到反馈
            scrollbar = self.ui.textEdit_results.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            print(f"显示语音反馈失败: {e}")

    def _clear_last_voice_feedback(self):
        """清除最后一条语音反馈消息"""
        try:
            if not hasattr(self, '_last_voice_feedback_message') or not self._last_voice_feedback_message:
                return

            current_text = self.ui.textEdit_results.toPlainText()
            lines = current_text.split('\n')

            # 🔥 修复：查找并移除语音反馈消息（不限于最后一行）
            # 从后往前查找最后一条语音反馈消息
            for i in range(len(lines) - 1, -1, -1):
                if self._last_voice_feedback_message in lines[i]:
                    # 移除找到的语音反馈行
                    lines.pop(i)
                    self.ui.textEdit_results.setPlainText('\n'.join(lines))

                    # 滚动到底部
                    scrollbar = self.ui.textEdit_results.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                    break

            # 清除记录
            self._last_voice_feedback_message = None

        except Exception as e:
            print(f"清除语音反馈失败: {e}")

    def safe_exit(self):
        """安全退出程序"""
        try:
            # 显示退出确认信息
            self.ui.textEdit_results.append("🚪 正在安全退出程序...")

            # 停止摄像头
            if hasattr(self, 'camera_handler') and self.camera_handler:
                self.ui.textEdit_results.append("📷 正在关闭摄像头...")
                self.camera_handler.stop_camera()

            # 停止语音控制
            if hasattr(self, 'voice_controller') and self.voice_controller:
                self.ui.textEdit_results.append("🎤 正在关闭语音控制...")
                self.voice_controller.disable_voice_control()

            # 停止AI诊断线程
            if hasattr(self, 'ai_diagnosis_thread') and self.ai_diagnosis_thread:
                self.ui.textEdit_results.append("🤖 正在停止AI诊断...")
                self.ai_diagnosis_thread.quit()
                self.ai_diagnosis_thread.wait(1000)  # 等待最多1秒

            self.ui.textEdit_results.append("✅ 程序已安全退出")

            # 延迟一点时间让用户看到退出信息
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self.close)

        except Exception as e:
            print(f"安全退出失败: {e}")
            # 如果安全退出失败，直接关闭
            self.close()

    def setup_exit_button_style(self):
        """设置退出按钮样式"""
        try:
            # 为退出按钮设置醒目的红色样式
            exit_button_style = """
                QPushButton#btn_exit {
                    background-color: #dc3545;
                    color: white;
                    border: 2px solid #dc3545;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 8px 16px;
                }
                QPushButton#btn_exit:hover {
                    background-color: #c82333;
                    border-color: #c82333;
                    transform: scale(1.05);
                }
                QPushButton#btn_exit:pressed {
                    background-color: #bd2130;
                    border-color: #bd2130;
                }
            """

            # 应用样式到退出按钮
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + exit_button_style)

            # 设置按钮提示文本
            self.ui.btn_exit.setToolTip("退出程序 (Ctrl+Q)")

        except Exception as e:
            print(f"设置退出按钮样式失败: {e}")

    def setup_connections(self):
        """设置信号连接"""
        # 按钮连接
        self.ui.btn_start_camera.clicked.connect(self.toggle_camera)
        self.ui.btn_start_test.clicked.connect(self.start_test)
        self.ui.btn_stop_test.clicked.connect(self.stop_test)
        self.ui.btn_voice_toggle.clicked.connect(self.toggle_voice_control)
        self.ui.btn_exit.clicked.connect(self.safe_exit)

        # 菜单连接
        self.ui.action_exit.triggered.connect(self.safe_exit)
        self.ui.action_about.triggered.connect(self.show_about)

        # 设置菜单连接
        self.ui.action_camera_settings.triggered.connect(self.show_camera_settings)
        self.ui.action_gesture_settings.triggered.connect(self.show_gesture_settings)

        # 语音控制器信号连接（确保始终连接）
        self.setup_voice_connections()

    def setup_voice_connections(self):
        """设置语音控制器信号连接"""
        try:
            if hasattr(self, 'voice_controller') and self.voice_controller:
                # 断开可能存在的旧连接（避免重复连接）
                try:
                    self.voice_controller.direction_command.disconnect()
                    self.voice_controller.test_control_command.disconnect()
                    self.voice_controller.system_control_command.disconnect()
                    self.voice_controller.voice_status_changed.disconnect()
                    self.voice_controller.voice_error.disconnect()
                    self.voice_controller.command_feedback.disconnect()
                except:
                    pass  # 忽略断开连接的错误

                # 重新连接语音控制信号
                self.voice_controller.direction_command.connect(self.handle_voice_direction)
                self.voice_controller.test_control_command.connect(self.handle_voice_test_control)
                self.voice_controller.system_control_command.connect(self.handle_voice_system_control)
                self.voice_controller.voice_status_changed.connect(self.update_voice_status)
                self.voice_controller.voice_error.connect(self.handle_voice_error)
                self.voice_controller.command_feedback.connect(self.show_voice_feedback)

                print("✅ 语音控制器信号连接已重新建立")
        except Exception as e:
            print(f"设置语音控制器信号连接失败: {e}")

    def toggle_camera(self):
        """切换摄像头状态"""
        try:
            # 检查摄像头是否已启动
            if (hasattr(self, 'camera_handler') and
                self.camera_handler and
                hasattr(self.camera_handler, 'running') and
                self.camera_handler.running):
                # 摄像头已启动，停止它
                self.stop_camera()
            else:
                # 摄像头未启动，启动它
                self.start_camera_and_gesture()
        except Exception as e:
            print(f"切换摄像头状态失败: {e}")
            self.ui.textEdit_results.append(f"❌ 切换摄像头状态失败: {str(e)}")
    
    def start_camera_and_gesture(self):
        """启动摄像头和手势识别"""
        # 防止重复点击
        if not self.ui.btn_start_camera.isEnabled():
            return

        try:
            # 如果摄像头已经启动，直接返回
            if (hasattr(self, 'camera_handler') and
                self.camera_handler and
                hasattr(self.camera_handler, 'running') and
                self.camera_handler.running):
                self.ui.textEdit_results.append("⚠️ 摄像头已经启动")
                return

            # 立即禁用按钮，防止重复点击
            self.ui.btn_start_camera.setEnabled(False)
            self.ui.btn_start_camera.setText("启动中...")
            self.ui.textEdit_results.append("📷 正在启动摄像头...")

            # 强制刷新界面
            QApplication.processEvents()

            # 初始化摄像头处理器（集成手势识别）
            # 使用配置文件中的摄像头设置
            camera_config = get_camera_config()
            camera_index = camera_config.get("default_camera_index", 0)
            resolution = camera_config.get("resolution", {"width": 640, "height": 480})
            fps = camera_config.get("fps", 30)
            exposure = camera_config.get("exposure", -6)
            brightness = camera_config.get("brightness", 128)
            contrast = camera_config.get("contrast", 128)

            self.camera_handler = CameraWithGestureHandler(
                camera_index=camera_index,
                resolution=resolution,
                fps=fps,
                exposure=exposure,
                brightness=brightness,
                contrast=contrast
            )
            self.communication = MockCommunication()
            # 初始化AI诊断（使用配置文件）
            config = get_siliconflow_config()
            self.ai_diagnosis = AIVisionDiagnosis(
                api_key=config.get("api_key"),
                model=config.get("default_model")
                # 不在这里设置回调，由线程处理
            )

            print(f"已加载配置 - 摄像头: {camera_index}, 分辨率: {resolution}, 帧率: {fps}")
            print(f"API配置 - 模型: {config.get('default_model')}, 密钥: {'已配置' if config.get('api_key') else '未配置'}")

            # 连接摄像头信号
            self.camera_handler.frame_ready.connect(self.update_camera_display)
            self.camera_handler.distance_updated.connect(self.update_distance)
            self.camera_handler.finger_direction_detected.connect(self.handle_finger_direction)
            self.camera_handler.gesture_status_changed.connect(self.update_gesture_status)

            # 连接通信信号
            self.communication.finger_direction_received.connect(self.handle_finger_direction)
            self.communication.distance_received.connect(self.update_distance)
            self.communication.connection_status_changed.connect(self.handle_connection_status)

            # 启动摄像头
            camera_started = self.camera_handler.start_camera()

            if camera_started:
                self.ui.btn_start_test.setEnabled(True)
                self.ui.btn_start_camera.setText("已启动")
                self.ui.btn_start_camera.setStyleSheet("background-color: #4CAF50; color: white;")
                self.ui.label_gesture_status.setText("运行中")
                self.ui.label_gesture_status.setStyleSheet("font-size: 14px; color: green;")
                self.ui.textEdit_results.append("✅ 摄像头启动成功")

                # 启动通信
                self.communication.connect_device()

                # 重新建立语音控制器信号连接（关键修复）
                self.setup_voice_connections()
                self.ui.textEdit_results.append("🎤 语音控制信号连接已重新建立")

                # 不重新启用按钮，保持"已启动"状态
            else:
                # 启动失败，恢复按钮状态
                self.ui.btn_start_camera.setEnabled(True)
                self.ui.btn_start_camera.setText("重试启动")
                self.ui.btn_start_camera.setStyleSheet("")
                self.ui.textEdit_results.append("❌ 摄像头启动失败，请检查摄像头连接")

        except Exception as e:
            # 异常处理，恢复按钮状态
            self.ui.btn_start_camera.setEnabled(True)
            self.ui.btn_start_camera.setText("重试启动")
            self.ui.btn_start_camera.setStyleSheet("")
            self.ui.textEdit_results.append(f"❌ 摄像头启动异常: {str(e)}")
            print(f"摄像头启动异常: {e}")
            traceback.print_exc()
    
    def update_camera_display(self, frame):
        """更新摄像头显示"""
        try:
            if frame is not None and frame.size > 0:
                pixmap = self.camera_handler.numpy_to_qpixmap(frame)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(self.ui.label_camera.size(), Qt.AspectRatioMode.KeepAspectRatio)
                    self.ui.label_camera.setPixmap(scaled_pixmap)
                else:
                    self.ui.label_camera.setText("摄像头画面处理失败")
            else:
                self.ui.label_camera.setText("摄像头无画面")
        except Exception as e:
            print(f"更新摄像头显示失败: {e}")
            self.ui.label_camera.setText(f"摄像头错误: {str(e)}")
    
    def handle_finger_direction(self, direction):
        """优化版本：处理手指方向信号"""
        # 预定义颜色映射，避免重复创建字典
        if not hasattr(self, '_color_map'):
            self._color_map = {
                "Up": "blue", "Down": "orange", "Left": "purple",
                "Right": "green", "None": "red"
            }
            self._style_template = "font-size: 16px; font-weight: bold; color: {};"

        # 更新界面显示
        self.ui.label_current_direction.setText(direction)
        color = self._color_map.get(direction, "red")
        self.ui.label_current_direction.setStyleSheet(self._style_template.format(color))

        # 如果正在测试，处理测试逻辑
        if self.is_testing:
            self.handle_test_direction(direction)
    
    def update_gesture_status(self, status):
        """更新手势状态"""
        try:
            self.ui.label_gesture_status.setText(str(status))
        except Exception as e:
            print(f"更新手势状态失败: {e}")
            # 使用安全的方式更新状态
            try:
                self.ui.label_gesture_status.setText("状态更新失败")
            except:
                pass
    
    def start_test(self):
        """开始视力测试"""
        self.is_testing = True
        self.current_vision = 5.0  # 从5.0开始测试
        self.consecutive_failures = 0
        self.test_results = []

        self.ui.btn_start_test.setEnabled(False)
        self.ui.btn_stop_test.setEnabled(True)

        # 通知语音控制器进入测试模式
        if self.voice_controller:
            self.voice_controller.set_test_mode(True)

        self.generate_new_test()
        self.test_timer.start(100)  # 100ms检查一次

        self.ui.textEdit_results.append("=== 视力测试开始 ===")
        self.ui.textEdit_results.append("🎤 现在可以使用语音指向方向：向上、向下、向左、向右")
        self.ui.label_status.setText("状态: 测试进行中...")

    def stop_test(self):
        """停止视力测试"""
        self.is_testing = False
        self.test_timer.stop()

        self.ui.btn_start_test.setEnabled(True)
        self.ui.btn_stop_test.setEnabled(False)

        # 通知语音控制器退出测试模式
        if self.voice_controller:
            self.voice_controller.set_test_mode(False)

        self.calculate_final_result()
        self.ui.label_status.setText("状态: 测试已停止")
        self.ui.textEdit_results.append("🎤 现在可以使用语音控制：开始测试、停止测试")
    
    def generate_new_test(self):
        """生成新的测试项目"""
        import random

        # 随机选择方向
        directions = ["Up", "Down", "Left", "Right"]
        self.current_direction = random.choice(directions)

        # 计算E字母大小
        width, height = self.vision_calculator.calculate_e_size(
            self.current_vision, self.current_distance)

        # 更新显示
        self.e_letter_widget.set_letter_params(width, self.current_direction)

        # 重置计时
        self.test_start_time = time.time()
        self.correct_start_time = 0

        self.ui.textEdit_results.append(f"视力 {self.current_vision}: {self.current_direction}")
        self.ui.textEdit_results.append("请指向E字开口方向")

    def handle_test_direction(self, direction):
        """处理测试中的方向检测"""
        if not self.is_testing:
            return

        current_time = time.time()

        if direction == self.current_direction:
            # 方向正确
            if self.correct_start_time == 0:
                self.correct_start_time = current_time
                self.ui.textEdit_results.append(f"开始正确指向: {direction}")
        else:
            # 方向错误，重置计时
            if self.correct_start_time > 0:
                self.ui.textEdit_results.append(f"方向改变: {direction} (需要: {self.current_direction})")
            self.correct_start_time = 0

        # 检查5秒超时
        if current_time - self.test_start_time >= 7.0:
            self.handle_test_timeout()
    
    def handle_test_success(self):
        """处理测试成功"""
        self.correct_start_time = 0
        self.flash_background("green")
        self.test_results.append((self.current_vision, True))
        self.consecutive_failures = 0

        self.ui.textEdit_results.append(f"✓ 视力 {self.current_vision} 测试成功")

        # 获取下一个视力级别
        next_vision = self.vision_calculator.get_next_vision_level(self.current_vision, True, {})
        if next_vision is None:
            self.ui.textEdit_results.append("已达到最高视力级别")
            self.complete_test()
        else:
            self.current_vision = next_vision
            self.ui.textEdit_results.append(f"进入下一级别: {self.current_vision}")
            self.generate_new_test()

    def handle_test_timeout(self):
        """处理测试超时"""
        self.correct_start_time = 0
        self.flash_background("red")
        self.test_results.append((self.current_vision, False))
        self.consecutive_failures += 1

        self.ui.textEdit_results.append(f"✗ 视力 {self.current_vision} 测试失败（超时）")

        # 检查是否测试完成
        if self.vision_calculator.is_test_complete(self.current_vision, self.consecutive_failures):
            self.complete_test()
        else:
            next_vision = self.vision_calculator.get_next_vision_level(self.current_vision, False, {})
            if next_vision is None:
                self.complete_test()
            else:
                self.current_vision = next_vision
                self.ui.textEdit_results.append(f"进入下一级别: {self.current_vision}")
                self.generate_new_test()

    def complete_test(self):
        """完成测试"""
        self.is_testing = False
        self.test_timer.stop()

        self.ui.btn_start_test.setEnabled(True)
        self.ui.btn_stop_test.setEnabled(False)

        # 通知语音控制器退出测试模式
        if self.voice_controller:
            self.voice_controller.set_test_mode(False)

        self.calculate_final_result()
        self.ui.textEdit_results.append("🎤 现在可以使用语音控制：开始测试、停止测试")
        self.ui.label_status.setText("状态: 测试完成")
    
    def calculate_final_result(self):
        """计算最终结果"""
        if not self.test_results:
            self.ui.textEdit_results.append("没有有效的测试结果")
            return

        final_vision = self.vision_calculator.calculate_final_vision(self.test_results)

        # 评估结果
        if final_vision >= 5.0:
            assessment = "视力正常"
            suggestion = "视力状况良好，请继续保持良好的用眼习惯"
        elif final_vision >= 4.5:
            assessment = "轻度视力下降"
            suggestion = "建议注意用眼卫生，适当休息，定期检查"
        else:
            assessment = "视力下降明显"
            suggestion = "建议及时到眼科医院进行详细检查"

        results = [
            "=== 测试结果 ===",
            f"最终视力值: {final_vision}",
            "\n测试过程:"
        ]

        for i, (vision, success) in enumerate(self.test_results, 1):
            result = "成功" if success else "失败"
            results.append(f"  {i}. 视力 {vision}: {result}")

        results.extend([
            f"\n视力评估: {assessment}",
            f"建议: {suggestion}"
        ])

        self.ui.textEdit_results.append('\n'.join(results))

        # 添加AI诊断
        self.add_ai_diagnosis()

    def check_test_progress(self):
        """检查测试进度"""
        if not self.is_testing:
            return

        current_time = time.time()
        elapsed = current_time - self.test_start_time

        # 检查是否达到成功条件
        if self.correct_start_time > 0:
            correct_duration = current_time - self.correct_start_time
            self.ui.label_status.setText(f"正确指向 {correct_duration:.1f}s / 2.0s")

            # 检查是否达到2秒成功条件
            if correct_duration >= 2.0:
                self.handle_test_success()
                return
        else:
            self.ui.label_status.setText(f"等待正确指向 {self.current_direction}...")

        # 检查5秒超时
        if elapsed >= 7.0:
            self.handle_test_timeout()

    def add_ai_diagnosis(self):
        """添加AI诊断分析（异步版本）"""
        try:
            self.ui.textEdit_results.append("\n=== AI智能诊断分析 ===")

            # 检查API密钥配置
            if not is_api_key_configured():
                self.ui.textEdit_results.append("⚠️ 未配置SiliconFlow API密钥，使用基础诊断模式")
                self.ui.textEdit_results.append("\n如需使用AI智能诊断，请配置API密钥：")
                self.ui.textEdit_results.append(get_api_setup_instructions())
                return

            # 显示开始信息
            self.ui.textEdit_results.append("🤖 正在启动AI诊断服务...")
            self.ui.textEdit_results.append("⏳ 请稍候，AI正在分析您的视力测试数据...")

            # 初始化流式显示状态
            self._stream_displayed = False
            self._stream_content = ""
            self._ai_diagnosis_start_pos = len(self.ui.textEdit_results.toPlainText())

            # 创建并启动AI诊断线程
            if self.ai_diagnosis_thread and self.ai_diagnosis_thread.isRunning():
                self.ai_diagnosis_thread.stop()

            self.ai_diagnosis_thread = AIDiagnosisThread(self.ai_diagnosis, self.test_results)

            # 连接信号
            self.ai_diagnosis_thread.progress_updated.connect(self.on_ai_progress_update)
            self.ai_diagnosis_thread.stream_started.connect(self.on_ai_stream_started)
            self.ai_diagnosis_thread.stream_content.connect(self.on_ai_stream_content)
            self.ai_diagnosis_thread.stream_ended.connect(self.on_ai_stream_ended)
            self.ai_diagnosis_thread.diagnosis_completed.connect(self.on_ai_diagnosis_completed)
            self.ai_diagnosis_thread.diagnosis_failed.connect(self.on_ai_diagnosis_failed)

            # 启动线程
            self.ai_diagnosis_thread.start()

        except Exception as e:
            self.ui.textEdit_results.append(f"\n❌ AI诊断启动失败: {str(e)}")
            self.ui.textEdit_results.append("请参考上述基础评估结果。")

    def on_ai_progress_update(self, message):
        """AI进度更新回调"""
        # 更新最后一行的进度信息
        current_text = self.ui.textEdit_results.toPlainText()
        lines = current_text.split('\n')

        # 如果最后一行是进度信息，则替换它
        if lines and ('正在启动' in lines[-1] or '正在调用' in lines[-1] or '尝试' in lines[-1]):
            lines[-1] = f"📡 {message}"
            self.ui.textEdit_results.setPlainText('\n'.join(lines))
        else:
            self.ui.textEdit_results.append(f"📡 {message}")

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_stream_started(self):
        """AI流式输出开始"""
        self.ui.textEdit_results.append("\n🌊 开始接收AI诊断结果...")
        self._stream_displayed = True
        self._stream_content = ""

        # 记录流式内容开始位置
        current_text = self.ui.textEdit_results.toPlainText()
        self._stream_start_marker = "🌊 开始接收AI诊断结果..."

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_stream_content(self, content):
        """AI流式内容更新"""
        self._stream_content += content

        # 实时更新显示
        current_text = self.ui.textEdit_results.toPlainText()
        start_pos = current_text.rfind(self._stream_start_marker)

        if start_pos != -1:
            # 保留开始标记之前的内容
            before_stream = current_text[:start_pos + len(self._stream_start_marker)]
            # 添加流式内容
            new_text = before_stream + "\n\n" + self._stream_content
            self.ui.textEdit_results.setPlainText(new_text)
        else:
            # 如果找不到标记，直接追加
            self.ui.textEdit_results.append(content)

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_stream_ended(self):
        """AI流式输出结束"""
        # 添加完成标记
        current_text = self.ui.textEdit_results.toPlainText()
        final_text = current_text + "\n\n✅ AI诊断完成"
        self.ui.textEdit_results.setPlainText(final_text)

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_diagnosis_completed(self, diagnosis):
        """AI诊断完成回调"""
        # 如果没有通过流式显示，则直接显示结果
        if not self._stream_displayed:
            self.ui.textEdit_results.append("\n" + diagnosis)
            self.ui.textEdit_results.append("\n✅ AI诊断完成")

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_diagnosis_failed(self, error_message):
        """AI诊断失败回调"""
        self.ui.textEdit_results.append(f"\n❌ AI诊断分析失败: {error_message}")
        self.ui.textEdit_results.append("请参考上述基础评估结果。")

        # 滚动到底部
        scrollbar = self.ui.textEdit_results.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def flash_background(self, color):
        """闪烁背景颜色"""
        self.e_letter_widget.set_background_color(color)
        self.flash_timer.start(500)  # 500ms后恢复
    
    def reset_background(self):
        """重置背景颜色"""
        self.e_letter_widget.set_background_color("white")
        self.flash_timer.stop()
    
    def update_distance(self, distance):
        """更新距离信息"""
        self.current_distance = distance
    
    def handle_connection_status(self, connected):
        """处理连接状态变化"""
        status = "已连接" if connected else "未连接"
        self.ui.label_status.setText(f"状态: {status}")
    
    # 已移除测试进度检查方法
    
    def show_about(self):
        """显示关于对话框"""
        from PySide6.QtWidgets import QMessageBox

        about_text = """
        电子视力系统 v2.0.0

        功能特性：
        • 实时手势识别
        • 语音控制识别
        • E字母显示
        • AI智能诊断
        • 可视化界面编辑

        语音命令：
        • 向上 / 向下 / 向左 / 向右

        技术栈：
        • PySide6 - 界面框架
        • OpenCV - 图像处理
        • MediaPipe - 手势识别
        • 火山引擎 - 语音识别
        • SiliconFlow - AI诊断

        开发团队：Vision System
        """

        QMessageBox.about(self, "关于", about_text)

    def show_camera_settings(self):
        """显示摄像头设置"""
        try:
            dialog = SettingsDialog(self)
            # 切换到摄像头设置标签页
            dialog.tab_widget.setCurrentIndex(1)
            dialog.exec()
        except Exception as e:
            print(f"打开设置对话框失败: {e}")
            self.ui.textEdit_results.append(f"❌ 打开设置失败: {str(e)}")

    def show_gesture_settings(self):
        """显示手势识别设置"""
        try:
            dialog = SettingsDialog(self)
            # 切换到系统设置标签页（包含手势识别参数）
            dialog.tab_widget.setCurrentIndex(3)
            dialog.exec()
        except Exception as e:
            print(f"打开设置对话框失败: {e}")
            self.ui.textEdit_results.append(f"❌ 打开设置失败: {str(e)}")

    # 已移除测试设置方法

    def apply_medical_theme(self):
        """应用医疗主题样式"""
        try:
            # 设置应用程序图标
            app_icon = resource_manager.get_icon('app')
            if not app_icon.isNull():
                self.setWindowIcon(app_icon)

            # 加载并应用样式表
            stylesheet = resource_manager.load_stylesheet()
            if stylesheet:
                self.setStyleSheet(stylesheet)

            # 为按钮添加图标
            self.apply_button_icons()

            # 设置窗口标题
            self.setWindowTitle("电子视力系统 - 专业版")

        except Exception as e:
            print(f"应用医疗主题失败: {e}")

    def apply_button_icons(self):
        """为按钮应用图标"""
        try:
            # 为主要按钮添加图标
            button_icons = {
                'btn_start_camera': 'camera'
            }

            for button_name, icon_name in button_icons.items():
                if hasattr(self.ui, button_name):
                    button = getattr(self.ui, button_name)
                    resource_manager.apply_button_icon(button, icon_name, (20, 20))

        except Exception as e:
            print(f"应用按钮图标失败: {e}")

    def closeEvent(self, event):
        """关闭事件"""
        # 停止AI诊断线程
        if self.ai_diagnosis_thread and self.ai_diagnosis_thread.isRunning():
            self.ai_diagnosis_thread.stop()

        # 停止摄像头
        if self.camera_handler:
            self.camera_handler.stop_camera()

        # 断开通信
        if self.communication:
            self.communication.disconnect()

        # 清理语音控制器
        if self.voice_controller:
            self.voice_controller.cleanup()

        event.accept()

def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("电子视力系统")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("Vision Test System")

        # 设置应用程序图标
        try:
            app_icon = resource_manager.get_icon('app')
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
        except Exception as e:
            print(f"设置应用图标失败: {e}")

        # 创建主窗口
        main_window = VisionMainWindow()
        main_window.show()

        # 运行应用程序
        sys.exit(app.exec())

    except Exception as e:
        print(f"程序启动失败: {e}")
        traceback.print_exc()
        # 确保在出错时也能正常退出
        try:
            sys.exit(1)
        except:
            pass

if __name__ == "__main__":
    main()
