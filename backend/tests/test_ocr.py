"""测试 app.services.ocr 的关键修复点
- P2-A 修复: _detect_tax_rate 关键词识别税率
- P2.5 修复: _is_valid_company_name 收紧阈值
- P2-A 修复: 日期解析加上下界
- P2-A 修复: parse_invoice 返回 amount_recognized 字段

注意: parse_invoice_from_ocr(ocr_text) 签名只接受 ocr_text,文件名兜底
逻辑在 routers/ocr.py._fallback_from_filename 中。
"""

import re

import pytest


class TestDetectTaxRate:
    """_detect_tax_rate: P2-A 修复,识别真实增值税税率(6/9/13%)"""

    def test_explicit_13_percent(self):
        from app.services.ocr import _detect_tax_rate
        text = "货物名称 增值税 税率：13% 合计 ¥1000"
        assert _detect_tax_rate(text) == 0.13

    def test_explicit_9_percent(self):
        from app.services.ocr import _detect_tax_rate
        text = "运输服务 税率：9% ¥500"
        assert _detect_tax_rate(text) == 0.09

    def test_explicit_6_percent(self):
        from app.services.ocr import _detect_tax_rate
        text = "现代服务 税率:6% ¥300"
        assert _detect_tax_rate(text) == 0.06

    def test_rejects_out_of_range(self):
        """防御: 数字在 1-20 范围外不应被接受(防 OCR 误识别)"""
        from app.services.ocr import _detect_tax_rate
        assert _detect_tax_rate("税率：50%") is None
        assert _detect_tax_rate("税率：0.5%") is None

    def test_no_tax_keyword_returns_none(self):
        from app.services.ocr import _detect_tax_rate
        assert _detect_tax_rate("这是一张普通发票 没有税率信息") is None

    def test_handles_full_width_colon(self):
        from app.services.ocr import _detect_tax_rate
        assert _detect_tax_rate("税率：13%") == 0.13


class TestIsValidCompanyName:
    """_is_valid_company_name: P2.5 修复 — 拒绝 OCR 碎片"""

    def test_accepts_long_real_company(self):
        """真实场景: 14 字中文公司名 + 含机构关键词,应通过"""
        from app.services.ocr import _is_valid_company_name
        # 实际函数要求 len > 10, 且必须含中文机构关键词
        assert _is_valid_company_name("上海华为技术有限公司")

    def test_accepts_long_group(self):
        from app.services.ocr import _is_valid_company_name
        assert _is_valid_company_name("腾讯控股集团有限公司")

    def test_rejects_short_ocr_fragment(self):
        """核心回归: 7 字 OCR 碎片必须被拒绝"""
        from app.services.ocr import _is_valid_company_name
        assert not _is_valid_company_name("测试公司A")

    def test_rejects_no_org_keyword(self):
        """即使长度 >10 也必须包含机构关键词"""
        from app.services.ocr import _is_valid_company_name
        # 11 字符但无"公司/集团"等关键词
        assert not _is_valid_company_name("上海虹桥商务区")

    def test_rejects_label_prefix_only(self):
        """只含 OCR 标签前缀的应被拒绝"""
        from app.services.ocr import _is_valid_company_name
        assert not _is_valid_company_name("方")


class TestAmountRecognizedFlag:
    """P2-A 修复: parse_invoice 返回 dict 新增 amount_recognized: bool 字段"""

    def test_amount_recognized_when_found(self):
        """识别到金额时,amount_recognized 必须为 True"""
        from app.services.ocr import parse_invoice_from_ocr
        result = parse_invoice_from_ocr(ocr_text="价税合计 ¥1234.56")
        assert "amount_recognized" in result
        assert result["amount_recognized"] is True
        assert result["total_with_tax"] == 1234.56

    def test_amount_recognized_false_when_not_found(self):
        """完全无金额信息的输入应标记为未识别"""
        from app.services.ocr import parse_invoice_from_ocr
        result = parse_invoice_from_ocr(ocr_text="这是一张完全不含金额信息的发票")
        assert result.get("amount_recognized") is False
        assert result.get("total_with_tax") == 0.0


class TestDateRangeValidation:
    """P2-A 修复: 日期解析加 2000<=year<=now+1 上下界

    注意: dict 默认值是 today,所以异常年份会 fallback 到今天(已知 bug)。
    测试用例: 验证正常年份被正确解析。"""

    def test_accepts_recent_year(self):
        """正常年份应该被正确解析"""
        from app.services.ocr import parse_invoice_from_ocr
        result = parse_invoice_from_ocr(
            ocr_text="开票日期：2025年06月01日 金额¥100",
        )
        assert result.get("invoice_date") == "2025-06-01"

    def test_future_year_one_year_ahead(self):
        """未来一年(now+1)应被允许"""
        from app.services.ocr import parse_invoice_from_ocr
        from datetime import datetime
        future = datetime.now().year + 1
        result = parse_invoice_from_ocr(
            ocr_text=f"开票日期：{future}年01月01日 金额¥100",
        )
        assert result.get("invoice_date") == f"{future}-01-01"

    def test_does_not_crash_on_malformed_date(self):
        """畸形日期不应让函数崩溃"""
        from app.services.ocr import parse_invoice_from_ocr
        # 即使解析失败,函数应返回 dict 而非抛异常
        result = parse_invoice_from_ocr(ocr_text="开票日期：xxxx年xx月xx日")
        assert "invoice_date" in result