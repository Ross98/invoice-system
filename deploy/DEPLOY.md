# 阿里云服务器部署指南

> 发票管理系统 (Invoice Management System) v1.0.1  
> 适用：阿里云 ECS（Ubuntu 22.04 / 24.04）

---

## 目录

- [一、架构概览](#一架构概览)
- [二、服务器选购建议](#二服务器选购建议)
- [三、部署方式一：Docker Compose（推荐）](#三部署方式一docker-compose推荐)
- [四、部署方式二：直接部署（systemd + Nginx）](#四部署方式二直接部署systemd--nginx)
- [五、域名与 SSL 证书](#五域名与-ssl-证书)
- [六、日常运维](#六日常运维)
- [七、文件清单](#七文件清单)

---

## 一、架构概览

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   浏览器      │────▶│  Nginx :80   │────▶│  FastAPI :8000   │
│  (用户访问)   │     │  (反向代理)   │     │  (后端 + 前端SPA) │
└──────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                          ┌────────▼─────────┐
                                          │  SQLite 数据库    │
                                          │  (data/invoice.db)│
                                          └──────────────────┘
```

- **Nginx**：反向代理，处理 HTTPS / Gzip / 静态文件缓存
- **FastAPI**：API 服务 + 前端 SPA 静态文件服务
- **SQLite**：嵌入式数据库，零配置，自动创建
- **Tesseract + Poppler**：OCR 引擎，识别发票图片/PDF

---

## 二、服务器选购建议

| 配置项 | 最低配置 | 推荐配置 |
|--------|---------|---------|
| CPU | 1 核 | 2 核 |
| 内存 | 1 GB | 2 GB |
| 系统盘 | 20 GB | 40 GB |
| 系统 | Ubuntu 22.04 / 24.04 | Ubuntu 22.04 |
| 带宽 | 1 Mbps | 3 Mbps+ |

> **预算参考**：阿里云 ECS 入门型（1核1G）约 ¥50/月，突发性能型（2核2G）约 ¥100/月。

购买 ECS 时注意：
1. 选择 **"突发性能实例"（t5/t6）** 性价比最高
2. 安全组放行端口：**22** (SSH)、**80** (HTTP)、**443** (HTTPS)
3. 建议绑定弹性公网 IP（EIP），方便后期迁移

---

## 三、部署方式一：Docker Compose（推荐）

### 3.1 服务器环境准备

```bash
# SSH 登录服务器
ssh root@<你的服务器公网IP>

# 安装 Docker
curl -fsSL https://get.docker.com | bash

# 启动 Docker
systemctl enable docker && systemctl start docker

# 安装 Docker Compose（如果未包含在 Docker 中）
apt-get install -y docker-compose-plugin
```

### 3.2 拉取项目代码

```bash
# SSH 方式（推荐，配置过 SSH Key）
cd /opt
git clone git@github.com:Ross98/invoice-system.git
cd invoice-system

# HTTPS 方式
git clone https://github.com/Ross98/invoice-system.git /opt/invoice-system
cd /opt/invoice-system
```

### 3.3 修改环境变量

```bash
# 编辑生产环境配置
vim deploy/.env.production
```

**关键修改**：

```ini
# ⚠️ 生产环境必须改！
CORS_ORIGINS=https://invoice.your-domain.com   # 替换为你的域名

# 如果没有域名，也可以先用 IP 访问（不推荐生产长期使用）
# CORS_ORIGINS=*
```

### 3.4 构建并启动

```bash
# 构建镜像（首次约 5-10 分钟）
docker compose -f deploy/docker-compose.yml build

# 后台启动
docker compose -f deploy/docker-compose.yml up -d

# 验证
docker compose -f deploy/docker-compose.yml ps
curl http://localhost/health
```

### 3.5 访问验证

打开浏览器访问 `http://<你的服务器IP>`，应该看到发票管理系统首页。

API 文档：`http://<你的服务器IP>/docs`

### 3.6 日常管理命令

```bash
# 查看日志
docker compose -f deploy/docker-compose.yml logs -f invoice-app

# 重启服务
docker compose -f deploy/docker-compose.yml restart

# 更新代码后重新部署
cd /opt/invoice-system
git pull origin main
docker compose -f deploy/docker-compose.yml build --no-cache
docker compose -f deploy/docker-compose.yml up -d

# 停止服务
docker compose -f deploy/docker-compose.yml down

# 查看资源使用
docker stats invoice-app
```

---

## 四、部署方式二：直接部署（systemd + Nginx）

### 4.1 使用一键初始化脚本

```bash
# SSH 登录服务器
ssh root@<服务器IP>

# 克隆项目
cd /opt
git clone https://github.com/Ross98/invoice-system.git
cd invoice-system

# 运行初始化（自动完成所有步骤）
chmod +x deploy/setup-server.sh
sudo ./deploy/setup-server.sh
```

脚本会自动完成：
- 系统包更新
- 安装 Tesseract OCR + Poppler + Nginx + Python 3.13
- 创建 Python 虚拟环境并安装依赖
- 构建前端静态文件
- 安装 systemd 服务并启动
- 配置 Nginx 反向代理
- 设置数据库定时备份

### 4.2 手动部署（分步操作）

#### Step 1 — 安装系统依赖

```bash
apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng \
    poppler-utils fonts-noto-cjk \
    nginx python3.13 python3.13-venv git curl
```

#### Step 2 — 创建虚拟环境

```bash
cd /opt/invoice-system/backend
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

#### Step 3 — 配置环境变量

```bash
cp deploy/.env.production backend/.env
vim backend/.env  # 修改 CORS_ORIGINS
```

#### Step 4 — 构建前端

```bash
cd /opt/invoice-system/frontend
npm ci && npm run build
cp -r dist ../backend/frontend_dist
```

#### Step 5 — 安装 systemd 服务

```bash
cp deploy/systemd/invoice-system.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now invoice-system
```

#### Step 6 — 配置 Nginx

```bash
cp deploy/nginx.conf /etc/nginx/sites-available/invoice-system
ln -sf /etc/nginx/sites-available/invoice-system /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

---

## 五、域名与 SSL 证书

### 5.1 域名解析

1. 在域名控制台添加 **A 记录**：
   ```
   类型: A
   主机记录: invoice (或 www)
   记录值: <你的 ECS 公网 IP>
   ```

2. 等待 DNS 生效（约 5-10 分钟），验证：
   ```bash
   ping invoice.your-domain.com
   ```

### 5.2 配置 Let's Encrypt 免费 SSL

```bash
# 安装 certbot
apt-get install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d invoice.your-domain.com

# 证书自动续期（已默认配置）
certbot renew --dry-run
```

### 5.3 启用 HTTPS 后的 CORS 修改

编辑 `backend/.env`：
```ini
CORS_ORIGINS=https://invoice.your-domain.com
```

然后重启服务：
```bash
# Docker 方式
docker compose -f deploy/docker-compose.yml restart invoice-app

# systemd 方式
systemctl restart invoice-system
```

---

## 六、日常运维

### 6.1 数据备份

```bash
# 手动备份
cp /opt/invoice-system/backend/data/invoice.db \
   /opt/invoice-system/backups/invoice-$(date +%Y%m%d).db

# 定时备份已自动配置（/etc/cron.daily/invoice-backup）
# 每天凌晨自动备份，保留 30 天
```

### 6.2 日志查看

```bash
# Docker 方式
docker compose -f deploy/docker-compose.yml logs -f --tail=100 invoice-app

# systemd 方式
journalctl -u invoice-system -f

# Nginx 日志
tail -f /var/log/nginx/invoice-access.log
tail -f /var/log/nginx/invoice-error.log
```

### 6.3 更新部署

```bash
# 1. 拉取最新代码
cd /opt/invoice-system && git pull origin main

# 2a. Docker 方式 — 重新构建
docker compose -f deploy/docker-compose.yml build --no-cache
docker compose -f deploy/docker-compose.yml up -d

# 2b. systemd 方式 — 重新构建前端并重启
cd frontend && npm ci && npm run build
cp -r dist ../backend/frontend_dist
systemctl restart invoice-system
```

### 6.4 监控

```bash
# CPU / 内存
htop

# 磁盘使用
df -h

# 服务状态
systemctl status invoice-system
systemctl status nginx
```

### 6.5 故障排查清单

| 故障现象 | 检查步骤 |
|---------|---------|
| 页面打不开 (502) | `systemctl status invoice-system` 看后端是否运行 |
| 页面打不开 (504) | `journalctl -u invoice-system` 看是否有报错 |
| OCR 识别失败 | `tesseract --version` 确认 Tesseract 已安装 |
| PDF 上传报错 | `pdftoppm -v` 确认 Poppler 已安装 |
| 中文乱码 | `fc-list :lang=zh` 确认中文字体已安装 |
| 上传文件无法保存 | `ls -ld /opt/invoice-system/backend/data/uploads` 确认目录权限 |

---

## 七、文件清单

```
deploy/
├── Dockerfile                   # Docker 多阶段构建（前端 + 后端 + OCR）
├── docker-compose.yml           # Docker Compose 编排（app + nginx）
├── .dockerignore               # Docker 构建排除清单
├── .env.production             # 生产环境变量模板
├── nginx.conf                  # Nginx 反向代理配置（含 SSL 模板）
├── setup-server.sh             # 阿里云 ECS 一键初始化脚本
├── systemd/
│   └── invoice-system.service   # systemd 服务单元
└── DEPLOY.md                   # 本文档
```

---

## 附录：阿里云安全组配置

登录阿里云控制台 → ECS → 安全组 → 配置规则，确保以下端口已放行：

| 端口 | 协议 | 来源 | 用途 |
|------|------|------|------|
| 22 | TCP | 0.0.0.0/0 | SSH 远程登录 |
| 80 | TCP | 0.0.0.0/0 | HTTP 访问 |
| 443 | TCP | 0.0.0.0/0 | HTTPS 访问 |

> **安全建议**：SSH (22) 端口建议限制为你的固定 IP 地址，避免被暴力破解。
