"""测试 app.schemas.invoice 的关键修复点
- BUG #9 修复: InvoiceResponse 排除 raw_text
- BUG #12 修复: InvoiceCreate 拒绝 is_reimbursed=True
- BUG #4 修复: InvoiceFileCreate 排除 file_path/blob_data
"""

import pytest
from pydantic import ValidationError


def _make_invoice_response(**overrides):
    """构造一个合法 InvoiceResponse,带最小必填字段"""
    from app.schemas.invoice import InvoiceResponse
    base = dict(
        id=1,
        invoice_number="12345678",
        invoice_code="",
        invoice_type="vat_special",
        invoice_date="2025-06-01",
        created_at="2025-06-01T00:00:00",
        updated_at="2025-06-01T00:00:00",
    )
    base.update(overrides)
    return InvoiceResponse(**base)


class TestInvoiceResponseExcludesRawText:
    """对外 API 响应绝对不能含 raw_text (OCR 原文,含购方税号等敏感数据)"""

    def test_raw_text_excluded_from_dump(self):
        """核心: raw_text 即使传入也必须被 exclude,不出现在 dump 中"""
        resp = _make_invoice_response(
            raw_text="SENSITIVE: 购方税号 91110000123456789X",
        )
        data = resp.model_dump()
        assert "raw_text" not in data
        assert "SENSITIVE" not in str(data)

    def test_raw_text_excluded_from_json(self):
        resp = _make_invoice_response(raw_text="SENSITIVE")
        json_str = resp.model_dump_json()
        assert "raw_text" not in json_str
        assert "SENSITIVE" not in json_str


class TestInvoiceCreateRejectsReimbursed:
    """Phase 2.5 修复: 创建发票时禁止直接设置 is_reimbursed=True (绕过报销流程)"""

    def test_rejects_reimbursed_true(self):
        from app.schemas.invoice import InvoiceCreate
        with pytest.raises(ValidationError) as exc:
            InvoiceCreate(
                invoice_number="11111111",
                invoice_code="",
                invoice_type="vat_special",
                invoice_date="2025-06-01",
                is_reimbursed=True,
            )
        assert "is_reimbursed" in str(exc.value)

    def test_accepts_reimbursed_false(self):
        from app.schemas.invoice import InvoiceCreate
        inv = InvoiceCreate(
            invoice_number="11111111",
            invoice_code="",
            invoice_type="vat_special",
            invoice_date="2025-06-01",
            is_reimbursed=False,
        )
        assert inv.is_reimbursed is False

    def test_defaults_to_false(self):
        from app.schemas.invoice import InvoiceCreate
        inv = InvoiceCreate(
            invoice_number="11111111",
            invoice_code="",
            invoice_type="vat_special",
            invoice_date="2025-06-01",
        )
        assert inv.is_reimbursed is False


class TestInvoiceFileCreateExcludesInternalFields:
    """Phase 2.5 修复: file_path/blob_data 禁止外部构造 (防路径遍历/BLOB 注入)"""

    def test_file_path_excluded_from_dump(self):
        from app.schemas.invoice import InvoiceFileCreate
        fc = InvoiceFileCreate(
            file_name="invoice.pdf",
            file_type="application/pdf",
            file_size=1024,
            storage_mode="path",
            file_path="/etc/passwd",
        )
        data = fc.model_dump()
        assert "file_path" not in data

    def test_blob_data_excluded_from_dump(self):
        from app.schemas.invoice import InvoiceFileCreate
        fc = InvoiceFileCreate(
            file_name="invoice.pdf",
            file_type="application/pdf",
            file_size=1024,
            storage_mode="blob",
            blob_data="aGVsbG8=",
        )
        data = fc.model_dump()
        assert "blob_data" not in data

    def test_required_fields_present(self):
        """确认对外字段正常序列化"""
        from app.schemas.invoice import InvoiceFileCreate
        fc = InvoiceFileCreate(
            file_name="invoice.pdf",
            file_type="application/pdf",
            file_size=2048,
            storage_mode="blob",
        )
        data = fc.model_dump()
        assert data["file_name"] == "invoice.pdf"
        assert data["storage_mode"] == "blob"
        assert data["file_size"] == 2048


class TestInvoiceFileResponseSchema:
    """对外响应不暴露 file_path/storage_mode"""

    def test_response_has_no_file_path(self):
        from app.schemas.invoice import InvoiceFileResponse
        from types import SimpleNamespace

        fake = SimpleNamespace(
            id=1,
            invoice_id=1,
            file_name="x.pdf",
            file_type="application/pdf",
            file_size=100,
            uploaded_at="2025-06-01T00:00:00",
            file_path="/secret/path",  # 必须被排除
            storage_mode="blob",       # 必须被排除
        )
        resp = InvoiceFileResponse.model_validate(fake)
        data = resp.model_dump()
        assert "file_path" not in data
        assert "storage_mode" not in data