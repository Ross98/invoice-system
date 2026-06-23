# 发票管理系统 (Invoice Management System)

基于 OCR 的发票识别与报销管理工具，支持电子发票、出租车票、火车票的自动识别、分类汇总和 Excel 导出。

> **最新版本**: [v2.1.0](https://github.com/Ross98/invoice-system/releases/tag/v2.1.0) — P0 安全修复 + 性能/UX 优化 + 测试 + CI

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vuetify + Vite |
| 后端 | Python 3.13 + FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| OCR | Tesseract 5.x + Poppler (pdftoppm) |
| 打包 | PyInstaller onedir |

## 功能特性

- **多格式发票识别** — 支持 PDF、PNG、JPG 电子发票 / 出租车票 / 火车票
- **OCR 自动提取** — 自动识别发票号码、金额、日期、销方名称、费用类型
- **智能仪表盘** — 本月统计、月度趋势图、分类占比、Top 消费单位排名
- **全局搜索** — 跨发票号码、OCR 原文、对方单位名称等 6 个维度搜索，关键词高亮
- **费用分类汇总** — 按费用类型分组统计，支持筛选、编辑、报销状态跟踪
- **Excel 导出** — 带有格式模板的汇总报表导出
- **系统设置** — OCR 配置、存储管理、数据库备份与重置
- **独立打包** — 解压即用，Tesseract/Poppler 随包分发

## 快速开始

### 下载使用（推荐）

从 [Release 页面](https://github.com/Ross98/invoice-system/releases) 下载最新版 `InvoiceSystem-*-win64.zip`，解压后运行 `InvoiceSystem.exe` 即可。

### 开发环境

#### 环境要求

- Windows 10/11 (64-bit)
- Python 3.10+
- Node.js 18+
- Tesseract OCR 5.x（需安装到系统或放入 `backend/runtime/`）
- Poppler（需安装到系统或放入 `backend/runtime/`）

#### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API 文档: http://localhost:8000/docs

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本（输出到 backend/frontend_dist/）
npm run build
```

## 开发工具链

```bash
# 后端 Lint
cd backend
.venv\Scripts\ruff.exe check app/

# 后端自动修复
.venv\Scripts\ruff.exe check --fix app/

# 后端测试 (49 用例, ~1s)
.venv\Scripts\python.exe -m pytest tests/ -v

# 前端 Lint
cd frontend
npm run lint

# 前端自动修复
npm run lint:fix

# 前端测试 (43 用例, ~1s)
npm test

# 前端覆盖率
npm run test:coverage

# 前端格式化
npm run format
```

### CI/CD

PR 与 push 到 `main` / `V2.0` 分支时会自动触发 [Tests workflow](.github/workflows/tests.yml):

| Job | 平台 | 检查 |
|-----|------|------|
| `backend` | Windows / Python 3.12 | `pytest --cov=app` → `ruff check` |
| `frontend` | Ubuntu / Node 20 | `npm ci` → `npm run lint` → `npm test` → `npm run build` → 上传产物 |
| `required` | Ubuntu | 两个 job 都 pass 才合并 |

CI 全绿标准: backend 49 pytest + frontend 43 vitest + ruff/ESLint 0 errors + npm run build 成功。

详见 [代码审查标准](docs/CODE_REVIEW_STANDARDS.md) 与 [CHANGELOG.md](CHANGELOG.md)。

## 目录结构

```
invoice-system/
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── views/           # 页面组件（仪表盘、发票管理、设置、统计）
│       ├── components/      # 通用组件
│       ├── layouts/         # 布局组件
│       ├── router/          # 路由配置
│       └── api/             # API 请求封装
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由（发票/OCR/搜索/统计/设置）
│   │   ├── services/        # OCR、Excel 等业务服务
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   └── config.py        # 配置管理
│   ├── frontend_dist/       # 前端构建产物（后端自动读取）
│   ├── templates/           # Excel 模板
│   ├── runtime/             # Tesseract + Poppler 运行时（不提交到 Git）
│   ├── data/                # 用户数据（数据库、上传文件）（不提交到 Git）
│   └── invoice-system.spec  # PyInstaller 打包配置
├── docs/                    # 文档（架构设计、代码审查标准）
├── build_package.py         # 发布包构建脚本
├── ruff.toml                # Python Lint 配置
├── pyrightconfig.json       # Python 类型检查配置
└── .pre-commit-config.yaml  # Pre-commit 钩子配置
```

## 构建 Windows 分发包

```bash
cd backend

# PyInstaller 打包
.venv\Scripts\python.exe -m PyInstaller invoice-system.spec --clean --noconfirm

# 完整构建（组装 runtime、模板、前端文件）
cd ..
backend\.venv\Scripts\python.exe build_package.py
```

输出目录：`backend/dist/InvoiceSystem-<version>-win64/`,内含 `InvoiceSystem.exe` 主程序、`Launcher.exe` 启动器、`runtime/` (Tesseract+Poppler)、`templates/` Excel 模板、`data/` 数据目录,以及 `启动发票管理系统.bat` 一键启动脚本。

## 生产部署

### 方式 A:Windows 单机部署（最简单）

适用:个人/小团队,1-10 人本地使用,无并发要求。

1. 从 [Release 页面](https://github.com/Ross98/invoice-system/releases) 下载 `InvoiceSystem-2.1.0-win64.zip`
2. 解压到任意目录(如 `D:\InvoiceSystem\`)
3. 首次启动双击 `启动发票管理系统.bat`,Launcher 会自动:
   - 启动 `InvoiceSystem.exe`(监听 8000 端口)
   - 等 `/health` 返回 200 后自动打开浏览器到 `http://127.0.0.1:8000`
4. 数据落地在 `<解压目录>\data\invoice.db`,上传文件在 `data\uploads\`

> **OCR 提醒**: 解压包已包含 Tesseract + Poppler,无需额外安装。如需中文识别包,首次启动会提示,见 `runtime\` 目录。

#### 防火墙放行(局域网共享)

如需同网段其他人访问,放行 8000 端口:

```powershell
# Windows 防火墙放行(管理员权限)
New-NetFirewallRule -DisplayName "InvoiceSystem" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

客户端访问 `http://<本机IP>:8000`。

### 方式 B:Linux 服务器部署（推荐生产）

适用:团队/企业,需 systemd 守护 + 反向代理 + HTTPS。

#### 1. 系统依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3-venv python3-dev tesseract-ocr \
  tesseract-ocr-chi-sim tesseract-ocr-chi-tra poppler-utils nginx

# CentOS/RHEL
sudo yum install -y python3.11 tesseract tesseract-chi-sim poppler-utils nginx
```

#### 2. 应用部署

```bash
# 创建系统用户(无登录权限,安全)
sudo useradd -r -m -d /opt/invoice-system -s /bin/bash invoice

# 复制项目(假设已 clone)
sudo -u invoice git clone https://github.com/Ross98/invoice-system.git /opt/invoice-system/app
cd /opt/invoice-system/app

# 后端依赖
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt

# 前端构建
cd frontend && npm ci && npm run build && cd ..
cp -r frontend/dist/* backend/frontend_dist/

# 数据库迁移(首次运行)
cd backend
ADMIN_TOKEN="<strong-secret>" \
HOST=0.0.0.0 PORT=8000 \
./.venv/bin/python -c "from app.database import init_db, seed_default_categories; init_db(); seed_default_categories()"
```

#### 3. systemd 服务

创建 `/etc/systemd/system/invoice-system.service`:

```ini
[Unit]
Description=Invoice Management System
After=network.target

[Service]
Type=simple
User=invoice
WorkingDirectory=/opt/invoice-system/app/backend
Environment="ADMIN_TOKEN=<your-strong-secret>"
Environment="HOST=0.0.0.0"
Environment="PORT=8000"
Environment="CORS_ORIGINS=https://invoice.your-domain.com"
ExecStart=/opt/invoice-system/app/backend/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

启动:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now invoice-system
sudo systemctl status invoice-system
```

#### 4. Nginx 反向代理 + HTTPS

`/etc/nginx/sites-available/invoice-system`:

```nginx
server {
    listen 80;
    server_name invoice.your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name invoice.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/invoice.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/invoice.your-domain.com/privkey.pem;

    client_max_body_size 50M;  # 支持最大上传

    # 上传文件单独路径
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000/uploads/;
        proxy_set_header Host $host;
        expires 7d;
    }

    # API + SPA
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;  # OCR 识别可能耗时
    }
}
```

启用:

```bash
sudo ln -s /etc/nginx/sites-available/invoice-system /etc/nginx/sites-enabled/
sudo certbot --nginx -d invoice.your-domain.com
sudo nginx -t && sudo systemctl reload nginx
```

#### 5. 数据备份

```bash
# 定时任务(crontab -e):每天凌晨备份
0 2 * * * cp /opt/invoice-system/app/backend/invoice.db /backup/invoice-$(date +\%Y\%m\%d).db

# 或使用系统自带 backup 端点(需 ADMIN_TOKEN)
curl -X POST -H "X-Admin-Token: <your-secret>" https://invoice.your-domain.com/api/settings/backup
```

#### 6. 监控

```bash
# 健康检查
curl https://invoice.your-domain.com/health

# 服务状态
sudo systemctl status invoice-system

# 日志(可选 journald)
sudo journalctl -u invoice-system -f
```

### 环境变量参考

| 变量 | 默认 | 说明 |
|------|------|------|
| `HOST` | `0.0.0.0` | 监听地址 |
| `PORT` | `8000` | 监听端口 |
| `DATABASE_URL` | `sqlite:///./invoice.db` | 数据库连接 |
| `UPLOAD_DIR` | `../uploads` | 上传目录(相对 backend/) |
| `MAX_FILE_SIZE_MB` | `10` | 单文件最大(MB) |
| `STORAGE_THRESHOLD_MB` | `1` | 大于此值改存磁盘 |
| `OCR_ENGINE` | `local` | OCR 引擎(local/cloud) |
| `TESSERACT_PATH` | _空_ | Tesseract 路径(空=自动) |
| `POPPLER_PATH` | _空_ | Poppler 路径(空=自动) |
| `CORS_ORIGINS` | `*` | 生产环境填具体域名,逗号分隔 |
| `ADMIN_TOKEN` | _None_ | `/api/settings/reset` & `/backup` 鉴权 token,生产必设 |
| `APP_VERSION` | 自动 | 显示用版本号 |

完整环境变量清单见 `backend/.env.example`。

## License

MIT
