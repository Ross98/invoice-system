# v2.1.0 — 发票管理系统

## 🎉 下载

- **Windows 一键包**: [InvoiceSystem-2.1.0-win64.zip](https://github.com/Ross98/invoice-system/releases/download/v2.1.0/InvoiceSystem-2.1.0-win64.zip) (155 MB)
- SHA256: `99796cb22c7ca97a7871d3a9d76f88fe9adca0b862ee03e84a345f276b58a71d`
- 解压双击 `启动发票管理系统.bat` 即可

## 📋 变更摘要

### 🔒 安全修复(P0,7 项)

| BUG | 修复 |
|-----|------|
| OCR 文件指针错位 → 静默识别失败 | `await file.seek(0)` 复位 |
| BLOB 字段删除不清理 → DB 膨胀 | `delete_file` 清空字段 |
| 大文件 `read()` 入内存 → OOM | 流式分块 1MB + 10MB 上限 |
| MIME 仅校验扩展名 → 任意文件上传 | 魔数嗅探 PDF/PNG/JPEG |
| `/api/settings/reset` & `/backup` 无鉴权 | `ADMIN_TOKEN` 强制 |
| API 响应含 `raw_text`/`file_path` 敏感数据 | 拆 Internal/Response schema |
| 发票创建可绕过报销流程 | `is_reimbursed=true` 拒绝 |

### ⚡ 性能优化(P2,~30 项)

- 3 处 N+1 修复(`selectinload`)
- 24 次月度统计合并为 1 次 SQL
- 复合索引 `idx_invoice_date_code_number`
- 汇总页改 `v-data-table-server` 分页(原 1k+ 行卡死)
- `Promise.allSettled` 并发批量报销
- OCR:税率/日期/金额识别全部智能化

### 🎨 UX 改进(P2)

- `alert/confirm` 全部替换为 `v-snackbar` + `v-dialog`
- 表单按钮加 `:disabled` 防重复提交
- 金额/税率字段加非负校验
- 404 fallback 路由

### 🧪 质量保证

- **后端 pytest**: 49 用例,0.59s 100% pass
- **前端 vitest**: 43 用例,0.65s 100% pass
- **ruff**: 0 errors / 0 warnings
- **ESLint**: 0 errors / 0 warnings(从 3444 修到 0)
- **GitHub Actions CI**: 双 job(backend + frontend)全绿
- **npm run build**: 验证生产构建

### 📝 破坏性变更

API 响应**不再包含** `raw_text`、`file_path`、`storage_mode`。如需内部访问请使用 `InvoiceInternal` schema。

## 🔄 升级

从 v2.0.x 升级:解压覆盖即可,SQLite 数据库兼容。首次运行会自动迁移 schema。

## 📚 完整 Changelog

详见 [CHANGELOG.md](https://github.com/Ross98/invoice-system/blob/main/CHANGELOG.md)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
