# SGA-CoW Docker镜像 - 企业微信+Dify深度集成优化版
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    zlib1g-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制requirements文件
COPY requirements.txt requirements-optional.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-optional.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs tmp

# 创建非root用户
RUN if ! id -u appuser >/dev/null 2>&1; then \
      if getent passwd 1000 >/dev/null 2>&1; then \
        useradd -m appuser; \
      else \
        useradd -m -u 1000 appuser; \
      fi; \
    fi && \
    chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:9899/health', timeout=5)" || exit 1

# 暴露端口
EXPOSE 9899

# 启动命令
CMD ["python", "app.py"]
