"""文件存储服务 - 混合存储策略（本地路径 + 数据库 BLOB）"""

import base64
import contextlib
from pathlib import Path

from ..config import settings


def store_file(file_content: bytes, file_name: str, invoice_id: int) -> tuple[str, str | None, str | None]:
    """
    存储文件，根据大小选择存储方式

    返回: (storage_mode, file_path, blob_data)
    """
    file_size = len(file_content)

    if file_size < settings.storage_threshold_bytes:
        # 小文件存数据库 BLOB
        blob_data = base64.b64encode(file_content).decode("utf-8")
        return "blob", None, blob_data
    else:
        # 大文件存本地
        upload_dir = settings.upload_dir_path / str(invoice_id)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        unique_name = f"{invoice_id}_{Path(file_name).name}"
        file_path = upload_dir / unique_name

        # 写入文件
        file_path.write_bytes(file_content)

        return "path", str(file_path.absolute()), None


def retrieve_file(storage_mode: str, file_path: str | None, blob_data: str | None) -> bytes:
    """根据存储方式读取文件内容"""
    if storage_mode == "blob" and blob_data:
        return base64.b64decode(blob_data)
    elif storage_mode == "path" and file_path:
        return Path(file_path).read_bytes()
    else:
        raise ValueError(f"无效的存储方式: {storage_mode}")


def delete_file(storage_mode: str, file_path: str | None) -> None:
    """删除文件（仅对 path 模式有效）"""
    if storage_mode == "path" and file_path:
        path = Path(file_path)
        if path.exists():
            path.unlink()

            # 尝试删除空目录
            with contextlib.suppress(OSError):
                path.parent.rmdir()  # 目录非空，不删除


def get_file_url(storage_mode: str, invoice_id: int, file_id: int, file_name: str) -> str:
    """获取文件的访问 URL"""
    if storage_mode == "blob":
        return f"/api/invoices/{invoice_id}/files/{file_id}/download"
    else:
        return f"/api/invoices/{invoice_id}/files/{file_id}/download"
