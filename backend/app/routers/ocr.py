"""OCR 相关 API 路由"""

from datetime import datetime
from pathlib import Path
import tempfile
import traceback

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.invoice import Counterpart, Invoice, InvoiceDetail
from ..schemas.invoice import InvoiceCreate
from ..services.ocr import is_available, ocr_image, ocr_pdf, parse_invoice_from_ocr

router = APIRouter(prefix="/api/ocr", tags=["OCR"])


def _fallback_from_filename(filename: str, parsed: dict, ocr_text: str) -> None:
    """从文件名兜底提取销方名称和发票号码（OCR 无法识别时使用）"""
    import re as _re

    fname = filename
    if not fname:
        return

    # 去掉扩展名
    fname_noext = _re.sub(r'\.[^.]+$', '', fname)

    # ===== 1. 兜底销方名称 =====
    # 文件名格式通常是：日期_金额_公司名  或  日期_公司名
    # 从文件名中提取中文公司名（4-40个中文字符含括号）
    if not parsed.get("counterpart_name") or parsed["counterpart_name"] in ("", "TAXI", "铁路客票"):
        company_patterns = [
            # 精确：公司/集团/厂/店/行/社 结尾的完整名称
            r'([\u4e00-\u9fff（）()]{2,8}(?:公司|集团|厂|店|行|社|部))',
            # 宽松：较长的中文字符串
            r'([\u4e00-\u9fff（）()]{6,40})',
        ]
        for pat in company_patterns:
            matches = _re.findall(pat, fname_noext)
            for m in matches:
                name = m.strip()
                # 过滤掉明显不是公司名的（如"电子发票"、"增值税"）
                # 但如果包含"公司"或"集团"则一定是公司名，不跳过
                skip_keywords = ["电子发票", "增值税", "普通发票", "专用发票", "出租车发票"]
                if any(kw in name for kw in skip_keywords):
                    continue
                # 如果匹配到的就是关键词本身（出行、运输、铁路等），跳过
                if name in ("出行", "运输", "铁路", "客运", "发票"):
                    continue
                if len(name) >= 4 and ("公司" in name or "集团" in name or len(name) >= 8):
                    parsed["counterpart_name"] = name
                    print(f"[DEBUG] 文件名兜底-销方: {name}", flush=True)
                    break
            if parsed.get("counterpart_name") and parsed["counterpart_name"] not in ("", "TAXI", "铁路客票"):
                break

    # ===== 2. 兜底发票号码 =====
    if not parsed.get("invoice_number"):
        date_match = _re.search(r'(?:^|[_-])(\d{6}|\d{8})(?:[_-]|$)', fname_noext)
        if date_match:
            ds = date_match.group(1)
            if len(ds) == 6:
                ds = "20" + ds
            import hashlib
            fname_hash = hashlib.md5(fname_noext.encode()).hexdigest()[:6].upper()
            parsed["invoice_number"] = f"FN-{ds}-{fname_hash}"
            print(f"[DEBUG] 文件名兜底-发票号码: {parsed['invoice_number']}", flush=True)
        else:
            import hashlib
            fname_hash = hashlib.md5(fname_noext.encode()).hexdigest()[:10].upper()
            parsed["invoice_number"] = f"FN-{fname_hash}"
            print(f"[DEBUG] 文件名兜底-发票号码(无日期): {parsed['invoice_number']}", flush=True)

    # ===== 2.5 兜底发票代码 =====
    # 出租车/铁路等特殊发票类型 OCR 通常识别不出发票代码
    if not parsed.get("invoice_code"):
        invoice_type = parsed.get("invoice_type", "")
        if invoice_type in ("出租车发票", "铁路电子客票"):
            # 用类型前缀 + 日期作为代码
            prefix = "TAXI" if invoice_type == "出租车发票" else "RAIL"
            date_match = _re.search(r'(?:^|[_-])(\d{6}|\d{8})(?:[_-]|$)', fname_noext)
            ds = ""
            if date_match:
                ds = date_match.group(1)
                if len(ds) == 6:
                    ds = "20" + ds
            parsed["invoice_code"] = f"{prefix}-{ds}" if ds else f"{prefix}-NODATE"
            print(f"[DEBUG] 文件名兜底-发票代码: {parsed['invoice_code']}", flush=True)

    # ===== 3. 兜底发票日期（从文件名提取 YYMMDD 或 YYYYMMDD）=====
    if not parsed.get("invoice_date") or parsed["invoice_date"] == "":
        date_match = _re.search(r'(?:^|[_-])(\d{6}|\d{8})(?:[_-]|$)', fname_noext)
        if date_match:
            ds = date_match.group(1)
            try:
                from datetime import datetime as _dt
                if len(ds) == 6:
                    dt = _dt.strptime(ds, "%y%m%d")
                else:
                    dt = _dt.strptime(ds, "%Y%m%d")
                parsed["invoice_date"] = dt.strftime("%Y-%m-%d")
                print(f"[DEBUG] 文件名兜底-日期: {parsed['invoice_date']}", flush=True)
            except (ValueError, KeyError):
                pass


@router.get("/status")
def get_ocr_status():
    """检查 OCR 服务状态"""
    return {
        "available": is_available(),
        "engine": "tesseract" if is_available() else "none",
        "message": "OCR 服务就绪" if is_available() else "Tesseract 未安装",
    }


@router.post("/recognize")
async def recognize_file(
    file: UploadFile = File(...),
    lang: str | None = "chi_sim+eng",
    db: Session = Depends(get_db),
):
    """上传文件进行 OCR 识别，返回识别文本"""
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR 服务不可用。请安装 Tesseract 5.x 并添加中文语言包。"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 保存临时文件
    ext = Path(file.filename).suffix.lower()
    allowed_exts = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 执行 OCR
        if ext == ".pdf":
            text = ocr_pdf(tmp_path, lang)
        else:
            text = ocr_image(tmp_path, lang)

        return {
            "filename": file.filename,
            "text": text,
            "language": lang,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR 识别失败: {e!s}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/recognize/{invoice_id}")
async def recognize_and_associate(
    invoice_id: int,
    file: UploadFile = File(...),
    lang: str | None = "chi_sim+eng",
    db: Session = Depends(get_db),
):
    """上传文件进行 OCR 识别，并关联到指定发票"""
    # 检查发票是否存在
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    # 先上传文件
    from ..routers.invoices import upload_invoice_file
    file_response = await upload_invoice_file(invoice_id, file, db)

    # 执行 OCR
    ocr_result = await recognize_file(file, lang, db)

    return {
        "file": file_response,
        "ocr_result": ocr_result,
        "message": "文件已上传并完成 OCR 识别",
    }


@router.post("/parse")
async def parse_invoice(
    file: UploadFile = File(...),
    lang: str | None = "chi_sim+eng",
    db: Session = Depends(get_db),
):
    """上传文件进行 OCR 识别并解析为结构化发票信息"""
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail="OCR 服务不可用。请安装 Tesseract 5.x 并添加中文语言包。"
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 保存临时文件
    ext = Path(file.filename).suffix.lower()
    allowed_exts = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 执行 OCR
        text = ""

        if ext == ".pdf":
            text = ocr_pdf(tmp_path, lang)
        else:
            text = ocr_image(tmp_path, lang)

        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=422,
                detail="OCR 未能从图片中识别到足够文字。请确保图片清晰、光照均匀，建议使用 300 DPI 以上的扫描件。"
            )

        # 解析为结构化信息
        parsed = parse_invoice_from_ocr(text)

        # 兜底：从文件名提取关键字段（适用于 OCR 无法识别销方/号码的情况）
        _fallback_from_filename(file.filename or "", parsed, text)

        # 兜底：从文件名提取金额（适用于 OCR 无法识别金额的情况）
        if not parsed.get("total_with_tax") or float(parsed.get("total_with_tax", 0)) == 0:
            import re as _re2
            fname = file.filename or ""
            # 先去掉末尾文件扩展名，再按 _ 和 - 切分
            fname_noext = _re2.sub(r'\.[^.]+$', '', fname)
            for part in _re2.split(r'[_-]', fname_noext):
                amt_m = _re2.match(r'^(\d{1,6}(?:\.\d{1,2})?)$', part)
                if amt_m:
                    try:
                        fname_amt = float(amt_m.group(1))
                        # 合理范围且不是 8 位日期
                        if 1 <= fname_amt <= 99999 and not _re2.match(r'^\d{8}$', amt_m.group(1)):
                            parsed["total_with_tax"] = fname_amt
                            parsed["total_amount"] = fname_amt
                            print(f"[DEBUG] 文件名金额兜底: {fname_amt} (from {part!r})", flush=True)
                            break
                    except (ValueError, KeyError):
                        pass

        # 兜底：OCR文本+文件名检测出租车发票
        # 出租车发票 OCR 文字质量差，"出租"关键词常无法识别
        # 改为检测出租车特有字段：电调费、节假日附加费、里程(km)、余额等
        is_taxi = False
        try:
            fname = (file.filename or "")
            is_taxi = any(kw in fname for kw in ["\u51fa\u79df\u8f66", "taxi", "\u51fa\u79df"])
        except Exception:
            pass
        if not is_taxi:
            # OCR 文本特征检测
            taxi_keywords = ["\u542b\u7535\u8c03\u8d39", "\u8282\u5047\u65e5\u9644\u52a0\u8d39", "\u4f59\u989d", "\u91cc\u7a0b", "\u8ba1\u4ef7", "\u6253\u8868", "\u7535\u8c03"]
            is_taxi = any(kw in text for kw in taxi_keywords)

        if is_taxi:
            parsed["invoice_type"] = "\u51fa\u79df\u8f66\u53d1\u7968"
            parsed["counterpart_name"] = "TAXI"
            parsed["invoice_number"] = "TAXI-" + (parsed.get("invoice_date") or datetime.now().strftime("%Y%m%d"))
            print("[DEBUG] taxi-detect: set invoice_type=taxi", flush=True)

        # 兜底：文件名检测铁路电子客票（铁路电子客票 OCR 也常失败）
        is_railway = False
        try:
            fname = (file.filename or "")
            is_railway = any(kw in fname for kw in ["\u94c1\u8def\u7535\u5b50\u5ba2\u7968", "\u94c1\u8def", "\u9ad8\u94c1", "\u706b\u8f66\u7968", "\u52a8\u8f66\u7968"])
        except Exception:
            pass
        if not is_railway:
            railway_keywords = ["\u94c1\u8def\u7535\u5b50\u5ba2\u7968", "\u94c1\u8def", "\u8f66\u6b21", "\u5ea7\u4f4d", "\u53d1\u8f66", "\u5230\u7ad9", "\u4e58\u8f66\u65e5\u671f"]
            is_railway = any(kw in text for kw in railway_keywords)

        if is_railway:
            parsed["invoice_type"] = "\u94c1\u8def\u7535\u5b50\u5ba2\u7968"
            # 铁路客票销方通常是 12306 或铁路局，OCR 识别不出时设为通用值
            if not parsed.get("counterpart_name"):
                parsed["counterpart_name"] = "\u94c1\u8def\u5ba2\u7968"
            if not parsed.get("invoice_number"):
                parsed["invoice_number"] = "RAIL-" + (parsed.get("invoice_date") or datetime.now().strftime("%Y%m%d"))
            print("[DEBUG] railway-detect: set invoice_type=railway", flush=True)

        # 处理销方单位
        counterpart_id = None
        if parsed["counterpart_name"]:
            counterpart = db.query(Counterpart).filter(Counterpart.name == parsed["counterpart_name"]).first()
            if not counterpart:
                counterpart = Counterpart(name=parsed["counterpart_name"])
                db.add(counterpart)
                db.commit()
                db.refresh(counterpart)
            counterpart_id = counterpart.id

        # 构建发票数据
        invoice_data = {
            "invoice_number": parsed.get("invoice_number") or None,  # 空字符串/None 不留 TEMP_
            "invoice_code": parsed["invoice_code"] or "",
            "invoice_type": parsed["invoice_type"],
            "invoice_date": parsed["invoice_date"],
            "total_amount": parsed["total_amount"],
            "tax_amount": parsed["tax_amount"],
            "total_with_tax": parsed["total_with_tax"],
            "check_code": parsed["check_code"],
            "counterpart_id": counterpart_id,
            "raw_text": text,  # 保存 OCR 原始文本用于调试
            "remark": parsed["remark"] or f"OCR识别导入，原始文件: {file.filename}",
            "details": []
        }

        return {
            "filename": file.filename,
            "raw_text": text[:500] + "..." if len(text) > 500 else text,
            "parsed": parsed,
            "invoice_data": invoice_data,
            "message": "OCR识别并解析完成"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] parse_invoice: {e}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发票解析失败: {e!s}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/import")
async def import_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
):
    """导入解析后的发票数据到数据库"""
    import traceback

    from sqlalchemy.exc import IntegrityError

    try:
        # 检查是否已存在相同发票号+发票代码的发票
        existing = db.query(Invoice).filter(
            Invoice.invoice_number == invoice_data.invoice_number,
            Invoice.invoice_code == invoice_data.invoice_code,
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"发票已存在：发票号码 {invoice_data.invoice_number}，发票代码 {invoice_data.invoice_code}"
            )

        # 创建发票
        invoice = Invoice(**invoice_data.model_dump(exclude={"details"}))
        db.add(invoice)

        # 添加明细
        for detail_data in invoice_data.details:
            detail = InvoiceDetail(invoice=invoice, **detail_data.model_dump())
            db.add(detail)

        db.commit()
        db.refresh(invoice)

        return {
            "success": True,
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "message": "发票导入成功"
        }
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"发票已存在（数据库约束）: {str(e.orig) if hasattr(e, 'orig') else str(e)}"
        ) from e
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发票导入失败: {e!s}") from e
