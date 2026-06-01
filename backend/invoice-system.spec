# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Invoice System (发票管理系统)
打包为 onedir 模式，运行时资源（Tesseract/Poppler）外部放置
"""

import os
import sys
from pathlib import Path

# ---- 基础配置 ----
APP_NAME = "InvoiceSystem"
ENTRY_SCRIPT = "main.py"
BACKEND_DIR = Path("C:/Users/12572/AppData/Roaming/Tencent/Marvis/User/oAN1i2RXnJ75mBIokH6tuqcm61mc/workspace/conv_19e4d530a79_617066ddd5ed/output/invoice-system/backend")

# ---- 需要打包的数据文件 ----
datas = []

# 前端静态文件（frontend_dist/ 避免与 PyInstaller dist/ 输出目录冲突）
frontend_dist = BACKEND_DIR / "frontend_dist"
if frontend_dist.exists():
    for root, _, files in os.walk(str(frontend_dist)):
        for f in files:
            src = os.path.join(root, f)
            dst_rel = os.path.relpath(src, str(BACKEND_DIR))
            dst = os.path.dirname(dst_rel)
            datas.append((src, dst))

# Excel 模板
templates_dir = BACKEND_DIR / "templates"
if templates_dir.exists():
    for root, _, files in os.walk(str(templates_dir)):
        for f in files:
            src = os.path.join(root, f)
            dst_rel = os.path.relpath(src, str(BACKEND_DIR))
            dst = os.path.dirname(dst_rel)
            datas.append((src, dst))

# ---- 隐藏导入（确保不被 tree-shaking 移除）----
hiddenimports = [
    # FastAPI / Starlette 相关的隐式导入
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "starlette",
    # 数据库
    "sqlalchemy.sql.default_comparator",
    # OCR
    "pdf2image",
    "pdfplumber",
    "PIL",
    "PIL._imaging",
    "PIL.Image",
    # Excel
    "openpyxl",
    "openpyxl.cell",
    "openpyxl.styles",
    "openpyxl.utils",
    # 其他
    "pypdfium2",
    "pydantic_settings",
    "multipart",
    "python_multipart",
    # app 模块
    "app",
    "app.config",
    "app.database",
    "app.models",
    "app.models.invoice",
    "app.schemas",
    "app.schemas.invoice",
    "app.services",
    "app.services.ocr",
    "app.services.file_storage",
    "app.routers",
    "app.routers.invoices",
    "app.routers.ocr",
    "app.resource_path",
]

# ---- 排除的大型/不需要的模块 ----
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "IPython",
    "jupyter",
    "notebook",
    "sphinx",
    "pytest",
    "setuptools",
    "pip",
    "wheel",
    "distutils",
    "test",
    "tests",
    "unittest",
]

# ---- PyInstaller Analysis ----
a = Analysis(
    [str(BACKEND_DIR / ENTRY_SCRIPT)],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# ---- PYZ (压缩 Python 字节码) ----
pyz = PYZ(a.pure)

# ---- EXE ----
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台，方便查看日志和错误
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ---- COLLECT (收集所有文件到 dist 目录) ----
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
