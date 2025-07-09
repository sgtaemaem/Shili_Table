"""
通信模块
处理与下位机的串口通信
"""
import serial
import json
import threading
import time
from PySide6.QtCore import QObject, Signal

class SerialCommunication(QObject):
    # 信号定义
    finger_direction_received = Signal(str)  # 手指方向信号
    distance_received = Signal(float)        # 距离信号
    connection_status_changed = Signal(bool) # 连接状态信号
    
    def __init__(self, port='COM3', baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        
        # 模拟数据（用于测试）
        self.mock_mode = True
        self.mock_distance = 100.0
        self.mock_direction = "Right"
        
    def connect_device(self):
        """连接串口"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.running = True
            self.read_thread = threading.Thread(target=self.read_data)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            self.connection_status_changed.emit(True)
            print(f"串口连接成功: {self.port}")
            return True
            
        except Exception as e:
            print(f"串口连接失败: {e}")
            self.mock_mode = True
            self.start_mock_data()
            return False
    
    def disconnect(self):
        """断开串口连接"""
        self.running = False
        if self.serial_conn:
            self.serial_conn.close()
        if self.read_thread:
            self.read_thread.join()
        self.connection_status_changed.emit(False)
    
    def read_data(self):
        """读取串口数据"""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    line = self.serial_conn.readline().decode('utf-8').strip()
                    if line:
                        self.parse_data(line)
                time.sleep(0.01)  # 10ms延迟
            except Exception as e:
                print(f"读取串口数据错误: {e}")
                break
    
    def parse_data(self, data):
        """解析接收到的数据"""
        try:
            # 假设数据格式为JSON: {"type": "direction", "value": "Right"}
            parsed_data = json.loads(data)
            
            if parsed_data.get("type") == "direction":
                direction = parsed_data.get("value")
                if direction in ["Up", "Down", "Left", "Right"]:
                    self.finger_direction_received.emit(direction)
            
            elif parsed_data.get("type") == "distance":
                distance = float(parsed_data.get("value", 0))
                if 0 < distance < 1000:  # 合理的距离范围
                    self.distance_received.emit(distance)
                    
        except json.JSONDecodeError:
            # 如果不是JSON格式，尝试简单解析
            if data.startswith("DIR:"):
                direction = data[4:].strip()
                if direction in ["Up", "Down", "Left", "Right"]:
                    self.finger_direction_received.emit(direction)
            elif data.startswith("DIST:"):
                try:
                    distance = float(data[5:].strip())
                    self.distance_received.emit(distance)
                except ValueError:
                    pass
        except Exception as e:
            print(f"解析数据错误: {e}")
    
    def send_command(self, command):
        """发送命令到下位机"""
        if self.serial_conn:
            try:
                self.serial_conn.write(f"{command}\n".encode('utf-8'))
                return True
            except Exception as e:
                print(f"发送命令失败: {e}")
                return False
        return False
    
    def start_mock_data(self):
        """启动模拟数据（用于测试）"""
        if not self.mock_mode:
            return
            
        def mock_data_thread():
            import random
            directions = ["Up", "Down", "Left", "Right"]
            
            while self.running:
                # 模拟距离变化
                distance_change = random.uniform(-2, 2)
                self.mock_distance = max(40, min(200, self.mock_distance + distance_change))
                self.distance_received.emit(self.mock_distance)
                
                # 模拟方向变化（较少频率）
                if random.random() < 0.1:  # 10%概率改变方向
                    self.mock_direction = random.choice(directions)
                
                self.finger_direction_received.emit(self.mock_direction)
                
                time.sleep(0.1)  # 100ms更新一次
        
        self.running = True
        mock_thread = threading.Thread(target=mock_data_thread)
        mock_thread.daemon = True
        mock_thread.start()
        
        self.connection_status_changed.emit(True)
        print("启动模拟数据模式")


class MockCommunication(QObject):
    """模拟通信类"""

    finger_direction_received = Signal(str)
    distance_received = Signal(float)
    connection_status_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.running = False
        self.distance = 100.0

    def connect_device(self):
        """模拟连接"""
        self.running = True
        self.connection_status_changed.emit(True)
        return True

    def disconnect(self):
        """模拟断开"""
        self.running = False
        self.connection_status_changed.emit(False)

    def send_command(self, command):
        """模拟发送命令"""
        return True
