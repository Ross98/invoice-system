from pydantic import BaseModel, Field, validator
from typing import Optional, List, Generic, TypeVar
from datetime import date, datetime

T = TypeVar("T")


# 基础 Schema
class CategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class CounterpartBase(BaseModel):
    name: str = Field(..., max_length=200)
    tax_id: Optional[str] = Field(None, max_length=50)


class CounterpartCreate(CounterpartBase):
    pass


class Counterpart(CounterpartBase):
    id: int
    
    class Config:
        from_attributes = True


# 发票相关 Schema
class InvoiceDetailBase(BaseModel):
    item_name: Optional[str] = Field(None, max_length=200)
    spec: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    tax_rate: Optional[float] = None
    service_date: Optional[date] = None


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
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_with_tax: Optional[float] = None
    check_code: Optional[str] = Field(None, max_length=100)
    counterpart_id: Optional[int] = None
    category_id: Optional[int] = None
    raw_text: Optional[str] = None
    remark: Optional[str] = None
    is_reimbursed: Optional[bool] = False


class InvoiceCreate(InvoiceBase):
    details: List[InvoiceDetailCreate] = []


class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_code: Optional[str] = Field(None, max_length=50)
    invoice_type: Optional[str] = Field(None, max_length=20)
    invoice_date: Optional[date] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_with_tax: Optional[float] = None
    check_code: Optional[str] = Field(None, max_length=100)
    counterpart_id: Optional[int] = None
    category_id: Optional[int] = None
    remark: Optional[str] = None
    is_reimbursed: Optional[bool] = None
    details: Optional[List[InvoiceDetailCreate]] = None


class Invoice(InvoiceBase):
    id: int
    counterpart: Optional[Counterpart] = None
    category: Optional[Category] = None
    details: List[InvoiceDetail] = []
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 文件相关 Schema
class InvoiceFileBase(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=20)
    file_size: int
    storage_mode: str = Field(..., max_length=10)


class InvoiceFileCreate(InvoiceFileBase):
    file_path: Optional[str] = Field(None, max_length=500)
    blob_data: Optional[str] = None  # Base64 编码


class InvoiceFile(InvoiceFileBase):
    id: int
    invoice_id: int
    file_path: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


# 查询和筛选 Schema
class InvoiceFilter(BaseModel):
    invoice_number: Optional[str] = None
    invoice_code: Optional[str] = None
    invoice_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    counterpart_id: Optional[int] = None
    category_id: Optional[int] = None
    search_text: Optional[str] = None
    
    class Config:
        from_attributes = True


# 分页响应 Schema
T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int