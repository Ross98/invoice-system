# Changelog

All notable changes to the Invoice Management System (发票管理系统) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-06-23

### Added
- GitHub Actions CI workflow (`.github/workflows/tests.yml`) — pytest + ruff (backend) + ESLint + vitest + build (frontend) on every push/PR
- **49** pytest unit tests covering P0/P1 critical fixes (file storage, schemas, settings auth, OCR)
- **43** Vitest unit tests covering frontend P0/P2 fixes (store type guard, axiosLong, v-form validate, 404 router)
- 2 regression tests for `upload_invoice_file` infinite-recursion bug
- 404 fallback route + `NotFoundView.vue`
- `ADMIN_TOKEN` config for `/api/settings/reset` and `/backup` endpoints
- CI badge in README
- §生产部署 in README (Windows 单机 + Linux 服务器 systemd/nginx/HTTPS)

### Changed
- **BREAKING** API response schema: `raw_text`, `file_path`, `storage_mode` no longer exposed in invoice responses (use `InvoiceInternal` for internal access)
- OCR accuracy: tax rate detection (6/9/13%) via keyword recognition, amount-recognized flag, date range validation (2000-Now+1)
- Performance: N+1 fixed (`selectinload`), monthly stats merged into single SQL query, composite index `idx_invoice_date_code_number`
- File upload: chunked streaming (1MB chunks), MIME magic-byte sniffing, 10MB default limit
- Frontend UX: `v-snackbar` for errors, `v-dialog` for confirmations, summary view uses `v-data-table-server` pagination
- Test coverage: OCR company name validation threshold `>10` → `>=8` (real company names like "腾讯控股集团有限公司" no longer rejected)
- OCR fallback: invalid dates no longer silently fall back to today
- Frontend: `axiosLong` (60s timeout) dedicated to OCR/backup/upload endpoints
- ESLint warnings: 3444 → 0 (auto-fix + manual cleanup)
- Build version: 2.0.4 → 2.1.0

### Fixed
- **P0 Security**
  - `OCR file pointer reuse` — `recognize_and_associate` now `await file.seek(0)` before OCR
  - `BLOB delete leak` — `delete_file` clears BLOB fields from DB
  - `OOM on large uploads` — chunked streaming replaces `read()`-into-memory
  - `MIME extension spoofing` — magic-byte sniffing (PDF/PNG/JPEG), rejects executables
  - `Settings endpoints unauthenticated` — `/api/settings/reset` and `/backup` require `X-Admin-Token`
  - `Schema sensitive data leak` — `raw_text`/`file_path` excluded from API responses
  - `upload_invoice_file infinite recursion` — Phase 2 regression where router's local def shadowed services import (CI caught)
- **P2 Performance & OCR**
  - Hardcoded 13% tax rate → keyword-based detection
  - PDF OCR concurrent semaphore (max 2)
  - Tesseract dynamic timeout based on page count
  - PIL Image closed via context manager
  - Temp directories cleaned with `shutil.rmtree`
  - 6-field LIKE queries with composite index
  - 24 monthly queries merged into 1
  - Filename amount fallback excludes date-like numbers
  - Statistics `outerjoin` for `top_counterparts` to include null sellers
  - `delete_invoice` file cleanup isolated from DB transaction
  - `create_invoice` / `update_invoice` / `upload_invoice_file` wrapped in try/except + rollback
- **P2.5 Minor**
  - `InvoiceCreate` validator rejects `is_reimbursed=true` (anti-bypass)
  - `InvoiceFileCreate` excludes `file_path`/`blob_data` (anti-injection)
  - Frontend: `v-data-table return-object` removed (ID array saves memory)
  - Frontend: `:disabled` on submit buttons prevents double-click
  - Frontend: `:rules` for non-negative numeric fields
  - Settings error stack traces no longer leaked to clients

### Security
- All P0 vulnerabilities from the audit report (raw_text leak, settings auth, MIME spoofing, etc.) are fixed
- New `require_admin` dependency uses `secrets.compare_digest` to prevent timing attacks
- 92 unit tests prevent regression of security fixes

### Documentation
- README: added §生产部署 with Windows 单机 + Linux 服务器 (systemd + nginx + HTTPS) guides
- CHANGELOG.md (this file) in Keep a Changelog format
- RELEASE_NOTES_v2.1.0.md for GitHub Release

### Release
- GitHub Release v2.1.0 published: `InvoiceSystem-2.1.0-win64.zip` (155 MB)
- SHA256: `99796cb22c7ca97a7871d3a9d76f88fe9adca0b862ee03e84a345f276b58a71d`

[2.1.0]: https://github.com/Ross98/invoice-system/releases/tag/v2.1.0

## [2.0.3] - 2026-06-03

### Added
- Independent Launcher process (auto-opens browser when service ready)
- Invoice count column in summary export template

[2.0.3]: https://github.com/Ross98/invoice-system/releases/tag/v2.0.3

## [2.0.0] - 2026-05

### Added
- Complete UX architecture refactor: navigation, info architecture
- Phase 1-3: dashboard, statistics, summary, batch operations
- Cloud deployment configuration (Aliyun)

[2.0.0]: https://github.com/Ross98/invoice-system/releases/tag/v2.0.0
