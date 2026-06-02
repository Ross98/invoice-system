# Phase 5.3: 全局搜索增强 — 交付报告

## 概述

对发票管理系统的全局搜索能力进行了全面增强。搜索范围从原来的 3 个字段扩展到 6 个字段 + 关联表，新增专用搜索端点，前端搜索对话框接入新 API 并支持匹配字段高亮展示。

## 变更内容

### 后端

#### 1. 增强 `GET /api/invoices` 的 search_text 过滤

**文件**: `backend/app/routers/invoices.py`

| 变更 | 原来 | 现在 |
|------|------|------|
| 搜索字段 | invoice_number, invoice_code, remark | + raw_text, check_code, **counterpart.name (JOIN)** |
| 关联查询 | 无 | LEFT JOIN counterparts 表 |

#### 2. 新增专用搜索端点 `GET /api/search`

**文件**: `backend/app/routers/search.py` (新建)

```bash
GET /api/search?q=关键词&limit=20
```

**响应结构**:
```json
{
  "query": "服务",
  "total": 16,
  "shown": 5,
  "items": [
    {
      "id": 18,
      "invoice_number": "29127541",
      "invoice_type": "...",
      "total_with_tax": 290.0,
      "is_reimbursed": false,
      "counterpart": { "id": 1, "name": "上海泰..." },
      "category": { "id": 2, "name": "交通" },
      "matches": [
        {
          "field": "counterpart",
          "label": "对方单位",
          "snippet": "上海泰和…<mark>服务</mark>…有限公司",
          "priority": 7
        },
        {
          "field": "remark",
          "label": "备注",
          "snippet": "…<mark>服务</mark>…",
          "priority": 6
        }
      ]
    }
  ]
}
```

**关键特性**:
- 6 个字段 + JOIN 关联搜索
- 匹配字段按优先级排序（发票号码 > 代码 > 单位 > 校验码 > 备注 > OCR）
- snippet 自动截取关键词前后各 30 字符 + 省略号
- `<mark>` 标签标记高亮区域

#### 3. 注册路由

**文件**: `backend/main.py`
- `from app.routers import ..., search`
- `app.include_router(search.router)`

### 前端

#### 1. 新增 searchApi

**文件**: `frontend/src/api/index.js`
```js
export const searchApi = {
  search(query, limit = 20) {
    return api.get('/search', { params: { q: query, limit } })
  }
}
```

#### 2. 搜索对话框重构

**文件**: `frontend/src/App.vue`

| 变更 | 原来 | 现在 |
|------|------|------|
| 数据源 | `invoiceApi.getInvoices()` | `searchApi.search()` |
| 结果列表行模式 | `lines="two"` (发票号+金额) | `lines="three"` (发票号+金额+匹配片段) |
| 匹配展示 | 无 | 彩色 chip 标签 + 黄色高亮片段 |
| 搜索提示 | "发票号码/单位名称/备注" | + "OCR原文" |

**matchColor 映射**:
- 发票号码 → `primary` (蓝)
- 发票代码 → `indigo` (靛蓝)
- 对方单位 → `orange` (橙)
- 校验码 → `teal` (青)
- 备注 → `purple` (紫)
- OCR原文 → `blue-grey` (灰蓝)

**高亮样式**:
```css
.match-snippet mark {
  background: #FFF176;  /* 亮黄 */
  color: #333;
  padding: 0 2px;
  border-radius: 2px;
  font-weight: 500;
}
```

## 测试验证

| 搜索词 | 命中数 | 匹配字段 |
|--------|-------|----------|
| 出租车 | 1 | 备注 |
| 服务 | 16 | OCR原文, 对方单位, 备注 |
| TAXI | 1 | 对方单位 (JOIN 生效) |
| 12345 | 0 | 正确空结果 ✓ |

## 文件清单

| 操作 | 文件 |
|------|------|
| 新建 | `backend/app/routers/search.py` |
| 修改 | `backend/app/routers/invoices.py` (search_text 增强) |
| 修改 | `backend/main.py` (注册 search router) |
| 修改 | `frontend/src/api/index.js` (新增 searchApi) |
| 修改 | `frontend/src/App.vue` (搜索重构 + 高亮展示) |
