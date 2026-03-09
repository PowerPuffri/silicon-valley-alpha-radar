#!/bin/bash
# Silicon Valley Alpha Radar - 持续监控服务启动脚本

PROJECT_DIR="/Users/zhipu_glm/.openclaw/workspace/silicon-valley-alpha-radar"
INTERVAL_MINUTES=30

cd "$PROJECT_DIR"

echo "============================================================"
echo "🚀 Silicon Valley Alpha Radar - 持续监控服务"
echo "============================================================"
echo ""
echo "📋 配置信息:"
echo "   项目目录: $PROJECT_DIR"
echo "   检查间隔: $INTERVAL_MINUTES 分钟"
echo "   推送渠道: Telegram (Chat ID: 7974510481)"
echo ""

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 启动服务
echo "📡 启动持续监控服务..."
echo ""
echo "提示: 使用 Ctrl+C 停止服务"
echo ""

python src/services/unified_push_service.py --start --interval $INTERVAL_MINUTES

echo ""
echo "============================================================"
echo "🛑 服务已停止"
echo "============================================================"
