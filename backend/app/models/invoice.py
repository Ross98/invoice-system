from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Category(Base):
    """消费分类"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    invoices = relationship("Invoice", back_populates="category")


class Counterpart(Base):
    """对方单位"""
    __tablename__ = "counterparts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50), nullable=True)

    invoices = relationship("Invoice", back_populates="counterpart")


class Invoice(Base):
    """发票主表"""
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", "invoice_code", name="uix_invoice_number_code"),
        Index("idx_invoice_date_code_number", "invoice_date", "invoice_number", "invoice_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), nullable=False)
    invoice_code = Column(String(50), nullable=False)
    invoice_type = Column(String(20), nullable=False)  # 增值税专票/普票/电子票
    invoice_date = Column(Date, nullable=False)
    total_amount = Column(Float, nullable=True)  # 不含税金额
    tax_amount = Column(Float, nullable=True)  # 税额
    total_with_tax = Column(Float, nullable=True)  # 含税总金额
    check_code = Column(String(100), nullable=True)  # 校验码
    raw_text = Column(Text, nullable=True)  # OCR 原始文本（调试和备查用）
    counterpart_id = Column(Integer, ForeignKey("counterparts.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    remark = Column(Text, nullable=True)
    is_reimbursed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    counterpart = relationship("Counterpart", back_populates="invoices")
    category = relationship("Category", back_populates="invoices")
    details = relationship("InvoiceDetail", back_populates="invoice", cascade="all, delete-orphan")
    files = relationship("InvoiceFile", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceDetail(Base):
    """消费明细"""
    __tablename__ = "invoice_details"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    item_name = Column(String(200), nullable=True)  # 品名/服务项
    spec = Column(String(200), nullable=True)  # 规格型号
    unit = Column(String(50), nullable=True)  # 单位
    quantity = Column(Float, nullable=True)  # 数量
    unit_price = Column(Float, nullable=True)  # 单价
    amount = Column(Float, nullable=True)  # 金额
    tax_rate = Column(Float, nullable=True)  # 税率
    service_date = Column(Date, nullable=True)  # 服务发生日期
    created_at = Column(DateTime, server_default=func.now())

    invoice = relationship("Invoice", back_populates="details")


class InvoiceFile(Base):
    """发票原文件"""
    __tablename__ = "invoice_files"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # PDF/PNG/JPG
    file_size = Column(Integer, nullable=False)  # 字节
    storage_mode = Column(String(10), nullable=False)  # path / blob
    file_path = Column(String(500), nullable=True)  # 本地路径（storage_mode=path）
    blob_data = Column(Text, nullable=True)  # Base64 编码的二进制数据（storage_mode=blob）
    uploaded_at = Column(DateTime, server_default=func.now())

    invoice = relationship("Invoice", back_populates="files")
