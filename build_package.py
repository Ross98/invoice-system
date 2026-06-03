# Invoice System - 完整打包构建脚本
# 用法: python build_package.py
# 输出: dist/InvoiceSystem-{version}-win64.zip
#       dist/InvoiceSystem-{version}-win64/  (解压即用)

import os
import sys
import shutil
import subprocess
from pathlib import Path
import datetime

PROJECT_ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = BACKEND_DIR / "dist"
BUILD_DIR = BACKEND_DIR / "build"
VERSION = "2.0.4"
PACKAGE_NAME = f"InvoiceSystem-{VERSION}-win64"
PACKAGE_DIR = DIST_DIR / PACKAGE_NAME

def run(cmd, cwd=None):
    """运行命令并打印输出"""
    print(f"  >> {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
        return False
    return True

def step(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")

def step1_build_frontend():
    """步骤1: 构建前端"""
    step("1/6 构建前端 Vue 应用")
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  前端依赖未安装，跳过")
        return False
    run(f"node node_modules/vite/bin/vite.js build", cwd=FRONTEND_DIR)
    return True

def step2_sync_frontend():
    """步骤2: 同步前端构建产物到后端"""
    step("2/6 同步前端静态文件")
    frontend_dist = FRONTEND_DIR / "dist"
    backend_dist = BACKEND_DIR / "dist"
    if not frontend_dist.exists():
        print("  前端 dist 不存在! 请先构建前端")
        return False
    if backend_dist.exists():
        shutil.rmtree(backend_dist)
    shutil.copytree(frontend_dist, backend_dist)
    print(f"  已复制: {frontend_dist} -> {backend_dist}")
    return True

def step3_pyinstaller_build_server():
    """步骤3: PyInstaller 打包服务端"""
    step("3/6 PyInstaller 打包服务端")
    spec_file = BACKEND_DIR / "invoice-system.spec"
    if not spec_file.exists():
        print("  spec 文件不存在!")
        return False
    python_exe = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = "python"
    run(f'"{python_exe}" -m PyInstaller invoice-system.spec --clean --noconfirm', cwd=BACKEND_DIR)
    return True


def step4_pyinstaller_build_launcher():
    """步骤4: PyInstaller 打包启动器"""
    step("4/6 PyInstaller 打包启动器")
    spec_file = BACKEND_DIR / "launcher.spec"
    if not spec_file.exists():
        print("  launcher.spec 文件不存在!")
        return False
    python_exe = BACKEND_DIR / ".venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = "python"
    run(f'"{python_exe}" -m PyInstaller launcher.spec --clean --noconfirm', cwd=BACKEND_DIR)

    # 将 Launcher.exe 复制到服务端的 dist 目录（共享 _internal/）
    launcher_dist = DIST_DIR / "Launcher"
    server_dist = DIST_DIR / "InvoiceSystem"
    launcher_exe = launcher_dist / "Launcher.exe"
    if launcher_exe.exists() and server_dist.exists():
        dest = server_dist / "Launcher.exe"
        shutil.copy2(launcher_exe, dest)
        print(f"  Launcher.exe 已整合到服务目录: {dest}")
    else:
        if not launcher_exe.exists():
            print("  PyInstaller 输出无 Launcher.exe")
            return False

    return True


def step5_assemble_package():
    """步骤5: 组装最终发布包"""
    step("5/6 组装发布包")
    pyinstaller_output = DIST_DIR / "InvoiceSystem"
    if not pyinstaller_output.exists():
        print("  PyInstaller 输出不存在!")
        return False
    
    # 清理旧包
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True)
    
    # 复制 PyInstaller 输出
    print("  复制应用文件...")
    for item in pyinstaller_output.iterdir():
        dest = PACKAGE_DIR / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    
    # 复制运行时（Tesseract + Poppler）
    runtime_src = BACKEND_DIR / "runtime"
    if runtime_src.exists():
        print("  复制 OCR 运行时...")
        runtime_dst = PACKAGE_DIR / "runtime"
        shutil.copytree(runtime_src, runtime_dst)
    
    # 创建数据目录
    data_dir = PACKAGE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "uploads").mkdir(exist_ok=True)
    
    # 复制模板到包外（用户可编辑）
    templates_src = BACKEND_DIR / "templates"
    templates_dst = PACKAGE_DIR / "templates"
    if templates_src.exists():
        shutil.copytree(templates_src, templates_dst)
    
    # 创建启动脚本
    create_launcher(PACKAGE_DIR)
    
    # 创建说明文件
    create_readme(PACKAGE_DIR)
    
    print(f"\n  发布包已组装: {PACKAGE_DIR}")
    return True

def create_launcher(pkg_dir):
    """创建启动批处理"""
    bat = pkg_dir / "启动发票管理系统.bat"
    bat.write_text("""@echo off
chcp 65001 >nul
title 发票管理系统
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"
echo.
echo ╔══════════════════════════════════════╗
echo ║       发票管理系统 v{version}            ║
echo ║       Invoice Management System      ║
echo ╚══════════════════════════════════════╝
echo.
echo 正在启动服务，请稍候...
echo.
echo ── 首次使用 ──
echo   OCR 发票识别需要 Tesseract 和 Poppler
echo   如未安装，请将 runtime 目录添加到系统 PATH
echo   或下载 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
echo.
Launcher.exe
pause
""".format(version=VERSION), encoding="utf-8")
    print("  已创建启动脚本")

def create_readme(pkg_dir):
    """创建说明文件"""
    readme = pkg_dir / "使用说明.txt"
    readme.write_text("""============================================
  发票管理系统 v{version} - 使用说明
============================================

【快速开始】
  双击 "启动发票管理系统.bat" 启动服务
  Launcher 将自动启动服务端并在浏览器中打开界面
  或手动访问 http://127.0.0.1:8000

【系统要求】
  - Windows 10/11 64位
  - 无需安装 Python 或 Node.js
  - 无需安装数据库（内置 SQLite）

【OCR 发票识别】
  如需使用 OCR 自动识别发票：
  1. 安装 Tesseract OCR:
     https://github.com/UB-Mannheim/tesseract/wiki
     安装时勾选中文语言包 (Chinese Simplified)
  2. 重启发票管理系统即可

【文件说明】
  Launcher.exe          - 启动器（自动打开浏览器）
  InvoiceSystem.exe     - 服务端主程序
  _internal/            - 程序运行库
  runtime/              - OCR 引擎（Tesseract + Poppler）
  templates/            - Excel 导出模板
  data/                 - 用户数据（数据库、上传文件）
  启动发票管理系统.bat   - 启动脚本

【数据位置】
  - 数据库: data/invoice.db
  - 上传文件: data/uploads/
  - Excel模板: templates/

【卸载】
  直接删除程序目录即可（无注册表写入）。
  数据文件在 data/ 目录下，如需保留请先备份。

【技术支持】
  RocStar Robotics - 罗伯盈德(南京)技术有限公司
""".format(version=VERSION), encoding="utf-8")
    print("  已创建使用说明")

def step6_create_archive():
    """步骤6: 创建压缩包"""
    step("6/6 创建压缩包")
    
    # 尝试使用 PowerShell Compress-Archive
    zip_path = DIST_DIR / f"{PACKAGE_NAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    
    ps_cmd = f'Compress-Archive -Path "{PACKAGE_DIR}" -DestinationPath "{zip_path}"'
    result = subprocess.run(
        ["powershell", "-Command", ps_cmd],
        capture_output=True, text=True
    )
    
    if result.returncode == 0 and zip_path.exists():
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        print(f"\n  [OK] 压缩包已创建: {zip_path}")
        print(f"   大小: {size_mb:.1f} MB")
    else:
        print(f"  [WARN] PowerShell 压缩失败: {result.stderr}")
        print(f"  手动压缩目录: {PACKAGE_DIR}")
    
    return True

def main():
    print("╔══════════════════════════════════════╗")
    print("║   发票管理系统 - 打包构建脚本         ║")
    print(f"║   版本: {VERSION}                      ║")
    print("╚══════════════════════════════════════╝")
    
    steps = [
        ("构建前端", step1_build_frontend, False),  # 可选
        ("同步前端", step2_sync_frontend, True),
        ("PyInstaller 服务端", step3_pyinstaller_build_server, True),
        ("PyInstaller 启动器", step4_pyinstaller_build_launcher, True),
        ("组装包", step5_assemble_package, True),
        ("创建压缩包", step6_create_archive, True),
    ]
    
    for name, func, required in steps:
        try:
            ok = func()
            if not ok and required:
                print(f"\n[ERR] 步骤 '{name}' 失败，构建中止")
                sys.exit(1)
            elif not ok:
                print(f"  [WARN] 步骤 '{name}' 跳过（非必需）")
        except Exception as e:
            if required:
                print(f"\n[ERR] 步骤 '{name}' 异常: {e}")
                sys.exit(1)
            print(f"  [WARN] 步骤 '{name}' 异常（非必需）: {e}")
    
    print(f"\n{'='*60}")
    print(f"  [OK] 打包完成!")
    print(f"  输出目录: {PACKAGE_DIR}")
    print(f"  压缩包: {DIST_DIR / PACKAGE_NAME}.zip")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
