"""
电子视力表系统主程序
"""
import sys
import numpy
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_with_ui import VisionMainWindow

def main():
    """主函数"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("电子视力系统")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("Vision System")

        main_window = VisionMainWindow()
        # 窗口已在 VisionMainWindow.__init__ 中设置为最大化
        main_window.show()

        sys.exit(app.exec())

    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
