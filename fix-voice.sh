#!/bin/bash

# 语音识别修复脚本
echo "🔧 开始修复语音识别问题..."

# 1. 停止当前容器
echo "📦 停止当前容器..."
docker stop sga-cow 2>/dev/null || true
docker rm sga-cow 2>/dev/null || true

# 2. 重新构建镜像（包含ffmpeg）
echo "🏗️ 重新构建Docker镜像..."
docker build -t sga-cow:latest .

# 3. 启动新容器
echo "🚀 启动新容器..."
docker run -d \
  --name sga-cow \
  --restart unless-stopped \
  -p 8081:8081 \
  -p 9899:9899 \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/tmp:/app/tmp" \
  sga-cow:latest

# 4. 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 5. 检查容器状态
echo "📊 检查容器状态..."
docker ps | grep sga-cow

# 6. 显示日志
echo "📋 显示最新日志..."
docker logs --tail 20 sga-cow

echo "✅ 语音识别修复完成！"
echo ""
echo "🎯 修复内容："
echo "  ✅ 添加了ffmpeg支持"
echo "  ✅ 增强了Azure语音识别错误处理"
echo "  ✅ 启用了语音识别配置"
echo "  ✅ 修复了文件下载功能"
echo ""
echo "📝 现在可以测试："
echo "  1. 发送语音消息测试语音识别"
echo "  2. 发送#reset测试重置功能"
echo "  3. 请求Dify生成文档测试文件下载"
