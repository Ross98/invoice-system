"""回归测试: 防止 upload_invoice_file 无限递归

历史 BUG: Phase 2 修复时,router/invoices.py 同时:
- import 了 services.upload_invoice_file (本意用作实际存储)
- 在 router 内定义了同名函数 upload_invoice_file (FastAPI endpoint)

Python 解析后,本地 def 覆盖了 import,所以 router 内的 upload_invoice_file
在第 239 行调用同名函数时实际调用自己 = 无限递归 = RecursionError。

修复: services 的版本改名为 stream_upload,router import 改名后调用。

本测试断言 router 的 upload 端点不会无限递归,且会正确调用 stream_upload。
"""

from unittest.mock import MagicMock, patch

import pytest


class TestUploadEndpointNoInfiniteRecursion:
    """核心回归测试: router upload_invoice_file 不能递归调用自己"""

    def test_router_upload_does_not_recurse_into_self(self):
        """如果 router 再次陷入无限递归,本测试会触发 RecursionError"""
        from app.routers import invoices

        assert hasattr(invoices, "upload_invoice_file"), (
            "router.upload_invoice_file 必须存在"
        )

        captured = {}

        def fake_stream_upload(fp, file_name, invoice_id, max_bytes):
            captured["called"] = True
            return ("blob", 100, None, "aGVsbG8=")

        with patch.object(invoices, "stream_upload", fake_stream_upload):
            fake_invoice = MagicMock(id=1)
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = (
                fake_invoice
            )

            upload_file = MagicMock()
            upload_file.filename = "test.pdf"
            upload_file.file.read.side_effect = [
                b"%PDF-1.4\n",
                b"%PDF-1.4\nfake content",
            ]

            try:
                invoices.upload_invoice_file(
                    invoice_id=1,
                    file=upload_file,
                    db=mock_db,
                )
            except RecursionError:
                pytest.fail(
                    "router.upload_invoice_file 陷入无限递归! "
                    "Phase 2 修复可能未正确拆分 services 与 router 的同名函数"
                )
            except Exception:
                # 其他异常可接受 (db.commit mock 失败等)
                pass

        assert captured.get("called"), (
            "stream_upload 应被 router 调用,而非 router 内部递归"
        )

    def test_services_exposes_stream_upload_not_upload_invoice_file(self):
        """services 不应再有 upload_invoice_file (那是 router 的 endpoint 名字)"""
        from app.services import file_storage

        assert hasattr(file_storage, "stream_upload"), (
            "services 必须暴露 stream_upload"
        )
        # 旧名字不应再存在,避免与 router endpoint 冲突
        assert not hasattr(file_storage, "upload_invoice_file"), (
            "services.upload_invoice_file 已删除 — 它与 router 同名会引发无限递归"
        )