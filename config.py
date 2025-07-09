"""
配置文件
管理API密钥和系统设置
"""
import json
import os
import cv2

# 配置文件路径
CONFIG_FILE = "user_config.json"

# SiliconFlow API配置
SILICONFLOW_CONFIG = {
    # API密钥 - 请在这里填入您的真实API密钥
    "api_key": None,  # 例如: "sk-your-real-api-key-here"

    # 可选的模型列表（基于SiliconFlow平台）
    "models": {
        # DeepSeek系列 - 最新推理模型
        "🔥 DeepSeek-R1 (最新推理模型)": "deepseek-ai/DeepSeek-R1",
        "DeepSeek-R1-0528 (优化版本)": "deepseek-ai/DeepSeek-R1-0528",
        "🆕 DeepSeek-R1-0120 (最新版)": "Pro/deepseek-ai/DeepSeek-R1-0120",
        "💎 DeepSeek-V3 (Pro版本)": "Pro/deepseek-ai/DeepSeek-V3",

        # Qwen系列 - 通义千问
        "Qwen3-32B (高性能)": "Qwen/Qwen3-32B",
        "Qwen3-14B (平衡性能)": "Qwen/Qwen3-14B",
        "⭐ Qwen3-8B (推荐，速度快)": "Qwen/Qwen3-8B",
        "🆕 Qwen3-30B-A3B (大模型)": "Qwen/Qwen3-30B-A3B",
        "QwenLong-L1-32B (长文本)": "Tongyi-Zhiven/QwenLong-L1-32B",

        # GLM系列 - 智谱AI
        "🆕 GLM-Z1-32B (智谱AI最新)": "THUDM/GLM-Z1-32B-0414",
        "GLM-4-32B (智谱AI)": "THUDM/GLM-4-32B-0414"
    },

    # 默认使用的模型（推荐使用速度较快的模型）
    "default_model": "Qwen/Qwen3-8B",

    # API设置（优化后的参数）
    "timeout": 15,      # 减少超时时间
    "max_tokens": 500,  # 减少token数提高速度
    "temperature": 0.3, # 降低温度提高一致性
    "top_p": 0.8
}

# 摄像头配置
CAMERA_CONFIG = {
    # 默认摄像头索引
    "default_camera_index": 0,

    # 摄像头分辨率
    "resolution": {
        "width": 640,
        "height": 480
    },

    # 帧率
    "fps": 30,

    # 曝光设置（-1为自动曝光，负值越小曝光越高）
    "exposure": -4,  # 比自动曝光更亮，适合室内环境

    # 亮度设置（0-255）
    "brightness": 128,

    # 对比度设置（0-255）
    "contrast": 128,

    # 自动检测可用摄像头
    "auto_detect": True
}

# 系统设置
SYSTEM_CONFIG = {
    # 是否启用AI诊断
    "enable_ai_diagnosis": True,

    # 是否在没有API密钥时显示提示
    "show_api_key_reminder": True,

    # 显示设置
    "auto_fullscreen": True,   # 是否启动时自动进入全屏模式（默认启用）
    "adaptive_layout": True,   # 是否启用自适应布局

    # 视力测试设置
    "vision_test": {
        "start_vision": 5.0,
        "min_vision": 4.0,
        "max_vision": 5.3,
        "success_hold_time": 1.0,  # 成功需要保持的时间（秒）- 减少到1秒
        "timeout_duration": 8.0,   # 超时时间（秒）- 保持5秒
        "stable_frames": 2         # 手势稳定需要的帧数 - 减少到2帧
    },

    # 语音识别设置 - 火山引擎
    "voice_recognition": {
        "enabled": True,           # 是否启用语音控制
        "mode": "volcengine",      # 使用火山引擎
        "language": "zh-CN",       # 识别语言
        "timeout": 3,              # 命令超时时间（秒）
        "auto_start": True,        # 程序启动时自动启用

        # 火山引擎设置
        "volcengine": {
            "app_id": "",           # 火山引擎APP ID
            "access_token": "",     # 火山引擎Access Token
            "secret_key": "",       # 火山引擎Secret Key
            "enable_itn": True,     # 启用文本规范化
            "enable_punc": True,    # 启用标点符号
            "enable_ddc": False,    # 启用语义顺滑
            "end_window_size": 800, # 强制判停时间(ms)
            "force_to_speech_time": 1000  # 强制语音时间(ms)
        },

        # 音频设置
        "audio": {
            "microphone_index": -1, # 麦克风设备索引 (-1表示默认设备)
            "sample_rate": 16000,   # 采样率
            "chunk_size": 3200,     # 音频块大小 (200ms)
            "channels": 1           # 声道数
        }
    }
}

# 用户配置（从文件加载，可动态修改）
USER_CONFIG = {
    "siliconflow": SILICONFLOW_CONFIG.copy(),
    "camera": CAMERA_CONFIG.copy(),
    "system": SYSTEM_CONFIG.copy()
}

def load_user_config():
    """从文件加载用户配置"""
    global USER_CONFIG
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                # 合并配置，保留默认值
                USER_CONFIG["siliconflow"].update(saved_config.get("siliconflow", {}))
                USER_CONFIG["camera"].update(saved_config.get("camera", {}))
                USER_CONFIG["system"].update(saved_config.get("system", {}))
    except Exception as e:
        print(f"加载配置文件失败: {e}")

def save_user_config():
    """保存用户配置到文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(USER_CONFIG, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False

def get_siliconflow_config():
    """获取SiliconFlow配置"""
    return USER_CONFIG["siliconflow"].copy()

def get_camera_config():
    """获取摄像头配置"""
    return USER_CONFIG["camera"].copy()

def get_system_config():
    """获取系统配置"""
    return USER_CONFIG["system"].copy()

def update_siliconflow_config(api_key=None, model=None, timeout=None, max_tokens=None):
    """更新SiliconFlow配置"""
    if api_key is not None:
        USER_CONFIG["siliconflow"]["api_key"] = api_key
    if model is not None:
        USER_CONFIG["siliconflow"]["default_model"] = model
    if timeout is not None:
        USER_CONFIG["siliconflow"]["timeout"] = timeout
    if max_tokens is not None:
        USER_CONFIG["siliconflow"]["max_tokens"] = max_tokens
    return save_user_config()

def update_camera_config(camera_index=None, resolution=None, fps=None, exposure=None, brightness=None, contrast=None):
    """更新摄像头配置"""
    if camera_index is not None:
        USER_CONFIG["camera"]["default_camera_index"] = camera_index
    if resolution is not None:
        USER_CONFIG["camera"]["resolution"] = resolution
    if fps is not None:
        USER_CONFIG["camera"]["fps"] = fps
    if exposure is not None:
        USER_CONFIG["camera"]["exposure"] = exposure
    if brightness is not None:
        USER_CONFIG["camera"]["brightness"] = brightness
    if contrast is not None:
        USER_CONFIG["camera"]["contrast"] = contrast
    return save_user_config()

def update_system_config(new_config):
    """更新系统配置"""
    USER_CONFIG["system"].update(new_config)
    return save_user_config()

def update_volcengine_config(app_id=None, access_token=None, secret_key=None):
    """更新火山引擎语音识别配置"""
    voice_config = USER_CONFIG["system"].get("voice_recognition", {})
    if "volcengine" not in voice_config:
        voice_config["volcengine"] = {}

    if app_id is not None:
        voice_config["volcengine"]["app_id"] = app_id
    if access_token is not None:
        voice_config["volcengine"]["access_token"] = access_token
    if secret_key is not None:
        voice_config["volcengine"]["secret_key"] = secret_key

    USER_CONFIG["system"]["voice_recognition"] = voice_config
    return save_user_config()

def get_volcengine_config():
    """获取火山引擎配置"""
    voice_config = get_voice_config()
    return voice_config.get("volcengine", {})

def is_volcengine_configured():
    """检查火山引擎是否配置完整"""
    config = get_volcengine_config()
    return (bool(config.get("app_id")) and
            bool(config.get("access_token")) and
            bool(config.get("secret_key")))

def get_voice_config():
    """获取语音识别配置 - 火山引擎"""
    return USER_CONFIG["system"].get("voice_recognition", {
        "enabled": True,
        "mode": "volcengine",      # 使用火山引擎
        "language": "zh-CN",
        "timeout": 3,
        "auto_start": True,

        # 火山引擎设置
        "volcengine": {
            "app_id": "",
            "access_token": "",
            "secret_key": "",
            "enable_itn": True,
            "enable_punc": True,
            "enable_ddc": False,
            "end_window_size": 800,
            "force_to_speech_time": 1000
        },

        # 音频设置
        "audio": {
            "microphone_index": -1,
            "sample_rate": 16000,
            "chunk_size": 3200,
            "channels": 1
        }
    })

def is_api_key_configured():
    """检查是否配置了API密钥"""
    api_key = USER_CONFIG["siliconflow"].get("api_key")
    return api_key is not None and len(str(api_key)) > 10

def get_available_models():
    """获取可用的模型列表"""
    return USER_CONFIG["siliconflow"]["models"]

def detect_available_cameras():
    """检测可用的摄像头设备"""
    available_cameras = []

    # 检测最多10个摄像头索引
    for i in range(10):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # 尝试读取一帧来确认摄像头可用
                ret, frame = cap.read()
                if ret and frame is not None:
                    # 获取摄像头信息
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))

                    available_cameras.append({
                        "index": i,
                        "name": f"摄像头 {i}",
                        "resolution": f"{width}x{height}",
                        "fps": fps if fps > 0 else "未知"
                    })
                cap.release()
        except Exception:
            continue

    return available_cameras

def get_api_setup_instructions():
    """获取API设置说明"""
    return """
请按以下步骤配置SiliconFlow API：

1. 访问 https://siliconflow.cn/
2. 注册账号并登录
3. 在控制台中获取API密钥
4. 在程序设置中配置API密钥
5. 重启程序即可使用AI诊断功能

推荐模型：
- 🔥 DeepSeek-R1: 最新推理模型，质量最高
- ⭐ Qwen3-8B: 推荐，速度快，质量好
- 🆕 DeepSeek-R1-0120: 最新版本
- 💎 DeepSeek-V3: Pro版本，功能强大
- GLM-Z1-32B: 智谱AI最新模型
"""

# 初始化时加载用户配置
try:
    load_user_config()
except Exception as e:
    print(f"加载用户配置失败: {e}")
