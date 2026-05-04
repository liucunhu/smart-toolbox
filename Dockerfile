# --- 第一阶段：基础环境准备 ---
FROM python:3.10-slim AS builder

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 配置阿里云 Debian 镜像源 (加速 apt-get)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources || \
    (echo "deb http://mirrors.aliyun.com/debian/ trixie main" > /etc/apt/sources.list && \
     echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main" >> /etc/apt/sources.list && \
     echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main" >> /etc/apt/sources.list)

# 安装系统依赖 (适配 Debian Trixie)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libpango-1.0-0 \
    libcairo2 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包 (使用阿里云镜像加速)
COPY requirements_core.txt .
RUN pip install --user \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    --default-timeout=100 \
    --retries=5 \
    -r requirements_core.txt

# 【关键修复】将用户安装目录加入 PATH，确保能找到 playwright 命令
# 同时指定浏览器安装路径，方便多阶段构建复制
ENV PATH=/root/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# 安装 Playwright 浏览器驱动 (安装在指定目录下)
RUN playwright install chromium
RUN playwright install-deps

# --- 第二阶段：最终运行环境 ---
FROM python:3.10-slim AS production

WORKDIR /app

# 创建非根用户以增强安全性
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# 从 builder 阶段复制已安装的 Python 包和 Playwright 浏览器
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /root/.cache/ms-playwright /ms-playwright

# 确保路径生效
ENV PATH=/home/appuser/.local/bin:$PATH \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 复制项目代码
COPY . .

# 更改文件所有权
RUN chown -R appuser:appuser /app

# 切换到非根用户
USER appuser

EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
