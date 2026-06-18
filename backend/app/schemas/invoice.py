from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# 基础 Schema
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: int | None = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CounterpartBase(BaseModel):
    name: str = Field(..., max_length=200)
    tax_id: str | None = Field(None, max_length=50)


class CounterpartCreate(CounterpartBase):
    pass


class Counterpart(CounterpartBase):
    id: int

    class Config:
        from_attributes = True


# 发票相关 Schema
class InvoiceDetailBase(BaseModel):
    item_name: str | None = Field(None, max_length=200)
    spec: str | None = Field(None, max_length=200)
    unit: str | None = Field(None, max_length=50)
    quantity: float | None = None
    unit_price: float | None = None
    amount: float | None = None
    tax_rate: float | None = None
    service_date: date | None = None


class InvoiceDetailCreate(InvoiceDetailBase):
    pass


class InvoiceDetail(InvoiceDetailBase):
    id: int
    invoice_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., max_length=50)
    invoice_code: str = Field(..., max_length=50)
    invoice_type: str = Field(..., max_length=20)
    invoice_date: date
    total_amount: float | None = None
    tax_amount: float | None = None
    total_with_tax: float | None = None
    check_code: str | None = Field(None, max_length=100)
    counterpart_id: int | None = None
    category_id: int | None = None
    raw_text: str | None = None
    remark: str | None = None
    is_reimbursed: bool | None = False


class InvoiceCreate(InvoiceBase):
    details: list[InvoiceDetailCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_number: str | None = Field(None, max_length=50)
    invoice_code: str | None = Field(None, max_length=50)
    invoice_type: str | None = Field(None, max_length=20)
    invoice_date: date | None = None
    total_amount: float | None = None
    tax_amount: float | None = None
    total_with_tax: float | None = None
    check_code: str | None = Field(None, max_length=100)
    counterpart_id: int | None = None
    category_id: int | None = None
    remark: str | None = None
    is_reimbursed: bool | None = None
    details: list[InvoiceDetailCreate] | None = None


class InvoiceResponse(InvoiceBase):
    """对外 API 响应：不含 OCR 原始文本等敏感字段"""
    id: int
    counterpart: Counterpart | None = None
    category: Category | None = None
    details: list[InvoiceDetail] = []
    created_at: datetime
    updated_at: datetime
    # 显式重写 raw_text 为排除字段，确保不进入 API 响应
    raw_text: str | None = Field(default=None, exclude=True)

    model_config = {"from_attributes": True}


# 内部使用的完整 Schema（含 raw_text），仅服务层使用，不暴露给 API
class InvoiceInternal(InvoiceBase):
    id: int
    counterpart: Counterpart | None = None
    category: Category | None = None
    details: list[InvoiceDetail] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 文件相关 Schema
class InvoiceFileBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=20)
    file_size: int


class InvoiceFileCreate(BaseModel):
    """文件创建输入：服务端使用，不暴露给 API"""
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=20)
    file_size: int
    storage_mode: str = Field(..., max_length=10)
    file_path: str | None = Field(None, max_length=500)
    blob_data: str | None = None  # Base64 编码


class InvoiceFileInternal(BaseModel):
    """内部完整文件 Schema：含存储路径等内部字段，仅服务层使用"""
    id: int
    invoice_id: int
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=20)
    file_size: int
    storage_mode: str = Field(..., max_length=10)
    file_path: str | None = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class InvoiceFileResponse(BaseModel):
    """对外 API 响应：不含 file_path、storage_mode 等内部实现细节"""
    id: int
    invoice_id: int
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=20)
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


# 查询和筛选 Schema
class InvoiceFilter(BaseModel):
    invoice_number: str | None = None
    invoice_code: str | None = None
    invoice_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    counterpart_id: int | None = None
    category_id: int | None = None
    search_text: str | None = None

    class Config:
        from_attributes = True


# 分页响应 Schema
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
