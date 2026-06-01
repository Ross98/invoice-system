"""
资源路径解析模块

兼容两种运行环境：
1. 开发环境（python main.py）→ 基于 __file__ 的相对路径
2. PyInstaller 打包环境 → 基于 sys.executable 的相对路径
"""

import os
import sys
from pathlib import Path


def _is_packaged() -> bool:
    """判断是否在 PyInstaller 打包环境中运行"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_base_dir() -> Path:
    """
    获取应用根目录。

    - 开发环境: backend/ 目录（main.py 所在目录）
    - 打包环境: .exe 所在目录（用户安装目录）
    """
    if _is_packaged():
        return Path(sys.executable).parent.resolve()
    # 开发环境: backend/ 目录 (main.py 的父目录)
    return Path(__file__).parent.parent.resolve()


def get_meipass_dir() -> Path:
    """
    获取 PyInstaller _MEIPASS 临时解压目录。
    仅在打包环境中有效，开发环境返回 None。
    """
    if _is_packaged():
        return Path(sys._MEIPASS)
    return None


def get_runtime_dir() -> Path:
    """
    获取运行时资源目录（Tesseract, Poppler 等）。
    - 打包环境: <exe所在>/runtime/
    - 开发环境: backend/runtime/
    """
    return get_base_dir() / "runtime"


def get_data_dir() -> Path:
    """
    获取用户数据目录（数据库、上传文件、配置等）。
    - 打包环境: <exe所在>/data/
    - 开发环境: backend/ 目录（保持兼容）
    """
    if _is_packaged():
        return get_base_dir() / "data"
    return get_base_dir()


def get_tesseract_path() -> str:
    """获取 Tesseract 可执行文件路径"""
    meipass = get_meipass_dir()
    tesseract_exe = "tesseract.exe"

    # 1. 环境变量
    env_path = os.environ.get("TESSERACT_PATH", "")
    if env_path and Path(env_path).exists():
        return env_path

    # 2. PyInstaller 打包环境：_MEIPASS 中有 bundled 的 tesseract
    if meipass:
        bundled = meipass / "runtime" / "tesseract" / tesseract_exe
        if bundled.exists():
            return str(bundled)

    # 3. 运行时目录
    local = get_runtime_dir() / "tesseract" / tesseract_exe
    if local.exists():
        return str(local)

    # 4. 常见安装路径
    import shutil
    for p in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]:
        if Path(p).exists():
            return p

    # 5. PATH
    found = shutil.which("tesseract")
    if found:
        return found

    return ""


def get_tessdata_dir() -> str:
    """获取 Tesseract 语言包目录"""
    tesseract_path = get_tesseract_path()
    if tesseract_path:
        parent = Path(tesseract_path).parent
        tessdata = parent / "tessdata"
        if tessdata.exists():
            return str(tessdata)
    return ""


def get_poppler_path() -> str:
    """获取 Poppler 的 bin 目录（含 pdftoppm.exe）"""
    meipass = get_meipass_dir()

    # 1. 环境变量
    env_path = os.environ.get("POPPLER_PATH", "")
    if env_path and (Path(env_path) / "pdftoppm.exe").exists():
        return env_path

    # 2. PyInstaller 打包环境
    if meipass:
        bundled = meipass / "runtime" / "poppler" / "bin"
        if (bundled / "pdftoppm.exe").exists():
            return str(bundled)

    # 3. 运行时目录
    local = get_runtime_dir() / "poppler" / "bin"
    if (local / "pdftoppm.exe").exists():
        return str(local)

    # 4. 常见安装路径
    import shutil
    for d in [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
        r"C:\Program Files\poppler\bin",
        r"C:\poppler\bin",
        r"C:\poppler-24.02.0\Library\bin",
    ]:
        exe = Path(d) / "pdftoppm.exe"
        if exe.exists():
            return d

    # 5. PATH
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        return str(Path(pdftoppm).parent)

    return ""


def get_template_path() -> Path:
    """
    获取 Excel 导出模板路径。
    - 打包环境: <exe>/templates/模板-2026费用报销表.xlsx
    - 开发环境: backend/../templates/ 或 原硬编码路径（兼容）
    """
    meipass = get_meipass_dir()
    template_name = "模板-2026费用报销表.xlsx"

    # 1. PyInstaller 打包
    if meipass:
        bundled = meipass / "templates" / template_name
        if bundled.exists():
            return bundled

    # 2. 运行时目录（用户可能替换模板）
    local_dir = get_base_dir() / "templates"
    local = local_dir / template_name
    if local.exists():
        return local

    # 3. 项目根目录下的 templates/
    project_root = get_base_dir().parent if not _is_packaged() else get_base_dir()
    project_template = project_root / "templates" / template_name
    if project_template.exists():
        return project_template

    # 4. 原文硬编码路径（开发环境兼容）
    legacy = Path(r"C:/Users/12572/Desktop/发票/模板-2026费用报销表.xlsx")
    if legacy.exists():
        return legacy

    return local_dir / template_name  # 返回预期路径，调用方自行处理不存在的情况


def get_frontend_dir() -> Path:
    """获取前端静态文件目录（frontend_dist/ 避免与 PyInstaller dist/ 冲突）"""
    meipass = get_meipass_dir()
    if meipass:
        return meipass / "frontend_dist"
    return get_base_dir() / "frontend_dist"


def ensure_directories() -> dict:
    """确保必要的运行时目录存在，返回各目录路径"""
    base = get_base_dir()
    dirs = {
        "data": base / "data" if _is_packaged() else base,
        "uploads": base / "data" / "uploads" if _is_packaged() else base.parent / "uploads",
        "templates": base / "templates",
        "runtime": base / "runtime",
    }
    for name, d in dirs.items():
        d.mkdir(parents=True, exist_ok=True)
    return dirs
