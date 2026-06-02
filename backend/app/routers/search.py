"""全局搜索 API 路由"""

import re
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_

from ..database import get_db
from ..models.invoice import Invoice, Counterpart

router = APIRouter(prefix="/api", tags=["搜索"])


def _highlight_snippet(text: Optional[str], keyword: str, max_len: int = 60) -> Optional[str]:
    """从文本中提取包含关键词的片段，并用 <mark> 标签高亮"""
    if not text:
        return None

    # 不区分大小写查找
    idx = text.lower().find(keyword.lower())
    if idx == -1:
        return None

    # 截取关键词前后各 max_len/2 字符
    half = max_len // 2
    start = max(0, idx - half)
    end = min(len(text), idx + len(keyword) + half)

    snippet = text[start:end]
    # 如果有截断，加省略号
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""

    # 高亮关键词（保留原始大小写）
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<mark>{m.group()}</mark>", snippet)

    return f"{prefix}{highlighted}{suffix}"


def _match_fields(invoice, keyword: str) -> List[dict]:
    """检查发票在哪些字段上匹配关键词，返回匹配信息列表"""
    matches = []
    keyword_lower = keyword.lower()

    # 按优先级排列的字段列表
    fields = [
        ("invoice_number", "发票号码", invoice.invoice_number, 10),
        ("invoice_code", "发票代码", invoice.invoice_code, 9),
        ("check_code", "校验码", invoice.check_code, 8),
        ("remark", "备注", invoice.remark, 6),
        ("raw_text", "OCR原文", invoice.raw_text, 5),
    ]

    for field_key, field_label, field_value, priority in fields:
        if field_value and keyword_lower in field_value.lower():
            snippet = _highlight_snippet(str(field_value), keyword)
            matches.append({
                "field": field_key,
                "label": field_label,
                "snippet": snippet,
                "priority": priority,
            })

    # 对方单位名称
    if invoice.counterpart and invoice.counterpart.name:
        if keyword_lower in invoice.counterpart.name.lower():
            snippet = _highlight_snippet(invoice.counterpart.name, keyword)
            matches.append({
                "field": "counterpart",
                "label": "对方单位",
                "snippet": snippet,
                "priority": 7,
            })

    # 按优先级降序排列
    matches.sort(key=lambda m: m["priority"], reverse=True)
    return matches


@router.get("/search")
def global_search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(20, ge=1, le=50, description="最大返回数量"),
    db: Session = Depends(get_db),
):
    """全局搜索发票

    搜索范围：
    - 发票号码、发票代码、校验码
    - 对方单位名称
    - 备注、OCR 原始文本

    返回结果包含匹配字段和高亮片段。
    """
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    # JOIN counterpart 以支持按单位名称搜索
    query = db.query(Invoice).options(
        selectinload(Invoice.counterpart),
        selectinload(Invoice.category),
    ).outerjoin(Counterpart, Invoice.counterpart_id == Counterpart.id)

    query = query.filter(
        or_(
            Invoice.invoice_number.like(f"%{escaped}%", escape="\\"),
            Invoice.invoice_code.like(f"%{escaped}%", escape="\\"),
            Invoice.remark.like(f"%{escaped}%", escape="\\"),
            Invoice.raw_text.like(f"%{escaped}%", escape="\\"),
            Invoice.check_code.like(f"%{escaped}%", escape="\\"),
            Counterpart.name.like(f"%{escaped}%", escape="\\"),
        )
    )

    total = query.count()
    invoices = query.order_by(Invoice.invoice_date.desc()).limit(limit).all()

    results = []
    for inv in invoices:
        matches = _match_fields(inv, q)
        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_code": inv.invoice_code,
            "invoice_type": inv.invoice_type,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "total_with_tax": inv.total_with_tax,
            "is_reimbursed": inv.is_reimbursed,
            "counterpart": {
                "id": inv.counterpart.id if inv.counterpart else None,
                "name": inv.counterpart.name if inv.counterpart else None,
            },
            "category": {
                "id": inv.category.id if inv.category else None,
                "name": inv.category.name if inv.category else None,
            },
            "matches": matches,  # 匹配字段 + 高亮片段
        })

    return {
        "query": q,
        "total": total,
        "shown": len(results),
        "items": results,
    }
