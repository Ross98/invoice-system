# 发票管理系统 (Invoice Management System)

基于 OCR 的发票识别与报销管理工具，支持电子发票、出租车票、火车票的自动识别、分类汇总和 Excel 导出。

> **最新版本**: [v2.0.2](https://github.com/Ross98/invoice-system/releases/tag/v2.0.2) — 紧急修复启动崩溃问题

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

# 前端 Lint
cd frontend
npm run lint

# 前端格式化
npm run format
```

详见 [代码审查标准](docs/CODE_REVIEW_STANDARDS.md)。

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

输出目录：`backend/dist/InvoiceSystem-<version>-win64/`

## License

MIT
