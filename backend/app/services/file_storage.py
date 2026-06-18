"""文件存储服务 - 混合存储策略（本地路径 + 数据库 BLOB）"""

import base64
import contextlib
from pathlib import Path
from typing import IO, TYPE_CHECKING

from ..config import settings

if TYPE_CHECKING:
    from ..models.invoice import InvoiceFile

# 流式写入块大小（1MB），避免大文件一次性读入内存
CHUNK_SIZE = 1024 * 1024
# MIME 嗅探所需的最大魔数长度
MAGIC_LEN = 16

# 合法魔数 → MIME 映射（覆盖白名单中的 PDF / PNG / JPEG）
_MAGIC_TABLE: list[tuple[bytes, str]] = [
    (b"%PDF-", "application/pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
]

# 合法 MIME → 允许的文件后缀集合
_MIME_TO_EXTS: dict[str, set[str]] = {
    "application/pdf": {"pdf"},
    "image/png": {"png"},
    "image/jpeg": {"jpg", "jpeg"},
}


def _detect_mime(content_head: bytes) -> str | None:
    """根据文件头魔数嗅探 MIME，未匹配返回 None"""
    for magic, mime in _MAGIC_TABLE:
        if content_head.startswith(magic):
            return mime
    return None


def _stream_to_destination(
    fp: IO[bytes], invoice_id: int, file_name: str, max_bytes: int
) -> tuple[str, int, str | None, str | None]:
    """
    流式读取 fp 写入存储后端，超出 max_bytes 抛 HTTPException(413)。

    始终先按 CHUNK_SIZE 读取到内存缓冲（用于小文件 BLOB 编码），
    若累计超过 storage_threshold_bytes 则改为边读边写磁盘。
    返回 (storage_mode, file_size, file_path, blob_data)。
    """
    from fastapi import HTTPException  # 延迟导入，避免 service 层强依赖 fastapi

    threshold = settings.storage_threshold_bytes
    buf = bytearray()
    total = 0
    disk_path: Path | None = None
    out_fp: IO[bytes] | None = None
    promoted_to_disk = False

    try:
        while True:
            chunk = fp.read(CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=413, detail="文件超过限制")
            # 超过阈值时，从内存切到磁盘流式写入
            if not promoted_to_disk and total > threshold:
                upload_dir = settings.upload_dir_path / str(invoice_id)
                upload_dir.mkdir(parents=True, exist_ok=True)
                unique_name = f"{invoice_id}_{Path(file_name).name}"
                disk_path = upload_dir / unique_name
                out_fp = disk_path.open("wb")
                # 把已积累的 buf 落盘
                out_fp.write(bytes(buf))
                buf.clear()
                promoted_to_disk = True
            if promoted_to_disk and out_fp is not None:
                out_fp.write(chunk)
            else:
                buf.extend(chunk)
    finally:
        if out_fp is not None:
            out_fp.close()

    if promoted_to_disk and disk_path is not None:
        return "path", total, str(disk_path.absolute()), None

    blob_data = base64.b64encode(bytes(buf)).decode("utf-8")
    return "blob", total, None, blob_data


def stream_upload(
    fp: IO[bytes], file_name: str, invoice_id: int, max_bytes: int
) -> tuple[str, int, str | None, str | None]:
    """流式上传入口：使用 CHUNK_SIZE 分块写入,强制 max_bytes 上限。

    返回 (storage_mode, file_size, file_path, blob_data)。
    超出 max_bytes 时由内部 _stream_to_destination 抛 HTTPException(413)。
    """
    return _stream_to_destination(fp, invoice_id, file_name, max_bytes)


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


def delete_file(file: "InvoiceFile") -> None:
    """删除文件：path 模式清理磁盘；blob 模式清空 DB 中 BLOB 字段以释放空间"""
    if file.storage_mode == "path" and file.file_path:
        path = Path(file.file_path)
        if path.exists():
            path.unlink()

            # 尝试删除空目录
            with contextlib.suppress(OSError):
                path.parent.rmdir()  # 目录非空，不删除
    elif file.storage_mode == "blob":
        # 清空 BLOB 相关字段,防止数据库持续膨胀
        file.blob_data = None
        file.file_size = 0
        file.file_path = None


def get_file_url(storage_mode: str, invoice_id: int, file_id: int, file_name: str) -> str:
    """获取文件的访问 URL"""
    if storage_mode == "blob":
        return f"/api/invoices/{invoice_id}/files/{file_id}/download"
    else:
        return f"/api/invoices/{invoice_id}/files/{file_id}/download"
