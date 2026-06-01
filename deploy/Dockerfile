# ============================================================
# 发票管理系统 - Docker 多阶段构建
# Stage 1: 前端构建 (Node.js)
# Stage 2: 后端运行 (Python 3.13 + Tesseract OCR + Poppler)
# ============================================================

# -------------------- Stage 1: 前端构建 --------------------
FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package.json frontend/package-lock.json ./

# 安装依赖（使用 npm ci 更快更稳）
RUN npm ci --registry=https://registry.npmmirror.com

# 复制前端源码
COPY frontend/ ./

# 构建生产版本
RUN npm run build


# -------------------- Stage 2: 后端运行 --------------------
FROM python:3.13-slim

LABEL maintainer="Adam Qin <qinxinyi98@gmail.com>"
LABEL description="发票管理系统 - Invoice Management System"

# 安装系统依赖（Tesseract OCR + Poppler + 中文字体）
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OCR 引擎
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    # PDF 转图片
    poppler-utils \
    # 中文字体（防止 Excel 导出中文乱码）
    fonts-noto-cjk \
    # 其他工具
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 验证 OCR 组件
RUN tesseract --version && pdftoppm -v

WORKDIR /app

# 复制 Python 依赖文件
COPY backend/requirements.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制后端源码
COPY backend/app/ ./app/
COPY backend/main.py ./

# 复制 Excel 模板
COPY backend/templates/ ./templates/

# 从 Stage 1 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist/ ./frontend_dist/

# 创建运行时数据目录
RUN mkdir -p /app/data/uploads /app/data/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fs http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--log-level", "info"]
