#!/bin/bash

# 电子视力表测试系统启动脚本
# 用于开机自动启动

# 设置工作目录
cd /home/cat/桌面/shilibiao/upji

# 等待桌面环境完全加载
sleep 10

# 设置显示环境变量
export DISPLAY=:0

# 设置其他必要的环境变量
export HOME=/home/cat
export USER=cat
export XDG_RUNTIME_DIR=/run/user/$(id -u cat)

# 记录启动日志
echo "$(date): 启动电子视力表测试系统" >> /var/log/vision_system.log

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "$(date): 错误 - 未找到Python3" >> /var/log/vision_system.log
    exit 1
fi

# 检查必要文件
if [ ! -f "main.py" ]; then
    echo "$(date): 错误 - 未找到main.py文件" >> /var/log/vision_system.log
    exit 1
fi

# 启动程序
echo "$(date): 正在启动程序..." >> /var/log/vision_system.log
python3 main.py >> /var/log/vision_system.log 2>&1

# 记录退出状态
echo "$(date): 程序退出，退出码: $?" >> /var/log/vision_system.log
