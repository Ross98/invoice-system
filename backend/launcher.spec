# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Invoice System Launcher
独立启动器 — 最小依赖，仅用标准库
"""

from pathlib import Path

APP_NAME = "Launcher"
ENTRY_SCRIPT = "launcher.py"
BACKEND_DIR = Path(SPECPATH)

# 无额外数据文件（纯启动器，无前端/模板数据依赖）
datas = []

# 无隐藏导入（仅标准库：subprocess, urllib, webbrowser, pathlib 等）
hiddenimports = []

# 排除大型库，减小体积
excludes = [
    "tkinter",
    "matplotlib",
    "numpy",
    "pandas",
    "scipy",
    "IPython",
    "jupyter",
    "sphinx",
    "pytest",
    "setuptools",
    "pip",
    "wheel",
    "distutils",
    "test",
    "tests",
    "unittest",
    "openpyxl",
    "PIL",
    "sqlalchemy",
    "alembic",
    "fastapi",
    "uvicorn",
    "starlette",
    "pydantic",
    "pydantic_settings",
    "pdf2image",
    "pdfplumber",
    "pypdfium2",
    "app",
]

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

pyz = PYZ(a.pure)

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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)
