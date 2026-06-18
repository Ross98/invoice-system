"""OCR 服务模块 - 支持本地 Tesseract 和云端 API"""

import contextlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading

from ..config import settings
from ..resource_path import get_poppler_path as _rp_poppler
from ..resource_path import get_tesseract_path as _rp_tesseract

# PDF OCR 并发保护：限制同时处理的 PDF 数量，防止多请求并发触发内存峰值叠加
PDF_SEMAPHORE = threading.Semaphore(2)


def _find_tesseract() -> str | None:
    """查找 tesseract 可执行文件路径（优先 resource_path 统一解析）"""
    # 1. 配置显式指定
    if settings.TESSERACT_PATH and Path(settings.TESSERACT_PATH).exists():
        return settings.TESSERACT_PATH
    # 2. resource_path 统一解析（含打包/开发环境）
    rp = _rp_tesseract()
    if rp:
        return rp
    # 3. PATH
    found = shutil.which("tesseract")
    return found


def _find_poppler() -> str | None:
    """查找 poppler (pdftoppm) 所在目录（优先 resource_path 统一解析）"""
    # 1. 配置显式指定
    if settings.POPPLER_PATH:
        poppler_dir = Path(settings.POPPLER_PATH)
        if poppler_dir.is_dir() and (poppler_dir / "pdftoppm.exe").exists():
            return str(poppler_dir)
    # 2. resource_path 统一解析（含打包/开发环境）
    rp = _rp_poppler()
    if rp:
        return rp
    # 3. PATH
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        return str(Path(pdftoppm).parent)
    return None


def _preprocess_image(image_path: str) -> str:
    """对图片进行预处理（灰度化、增强对比度、二值化），返回预处理后的临时文件路径"""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    with Image.open(image_path) as img:
        # 如果图片太小，放大到合理尺寸（至少宽度 1500px）
        w, h = img.size
        min_width = 1500
        if w < min_width:
            scale = min_width / w
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        # 转灰度
        if img.mode != 'L':
            img = img.convert('L')

        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # 锐化
        img = img.filter(ImageFilter.SHARPEN)

        # 自适应二值化（使用 PIL 的 threshold 方法）
        # 先获取像素直方图，使用大津法自动计算阈值
        try:
            img = ImageOps.autocontrast(img, cutoff=5)
            # 再手动二值化：计算平均值作为阈值
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            threshold = int(avg * 0.85)  # 稍微偏暗
            img = img.point(lambda p: 255 if p > threshold else 0)
        except Exception:
            # 兜底：简单二值化
            img = img.point(lambda p: 255 if p > 127 else 0)

        # 保存到临时文件
        fd, preprocessed_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(preprocessed_path, "PNG")

    return preprocessed_path


def _run_tesseract(image_path: str, lang: str, psm: int | None = None, page_count: int = 1) -> str:
    """调用 Tesseract 执行 OCR

    page_count: 调用方预估的页数/图片数，用于动态调整超时阈值
    """
    tesseract_path = _find_tesseract()
    if not tesseract_path:
        raise RuntimeError(
            "Tesseract 未安装或未找到。请安装 Tesseract 5.x 并添加中文语言包，"
            "或在 .env 中配置 TESSERACT_PATH。"
        )

    # 使用专属临时目录统一管理 tesseract 输出的所有文件（.txt/.tsv/.hocr/.osd/.box）
    tmp_dir = tempfile.mkdtemp(prefix="ocr_tess_")
    out_base = os.path.join(tmp_dir, "out")
    out_path = out_base + ".txt"

    # 动态超时：每页 30s + 60s 基础，最低 120s（兼容 10+ 页高分辨率 PDF）
    timeout = max(120, 60 + page_count * 30)

    try:
        cmd = [tesseract_path, image_path, out_base, "-l", lang]
        if psm is not None:
            cmd.extend(["--psm", str(psm)])

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
        )

        if not os.path.exists(out_path):
            stderr_msg = getattr(result, 'stderr', '').strip() or ''
            raise RuntimeError(f"OCR 输出文件未生成: {stderr_msg}")

        output = Path(out_path).read_text(encoding="utf-8").strip()

        if not output:
            stderr_msg = getattr(result, 'stderr', '').strip() or ''
            raise RuntimeError(f"OCR 识别无结果: {stderr_msg}")

        return output
    finally:
        # 一次性清理整个临时目录中的所有 tesseract 产物（.txt/.tsv/.hocr/.osd/.box）
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ocr_image(image_path: str, lang: str = "chi_sim+eng", page_count: int = 1) -> str:
    """对图片进行 OCR 识别，返回文本结果（含预处理增强）"""

    # 尝试多种 PSM 模式，从最宽松到最优化
    psm_modes = [None, 3, 6]  # None=默认, 3=全自动, 6=统一文本块

    last_error = None

    for psm in psm_modes:
        try:
            # 直接 OCR（不预处理）先试一次
            return _run_tesseract(image_path, lang, psm, page_count=page_count)
        except RuntimeError as e:
            last_error = e
            continue

    # 原始图片 OCR 全部失败，尝试预处理增强
    preprocessed_path = None
    try:
        preprocessed_path = _preprocess_image(image_path)

        for psm in psm_modes:
            try:
                return _run_tesseract(preprocessed_path, lang, psm, page_count=page_count)
            except RuntimeError as e:
                last_error = e
                continue

        raise last_error or RuntimeError("所有 OCR 尝试均失败")
    finally:
        if preprocessed_path and os.path.exists(preprocessed_path):
            with contextlib.suppress(OSError):
                os.unlink(preprocessed_path)


def ocr_pdf(pdf_path: str, lang: str = "chi_sim+eng") -> str:
    """对 PDF 进行 OCR 识别，先将 PDF 转为图片再 OCR"""
    import tempfile

    with PDF_SEMAPHORE:
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise RuntimeError(
                "PDF OCR 需要 pdf2image 库。请运行: pip install pdf2image"
            ) from None

        # 先尝试 pdfplumber 直接提取文本层（对电子发票 PDF 通常有文本层）
        pdf_text = _extract_pdf_text_layer(pdf_path, "")
        if pdf_text and len(pdf_text) >= 100:
            import re as _re
            has_keyword = bool(_re.search(r'发票|票据|客票|运输|客运', pdf_text))
            has_amount = bool(_re.search(r'[¥￥革]\s*\d|价税合计|票价|金额|合计', pdf_text))
            if has_keyword and has_amount:
                return pdf_text  # 文本层提取成功，直接返回

        # pdfplumber 不足，用图片 OCR
        images = []  # List of PIL Image objects

        # 方法1: pdf2image + poppler（优先，质量最好）
        poppler_path = _find_poppler()
        print(f"[DEBUG] ocr_pdf: poppler_path={poppler_path!r} pdf={pdf_path!r}", flush=True)
        pdf2image_err = None
        try:
            images = convert_from_path(pdf_path, dpi=200, poppler_path=poppler_path)
        except Exception as exc:
            pdf2image_err = exc
            print(f"[DEBUG] convert_from_path failed: {exc}, trying pypdfium2", flush=True)

        # 方法2: pypdfium2 渲染（不依赖 poppler，Windows 更可靠）
        if not images:
            try:
                import pypdfium2 as pdfium
                doc = pdfium.PdfDocument(pdf_path)
                n_pages = len(doc)
                print(f"[DEBUG] pypdfium2: {n_pages} pages", flush=True)
                for i in range(n_pages):
                    page = doc[i]
                    bitmap = page.render(scale=3.0)  # scale 3.0 ≈ 216 DPI, 铁路客票等长条形票据需要更高分辨率
                    pil_img = bitmap.to_pil()
                    images.append(pil_img)
                    page.close()
                    bitmap.close()
                doc.close()
            except Exception as exc2:
                print(f"[DEBUG] pypdfium2 also failed: {exc2}", flush=True)
                # 两个方法都失败，有文字层就返回文字层
                if pdf_text:
                    return pdf_text
                raise RuntimeError(f"PDF 转图片失败: pdf2image={pdf2image_err}, pypdfium2={exc2}") from exc2

        texts = []

        if pdf_text:
            texts.append(f"[文本层]\n{pdf_text}")

        for i, img in enumerate(images):
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name, "PNG")
                tmp_path = tmp.name

            try:
                page_text = ocr_image(tmp_path, lang, page_count=len(images))
                texts.append(f"[第 {i+1} 页 OCR]\n{page_text}")
            except Exception as e:
                texts.append(f"[第 {i+1} 页]\n[OCR失败: {e}]")
            finally:
                Path(tmp_path).unlink(missing_ok=True)

        return "\n\n".join(texts) if texts else (pdf_text or "")


def _extract_pdf_text_layer(pdf_path: str, fallback_text: str = "") -> str:
    """使用 pdfplumber 直接提取 PDF 文字层（适用于嵌入式字体渲染的 PDF，如铁路电子客票）"""
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            texts = []
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    texts.append(f"[第 {i+1} 页]\n{t}")
            if texts:
                return "\n\n".join(texts)
    except Exception:
        pass
    return fallback_text


def ocr_file(file_path: str) -> str:
    """自动判断文件类型并执行 OCR"""
    ext = Path(file_path).suffix.lower()

    if ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"):
        return ocr_image(file_path)
    elif ext == ".pdf":
        return ocr_pdf(file_path)
    else:
        raise ValueError(f"不支持的文件类型: {ext}，支持: PNG/JPG/PDF")


def is_available() -> bool:
    """检查 OCR 服务是否可用"""
    return _find_tesseract() is not None


def parse_invoice_from_ocr(ocr_text: str) -> dict:
    """从 OCR 文本中解析发票信息（规则+LLM混合模式）"""
    from datetime import datetime
    import re

    result = {
        "invoice_number": "",
        "invoice_code": "",
        "invoice_type": "增值税普通发票",
        "invoice_date": datetime.now().strftime("%Y-%m-%d"),
        "total_amount": 0.0,
        "tax_amount": 0.0,
        "total_with_tax": 0.0,
        "amount_recognized": False,
        "check_code": "",
        "counterpart_name": "",
        "buyer_name": "",
        "remark": "",
        "raw_text": ocr_text
    }

    # 调试日志（使用 repr 避免 Windows GBK 编码问题）
    with contextlib.suppress(Exception):
        print(f"[DEBUG] OCR text length: {len(ocr_text)}", flush=True)

    # 1. 规则解析
    # ===== 发票号码：多策略提取 =====
    # 策略1：关键词"发票号码"后跟数字（标准为12-20位，老发票可能8位）
    invoice_number_match = re.search(r'发票号码[:：]?\s*(\d{12,20})', ocr_text, re.IGNORECASE)
    if invoice_number_match:
        result["invoice_number"] = invoice_number_match.group(1)

    # 策略2：OCR 可能把"发票号码"识别为分离的字符（如"发票 号码"、"发 票 号 码"等）
    if not result["invoice_number"]:
        inv_num_loose = re.search(r'发票\s*号\s*码\s*[:：]?\s*(\d{12,20})', ocr_text)
        if inv_num_loose:
            result["invoice_number"] = inv_num_loose.group(1)

    # 策略3：查找"号码"关键词（有些发票格式只用"号码"）
    if not result["invoice_number"]:
        num_only = re.search(r'(?:号码|编号)\s*[:：]?\s*(\d{12,20})', ocr_text)
        if num_only:
            result["invoice_number"] = num_only.group(1)

    # 策略4：查找 20 位数字序列 —— 电子发票的标准发票号码（含发票代码+号码，
    #   通常是 10位代码 + 8位号码 + 2位校验，或 12位代码 + 8位号码）
    #   在 OCR 文本中，这种长数字串大概率就是发票号码
    if not result["invoice_number"]:
        # 先找标准的 20 位数字串（完整的发票号码格式）
        long_num = re.search(r'(?<!\d)(\d{18,22})(?!\d)', ocr_text)
        if long_num:
            candidate = long_num.group(1)
            # 排除纯 0000 之类的无效号码
            if len(set(candidate)) > 1:
                result["invoice_number"] = candidate
                print(f"[DEBUG] 策略4 从 18-22 位数字串提取发票号码: {candidate}", flush=True)

    # 策略5：查找单独出现的长数字串（有些发票 OCR 后号码独立一行）
    if not result["invoice_number"]:
        standalone_nums = re.findall(r'(?:^|\n)\s*(\d{12,22})\s*(?:\n|$)', ocr_text, re.MULTILINE)
        for num in standalone_nums:
            if len(set(num)) > 2:  # 排除像 0000000000 的无效序列
                result["invoice_number"] = num
                print(f"[DEBUG] 策略5 从独立行提取发票号码: {num}", flush=True)
                break

    # 策略6（兜底）：8 位短号码——保留以兼容老版定额发票
    if not result["invoice_number"]:
        short_num = re.search(r'发票号码[:：]?\s*(\d{8})(?!\d)', ocr_text, re.IGNORECASE)
        if short_num and len(set(short_num.group(1))) > 1:
            result["invoice_number"] = short_num.group(1)
            print(f"[DEBUG] 策略6 从8位短号码提取发票号码: {short_num.group(1)}", flush=True)

    # 发票代码：通常为10-12位数字
    invoice_code_match = re.search(r'发票代码[:：]?\s*(\d{10,12})', ocr_text, re.IGNORECASE)
    if invoice_code_match:
        result["invoice_code"] = invoice_code_match.group(1)

    # 如果发票代码仍为空但发票号码有20位，则前10或12位即为代码
    if not result["invoice_code"] and result["invoice_number"] and len(result["invoice_number"]) >= 18:
        # 尝试拆分：10位代码 + 剩余为号码 / 12位代码 + 剩余为号码
        for code_len in [12, 10]:
            if len(result["invoice_number"]) > code_len:
                result["invoice_code"] = result["invoice_number"][:code_len]
                result["invoice_number"] = result["invoice_number"][code_len:]
                break

    # 开票日期
    date_patterns = [
        r'开票日期[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
        r'日期[:：]?\s*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?)',
        r'(\d{4}年\d{1,2}月\d{1,2}日)'
    ]
    for pattern in date_patterns:
        date_match = re.search(pattern, ocr_text)
        if date_match:
            date_str = date_match.group(1)
            try:
                # 标准化日期格式
                date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-')
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                # 上下界校验：拒绝 0001-01-01 / 9999-12-31 等异常日期
                if not (2000 <= dt.year <= datetime.now().year + 1):
                    continue
                result["invoice_date"] = dt.strftime("%Y-%m-%d")
                break
            except (ValueError, KeyError):
                pass

    # 金额相关 - 增强识别（支持更多格式）
    # 先收集所有金额，然后智能选择
    all_amounts = []
    # 记录每个来源的原始文本位置，用于去重和调试
    _amount_sources = {}  # float -> source_desc

    # === 第1组：带货币符号的金额 ===
    amount_patterns_currency = [
        # ¥423.00 格式（革是¥的常见OCR误识别）
        r'[¥￥革]\s*([\d,]+\.?\d*)',
        # 3) ¥423.00 括号内金额
        r'[\)]\s*[¥￥革]\s*([\d,]+\.?\d*)',
    ]

    for pattern in amount_patterns_currency:
        matches = re.finditer(pattern, ocr_text)
        for match in matches:
            try:
                raw = match.group(1).replace(',', '').replace(' ', '')
                amount = float(raw)
                if amount < 0.01 or amount > 1_000_000_000:
                    continue
                if amount not in _amount_sources:
                    all_amounts.append(amount)
                    _amount_sources[amount] = f'currency:{raw}'
            except ValueError:
                pass

    # === 第2组：关键词引导的金额（紧邻关键词） ===
    amount_patterns_keyword = [
        # 价税合计（小写）¥19.30 —— 最权威的价税合计来源
        r'价税合计[^¥]{0,40}小写[^¥]{0,5}[¥￥革]\s*([\d,]+\.\d{2})',
        r'(?:价税合计|合计|总计|金额|应付|票价|小写)[:：\s]*([¥￥]?[\d,]+\.?\d*)',
        # 表格列头后跟随的数字（处理OCR表格中"金额 423.00"的情况）
        r'(?:金额|价税)[^0-9]{0,8}([¥￥]?[\d,]+\.\d{1,2})',
    ]

    for pattern in amount_patterns_keyword:
        matches = re.finditer(pattern, ocr_text)
        for match in matches:
            try:
                raw = match.group(1).replace('¥', '').replace('￥', '').replace(',', '').replace(' ', '')
                amount = float(raw)
                if amount < 0.01 or amount > 1_000_000_000:
                    continue
                if amount not in _amount_sources:
                    all_amounts.append(amount)
                    _amount_sources[amount] = f'keyword:{raw}'
            except ValueError:
                pass

    # === 第3组：兜底 — 全文扫描，必须带小数点（中国发票金额永远有角分）===
    # 不匹配纯整数的长数字——那些是序列号/校验码/信用代码片段，不是金额
    fallback_amounts = re.findall(
        r'(?<![¥￥\w.])(\d{1,7}\.\d{1,2})(?![,\d])(?!%)(?!\s*[x×])', ocr_text
    )
    for raw in fallback_amounts:
        try:
            amount = float(raw)
            if amount <= 0.5 or amount > 1_000_000_000:
                continue
            if amount not in _amount_sources:
                all_amounts.append(amount)
                _amount_sources[amount] = f'fallback:{raw}'
        except ValueError:
            pass

    # === 智能选择金额 ===
    if all_amounts:
        # 将所有金额分为「可信」（¥前缀 / 关键词相邻）和「不可信」（兜底扫描）
        trusted_amounts = [
            a for a in all_amounts
            if 'currency' in _amount_sources.get(a, '') or 'keyword' in _amount_sources.get(a, '')
        ]
        untrusted_amounts = [
            a for a in all_amounts
            if 'fallback' in _amount_sources.get(a, '')
        ]

        # 策略：优先从可信来源选金额。如果可信来源的金额与不可信来源差距巨大
        # （不可信最大值 > 可信最大值 * 100），说明不可信来源混入了噪声数字，丢弃之
        _candidates = list(trusted_amounts)
        if untrusted_amounts and trusted_amounts:
            if max(untrusted_amounts) <= max(trusted_amounts) * 100:
                _candidates += untrusted_amounts
            # 否则 discard untrusted (noise)
        elif untrusted_amounts:
            _candidates += untrusted_amounts

        if _candidates:
            result["total_with_tax"] = max(_candidates)
        else:
            result["total_with_tax"] = max(all_amounts)

        # 如果有多个金额，尝试推断金额和税额
        # 先找与 total_with_tax 最接近但小于它的金额作为不含税金额
        others = sorted({a for a in _candidates if a < result["total_with_tax"]}, reverse=True)
        if others:
            result["total_amount"] = others[0]
            if len(others) >= 2:
                # 最小的是税额
                result["tax_amount"] = others[-1]
            else:
                result["tax_amount"] = round(result["total_with_tax"] - result["total_amount"], 2)
        else:
            # 尝试从 OCR 文本中识别实际税率（6%/9%/13%）
            detected_rate = _detect_tax_rate(ocr_text)
            if detected_rate is not None:
                result["total_amount"] = round(result["total_with_tax"] / (1 + detected_rate), 2)
                result["tax_amount"] = round(result["total_with_tax"] - result["total_amount"], 2)
            else:
                # 兜底：未识别到税率时不强行反算，保留识别到的 total_with_tax
                result["total_amount"] = 0.0
                result["tax_amount"] = 0.0
    else:
        pass  # 未发现有效金额

    # 标记金额识别状态
    result["amount_recognized"] = bool(result["total_with_tax"] > 0)

    # 销方名称（处理OCR分拆：销 售 方 名称 / 售 名称 / 销售方名称 等变体）
    seller_match = re.search(r'(?:销[售\s]*方?\s*名\s*称|售\s*名\s*称)[:：]?\s*([^\n]+)', ocr_text)
    if seller_match:
        name = seller_match.group(1).strip()
        if _is_valid_company_name(name):
            result["counterpart_name"] = name

    # 购买方名称（同样处理OCR分拆；如果同行后面跟着"售"则截断只取购买方部分）
    buyer_match = re.search(r'(?:购[买\s]*方?\s*名\s*称|买\s*名\s*称)[:：]?\s*([^售\n]+?)(?:\s*售\s*名|\s*销|$)', ocr_text)
    if buyer_match:
        name = buyer_match.group(1).strip()
        if _is_valid_company_name(name):
            result["buyer_name"] = name

    # 铁路电子客票特殊处理
    if "铁路电子客票" in ocr_text or "铁路" in ocr_text:
        result["invoice_type"] = "铁路电子客票"
        result["counterpart_name"] = "中国铁路"
        # 铁路客票：发票号码格式为 发票号码:26119110010004463100
        # 注意：只在尚未识别出号码时才用铁路客票格式提取，避免覆盖已有的拆分结果
        if not result["invoice_number"]:
            rail_invoice = re.search(r'发票号码[:：]\s*(\d{8,20})', ocr_text)
            if rail_invoice:
                result["invoice_number"] = rail_invoice.group(1)
        # 铁路客票：购买方名称（清理信用代码）
        rail_buyer = re.search(r'购买方名称[:：]\s*([^\n]+)', ocr_text)
        if rail_buyer:
            buyer_text = rail_buyer.group(1).strip()
            # 移除信用代码部分
            buyer_text = re.sub(r'\s*统一社会信用代码[：:]\s*\S+', '', buyer_text)
            result["buyer_name"] = buyer_text.strip()
        # 铁路客票：票价（￥533.00 格式）
        rail_price = re.search(r'[¥￥革]\s*([\d,]+\.?\d{0,2})', ocr_text)
        if rail_price:
            try:
                price_str = rail_price.group(1).replace(',', '').replace(' ', '')
                price = float(price_str)
                if price < 1_000_000_000:
                    result["total_with_tax"] = price
                    result["total_amount"] = round(price / 1.09, 2)  # 铁路客票税率9%
                    result["tax_amount"] = round(price - result["total_amount"], 2)
            except (ValueError, KeyError):
                pass

    # 运输服务电子发票（普通发票）特殊处理
    if "运输服务" in ocr_text or "客运服务费" in ocr_text:
        result["invoice_type"] = "运输服务电子发票"
        # 通过信用代码和公司名称的行对应关系提取名称
        _extract_transport_names(ocr_text, result)

        # 运输服务发票：金额/税额/价税合计 三行格式
        # 匹配所有 ¥ 开头的金额
        transport_amounts = re.findall(r'[¥￥革]\s*([\d,]+\.?\d{2})', ocr_text)
        if len(transport_amounts) >= 2:
            try:
                amounts = [float(a.replace(',', '').replace(' ', '')) for a in transport_amounts]
                amounts = [a for a in amounts if a < 1_000_000_000]
                if len(amounts) >= 2:
                    # 最大的是价税合计（28.60），其余是金额（28.32）和税额（0.28）
                    result["total_with_tax"] = max(amounts)
                    others = [a for a in amounts if a != result["total_with_tax"]]
                    if len(others) >= 2:
                        result["total_amount"] = max(others)
                        result["tax_amount"] = min(others)
                    elif len(others) == 1:
                        result["total_amount"] = others[0]
                        result["tax_amount"] = round(result["total_with_tax"] - result["total_amount"], 2)
            except (ValueError, KeyError):
                pass

    # 出租汽车发票特殊处理
    # 特征：含"出租"/"计价"/"里程"/"打表"，金额格式通常为整数或 xx.x/xx.xx
    if any(kw in ocr_text for kw in ["出租汽车", "出租车", "计价器", "里程", "打表", "出租"]):
        result["invoice_type"] = "出租车发票"
        result["counterpart_name"] = "TAXI"
        result["invoice_number"] = ""  # 出租车发票无标准发票号码

        # 1. 优先匹配"金额"/"计价金额"/"实收"/"应付"关键词后跟的数字
        taxi_amount_patterns = [
            r'(?:金额|计价金额|实收|应付|合计|票价|费用|收费)[^0-9]{0,6}[¥￥]?\s*([\d]+\.?\d{0,2})',
            r'[¥￥]\s*([\d]+\.?\d{0,2})',   # ¥32 / ¥32.00
            r'(?:^|\n)\s*([\d]{1,4}\.?\d{0,2})\s*(?:元|$|\n)',  # 独立行的金额
        ]
        taxi_amount = None
        for pat in taxi_amount_patterns:
            m = re.search(pat, ocr_text, re.MULTILINE)
            if m:
                try:
                    v = float(m.group(1).strip())
                    if 1.0 <= v <= 9999:
                        taxi_amount = v
                        print(f"[DEBUG] 出租车金额匹配 pattern={pat!r} value={v}", flush=True)
                        break
                except (ValueError, KeyError):
                    pass

        # 2. 兜底：从全文所有数字中找最合理的金额（1-999 范围，过滤掉序号/日期/编号）
        if taxi_amount is None:
            candidates = re.findall(r'(?<!\d)([\d]{1,3}\.?\d{0,2})(?!\d)', ocr_text)
            plausible = []
            for c in candidates:
                try:
                    v = float(c)
                    if 5.0 <= v <= 999:
                        plausible.append(v)
                except (ValueError, KeyError):
                    pass
            if plausible:
                taxi_amount = max(plausible)
                print(f"[DEBUG] 出租车金额兜底: {taxi_amount}", flush=True)

        if taxi_amount is not None:
            result["total_with_tax"] = taxi_amount
            # 出租车发票无税（或按6%/9%，但通常不分项），简化处理
            result["total_amount"] = taxi_amount
            result["tax_amount"] = 0.0

        # 出租车发票日期：有些格式为"2026-05-29"或"20260529"
        taxi_date = re.search(
            r'(?:日期[:：]?\s*)?(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}日?|\d{8})',
            ocr_text
        )
        if taxi_date:
            ds = taxi_date.group(1).strip()
            if re.match(r'^\d{8}$', ds):
                # 20260529 → 2026-05-29
                ds = f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
            else:
                ds = ds.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-')
            try:
                from datetime import datetime as _dt
                result["invoice_date"] = _dt.strptime(ds, "%Y-%m-%d").strftime("%Y-%m-%d")
            except (ValueError, KeyError):
                pass

    # 校验码
    check_code_match = re.search(r'校验码[:：]?\s*([0-9a-zA-Z]{20,})', ocr_text, re.IGNORECASE)
    if check_code_match:
        result["check_code"] = check_code_match.group(1)

    # 2. 如果关键字段缺失或置信度低，尝试 LLM 解析（TODO: 后续实现）
    # 这里先返回规则解析结果

    return result


# OCR 中的无效名称片段（字段标签、页眉页脚等碎片）
_INVALID_NAME_FRAGMENTS = {"方", "息", "销", "购", "章", "制", "国", "备", "注", "信",
                           "买", "售", "价", "税", "合", "计", "出", "行", "开"}
_INVALID_NAMES = {"方", "息", "销", "购", "章", "制", "国", "备", "注",
                  "信 信", "息 息", "方 方"}
# OCR 标签前缀，在提取公司名称时去除
_NAME_LABEL_PREFIXES = ["名称：", "名称:", "购买方名称：", "购买方名称:",
                        "销售方名称：", "销售方名称:", "销方名称：", "销方名称:",
                        "统一社会信用代码：", "统一社会信用代码:", "统一社会信用代码/纳税人识别号：",
                        "统一社会信用代码/纳税人识别号:", "纳税人识别号：", "纳税人识别号:"]


def _clean_company_name(name: str) -> str:
    """去除常见的OCR标签前缀"""
    if not name:
        return ""
    name = name.strip()
    for prefix in _NAME_LABEL_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):].strip()
            break
    return name


def _is_valid_company_name(name: str) -> bool:
    """验证提取的名称是否是有效的公司名称（而非OCR碎片）"""
    name = _clean_company_name(name)
    if not name or len(name) < 4:
        return False
    if name in _INVALID_NAMES:
        return False
    # 如果名称只由无效碎片组成，拒绝
    if all(frag in _INVALID_NAME_FRAGMENTS for frag in name.split()):
        return False
    # 必须包含至少一个"公司"相关的词，或长度超过6（减少误匹配）
    return "公司" in name or "集团" in name or "厂" in name or len(name) > 6


def _detect_tax_rate(ocr_text: str) -> float | None:
    """从 OCR 文本中识别增值税税率（返回小数，如 0.13 表示 13%）

    策略：
    1. 优先匹配"税率"关键词后跟数字
    2. 兜底匹配"增值税"上下文附近的百分比数字
    3. 数字必须在 1-20 范围内（中国增值税税率常见值）
    """
    # 策略1: 显式的"税率"关键词
    rate_match = re.search(r'税率\s*[:：]?\s*(\d+(?:\.\d+)?)\s*%', ocr_text)
    if rate_match:
        rate_val = float(rate_match.group(1))
        if 1.0 <= rate_val <= 20.0:
            return rate_val / 100.0

    # 策略2: "增值税"附近出现的百分比数字
    context_patterns = [
        r'增值税[^%]{0,20}(\d+(?:\.\d+)?)\s*%',
        r'(\d+(?:\.\d+)?)\s*%[^%]{0,20}增值税',
    ]
    for pat in context_patterns:
        m = re.search(pat, ocr_text)
        if m:
            rate_val = float(m.group(1))
            if 1.0 <= rate_val <= 20.0:
                return rate_val / 100.0

    return None


def _extract_transport_names(ocr_text: str, result: dict):
    """运输服务发票：通过信用代码所在行和上一行的位置对应提取名称

    典型布局：
        南京鹏辰机器人有限公司 青岛路远信息技术有限公司南京分公司
        91320113MACKU9RJ27 91320102MADQ9WG88F

    策略：找到信用代码所在行，从上一行按空格分割提取公司名称，
    按位置对应（第1个名称→第1个代码=购买方，第2个名称→第2个代码=销售方）
    """
    lines = ocr_text.split('\n')

    # 找所有信用代码及其行号
    code_lines = []  # [(line_index, [code1, code2, ...])]
    for i, line in enumerate(lines):
        codes = re.findall(r'(?=.*[A-Za-z])[0-9A-HJ-NP-Z]{18}', line)
        if codes:
            code_lines.append((i, codes))

    if not code_lines:
        return

    # 取第一个有代码的行
    code_line_idx, codes = code_lines[0]

    # 从代码行上方扫描（最多3行）寻找公司名称
    company_names = []
    for offset in range(1, 4):  # 向上扫描1-3行
        look_idx = code_line_idx - offset
        if look_idx < 0:
            break
        prev_line = lines[look_idx].strip()
        tokens = prev_line.split()
        # 过滤明显的标签碎片行（如"方 方"、"买 售"、"信 息"等）
        meaningful_tokens = [t for t in tokens if t not in _INVALID_NAME_FRAGMENTS]
        meaningful_text = ''.join(meaningful_tokens)
        if len(meaningful_text) < 4:
            continue  # 跳过片段行
        company_names = _split_into_company_names(tokens, expected_count=len(codes))
        if company_names:
            break
        # 回退：用正则直接捕获中文字符序列
        company_names = re.findall(r'[\u4e00-\u9fff（）()]{4,30}', prev_line)
        if company_names:
            break

    # 按位置分配：第1个→buyer，第2个→counterpart
    # 运输服务发票中，行对应法比 regex 更可靠，直接覆盖
    if company_names and len(company_names) >= 1:
        name = _clean_company_name(company_names[0])
        if _is_valid_company_name(name):
            result["buyer_name"] = name
    if company_names and len(company_names) >= 2:
        name = _clean_company_name(company_names[1])
        if _is_valid_company_name(name):
            result["counterpart_name"] = name

    # 回退：如果上述方法未提取到名称，尝试信用代码反向查找
    if not result.get("buyer_name") or not result.get("counterpart_name"):
        _fallback_credit_code_lookup(ocr_text, result)


def _split_into_company_names(tokens: list, expected_count: int) -> list:
    """将空格分割的词元合并成公司名称"""
    if not tokens:
        return []
    # 移除明显的无效片段
    valid_tokens = [t for t in tokens if t not in _INVALID_NAME_FRAGMENTS and len(t) > 1]
    if not valid_tokens:
        return []

    # 如果token数与预期一致，直接返回
    if len(valid_tokens) == expected_count:
        return valid_tokens

    # 如果token数少于预期，保持不变
    if len(valid_tokens) < expected_count:
        return valid_tokens

    # Token数多余预期：需要合并相邻的token
    # 基于公司名称特征（以有限公司/分公司/集团结尾）来合并
    names = []
    current_parts = []
    for token in valid_tokens:
        current_parts.append(token)
        combined = ''.join(current_parts)
        if re.search(r'(有限公司|分公司|集团|厂|店|行|社|部)$', combined):
            names.append(combined)
            current_parts = []
        elif len(names) == expected_count - 1:
            # 剩余所有token合并为最后一个名称
            names.append(''.join(current_parts))
            current_parts = []
    if current_parts:
        names.append(''.join(current_parts))
    return names


def _fallback_credit_code_lookup(ocr_text: str, result: dict):
    """回退：通过信用代码位置反向查找公司名称"""
    credit_codes = re.findall(r'(?=.*[A-Za-z])[0-9A-HJ-NP-Z]{18}', ocr_text)
    for cc in credit_codes:
        idx = ocr_text.find(cc)
        if idx < 0:
            continue
        # 查找紧邻代码之前的文本（最多往前搜100个字符，不含其他代码）
        search_start = max(0, idx - 100)
        preceding = ocr_text[search_start:idx]
        # 如果前面有其他代码，截断到代码之后
        prev_code = re.search(r'(?=.*[A-Za-z])[0-9A-HJ-NP-Z]{18}\s*$', preceding)
        if prev_code:
            # 前面的代码挡住了，改为按行查找
            lines = preceding.split('\n')
            # 找最后一个有中文内容的行
            for line in reversed(lines):
                names = re.findall(r'[\u4e00-\u9fff（）()]{4,30}', line)
                if names:
                    name = names[-1]  # 取最后一个（最接近代码的）
                    if _is_valid_company_name(name):
                        if not result.get("buyer_name"):
                            result["buyer_name"] = name
                        elif not result.get("counterpart_name"):
                            result["counterpart_name"] = name
                        break
            continue

        name_match = re.search(r'([\u4e00-\u9fff（）()]{4,30})\s*$', preceding)
        if name_match:
            name = name_match.group(1).strip()
            if _is_valid_company_name(name):
                if not result.get("buyer_name"):
                    result["buyer_name"] = name
                elif not result.get("counterpart_name"):
                    result["counterpart_name"] = name
                else:
                    break
