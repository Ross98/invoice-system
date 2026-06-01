# 发票管理系统 (Invoice Management System)

基于 OCR 的发票识别与报销管理工具，支持电子发票、出租车票、火车票的自动识别、分类汇总和 Excel 导出。

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
- **费用分类汇总** — 按费用类型分组统计，支持筛选、编辑
- **Excel 导出** — 带有格式模板的汇总报表导出
- **独立打包** — 解压即用，Tesseract/Poppler 随包分发

## 快速开始

### 环境要求

- Windows 10/11 (64-bit)
- Python 3.10+
- Node.js 18+
- Tesseract OCR 5.x（需安装到系统或放入 `backend/runtime/`）
- Poppler（需安装到系统或放入 `backend/runtime/`）

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置
cp .env.example .env
# 按需编辑 .env 中的路径配置

# 启动开发服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

构建后前端产物输出到 `frontend/dist/`，后端会自动读取该目录。

## 目录结构

```
invoice-system/
├── frontend/                # Vue 3 前端
│   └── src/
│       ├── views/           # 页面组件
│       ├── components/      # 通用组件
│       └── api/             # API 请求封装
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── routers/         # API 路由
│   │   ├── services/        # OCR、Excel 等业务服务
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   └── config.py        # 配置管理
│   ├── templates/           # Excel 模板
│   ├── runtime/             # Tesseract + Poppler 运行时 (不提交到 Git)
│   ├── data/                # 用户数据（数据库、上传文件）(不提交到 Git)
│   └── invoice-system.spec  # PyInstaller 打包配置
└── build_package.py         # 发布包构建脚本
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

分发包包含：
- `InvoiceSystem.exe` — 自包含可执行文件
- `start.bat` — 启动脚本
- `runtime/` — Tesseract OCR + Poppler
- `templates/` — Excel 模板
- `frontend_dist/` — 前端静态文件
- `data/` — 用户数据目录（数据库、上传文件）

## 环境变量

参见 `.env.example`：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | `sqlite:///./invoice.db` |
| `UPLOAD_DIR` | 上传文件目录 | `../uploads` |
| `MAX_FILE_SIZE_MB` | 最大上传文件 (MB) | `10` |
| `OCR_ENGINE` | OCR 引擎 | `local` |
| `TESSERACT_PATH` | Tesseract 路径 | 自动检测 |
| `POPPLER_PATH` | Poppler 路径 | 自动检测 |

## License

MIT
