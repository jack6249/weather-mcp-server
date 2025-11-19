# Multi-stage build for weather-mcp-server (Stdio 模式)
FROM python:3.12-slim-bookworm as base

# 设置工作目录
WORKDIR /app

# 精简系统依赖（无需 curl，因无网络端口检查）
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*  # 清理缓存减小镜像体积

# 复制依赖文件
COPY pyproject.toml requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY server.py ./

# 环境变量：确保 Python 输出实时刷新（适合日志查看）
ENV PYTHONUNBUFFERED=1

# 运行 Stdio 模式的 MCP 服务器（无端口监听）
CMD ["python", "server.py"]