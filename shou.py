import cv2
import mediapipe as mp
import math

def get_finger_direction(hand_landmarks):
    '''
        检测食指指向方向
        使用食指关键点计算方向向量
    '''
    # 食指关键点索引：5(MCP), 6(PIP), 7(DIP), 8(TIP)
    # 使用MCP到TIP的向量来确定方向
    mcp = hand_landmarks[5]  # 食指根部
    tip = hand_landmarks[8]  # 食指尖端

    # 计算方向向量
    direction_x = tip[0] - mcp[0]
    direction_y = tip[1] - mcp[1]

    # 计算角度（以水平向右为0度，逆时针为正）
    angle = math.degrees(math.atan2(-direction_y, direction_x))  # 注意y轴翻转

    # 根据角度判断方向
    if -45 <= angle <= 45:
        return "Right"
    elif 45 < angle <= 135:
        return "Up"
    elif 135 < angle <= 180 or -180 <= angle < -135:
        return "Left"
    else:  # -135 <= angle < -45
        return "Down"

def is_index_finger_extended(hand_landmarks):
    '''
        简单检测食指是否伸出
        通过比较食指尖端和中指关节的位置来判断
    '''
    # 食指尖端
    index_tip = hand_landmarks[8]
    # 中指第二关节
    middle_pip = hand_landmarks[10]
    # 手腕
    wrist = hand_landmarks[0]

    # 计算食指尖端到手腕的距离
    index_distance = math.sqrt((index_tip[0] - wrist[0])**2 + (index_tip[1] - wrist[1])**2)
    # 计算中指关节到手腕的距离
    middle_distance = math.sqrt((middle_pip[0] - wrist[0])**2 + (middle_pip[1] - wrist[1])**2)

    # 如果食指尖端距离手腕比中指关节远，认为食指伸出
    return index_distance > middle_distance * 0.9

def detect():
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75)
    cap = cv2.VideoCapture(0)
    while True:
        ret,frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame= cv2.flip(frame,1)
        results = hands.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                hand_local = []
                for i in range(21):
                    x = hand_landmarks.landmark[i].x*frame.shape[1]
                    y = hand_landmarks.landmark[i].y*frame.shape[0]
                    hand_local.append((x,y))
                if hand_local:
                    # 检测食指是否伸出
                    if is_index_finger_extended(hand_local):
                        # 获取食指指向方向
                        direction = get_finger_direction(hand_local)
                        display_text = f"Direction: {direction}"
                        cv2.putText(frame, display_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
                    else:
                        # 显示提示信息
                        cv2.putText(frame, "Point with index finger", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('MediaPipe Hands', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    cap.release()

if __name__ == '__main__':
    detect()
