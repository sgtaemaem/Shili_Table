"""
集成手势识别的摄像头处理模块 - 优化版本
实时显示手指方向
"""
import cv2
import numpy as np
import mediapipe as mp
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage, QPixmap

from shou import get_finger_direction, is_index_finger_extended

class CameraWithGestureHandler(QThread):
    """集成手势识别的摄像头处理器"""
    
    # 信号定义
    frame_ready = Signal(np.ndarray)
    distance_updated = Signal(float)
    finger_direction_detected = Signal(str)  # 新增：手指方向信号
    gesture_status_changed = Signal(str)     # 新增：手势状态信号
    
    def __init__(self, camera_index=0, resolution=None, fps=30, exposure=100, brightness=128, contrast=128):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.running = False
        self.current_distance = 100.0

        # 摄像头参数
        self.resolution = resolution or {"width": 640, "height": 480}
        self.fps = fps
        self.exposure = exposure
        self.brightness = brightness
        self.contrast = contrast

        # 预初始化MediaPipe组件
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.hands = None

        # 手势识别状态
        self.current_direction = "None"
        self.finger_extended = False

        # 优化：减少稳定性检测的帧数要求
        self.direction_history = []
        self.direction_stable_count = 0
        self.required_stable_frames = 3  # 减少到3帧提高响应速度

        # 预定义常用颜色，避免重复创建
        self.colors = {
            'green': (0, 255, 0),
            'red': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
            'white': (255, 255, 255)
        }
        
    def start_camera(self):
        """启动摄像头"""
        try:
            # 初始化MediaPipe
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.75,
                min_tracking_confidence=0.75
            )

            # 初始化摄像头
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False

            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution["width"])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution["height"])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # 设置曝光和图像质量参数
            self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness / 255.0)  # 归一化到0-1
            self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast / 255.0)      # 归一化到0-1

            self.running = True
            self.start()
            return True

        except Exception:
            return False
    
    def stop_camera(self):
        """停止摄像头"""
        self.running = False
        if self.cap:
            self.cap.release()
        if self.hands:
            self.hands.close()
        self.wait()
    
    def run(self):
        """摄像头线程主循环"""
        retry_count = 0
        max_retries = 5
        
        while self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None and frame.size > 0:
                    # 处理帧（包括手势识别）
                    processed_frame = self.process_frame_with_gesture(frame)
                    
                    # 发送处理后的帧
                    self.frame_ready.emit(processed_frame)
                    retry_count = 0  # 重置重试计数
                else:
                    retry_count += 1

                # 如果连续失败太多次，尝试重新初始化摄像头
                if retry_count >= max_retries:
                    self.reinitialize_camera()
                    retry_count = 0

            except Exception:
                retry_count += 1
                if retry_count >= max_retries:
                    break
            
            self.msleep(33)  # 约30fps
    
    def process_frame_with_gesture(self, frame):
        """处理帧并进行手势识别"""
        # 水平翻转画面（镜像效果）
        frame = cv2.flip(frame, 1)
        
        # 转换颜色空间用于MediaPipe处理
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 进行手势识别
        results = self.hands.process(frame_rgb)
        
        # 转换回BGR用于显示
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        
        # 处理手势识别结果
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # 绘制手部关键点
                self.mp_drawing.draw_landmarks(
                    frame_bgr, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # 提取手部关键点坐标
                hand_local = []
                for i in range(21):
                    x = hand_landmarks.landmark[i].x * frame_bgr.shape[1]
                    y = hand_landmarks.landmark[i].y * frame_bgr.shape[0]
                    hand_local.append((x, y))
                
                # 进行手势分析
                self.analyze_gesture(hand_local, frame_bgr)
        else:
            # 没有检测到手部
            self.finger_extended = False
            self.current_direction = "None"
            self.direction_history.clear()
            self.direction_stable_count = 0
            
            # 显示提示信息
            cv2.putText(frame_bgr, "Show your hand to camera", (50, 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 发送状态信号
            self.gesture_status_changed.emit("No hand detected")
        
        # 添加距离信息和其他信息
        frame_with_info = self.add_info_to_frame(frame_bgr)
        
        return frame_with_info
    
    def analyze_gesture(self, hand_landmarks, frame):
        """分析手势"""
        try:
            # 检测食指是否伸出
            finger_extended = is_index_finger_extended(hand_landmarks)
            self.finger_extended = finger_extended
            
            if finger_extended:
                # 获取食指指向方向
                direction = get_finger_direction(hand_landmarks)
                
                # 方向稳定性检测
                self.direction_history.append(direction)
                if len(self.direction_history) > self.required_stable_frames:
                    self.direction_history.pop(0)
                
                # 检查方向是否稳定
                if len(self.direction_history) >= self.required_stable_frames:
                    if all(d == direction for d in self.direction_history):
                        # 方向稳定
                        if self.current_direction != direction:
                            self.current_direction = direction
                            # 只在方向改变时发送信号
                            self.finger_direction_detected.emit(direction)

                        self.direction_stable_count += 1
                    else:
                        # 方向不稳定，重置
                        if self.current_direction != "None":
                            self.current_direction = "None"
                            self.finger_direction_detected.emit("None")
                        self.direction_stable_count = 0
                
                # 在画面上显示方向信息
                display_text = f"Direction: {direction}"
                confidence_text = f"Stable: {len(self.direction_history)}/{self.required_stable_frames}"
                
                cv2.putText(frame, display_text, (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                cv2.putText(frame, confidence_text, (50, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                # 发送状态信号
                status = f"Pointing {direction} (Stable: {self.direction_stable_count})"
                self.gesture_status_changed.emit(status)
                
            else:
                # 食指未伸出
                self.current_direction = "None"
                self.direction_history.clear()
                self.direction_stable_count = 0
                
                cv2.putText(frame, "Point with index finger", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                
                self.gesture_status_changed.emit("Index finger not extended")
                
        except Exception as e:
            self.gesture_status_changed.emit(f"Gesture analysis error: {e}")
    
    def add_info_to_frame(self, frame):
        """优化版本：在画面上添加信息"""
        # 预计算常用值
        height, width = frame.shape[:2]

        # 使用预定义颜色
        distance_color = self.colors['green'] if 40 <= self.current_distance <= 200 else self.colors['red']
        status_text = "Distance OK" if 40 <= self.current_distance <= 200 else "Distance Error"

        # 批量添加文本信息
        texts = [
            (f"Distance: {self.current_distance:.1f} cm", (10, height - 80), 0.8, self.colors['green']),
            (status_text, (10, height - 50), 0.6, distance_color),
            (f"Current: {self.current_direction}", (10, height - 20), 0.6, self.colors['magenta'])
        ]

        for text, pos, scale, color in texts:
            cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2)

        # 添加测试区域指示框
        center_x, center_y = width // 2, height // 2
        box_size = 100

        cv2.rectangle(frame,
                     (center_x - box_size, center_y - box_size),
                     (center_x + box_size, center_y + box_size),
                     self.colors['yellow'], 2)

        cv2.putText(frame, "Test Area",
                   (center_x - 50, center_y + box_size + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors['yellow'], 1)

        return frame
    
    def reinitialize_camera(self):
        """重新初始化摄像头"""
        try:
            if self.cap:
                self.cap.release()
            
            # 等待一下再重新初始化
            self.msleep(1000)
            
            self.cap = cv2.VideoCapture(self.camera_index)
            if self.cap.isOpened():
                # 重新设置摄像头参数
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution["width"])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution["height"])
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)

                # 重新设置曝光和图像质量参数
                self.cap.set(cv2.CAP_PROP_EXPOSURE, self.exposure)
                self.cap.set(cv2.CAP_PROP_BRIGHTNESS, self.brightness / 255.0)
                self.cap.set(cv2.CAP_PROP_CONTRAST, self.contrast / 255.0)
                return True
            else:
                return False
        except Exception:
            return False
    
    def update_distance(self, distance):
        """更新距离信息"""
        self.current_distance = distance
        self.distance_updated.emit(distance)
    
    def get_current_direction(self):
        """获取当前检测到的方向"""
        return self.current_direction
    
    def is_finger_extended(self):
        """检查食指是否伸出"""
        return self.finger_extended
    
    def numpy_to_qimage(self, frame):
        """将numpy数组转换为QImage"""
        height, width, _ = frame.shape
        bytes_per_line = 3 * width
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_image = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        return q_image
    
    def numpy_to_qpixmap(self, frame):
        """将numpy数组转换为QPixmap"""
        q_image = self.numpy_to_qimage(frame)
        return QPixmap.fromImage(q_image)
