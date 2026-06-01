#!/bin/bash
# ============================================================
# 发票管理系统 - 阿里云 ECS 一键初始化脚本
# 适用系统: Ubuntu 22.04 / 24.04
#
# 用法:
#   1. 将此脚本上传到服务器 /opt/ 目录
#   2. chmod +x setup-server.sh
#   3. sudo ./setup-server.sh
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[OK]${NC}  $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; exit 1; }

# ==================== 检查权限 ====================
if [ "$EUID" -ne 0 ]; then
    err "请使用 sudo 运行此脚本"
fi

echo "============================================"
echo "  发票管理系统 - 阿里云 ECS 环境初始化"
echo "============================================"
echo ""

# ==================== 1. 系统更新 ====================
log "更新系统包..."
apt-get update && apt-get upgrade -y

# ==================== 2. 安装系统依赖 ====================
log "安装 OCR 运行时依赖..."
apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    poppler-utils \
    fonts-noto-cjk \
    nginx \
    python3.13 \
    python3.13-venv \
    python3-pip \
    git \
    curl \
    ufw

# ==================== 3. 创建项目目录 ====================
log "创建项目目录..."
mkdir -p /opt/invoice-system
chown -R www-data:www-data /opt/invoice-system

# ==================== 4. 配置防火墙 ====================
log "配置防火墙..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw --force enable
ufw status verbose

# ==================== 5. 拉取项目代码 ====================
log "拉取项目代码..."
if [ -d "/opt/invoice-system/.git" ]; then
    warn "项目已存在，执行 git pull..."
    cd /opt/invoice-system
    git pull origin main
else
    # 请替换为你的仓库地址
    git clone https://github.com/Ross98/invoice-system.git /opt/invoice-system
    cd /opt/invoice-system
fi

# ==================== 6. 创建 Python 虚拟环境 ====================
log "创建 Python 虚拟环境..."
cd /opt/invoice-system/backend
python3.13 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ==================== 7. 设置环境变量 ====================
log "设置环境变量..."
if [ ! -f /opt/invoice-system/backend/.env ]; then
    cp /opt/invoice-system/deploy/.env.production /opt/invoice-system/backend/.env
    log "已创建 .env 文件，请根据需要修改 /opt/invoice-system/backend/.env"
fi

# ==================== 8. 构建前端 ====================
log "构建前端（Node.js 18+）..."
if ! command -v node &> /dev/null; then
    warn "Node.js 未安装，正在安装..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi

cd /opt/invoice-system/frontend
npm ci --registry=https://registry.npmmirror.com
npm run build
cp -r dist ../backend/frontend_dist
log "前端构建完成"

# ==================== 9. 安装 systemd 服务 ====================
log "安装 systemd 服务..."
cp /opt/invoice-system/deploy/systemd/invoice-system.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable invoice-system
systemctl start invoice-system
sleep 2
systemctl status invoice-system --no-pager

# ==================== 10. 配置 Nginx ====================
log "配置 Nginx..."
cp /opt/invoice-system/deploy/nginx.conf /etc/nginx/sites-available/invoice-system
ln -sf /etc/nginx/sites-available/invoice-system /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# ==================== 11. 设置定时备份 ====================
log "设置数据库定时备份..."
cat > /etc/cron.daily/invoice-backup << 'CRONEOF'
#!/bin/bash
BACKUP_DIR="/opt/invoice-system/backups"
mkdir -p "$BACKUP_DIR"
cp /opt/invoice-system/backend/data/invoice.db "$BACKUP_DIR/invoice-$(date +%Y%m%d).db"
# 保留最近 30 天
find "$BACKUP_DIR" -name "invoice-*.db" -mtime +30 -delete
CRONEOF
chmod +x /etc/cron.daily/invoice-backup

# ==================== 完成 ====================
echo ""
echo "============================================"
echo "  初始化完成！"
echo "============================================"
echo ""
echo "  访问地址: http://$(curl -s ifconfig.me)"
echo "  API 文档: http://$(curl -s ifconfig.me)/docs"
echo ""
echo "  项目目录: /opt/invoice-system"
echo "  配置文件: /opt/invoice-system/backend/.env"
echo "  数据库:   /opt/invoice-system/backend/data/invoice.db"
echo ""
echo "  常用命令:"
echo "    systemctl status invoice-system   # 查看服务状态"
echo "    journalctl -u invoice-system -f   # 查看日志"
echo "    systemctl restart invoice-system  # 重启服务"
echo ""
echo "  下一步:"
echo "    1. 修改 /opt/invoice-system/backend/.env 中的 CORS_ORIGINS"
echo "    2. 配置 SSL 证书 (certbot)"
echo "    3. 修改 nginx.conf 中的 server_name"
echo ""
