#!/bin/bash

# UPJI视力测试系统开机自启动安装脚本

echo "🚀 开始安装UPJI视力测试系统开机自启动..."

# 获取当前用户和路径信息
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)
SERVICE_NAME="upji-vision-test"

echo "📋 安装信息:"
echo "   当前用户: $CURRENT_USER"
echo "   当前路径: $CURRENT_DIR"
echo "   服务名称: $SERVICE_NAME"

# 检查是否在正确的目录
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 当前目录没有找到main.py文件"
    echo "   请在upji目录下运行此脚本"
    exit 1
fi

# 检查Python3是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3命令"
    echo "   请先安装Python3"
    exit 1
fi

echo "✅ 环境检查通过"

# 方法1: 使用systemd用户服务（推荐）
echo ""
echo "🔧 方法1: 安装systemd用户服务（推荐）"

# 创建用户systemd目录
USER_SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$USER_SYSTEMD_DIR"

# 获取用户ID
USER_ID=$(id -u $CURRENT_USER)

# 创建服务文件
cat > "$USER_SYSTEMD_DIR/${SERVICE_NAME}.service" << EOF
[Unit]
Description=UPJI Vision Test Application
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
WorkingDirectory=$CURRENT_DIR
Environment=DISPLAY=:0
Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID
Environment=PULSE_RUNTIME_PATH=/run/user/$USER_ID/pulse
ExecStart=/usr/bin/python3 $CURRENT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

echo "✅ 服务文件已创建: $USER_SYSTEMD_DIR/${SERVICE_NAME}.service"

# 重新加载systemd配置
systemctl --user daemon-reload

# 启用服务
systemctl --user enable "${SERVICE_NAME}.service"

echo "✅ 用户服务已启用"

# 启用用户服务的开机自启动
sudo loginctl enable-linger "$CURRENT_USER"

echo "✅ 用户服务开机自启动已启用"

echo ""
echo "🔧 方法2: 创建桌面自启动文件（备用方案）"

# 创建桌面自启动目录
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

# 创建桌面自启动文件
cat > "$AUTOSTART_DIR/upji-vision-test.desktop" << EOF
[Desktop Entry]
Type=Application
Name=UPJI Vision Test
Comment=UPJI视力测试系统
Exec=python3 $CURRENT_DIR/main.py
Icon=applications-science
Terminal=false
StartupNotify=true
Categories=Science;Education;
X-GNOME-Autostart-enabled=true
EOF

echo "✅ 桌面自启动文件已创建: $AUTOSTART_DIR/upji-vision-test.desktop"

echo ""
echo "🎯 安装完成！"
echo ""
echo "📋 服务管理命令:"
echo "   查看服务状态: systemctl --user status ${SERVICE_NAME}"
echo "   启动服务:     systemctl --user start ${SERVICE_NAME}"
echo "   停止服务:     systemctl --user stop ${SERVICE_NAME}"
echo "   重启服务:     systemctl --user restart ${SERVICE_NAME}"
echo "   查看日志:     journalctl --user -u ${SERVICE_NAME} -f"
echo "   禁用服务:     systemctl --user disable ${SERVICE_NAME}"
echo ""
echo "📋 测试方法:"
echo "   1. 重启电脑测试开机自启动"
echo "   2. 或者手动启动服务: systemctl --user start ${SERVICE_NAME}"
echo ""
echo "⚠️  注意事项:"
echo "   - 确保系统启动时已登录到桌面环境"
echo "   - 如果遇到问题，可以查看日志进行调试"
echo "   - 程序需要摄像头和麦克风权限"
echo "   - 如果需要卸载，运行: systemctl --user disable ${SERVICE_NAME}"
echo ""
echo "🎉 UPJI视力测试系统开机自启动安装完成！"
