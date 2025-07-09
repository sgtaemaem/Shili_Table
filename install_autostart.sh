#!/bin/bash

# 电子视力表测试系统开机自启动安装脚本

echo "🚀 正在配置电子视力表测试系统开机自启动..."
echo ""

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  请不要使用root用户运行此脚本"
    echo "   请使用普通用户账户运行: ./install_autostart.sh"
    exit 1
fi

# 获取当前用户和路径信息
CURRENT_USER=$(whoami)
CURRENT_DIR=$(pwd)
HOME_DIR=$HOME

echo "📋 配置信息："
echo "   用户: $CURRENT_USER"
echo "   程序路径: $CURRENT_DIR"
echo "   用户主目录: $HOME_DIR"
echo ""

# 检查必要文件
if [ ! -f "main.py" ]; then
    echo "❌ 错误：未找到main.py文件"
    echo "   请确保在正确的目录中运行此脚本"
    exit 1
fi

if [ ! -f "start_vision_system.sh" ]; then
    echo "❌ 错误：未找到start_vision_system.sh文件"
    echo "   请先运行脚本生成启动文件"
    exit 1
fi

# 更新启动脚本中的路径
echo "🔧 更新启动脚本路径..."
sed -i "s|/home/cat/桌面/shilibiao/upji|$CURRENT_DIR|g" start_vision_system.sh
sed -i "s|/home/cat|$HOME_DIR|g" start_vision_system.sh
sed -i "s|USER=cat|USER=$CURRENT_USER|g" start_vision_system.sh
sed -i "s|id -u cat|id -u $CURRENT_USER|g" start_vision_system.sh

# 更新服务文件中的路径和用户
echo "🔧 更新服务文件配置..."
sed -i "s|User=cat|User=$CURRENT_USER|g" vision-system.service
sed -i "s|Group=cat|Group=$CURRENT_USER|g" vision-system.service
sed -i "s|/home/cat/桌面/shilibiao/upji|$CURRENT_DIR|g" vision-system.service
sed -i "s|/home/cat|$HOME_DIR|g" vision-system.service

# 创建用户systemd目录
SYSTEMD_USER_DIR="$HOME_DIR/.config/systemd/user"
mkdir -p "$SYSTEMD_USER_DIR"

# 复制服务文件
echo "📁 安装服务文件..."
cp vision-system.service "$SYSTEMD_USER_DIR/"

# 重新加载systemd配置
echo "🔄 重新加载systemd配置..."
systemctl --user daemon-reload

# 启用服务
echo "✅ 启用开机自启动..."
systemctl --user enable vision-system.service

# 创建日志文件目录
echo "📝 创建日志目录..."
sudo mkdir -p /var/log
sudo touch /var/log/vision_system.log
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/vision_system.log

echo ""
echo "🎉 开机自启动配置完成！"
echo ""
echo "📋 管理命令："
echo "   查看服务状态: systemctl --user status vision-system"
echo "   启动服务:     systemctl --user start vision-system"
echo "   停止服务:     systemctl --user stop vision-system"
echo "   禁用自启动:   systemctl --user disable vision-system"
echo "   查看日志:     tail -f /var/log/vision_system.log"
echo ""
echo "💡 提示："
echo "   - 系统重启后程序将自动启动"
echo "   - 程序会在桌面环境加载完成后启动"
echo "   - 如果启动失败，会自动重试"
echo "   - 所有日志记录在 /var/log/vision_system.log"
echo ""
echo "🔧 如需测试，可以运行: systemctl --user start vision-system"
