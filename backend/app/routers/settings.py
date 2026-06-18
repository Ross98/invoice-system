"""系统设置 API — OCR配置 / 存储配置 / 备份 / 重置"""

import secrets
from datetime import datetime
import json
from pathlib import Path
import shutil
import sys

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings as app_settings
from app.database import Base, SessionLocal, engine, seed_default_categories

router = APIRouter(prefix="/api/settings", tags=["settings"])


def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    token: str | None = Query(default=None),
):
    """管理接口鉴权：未配置 ADMIN_TOKEN 时本地不强制；设了以后强制校验。"""
    expected = app_settings.ADMIN_TOKEN
    if not expected:
        return  # 本地开发/未部署环境：跳过校验
    provided = x_admin_token or token
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="未授权：需要有效的 Admin Token")


# ── settings.json 读写 ──

def _get_data_dir() -> Path:
    """获取数据目录"""
    if getattr(sys, "frozen", False):
        data_dir = Path(sys.executable).parent / "data"
    else:
        data_dir = Path(__file__).parent.parent.parent
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _load_user_settings() -> dict:
    path = _get_data_dir() / "settings.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_user_settings(data: dict):
    path = _get_data_dir() / "settings.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Pydantic models ──

class OcrSettings(BaseModel):
    ocr_lang: str = "chi_sim+eng"
    tesseract_path: str = ""
    use_cloud_ocr: bool = False
    cloud_api_key: str = ""
    cloud_provider: str = "baidu"


class StorageSettings(BaseModel):
    file_size_threshold_mb: int = 1
    auto_cleanup: bool = True
    cleanup_days: int = 30


# ── 端点 ──

@router.get("")
def get_settings():
    """获取所有设置项"""
    user = _load_user_settings()
    return {
        "ocr": {
            "lang": user.get("ocr_lang", "chi_sim+eng"),
            "tesseract_path": user.get("tesseract_path", ""),
            "use_cloud": user.get("use_cloud_ocr", False),
            "cloud_api_key": user.get("cloud_api_key", ""),
            "cloud_provider": user.get("cloud_provider", "baidu"),
        },
        "storage": {
            "upload_path": str(app_settings.upload_dir_path),
            "file_size_threshold_mb": user.get(
                "file_size_threshold_mb", app_settings.STORAGE_THRESHOLD_MB
            ),
            "auto_cleanup": user.get("auto_cleanup", True),
            "cleanup_days": user.get("cleanup_days", 30),
        },
        "app": {
            "version": app_settings.APP_VERSION,
            "title": app_settings.APP_TITLE,
        },
    }


@router.put("/ocr")
def save_ocr_settings(data: OcrSettings):
    """保存 OCR 设置"""
    user = _load_user_settings()
    user["ocr_lang"] = data.ocr_lang
    user["tesseract_path"] = data.tesseract_path
    user["use_cloud_ocr"] = data.use_cloud_ocr
    user["cloud_api_key"] = data.cloud_api_key
    user["cloud_provider"] = data.cloud_provider
    _save_user_settings(user)
    return {"message": "OCR 设置已保存", "data": data.model_dump()}


@router.put("/storage")
def save_storage_settings(data: StorageSettings):
    """保存存储设置"""
    user = _load_user_settings()
    user["file_size_threshold_mb"] = data.file_size_threshold_mb
    user["auto_cleanup"] = data.auto_cleanup
    user["cleanup_days"] = data.cleanup_days
    _save_user_settings(user)
    return {"message": "存储设置已保存", "data": data.model_dump()}


@router.post("/backup", dependencies=[Depends(require_admin)])
def backup_database():
    """备份 SQLite 数据库，返回 .db 文件下载"""
    # 定位数据库文件
    db_url = app_settings.database_url
    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url[10:])  # 去掉 sqlite:/// 前缀
    else:
        raise HTTPException(status_code=500, detail="仅支持 SQLite 数据库备份")

    if not db_path.exists():
        raise HTTPException(status_code=404, detail="数据库文件不存在")

    # 复制到临时位置
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"invoice_backup_{timestamp}.db"
    backup_dir = _get_data_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / backup_name
    shutil.copy2(db_path, backup_path)

    return FileResponse(
        path=str(backup_path),
        filename=backup_name,
        media_type="application/octet-stream",
    )


@router.post("/reset", dependencies=[Depends(require_admin)])
def reset_database():
    """清空数据库并重新初始化"""
    try:
        # 关闭所有连接
        SessionLocal.close_all()
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        # 重新创建
        Base.metadata.create_all(bind=engine)
        # 重新插入种子数据
        seed_default_categories()
        return {"message": "数据库已重置"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库重置失败: {e!s}") from e
