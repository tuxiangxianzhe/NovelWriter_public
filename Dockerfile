# ── Stage 1: 构建前端 ─────────────────────────────────────────────────────────
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

# ── Stage 2: Python 后端 + 前端产物 ──────────────────────────────────────────
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 替换 apt 为阿里云源
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn && \
    pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu --trusted-host download.pytorch.org && \
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 下载指定的 NLTK 资源
RUN python -c "import nltk; nltk.download('punkt_tab')"

# 复制项目文件
COPY . .

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# 创建数据目录和默认数据文件
RUN mkdir -p /app/output /app/styles /app/prompts
RUN echo '{"projects":{},"active_project":""}' > /app/projects.json
RUN echo '[]' > /app/xp_presets.json

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/api/health')" || exit 1

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "7860"]
