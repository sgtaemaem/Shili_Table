"""
简化的设置对话框
避免复杂的UI导致的问题
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QSpinBox, QComboBox, QPushButton, QGroupBox,
                            QMessageBox, QTabWidget, QWidget, QFormLayout)
from PySide6.QtCore import Qt
import json
import os

class SimpleSettingsDialog(QDialog):
    """简化的设置对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("摄像头设置")
        self.setModal(True)
        self.resize(400, 300)
        
        # 加载当前配置
        self.load_config()
        
        # 创建界面
        self.setup_ui()
        
        # 连接信号
        self.setup_connections()
    
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
            "system": {
                "camera": {
                    "default_camera_index": 0,
                    "resolution": {"width": 640, "height": 480},
                    "fps": 30
                },
                "auto_fullscreen": True
            }
        }
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 摄像头设置组
        camera_group = QGroupBox("摄像头设置")
        camera_layout = QFormLayout(camera_group)
        
        # 摄像头索引
        self.camera_index_spin = QSpinBox()
        self.camera_index_spin.setRange(0, 10)
        self.camera_index_spin.setValue(
            self.config.get("system", {}).get("camera", {}).get("default_camera_index", 0)
        )
        camera_layout.addRow("摄像头设备:", self.camera_index_spin)
        
        # 分辨率选择
        self.resolution_combo = QComboBox()
        resolutions = [
            ("640x480", {"width": 640, "height": 480}),
            ("1280x720", {"width": 1280, "height": 720}),
            ("1920x1080", {"width": 1920, "height": 1080})
        ]
        
        current_res = self.config.get("system", {}).get("camera", {}).get("resolution", {"width": 640, "height": 480})
        current_index = 0
        
        for i, (text, res) in enumerate(resolutions):
            self.resolution_combo.addItem(text, res)
            if res["width"] == current_res["width"] and res["height"] == current_res["height"]:
                current_index = i
        
        self.resolution_combo.setCurrentIndex(current_index)
        camera_layout.addRow("分辨率:", self.resolution_combo)
        
        # 帧率
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(
            self.config.get("system", {}).get("camera", {}).get("fps", 30)
        )
        camera_layout.addRow("帧率:", self.fps_spin)
        
        layout.addWidget(camera_group)
        
        # 显示设置组
        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout(display_group)
        
        # 自动全屏
        self.fullscreen_combo = QComboBox()
        self.fullscreen_combo.addItem("启用自动全屏", True)
        self.fullscreen_combo.addItem("禁用自动全屏", False)
        
        auto_fullscreen = self.config.get("system", {}).get("auto_fullscreen", True)
        self.fullscreen_combo.setCurrentIndex(0 if auto_fullscreen else 1)
        display_layout.addRow("启动模式:", self.fullscreen_combo)
        
        layout.addWidget(display_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("测试摄像头")
        self.save_button = QPushButton("保存设置")
        self.cancel_button = QPushButton("取消")
        
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def setup_connections(self):
        """连接信号"""
        self.test_button.clicked.connect(self.test_camera)
        self.save_button.clicked.connect(self.save_settings)
        self.cancel_button.clicked.connect(self.reject)
    
    def test_camera(self):
        """测试摄像头"""
        try:
            import cv2
            camera_index = self.camera_index_spin.value()
            
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                QMessageBox.information(self, "测试结果", f"摄像头 {camera_index} 连接正常")
                cap.release()
            else:
                QMessageBox.warning(self, "测试结果", f"摄像头 {camera_index} 无法连接")
        except Exception as e:
            QMessageBox.critical(self, "测试失败", f"测试摄像头时出错: {str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 更新配置
            if "system" not in self.config:
                self.config["system"] = {}
            if "camera" not in self.config["system"]:
                self.config["system"]["camera"] = {}
            
            self.config["system"]["camera"]["default_camera_index"] = self.camera_index_spin.value()
            self.config["system"]["camera"]["resolution"] = self.resolution_combo.currentData()
            self.config["system"]["camera"]["fps"] = self.fps_spin.value()
            self.config["system"]["auto_fullscreen"] = self.fullscreen_combo.currentData()
            
            # 保存到文件
            with open("user_config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "保存成功", "设置已保存，重启程序后生效")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存设置时出错: {str(e)}")
