"""测试 app.services.file_storage 的关键修复点
- BUG #4 修复: _detect_mime 通过文件头魔数嗅探
- BUG #3 修复: _stream_to_destination 流式分块 + max_bytes 上限
- BUG #2 修复: delete_file 对 BLOB 模式清空字段
"""

import base64
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


class TestDetectMime:
    """_detect_mime: 文件头魔数嗅探,防扩展名伪造"""

    def test_detects_pdf_magic(self):
        from app.services.file_storage import _detect_mime
        assert _detect_mime(b"%PDF-1.4\n...") == "application/pdf"

    def test_detects_png_magic(self):
        from app.services.file_storage import _detect_mime
        png_head = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        assert _detect_mime(png_head) == "image/png"

    def test_detects_jpeg_magic(self):
        from app.services.file_storage import _detect_mime
        assert _detect_mime(b"\xff\xd8\xff\xe0\x00\x10JFIF") == "image/jpeg"

    def test_rejects_executable(self):
        """核心安全测试: Windows .exe MZ 头必须被拒绝"""
        from app.services.file_storage import _detect_mime
        exe_head = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 8
        assert _detect_mime(exe_head) is None

    def test_rejects_elf_executable(self):
        """Linux ELF 也必须被拒绝"""
        from app.services.file_storage import _detect_mime
        elf_head = b"\x7fELF\x02\x01\x01" + b"\x00" * 8
        assert _detect_mime(elf_head) is None

    def test_rejects_empty_input(self):
        from app.services.file_storage import _detect_mime
        assert _detect_mime(b"") is None

    def test_rejects_random_bytes(self):
        from app.services.file_storage import _detect_mime
        assert _detect_mime(b"random plain text content") is None


class TestStreamToDestination:
    """_stream_to_destination: 流式分块 + max_bytes 强制上限"""

    def test_small_file_uses_blob(self):
        """小文件(< threshold) 走 BLOB 模式"""
        from app.services.file_storage import _stream_to_destination
        fp = MagicMock()
        fp.read.side_effect = [b"x" * 100, b""]
        mode, size, path, blob = _stream_to_destination(fp, 999, "t.pdf", 1024 * 1024)
        assert mode == "blob"
        assert size == 100
        assert path is None
        assert blob is not None
        decoded = base64.b64decode(blob)
        assert decoded == b"x" * 100

    def test_oversized_file_raises_413(self):
        """核心修复点: 超 max_bytes 必须 413 而非 OOM"""
        from app.services.file_storage import _stream_to_destination
        fp = MagicMock()
        # 第一个 chunk 就超 100 字节
        fp.read.side_effect = [b"x" * 200, b""]
        with pytest.raises(HTTPException) as exc:
            _stream_to_destination(fp, 999, "huge.pdf", 100)
        assert exc.value.status_code == 413

    def test_streaming_uses_chunks(self):
        """确认使用 CHUNK_SIZE 分块,非一次性 read"""
        from app.services.file_storage import CHUNK_SIZE, _stream_to_destination
        fp = MagicMock()
        # 模拟 3 个 CHUNK + 终止空 chunk
        fp.read.side_effect = [b"a" * CHUNK_SIZE, b"b" * CHUNK_SIZE, b"c" * 100, b""]
        mode, size, path, blob = _stream_to_destination(fp, 999, "big.bin", 100 * 1024 * 1024)
        # 调用了 4 次 read (3 数据 + 1 空终止)
        assert fp.read.call_count == 4
        assert size == CHUNK_SIZE * 2 + 100


class TestDeleteFile:
    """delete_file: P0 修复点 — BLOB 模式必须清空 DB 字段"""

    def test_blob_mode_clears_fields(self):
        """核心回归测试: 删 BLOB 模式文件后,blob_data/file_size/file_path 必须清空"""
        from app.services.file_storage import delete_file

        fake_file = MagicMock()
        fake_file.storage_mode = "blob"
        fake_file.blob_data = "aGVsbG8="
        fake_file.file_size = 1234
        fake_file.file_path = None

        delete_file(fake_file)

        assert fake_file.blob_data is None
        assert fake_file.file_size == 0
        assert fake_file.file_path is None

    def test_path_mode_deletes_disk_file(self, tmp_path):
        from app.services.file_storage import delete_file

        target = tmp_path / "test.pdf"
        target.write_bytes(b"content")
        assert target.exists()

        fake_file = MagicMock()
        fake_file.storage_mode = "path"
        fake_file.file_path = str(target)

        delete_file(fake_file)
        assert not target.exists()

    def test_path_mode_handles_missing_file(self):
        """不存在的文件应静默处理,不抛错"""
        from app.services.file_storage import delete_file

        fake_file = MagicMock()
        fake_file.storage_mode = "path"
        fake_file.file_path = "/nonexistent/path/foo.pdf"

        # 不应抛异常
        delete_file(fake_file)