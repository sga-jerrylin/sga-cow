# SGA-CoW Docker部署指南

本文档介绍如何使用Docker部署SGA-CoW项目，实现快速、便捷的容器化部署。

## 🚀 快速开始

### 前提条件

1. **安装Docker**: 从 [Docker官网](https://www.docker.com/) 下载并安装Docker
2. **安装Docker Compose**: 通常随Docker一起安装
3. **验证安装**: 执行以下命令验证安装成功
   ```bash
   docker --version
   docker-compose --version  # 或 docker compose version
   ```

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/sga-jerrylin/sga-cow.git
cd sga-cow

# 2. 复制环境变量配置文件
cp .env.example .env

# 3. 编辑配置文件（重要！）
vim .env  # 或使用其他编辑器

# 4. 启动服务
docker-compose up -d
```

## 📋 配置说明

### 环境变量配置

编辑 `.env` 文件，填入以下必要配置：

```bash
# Dify配置 (必填)
DIFY_API_KEY=your-dify-api-key-here
DIFY_API_BASE=https://api.dify.ai/v1
DIFY_APP_TYPE=chatbot

# 企业微信配置 (必填)
WECHATCOM_CORP_ID=your-corp-id-here
WECHATCOMAPP_SECRET=your-app-secret-here
WECHATCOMAPP_AGENT_ID=your-agent-id-here
WECHATCOMAPP_TOKEN=your-token-here
WECHATCOMAPP_AES_KEY=your-aes-key-here
```

### 性能优化配置

```bash
# 并发和性能配置
DIFY_MAX_WORKERS=10          # 并发线程数
DIFY_MAX_RETRIES=3           # 重试次数
DIFY_TIMEOUT=30              # 超时时间(秒)
DIFY_RETRY_DELAY=1.0         # 重试延迟(秒)
```

## 🔧 Docker Compose配置

### 基础配置

`docker-compose.yml` 文件包含以下服务配置：

- **端口映射**: 9899:9899 (Web界面)
- **数据卷**: 配置文件、日志、临时文件
- **环境变量**: 从 `.env` 文件加载
- **健康检查**: 自动监控服务状态
- **重启策略**: 异常时自动重启

### 自定义配置

如需自定义配置，可以修改 `docker-compose.yml`:

```yaml
services:
  sga-cow:
    ports:
      - "8080:9899"  # 修改外部端口
    environment:
      - DEBUG=true   # 启用调试模式
    volumes:
      - ./custom-config.json:/app/config.json:ro  # 使用自定义配置
```

## 🛠️ 管理命令

### 使用Docker Compose

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

### 使用部署脚本 (Linux/Mac)

```bash
# 启动服务
./docker-deploy.sh start

# 停止服务
./docker-deploy.sh stop

# 重启服务
./docker-deploy.sh restart

# 查看日志
./docker-deploy.sh logs

# 查看状态
./docker-deploy.sh status

# 进入容器
./docker-deploy.sh enter
```

### Windows PowerShell

```powershell
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f sga-cow

# 进入容器
docker exec -it sga-cow /bin/bash

# 停止服务
docker-compose down
```

## 📊 监控和维护

### 健康检查

容器内置健康检查，可通过以下方式查看：

```bash
# 查看容器健康状态
docker ps

# 查看详细健康检查信息
docker inspect sga-cow | grep -A 10 Health
```

### 日志管理

```bash
# 查看实时日志
docker-compose logs -f sga-cow

# 查看最近100行日志
docker-compose logs --tail 100 sga-cow

# 查看特定时间段日志
docker-compose logs --since "2025-01-19T10:00:00" sga-cow
```

### 资源监控

```bash
# 查看容器资源使用
docker stats sga-cow

# 查看容器详细信息
docker inspect sga-cow
```

## 🔄 更新和升级

### 更新代码

```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码
git pull origin master

# 3. 重新构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d
```

### 版本管理

```bash
# 使用特定版本
docker-compose down
docker pull sga-cow:v2.0.0
docker-compose up -d

# 回滚到上一版本
docker-compose down
docker tag sga-cow:v2.0.0 sga-cow:latest
docker-compose up -d
```

## 🐛 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 查看启动日志
   docker-compose logs sga-cow
   
   # 检查配置文件
   docker-compose config
   ```

2. **端口冲突**
   ```bash
   # 修改docker-compose.yml中的端口映射
   ports:
     - "8080:9899"  # 改为其他端口
   ```

3. **配置文件问题**
   ```bash
   # 验证.env文件格式
   cat .env | grep -v "^#" | grep -v "^$"
   
   # 重新生成配置
   cp .env.example .env
   ```

4. **权限问题**
   ```bash
   # 修复文件权限
   sudo chown -R 1000:1000 logs tmp
   ```

### 调试模式

启用调试模式获取更多信息：

```bash
# 在.env文件中设置
DEBUG=true

# 重启服务
docker-compose restart
```

## 📈 性能优化

### 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  sga-cow:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### 网络优化

```yaml
networks:
  sga-cow-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🔒 安全配置

### 环境变量安全

```bash
# 设置.env文件权限
chmod 600 .env

# 使用Docker secrets (生产环境)
echo "your-api-key" | docker secret create dify_api_key -
```

### 网络安全

```yaml
# 仅暴露必要端口
ports:
  - "127.0.0.1:9899:9899"  # 仅本地访问

# 使用自定义网络
networks:
  - internal
```

## 📝 备份和恢复

### 数据备份

```bash
# 备份配置和日志
tar -czf sga-cow-backup-$(date +%Y%m%d).tar.gz .env logs/

# 备份Docker镜像
docker save sga-cow:latest | gzip > sga-cow-image.tar.gz
```

### 数据恢复

```bash
# 恢复配置
tar -xzf sga-cow-backup-20250119.tar.gz

# 恢复Docker镜像
docker load < sga-cow-image.tar.gz
```

---

如有问题，请查看 [GitHub Issues](https://github.com/sga-jerrylin/sga-cow/issues) 或联系技术支持。
