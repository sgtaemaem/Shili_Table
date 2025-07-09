# 电子视力系统 - 专业版

## 功能特性

- **实时手势识别**：使用MediaPipe检测食指指向方向
- **E字母显示**：动态调整大小和方向的E字母显示
- **AI智能诊断**：集成SiliconFlow API，提供专业视力分析
- **专业医疗界面**：采用医疗级蓝白配色方案，图标丰富
- **Qt Designer支持**：界面使用.ui文件，可视化编辑
- **实时方向显示**：摄像头画面中实时显示检测到的手指方向
- **配置管理**：完整的摄像头和API设置界面

## 快速开始

### 运行程序
```bash
cd upji
python main.py
```

### 使用步骤
1. 启动程序后，点击"启动摄像头"按钮
2. 摄像头画面中会显示手势识别状态
3. 用食指指向不同方向
4. 界面下方会实时显示当前检测到的方向

## 界面编辑

使用Qt Designer编辑界面：
1. 打开 `vision_ui.ui` 文件
2. 修改界面布局、颜色、控件等
3. 保存后重新运行程序查看效果

## 核心文件

- `main.py` - 主程序入口
- `run.py` - 启动脚本（自动检查依赖）
- `main_with_ui.py` - 主窗口实现（美化版本）
- `camera_with_gesture.py` - 摄像头和手势识别
- `vision_test_ui.ui` - Qt Designer界面文件
- `shou.py` - 手势识别算法
- `vision_calculator.py` - 视力计算
- `ai_diagnosis.py` - AI诊断（SiliconFlow集成）
- `communication.py` - 通信模块
- `config.py` - 配置管理
- `settings_dialog.py` - 设置对话框
- `resources_manager.py` - 资源管理器

## 资源文件

- `resources/icons/` - 医疗主题图标
- `resources/images/` - 背景图片和素材
- `resources/styles/` - 医疗主题样式表

## 系统要求

- Python 3.8+
- PyQt6
- OpenCV
- MediaPipe
- NumPy

## 安装依赖

```bash
pip install -r requirements.txt
```

## 手势识别说明

- 需要良好的光线条件
- 与摄像头保持适当距离（40-200cm）
- 用食指明确指向目标方向
- 系统会检测连续5帧相同方向才确认稳定
