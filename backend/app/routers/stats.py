"""统计汇总 API 路由"""

from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.invoice import Category, Counterpart, Invoice

router = APIRouter(prefix="/api/stats", tags=["统计汇总"])


@router.get("/dashboard")
def get_dashboard_stats(
    year: int | None = Query(None),
    month: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """获取仪表盘汇总数据"""
    now = datetime.now()
    y = year or now.year
    m = month or now.month

    month_start = date(y, m, 1)
    if m == 12:
        month_end = date(y + 1, 1, 1)
    else:
        month_end = date(y, m + 1, 1)

    # --- 本月统计 ---
    month_q = db.query(Invoice).filter(
        Invoice.invoice_date >= month_start,
        Invoice.invoice_date < month_end,
    )
    month_total = month_q.count()
    month_amount = month_q.with_entities(
        func.coalesce(func.sum(Invoice.total_with_tax), 0)
    ).scalar() or 0
    month_tax = month_q.filter(Invoice.tax_amount.isnot(None)).with_entities(
        func.coalesce(func.sum(Invoice.tax_amount), 0)
    ).scalar() or 0
    month_reimbursed = month_q.filter(Invoice.is_reimbursed).count()
    month_pending = month_total - month_reimbursed

    # --- 全部累计 ---
    total_count = db.query(Invoice).count()
    total_amount = db.query(
        func.coalesce(func.sum(Invoice.total_with_tax), 0)
    ).scalar() or 0
    total_reimbursed = db.query(Invoice).filter(
        Invoice.is_reimbursed
    ).count()

    # --- 全年统计 ---
    year_start = date(y, 1, 1)
    year_end = date(y + 1, 1, 1)
    year_amount = db.query(Invoice).filter(
        Invoice.invoice_date >= year_start,
        Invoice.invoice_date < year_end,
    ).with_entities(
        func.coalesce(func.sum(Invoice.total_with_tax), 0)
    ).scalar() or 0

    # --- 月度趋势（过去12个月） ---
    trend_data = []
    for i in range(11, -1, -1):
        dt = now - relativedelta(months=i)
        sm = date(dt.year, dt.month, 1)
        if dt.month == 12:
            em = date(dt.year + 1, 1, 1)
        else:
            em = date(dt.year, dt.month + 1, 1)

        count = db.query(Invoice).filter(
            Invoice.invoice_date >= sm, Invoice.invoice_date < em
        ).count()
        amount = db.query(Invoice).filter(
            Invoice.invoice_date >= sm, Invoice.invoice_date < em
        ).with_entities(
            func.coalesce(func.sum(Invoice.total_with_tax), 0)
        ).scalar() or 0

        trend_data.append({
            "year": dt.year,
            "month": dt.month,
            "label": f"{dt.month}月",
            "count": count,
            "amount": round(float(amount), 2),
        })

    # --- 分类占比 ---
    cat_rows = db.query(
        Category.name,
        func.coalesce(func.sum(Invoice.total_with_tax), 0).label("total"),
        func.count(Invoice.id).label("cnt"),
    ).outerjoin(Invoice, Invoice.category_id == Category.id).filter(
        Invoice.invoice_date >= year_start,
        Invoice.invoice_date < year_end,
    ).group_by(Category.id, Category.name).order_by(func.sum(Invoice.total_with_tax).desc()).all()

    category_dist = []
    for name, total, cnt in cat_rows:
        if not name:
            name = "其他"
        category_dist.append({
            "name": name,
            "amount": round(float(total), 2),
            "count": cnt,
        })

    # --- Top 消费单位 ---
    top_rows = db.query(
        Counterpart.name,
        func.coalesce(func.sum(Invoice.total_with_tax), 0).label("total"),
        func.count(Invoice.id).label("cnt"),
    ).join(Invoice, Invoice.counterpart_id == Counterpart.id).filter(
        Invoice.invoice_date >= year_start,
        Invoice.invoice_date < year_end,
    ).group_by(Counterpart.id, Counterpart.name).order_by(func.sum(Invoice.total_with_tax).desc()).limit(5).all()

    top_counterparts = []
    for name, total, cnt in top_rows:
        if not name:
            name = "未知"
        top_counterparts.append({
            "name": name,
            "amount": round(float(total), 2),
            "count": cnt,
        })

    # --- 最近发票（前5条） ---
    recent_query = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(5)
    recent = []
    for inv in recent_query:
        recent.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "invoice_date": str(inv.invoice_date) if inv.invoice_date else None,
            "total_with_tax": inv.total_with_tax,
            "invoice_type": inv.invoice_type,
            "is_reimbursed": inv.is_reimbursed,
        })

    return {
        "month": {
            "year": y,
            "month": m,
            "total_count": month_total,
            "total_amount": round(float(month_amount), 2),
            "total_tax": round(float(month_tax), 2),
            "reimbursed_count": month_reimbursed,
            "pending_count": month_pending,
        },
        "overall": {
            "total_count": total_count,
            "total_amount": round(float(total_amount), 2),
            "total_reimbursed": total_reimbursed,
        },
        "year": {
            "year": y,
            "total_amount": round(float(year_amount), 2),
        },
        "monthly_trend": trend_data,
        "category_distribution": category_dist,
        "top_counterparts": top_counterparts,
        "recent_invoices": recent,
    }
