"""
完整的设置对话框
包含摄像头、语音、AI API等所有设置选项
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QSpinBox, QComboBox, QPushButton, QGroupBox,
                            QMessageBox, QTabWidget, QWidget, QFormLayout,
                            QLineEdit, QCheckBox, QDoubleSpinBox, QSlider,
                            QTextEdit, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPalette, QPixmap, QPainter
import json
import os

class SettingsDialog(QDialog):
    """完整的设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 电子视力系统设置")
        self.setModal(True)
        self.resize(700, 600)

        # 设置窗口样式
        self.setup_window_style()

        # 加载当前配置
        self.load_config()

        # 创建界面
        self.setup_ui()

        # 连接信号
        self.setup_connections()

    def setup_window_style(self):
        """设置窗口样式"""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-radius: 10px;
            }
            QTabWidget::pane {
                border: 2px solid #dee2e6;
                border-radius: 8px;
                background: white;
                margin-top: 5px;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 #f8f9fa);
                border: 2px solid #dee2e6;
                border-bottom: none;
                border-radius: 8px 8px 0 0;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: bold;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border-color: #0056b3;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-color: #2196f3;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #495057;
                font-size: 14px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #007bff, stop:1 #0056b3);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0056b3, stop:1 #004085);
            }
            QPushButton:pressed {
                background: #004085;
            }
            QPushButton#resetButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc3545, stop:1 #c82333);
            }
            QPushButton#resetButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c82333, stop:1 #a71e2a);
            }
            QPushButton#testButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #28a745, stop:1 #1e7e34);
            }
            QPushButton#testButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e7e34, stop:1 #155724);
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 2px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                background: white;
                selection-background-color: #007bff;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #007bff;
                outline: none;
            }
            QCheckBox {
                spacing: 8px;
                font-weight: normal;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #007bff;
                border-color: #007bff;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xMC42IDEuNEwzLjkgOC4xTDEuNCA1LjYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
            QLabel {
                color: #495057;
                font-weight: normal;
            }
        """)

        # 设置字体
        font = QFont()
        font.setFamily("Microsoft YaHei, SimHei, Arial")
        font.setPointSize(10)
        self.setFont(font)
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists("user_config.json"):
                with open("user_config.json", "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            else:
                self.config = self.get_default_config()
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "siliconflow": {
                "api_key": "",
                "default_model": "Qwen/Qwen3-8B",
                "timeout": 15,
                "max_tokens": 500,
                "temperature": 0.3,
                "top_p": 0.8
            },
            "camera": {
                "default_camera_index": 0,
                "resolution": {"width": 640, "height": 480},
                "fps": 30,
                "exposure": -4,
                "brightness": 128,
                "contrast": 128
            },
            "system": {
                "auto_fullscreen": True,
                "enable_ai_diagnosis": True,
                "voice_recognition": {
                    "enabled": False,
                    "volcengine": {
                        "app_id": "",
                        "access_token": "",
                        "secret_key": ""
                    },
                    "audio": {
                        "microphone_index": -1,
                        "sample_rate": 16000,
                        "chunk_size": 1024,
                        "channels": 1
                    },
                    "auto_start": False
                }
            }
        }
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # AI API设置标签页
        self.setup_ai_tab()
        
        # 摄像头设置标签页
        self.setup_camera_tab()
        
        # 语音设置标签页
        self.setup_voice_tab()
        
        # 系统设置标签页
        self.setup_system_tab()
        
        layout.addWidget(self.tab_widget)
        
        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-top: 1px solid #dee2e6;
                border-radius: 0 0 10px 10px;
                padding: 10px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)

        # 创建带图标的按钮
        self.test_button = QPushButton("🧪 测试设置")
        self.test_button.setObjectName("testButton")
        self.test_button.setToolTip("测试当前标签页的设置")

        self.save_button = QPushButton("💾 保存设置")
        self.save_button.setToolTip("保存所有设置并关闭对话框")

        self.cancel_button = QPushButton("❌ 取消")
        self.cancel_button.setToolTip("取消修改并关闭对话框")

        self.reset_button = QPushButton("🔄 恢复默认")
        self.reset_button.setObjectName("resetButton")
        self.reset_button.setToolTip("将所有设置恢复为默认值")

        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addWidget(button_frame)
    
    def setup_ai_tab(self):
        """设置AI API标签页"""
        ai_widget = QWidget()
        layout = QVBoxLayout(ai_widget)
        
        # SiliconFlow API设置
        api_group = QGroupBox("SiliconFlow API设置")
        api_layout = QFormLayout(api_group)
        
        # API密钥
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key = self.config.get("siliconflow", {}).get("api_key", "")
        self.api_key_edit.setText(api_key)
        api_layout.addRow("API密钥:", self.api_key_edit)
        
        # 显示API密钥按钮
        show_key_btn = QPushButton("显示/隐藏")
        show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        api_layout.addRow("", show_key_btn)
        
        # 模型选择
        self.model_combo = QComboBox()
        models = [
            ("Qwen3-8B (推荐，速度快)", "Qwen/Qwen3-8B"),
            ("Qwen3-14B (平衡性能)", "Qwen/Qwen3-14B"),
            ("Qwen3-32B (高性能)", "Qwen/Qwen3-32B"),
            ("DeepSeek-R1 (最新推理)", "deepseek-ai/DeepSeek-R1"),
            ("GLM-4-32B (智谱AI)", "THUDM/GLM-4-32B-0414")
        ]
        
        current_model = self.config.get("siliconflow", {}).get("default_model", "Qwen/Qwen3-8B")
        for name, value in models:
            self.model_combo.addItem(name, value)
            if value == current_model:
                self.model_combo.setCurrentText(name)
        
        api_layout.addRow("AI模型:", self.model_combo)
        
        # API参数
        siliconflow_config = self.config.get("siliconflow", {})
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 60)
        self.timeout_spin.setValue(siliconflow_config.get("timeout", 15))
        api_layout.addRow("超时时间(秒):", self.timeout_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 2000)
        self.max_tokens_spin.setValue(siliconflow_config.get("max_tokens", 500))
        api_layout.addRow("最大Token数:", self.max_tokens_spin)
        
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 1.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(siliconflow_config.get("temperature", 0.3))
        api_layout.addRow("温度参数:", self.temperature_spin)
        
        layout.addWidget(api_group)
        layout.addStretch()
        
        self.tab_widget.addTab(ai_widget, "🤖 AI智能")
    
    def setup_camera_tab(self):
        """设置摄像头标签页"""
        camera_widget = QWidget()
        layout = QVBoxLayout(camera_widget)
        
        # 摄像头基本设置
        camera_group = QGroupBox("摄像头设置")
        camera_layout = QFormLayout(camera_group)
        
        camera_config = self.config.get("camera", {})
        
        # 摄像头索引
        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 10)
        self.camera_index_spin.setValue(camera_config.get("default_camera_index", 0))
        camera_layout.addRow("摄像头设备:", self.camera_index_spin)
        
        # 分辨率
        self.resolution_combo = QComboBox()
        resolutions = [
            ("640x480", {"width": 640, "height": 480}),
            ("1280x720", {"width": 1280, "height": 720}),
            ("1920x1080", {"width": 1920, "height": 1080})
        ]
        
        current_resolution = camera_config.get("resolution", {"width": 640, "height": 480})
        for name, value in resolutions:
            self.resolution_combo.addItem(name, value)
            if value == current_resolution:
                self.resolution_combo.setCurrentText(name)
        
        camera_layout.addRow("分辨率:", self.resolution_combo)
        
        # 帧率
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(10, 60)
        self.fps_spin.setValue(camera_config.get("fps", 30))
        camera_layout.addRow("帧率:", self.fps_spin)
        
        layout.addWidget(camera_group)
        
        # 摄像头高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 曝光
        self.exposure_spin = QSpinBox()
        self.exposure_spin.setRange(-10, 0)
        self.exposure_spin.setValue(camera_config.get("exposure", -4))
        advanced_layout.addRow("曝光值:", self.exposure_spin)
        
        # 亮度
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 255)
        self.brightness_spin.setValue(camera_config.get("brightness", 128))
        advanced_layout.addRow("亮度:", self.brightness_spin)
        
        # 对比度
        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(0, 255)
        self.contrast_spin.setValue(camera_config.get("contrast", 128))
        advanced_layout.addRow("对比度:", self.contrast_spin)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        self.tab_widget.addTab(camera_widget, "📹 摄像头")

    def setup_voice_tab(self):
        """设置语音标签页"""
        voice_widget = QWidget()
        layout = QVBoxLayout(voice_widget)

        # 语音识别设置
        voice_group = QGroupBox("火山引擎语音识别")
        voice_layout = QFormLayout(voice_group)

        voice_config = self.config.get("system", {}).get("voice_recognition", {})
        volcengine_config = voice_config.get("volcengine", {})

        # 启用语音识别
        self.voice_enabled_check = QCheckBox()
        self.voice_enabled_check.setChecked(voice_config.get("enabled", False))
        voice_layout.addRow("🎙️ 启用语音识别:", self.voice_enabled_check)

        # 自动启动
        self.voice_autostart_check = QCheckBox()
        self.voice_autostart_check.setChecked(voice_config.get("auto_start", False))
        voice_layout.addRow("🚀 程序启动时自动启用:", self.voice_autostart_check)

        # 性能优化提示
        perf_label = QLabel("💡 提示：语音识别会消耗较多系统资源，建议按需启用")
        perf_label.setStyleSheet("color: #6c757d; font-style: italic; margin: 5px;")
        voice_layout.addRow("", perf_label)

        # 火山引擎配置
        self.app_id_edit = QLineEdit()
        self.app_id_edit.setText(volcengine_config.get("app_id", ""))
        voice_layout.addRow("APP ID:", self.app_id_edit)

        self.access_token_edit = QLineEdit()
        self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.access_token_edit.setText(volcengine_config.get("access_token", ""))
        voice_layout.addRow("Access Token:", self.access_token_edit)

        self.secret_key_edit = QLineEdit()
        self.secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.secret_key_edit.setText(volcengine_config.get("secret_key", ""))
        voice_layout.addRow("Secret Key:", self.secret_key_edit)

        # 显示密钥按钮
        show_voice_btn = QPushButton("显示/隐藏密钥")
        show_voice_btn.clicked.connect(self.toggle_voice_key_visibility)
        voice_layout.addRow("", show_voice_btn)

        layout.addWidget(voice_group)

        # 音频设置
        audio_group = QGroupBox("音频设置")
        audio_layout = QFormLayout(audio_group)

        audio_config = voice_config.get("audio", {})

        # 麦克风设备
        self.mic_index_spin = QSpinBox()
        self.mic_index_spin.setRange(-1, 10)
        self.mic_index_spin.setValue(audio_config.get("microphone_index", -1))
        audio_layout.addRow("麦克风设备(-1=默认):", self.mic_index_spin)

        # 采样率
        self.sample_rate_combo = QComboBox()
        sample_rates = [("8000 Hz", 8000), ("16000 Hz", 16000), ("44100 Hz", 44100)]
        current_rate = audio_config.get("sample_rate", 16000)
        for name, value in sample_rates:
            self.sample_rate_combo.addItem(name, value)
            if value == current_rate:
                self.sample_rate_combo.setCurrentText(name)
        audio_layout.addRow("采样率:", self.sample_rate_combo)

        # 音频块大小
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(512, 4096)
        self.chunk_size_spin.setSingleStep(512)
        self.chunk_size_spin.setValue(audio_config.get("chunk_size", 1024))
        self.chunk_size_spin.setToolTip("较小的值可以降低延迟，但可能影响识别准确性")
        audio_layout.addRow("🔧 音频块大小:", self.chunk_size_spin)

        # 延迟优化选项
        self.low_latency_check = QCheckBox()
        self.low_latency_check.setChecked(audio_config.get("low_latency_mode", True))
        self.low_latency_check.setToolTip("启用低延迟模式可以提高响应速度")
        audio_layout.addRow("⚡ 低延迟模式:", self.low_latency_check)

        layout.addWidget(audio_group)
        layout.addStretch()

        self.tab_widget.addTab(voice_widget, "🎙️ 语音识别")

    def setup_system_tab(self):
        """设置系统标签页"""
        system_widget = QWidget()
        layout = QVBoxLayout(system_widget)

        # 显示设置
        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout(display_group)

        system_config = self.config.get("system", {})

        # 自动全屏
        self.fullscreen_check = QCheckBox()
        self.fullscreen_check.setChecked(system_config.get("auto_fullscreen", True))
        display_layout.addRow("启动时自动全屏:", self.fullscreen_check)

        layout.addWidget(display_group)

        # AI诊断设置
        ai_group = QGroupBox("AI诊断设置")
        ai_layout = QFormLayout(ai_group)

        # 启用AI诊断
        self.ai_enabled_check = QCheckBox()
        self.ai_enabled_check.setChecked(system_config.get("enable_ai_diagnosis", True))
        ai_layout.addRow("启用AI诊断:", self.ai_enabled_check)

        # API密钥提醒
        self.api_reminder_check = QCheckBox()
        self.api_reminder_check.setChecked(system_config.get("show_api_key_reminder", True))
        ai_layout.addRow("显示API密钥提醒:", self.api_reminder_check)

        layout.addWidget(ai_group)

        # 视力测试设置
        test_group = QGroupBox("视力测试设置")
        test_layout = QFormLayout(test_group)

        vision_config = system_config.get("vision_test", {})

        # 起始视力
        self.start_vision_spin = QDoubleSpinBox()
        self.start_vision_spin.setRange(4.0, 5.5)
        self.start_vision_spin.setSingleStep(0.1)
        self.start_vision_spin.setValue(vision_config.get("start_vision", 5.0))
        test_layout.addRow("起始视力:", self.start_vision_spin)

        # 成功保持时间
        self.hold_time_spin = QDoubleSpinBox()
        self.hold_time_spin.setRange(0.5, 5.0)
        self.hold_time_spin.setSingleStep(0.1)
        self.hold_time_spin.setValue(vision_config.get("success_hold_time", 1.0))
        test_layout.addRow("成功保持时间(秒):", self.hold_time_spin)

        # 超时时间
        self.timeout_test_spin = QDoubleSpinBox()
        self.timeout_test_spin.setRange(3.0, 10.0)
        self.timeout_test_spin.setSingleStep(0.5)
        self.timeout_test_spin.setValue(vision_config.get("timeout_duration", 5.0))
        test_layout.addRow("超时时间(秒):", self.timeout_test_spin)

        # 稳定帧数
        self.stable_frames_spin = QSpinBox()
        self.stable_frames_spin.setRange(1, 10)
        self.stable_frames_spin.setValue(vision_config.get("stable_frames", 2))
        test_layout.addRow("手势稳定帧数:", self.stable_frames_spin)

        layout.addWidget(test_group)
        layout.addStretch()

        self.tab_widget.addTab(system_widget, "⚙️ 系统设置")

    def setup_connections(self):
        """设置信号连接"""
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.test_button.clicked.connect(self.test_settings)

    def toggle_api_key_visibility(self):
        """切换API密钥显示/隐藏"""
        if self.api_key_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_voice_key_visibility(self):
        """切换语音密钥显示/隐藏"""
        if self.access_token_edit.echoMode() == QLineEdit.EchoMode.Password:
            self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.secret_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.access_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def test_settings(self):
        """测试设置"""
        try:
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:  # AI设置
                self.test_ai_settings()
            elif current_tab == 1:  # 摄像头设置
                self.test_camera_settings()
            elif current_tab == 2:  # 语音设置
                self.test_voice_settings()
            else:  # 系统设置
                QMessageBox.information(self, "测试", "系统设置无需测试")
        except Exception as e:
            QMessageBox.warning(self, "测试失败", f"测试设置时出错: {str(e)}")

    def test_ai_settings(self):
        """测试AI设置"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "测试失败", "请先输入API密钥")
            return

        QMessageBox.information(self, "测试", "AI API设置看起来正常\n(实际连接测试需要在主程序中进行)")

    def test_camera_settings(self):
        """测试摄像头设置"""
        try:
            import cv2
            camera_index = self.camera_index_spin.value()
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                cap.release()
                QMessageBox.information(self, "测试成功", f"摄像头 {camera_index} 可以正常使用")
            else:
                QMessageBox.warning(self, "测试失败", f"无法打开摄像头 {camera_index}")
        except ImportError:
            QMessageBox.warning(self, "测试失败", "OpenCV未安装，无法测试摄像头")
        except Exception as e:
            QMessageBox.warning(self, "测试失败", f"摄像头测试失败: {str(e)}")

    def test_voice_settings(self):
        """测试语音设置"""
        app_id = self.app_id_edit.text().strip()
        access_token = self.access_token_edit.text().strip()
        secret_key = self.secret_key_edit.text().strip()

        if not all([app_id, access_token, secret_key]):
            QMessageBox.warning(self, "测试失败", "请填写完整的火山引擎配置信息")
            return

        QMessageBox.information(self, "测试", "语音识别配置看起来正常\n(实际连接测试需要在主程序中进行)")

    def reset_to_defaults(self):
        """恢复默认设置"""
        reply = QMessageBox.question(self, "确认", "确定要恢复所有设置到默认值吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.config = self.get_default_config()
            self.load_values_to_ui()
            QMessageBox.information(self, "完成", "已恢复默认设置")

    def load_values_to_ui(self):
        """将配置值加载到UI控件"""
        # AI设置
        siliconflow_config = self.config.get("siliconflow", {})
        self.api_key_edit.setText(siliconflow_config.get("api_key", ""))

        # 摄像头设置
        camera_config = self.config.get("camera", {})
        self.camera_index_spin.setValue(camera_config.get("default_camera_index", 0))
        self.fps_spin.setValue(camera_config.get("fps", 30))

        # 语音设置
        voice_config = self.config.get("system", {}).get("voice_recognition", {})
        self.voice_enabled_check.setChecked(voice_config.get("enabled", True))

        # 系统设置
        system_config = self.config.get("system", {})
        self.fullscreen_check.setChecked(system_config.get("auto_fullscreen", True))

    def save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            # SiliconFlow设置
            if "siliconflow" not in self.config:
                self.config["siliconflow"] = {}

            self.config["siliconflow"]["api_key"] = self.api_key_edit.text().strip()
            self.config["siliconflow"]["default_model"] = self.model_combo.currentData()
            self.config["siliconflow"]["timeout"] = self.timeout_spin.value()
            self.config["siliconflow"]["max_tokens"] = self.max_tokens_spin.value()
            self.config["siliconflow"]["temperature"] = self.temperature_spin.value()

            # 摄像头设置
            if "camera" not in self.config:
                self.config["camera"] = {}

            self.config["camera"]["default_camera_index"] = self.camera_index_spin.value()
            self.config["camera"]["resolution"] = self.resolution_combo.currentData()
            self.config["camera"]["fps"] = self.fps_spin.value()
            self.config["camera"]["exposure"] = self.exposure_spin.value()
            self.config["camera"]["brightness"] = self.brightness_spin.value()
            self.config["camera"]["contrast"] = self.contrast_spin.value()

            # 系统设置
            if "system" not in self.config:
                self.config["system"] = {}

            self.config["system"]["auto_fullscreen"] = self.fullscreen_check.isChecked()
            self.config["system"]["enable_ai_diagnosis"] = self.ai_enabled_check.isChecked()
            self.config["system"]["show_api_key_reminder"] = self.api_reminder_check.isChecked()

            # 语音识别设置
            if "voice_recognition" not in self.config["system"]:
                self.config["system"]["voice_recognition"] = {}

            voice_config = self.config["system"]["voice_recognition"]
            voice_config["enabled"] = self.voice_enabled_check.isChecked()
            voice_config["auto_start"] = self.voice_autostart_check.isChecked()

            if "volcengine" not in voice_config:
                voice_config["volcengine"] = {}

            voice_config["volcengine"]["app_id"] = self.app_id_edit.text().strip()
            voice_config["volcengine"]["access_token"] = self.access_token_edit.text().strip()
            voice_config["volcengine"]["secret_key"] = self.secret_key_edit.text().strip()

            if "audio" not in voice_config:
                voice_config["audio"] = {}

            voice_config["audio"]["microphone_index"] = self.mic_index_spin.value()
            voice_config["audio"]["sample_rate"] = self.sample_rate_combo.currentData()
            voice_config["audio"]["chunk_size"] = self.chunk_size_spin.value()
            voice_config["audio"]["low_latency_mode"] = self.low_latency_check.isChecked()

            # 视力测试设置
            if "vision_test" not in self.config["system"]:
                self.config["system"]["vision_test"] = {}

            vision_config = self.config["system"]["vision_test"]
            vision_config["start_vision"] = self.start_vision_spin.value()
            vision_config["success_hold_time"] = self.hold_time_spin.value()
            vision_config["timeout_duration"] = self.timeout_test_spin.value()
            vision_config["stable_frames"] = self.stable_frames_spin.value()

            # 保存到文件
            with open("user_config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "保存成功", "设置已保存，重启程序后生效")
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {str(e)}")
            print(f"保存设置失败: {e}")
            import traceback
            traceback.print_exc()
