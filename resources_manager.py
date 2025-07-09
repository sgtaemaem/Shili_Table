"""
资源管理模块
管理应用程序的图标、图片和样式资源
"""
import os
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize

class ResourceManager:
    """资源管理器"""
    
    def __init__(self):
        # 获取资源文件夹路径
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.resources_path = os.path.join(self.base_path, "resources")
        self.icons_path = os.path.join(self.resources_path, "icons")
        self.images_path = os.path.join(self.resources_path, "images")
        self.styles_path = os.path.join(self.resources_path, "styles")
        
        # 确保资源文件夹存在
        self._ensure_directories()
        
        # 预加载常用图标
        self._preload_icons()
    
    def _ensure_directories(self):
        """确保资源目录存在"""
        for path in [self.resources_path, self.icons_path, self.images_path, self.styles_path]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
    
    def _preload_icons(self):
        """预加载常用图标"""
        self.icons = {}
        icon_files = {
            'eye': 'eye.svg',
            'camera': 'camera.svg',
            'settings': 'settings.svg',
            'start': 'start.svg',
            'stop': 'stop.svg',
            'ai': 'ai.svg',
            'medical': 'medical.svg',
            'app': 'app_icon.svg'
        }
        
        for name, filename in icon_files.items():
            icon_path = os.path.join(self.icons_path, filename)
            if os.path.exists(icon_path):
                self.icons[name] = QIcon(icon_path)
            else:
                # 如果文件不存在，创建一个空图标
                self.icons[name] = QIcon()
    
    def get_icon(self, name: str) -> QIcon:
        """
        获取图标
        
        Args:
            name: 图标名称 ('eye', 'camera', 'settings', 'start', 'stop', 'ai', 'medical', 'app')
        
        Returns:
            QIcon: 图标对象
        """
        return self.icons.get(name, QIcon())
    
    def get_icon_path(self, filename: str) -> str:
        """
        获取图标文件路径
        
        Args:
            filename: 图标文件名
        
        Returns:
            str: 完整的文件路径
        """
        return os.path.join(self.icons_path, filename)
    
    def get_image_path(self, filename: str) -> str:
        """
        获取图片文件路径
        
        Args:
            filename: 图片文件名
        
        Returns:
            str: 完整的文件路径
        """
        return os.path.join(self.images_path, filename)
    
    def get_pixmap(self, filename: str, size: tuple = None) -> QPixmap:
        """
        获取图片像素图
        
        Args:
            filename: 图片文件名
            size: 可选的尺寸 (width, height)
        
        Returns:
            QPixmap: 像素图对象
        """
        image_path = self.get_image_path(filename)
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if size:
                pixmap = pixmap.scaled(size[0], size[1], Qt.AspectRatioMode.KeepAspectRatio, 
                                     Qt.TransformationMode.SmoothTransformation)
            return pixmap
        return QPixmap()
    
    def load_stylesheet(self, filename: str = "medical_theme.qss") -> str:
        """
        加载样式表
        
        Args:
            filename: 样式表文件名
        
        Returns:
            str: 样式表内容
        """
        style_path = os.path.join(self.styles_path, filename)
        if os.path.exists(style_path):
            try:
                with open(style_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                print(f"加载样式表失败: {e}")
                return ""
        return ""
    
    def apply_button_icon(self, button, icon_name: str, size: tuple = (24, 24)):
        """
        为按钮应用图标
        
        Args:
            button: QPushButton对象
            icon_name: 图标名称
            size: 图标尺寸
        """
        icon = self.get_icon(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
            button.setIconSize(QSize(size[0], size[1]))
    
    def get_available_icons(self) -> list:
        """
        获取可用的图标列表
        
        Returns:
            list: 可用图标名称列表
        """
        return list(self.icons.keys())
    
    def icon_exists(self, name: str) -> bool:
        """
        检查图标是否存在
        
        Args:
            name: 图标名称
        
        Returns:
            bool: 图标是否存在
        """
        return name in self.icons and not self.icons[name].isNull()

# 全局资源管理器实例
resource_manager = ResourceManager()
