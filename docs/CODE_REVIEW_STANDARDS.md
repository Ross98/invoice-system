# 代码审查标准与流程 — Invoice System v2.0

> 制定日期：2026-06-02 | 适用范围：发票管理系统全栈项目 | 强制等级：全团队遵循

---

## 一、审查维度（Review Dimensions）

每个 PR 必须从以下六个维度审查。任一维度不达标，按严重等级标记。

| 维度 | 权重 | 核心关注点 |
|---|---|---|
| **安全性** | ⭐⭐⭐⭐⭐ | 输入校验、SQL注入、XSS、认证授权、敏感数据泄露、文件路径遍历 |
| **架构与设计** | ⭐⭐⭐⭐ | 分层正确性、职责单一、接口契约、数据一致性、扩展性 |
| **代码质量** | ⭐⭐⭐⭐ | 可读性、命名规范、函数长度、重复代码、注释质量、类型安全 |
| **性能** | ⭐⭐⭐ | 数据库查询效率、缓存策略、前端渲染性能、打包体积 |
| **测试** | ⭐⭐⭐ | 测试覆盖率、边界条件、错误路径、回归保护 |
| **文档与日志** | ⭐⭐ | API 文档、代码注释、变更日志、错误日志可追踪性 |

---

## 二、严重等级定义

| 等级 | 标识 | 定义 | 处理方式 |
|---|---|---|---|
| **P0 · 阻断** | 🔴 | 安全漏洞、数据丢失风险、生产环境崩溃、硬编码个人凭据 | **必须修复**，禁止合并 |
| **P1 · 严重** | 🟠 | 架构违规、业务逻辑错误、裸 except 吞异常、依赖缺失 | **必须修复**，或经 Tech Lead 豁免 |
| **P2 · 一般** | 🟡 | 代码风格不一致、函数过长、缺少类型注解、调试日志残留 | **建议修复**，可开 follow-up issue |
| **P3 · 建议** | 🔵 | 命名优化、注释补充、重构建议、性能微优化 | 自行决定，不做阻断 |

---

## 三、审查流程

```
开发者提交 PR
    │
    ▼
┌──────────────────┐
│  ① 自动化检查     │  ← CI 管道：lint → type-check → test → build
│  (必须全部通过)   │
└──────┬───────────┘
       │ 通过
       ▼
┌──────────────────┐
│  ② 作者自审       │  ← 填写自审清单，在 PR 描述中打勾
│  (Self-Review)    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  ③ 同行审查       │  ← 至少 1 名 Reviewer
│  (Peer Review)    │     复杂变更（>200 行或涉及架构）至少 2 名
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  ④ 修复与复检     │  ← Author 修复 → Reviewer 确认
│  (Fix & Recheck)  │
└──────┬───────────┘
       │ 全部通过
       ▼
┌──────────────────┐
│  ⑤ 合并到主分支   │  ← Squash & Merge，保留干净历史
└──────────────────┘
```

### 审查时效

| 场景 | 时限 | 备注 |
|---|---|---|
| 紧急修复（P0 bug） | 1 小时内 | 可申请单人审查豁免，事后补审 |
| 常规 PR（<200 行） | 4 工作小时内 | |
| 大型 PR（200-500 行） | 1 工作日内 | 建议拆分为多个小 PR |
| 架构级变更（>500 行） | 2 工作日内 | 需提前发设计文档，走 RFC 流程 |

### PR 大小限制

- **单个 PR 不超过 500 行**（不含测试、配置文件、自动生成代码）
- 超过 500 行的变更必须拆分为逻辑独立的多个 PR
- 新增路由/组件 + 对应测试算一个逻辑单元

---

## 四、后端审查清单（Python / FastAPI / SQLAlchemy）

### 安全性 🔐

- [ ] **输入校验**：所有用户输入都经过 Pydantic Schema 校验，没有裸 `request.json()` 或直接取 `Query()` 参数后不做校验就使用
- [ ] **SQL 注入**：所有数据库操作使用 SQLAlchemy ORM 参数化查询，严禁拼接 SQL 字符串
- [ ] **文件安全**：文件上传验证了 MIME 类型、扩展名白名单、文件大小限制；文件路径使用 `safe_join()` 防止目录遍历
- [ ] **异常处理**：没有 `except:` 裸捕获（必须用 `except Exception:`）；没有吞异常（至少要 `logger.exception()`）
- [ ] **敏感数据**：配置中的密钥、密码使用环境变量或 `.env`，不硬编码；API 响应不泄露数据库错误细节

### 架构与设计 🏗️

- [ ] **分层正确**：路由层只做参数解析和响应格式化，业务逻辑在 service 层，数据访问通过 ORM
- [ ] **函数职责单一**：单个函数不超过 80 行（复杂业务不超过 120 行），函数名能准确描述其行为
- [ ] **路由规范**：URL 使用 RESTful 风格（复数名词），HTTP 方法语义正确（GET/POST/PUT/DELETE）
- [ ] **Schema 设计**：Base/Create/Update/Response 分离，Request 和 Response Schema 不混用
- [ ] **依赖注入**：数据库 session 通过 FastAPI `Depends(get_db)` 获取，不在模块级别创建全局连接
- [ ] **配置管理**：所有可配置项通过 `config.py` 的 `Settings` 类管理，不从代码中直接读环境变量

### 代码质量 ✨

- [ ] **类型注解**：所有公共函数有完整的参数类型和返回值类型注解；复杂类型使用 `TypeAlias` 或 Pydantic Model
- [ ] **异常处理**：自定义业务异常类（如 `InvoiceNotFoundError`）；路由层有统一的异常处理器
- [ ] **日志规范**：使用 `logging` 模块（非 `print()`）；区分 DEBUG/INFO/WARNING/ERROR 等级；关键操作记录 INFO 日志
- [ ] **数据库操作**：批量操作使用 `bulk_insert_mappings` 或 `insert().values()` 而非逐条 `add()`；关联查询使用 `joinedload()` 避免 N+1
- [ ] **事务管理**：写操作明确事务边界，必要时使用 `session.begin()`；异常时回滚
- [ ] **无调试残留**：删除所有 `print("[DEBUG]")`、`breakpoint()`、`pdb.set_trace()`

### 性能 ⚡

- [ ] **查询优化**：高频查询有数据库索引；列表查询有分页；ORM 查询使用 `options(joinedload())` 预加载关联
- [ ] **避免 N+1**：循环内没有数据库查询；关联数据通过 JOIN 或 `selectinload` 一次性加载
- [ ] **文件处理**：大文件不全部读入内存，使用流式处理；图片 OCR 前做了尺寸限制

### 测试 🧪

- [ ] **新增功能有测试**：新路由有至少一个 happy-path 测试 + 一个错误路径测试
- [ ] **边界条件**：空输入、超长输入、特殊字符、并发请求有测试覆盖
- [ ] **测试隔离**：测试使用独立数据库（`:memory:` 或临时文件），测试间不共享状态

---

## 五、前端审查清单（Vue 3 / Vuetify 3 / Vite）

### 安全性 🔐

- [ ] **XSS 防护**：用户输入的 HTML 内容使用 Vue 的 `{{ }}` 插值（自动转义），非必要不使用 `v-html`
- [ ] **API 请求**：请求包含必要的认证头；敏感操作（删除、重置）有确认弹窗
- [ ] **依赖安全**：新增 npm 包经安全审计（`npm audit`），无已知高危漏洞

### 架构与设计 🏗️

- [ ] **组件拆分**：单个组件不超过 300 行；可复用 UI 放入 `components/`；页面级逻辑放入 `views/`
- [ ] **状态管理**：跨组件共享状态使用 Pinia store；局部状态使用 `ref`/`reactive`；不在组件间通过 `$parent`/`$refs` 传数据
- [ ] **API 层分离**：所有 API 调用通过 `api/index.js` 的统一 Axios 实例；不在组件中直接 `fetch()` 或 `axios()`
- [ ] **路由规范**：路由使用懒加载；`meta` 字段包含 `title` 和 `breadcrumb`；重定向使用 `redirect` 配置而非组件内跳转
- [ ] **无遗留代码**：删除不再使用的旧视图（如 `UploadView.vue`、`NewInvoiceView.vue`）

### 代码质量 ✨

- [ ] **一致性**：所有用户反馈使用 Vuetify `v-snackbar`（非 `alert()`）；加载状态使用 `v-skeleton-loader` 或 `:loading` 属性
- [ ] **表单验证**：使用 Vuetify `:rules` + `validate-on="blur lazy"`，自定义规则提取到共享模块
- [ ] **错误处理**：API 错误统一由 `api/index.js` 的响应拦截器处理；组件中捕获 promise rejection 并展示友好错误信息
- [ ] **无调试残留**：删除所有 `console.log()`、`console.debug()` 调用
- [ ] **命名规范**：Vue 组件使用 PascalCase 文件名；事件处理函数以 `on`/`handle` 开头；布尔变量以 `is`/`has`/`can` 开头

### 性能 ⚡

- [ ] **懒加载**：路由组件使用动态 `import()`；大型依赖（如 Chart.js）按需加载
- [ ] **计算属性**：复杂数据转换使用 `computed`（非 `method` 或 `watch` 副作用）
- [ ] **列表优化**：大列表（>100 项）使用虚拟滚动或分页；`:key` 绑定唯一 ID（非 `index`）
- [ ] **打包体积**：新依赖引入需说明理由；不重复引入已有功能的包

### 测试 🧪

- [ ] **新增组件有测试**：关键交互（按钮点击、表单提交）有 vitest 测试
- [ ] **Store 测试**：新增 Pinia action 有对应的单元测试

---

## 六、通用审查规则（前后端均适用）

- [ ] **命名规范**：文件名使用 kebab-case（如 `invoice-detail.vue`）；Python 变量/函数使用 snake_case；JS 变量/函数使用 camelCase
- [ ] **DRY 原则**：相同逻辑不出现 3 次以上；提取为共享函数/组件/工具类
- [ ] **注释质量**：注释解释"为什么"（Why），而非"是什么"（What）；代码本身应解释 What
- [ ] **无魔法数字**：所有业务常量定义为命名常量或枚举
- [ ] **CHANGELOG**：用户可见的功能变更、API 变更、破坏性变更需在 PR 描述中标注
- [ ] **依赖声明**：后端新增 pip 包 → 更新 `requirements.txt`；前端新增 npm 包 → 更新 `package.json`
- [ ] **环境变量**：新增环境变量 → 更新 `.env.example` 并附说明注释

---

## 七、工具链配置

### 7.1 后端：Ruff (Linter + Formatter)

```toml
# ruff.toml — 项目根目录
```

检查项：
- `F` (Pyflakes)：未使用导入、未定义变量
- `E/W` (pycodestyle)：PEP 8 风格
- `I` (isort)：导入排序
- `B` (flake8-bugbear)：常见 bug 检测
- `SIM` (flake8-simplify)：代码简化建议
- `C4` (flake8-comprehensions)：推导式优化
- `UP` (pyupgrade)：现代语法升级

### 7.2 后端：Pyright (类型检查)

```jsonc
// pyrightconfig.json — 项目根目录
```

- 严格模式（`typeCheckingMode: "standard"`）
- 排除 `frontend/`、`node_modules/`、`__pycache__/`

### 7.3 前端：ESLint + Prettier

ESLint 规则基于 `eslint:recommended` + `plugin:vue/vue3-recommended`，Prettier 统一格式化。

### 7.4 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
```

提交前自动执行：
1. **后端**：ruff check + ruff format --check
2. **前端**：eslint --fix + prettier --check
3. **通用**：检查调试语句（`print(`、`console.log`、`breakpoint()`）
4. **通用**：检查硬编码路径、密钥

### 7.5 CI 管道（GitHub Actions 建议结构）

```yaml
name: Code Quality
on: [pull_request]

jobs:
  backend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-ruff@v1
      - run: ruff check backend/
      - run: ruff format --check backend/

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cd frontend && npm ci && npm run lint

  backend-test:
    runs-on: ubuntu-latest
    steps:
      - run: cd backend && pytest --cov=app --cov-report=term-missing
```

---

## 八、PR 模板

见 `.github/pull_request_template.md`。

主要内容：
1. 变更类型（功能/修复/重构/文档/CI）
2. 关联 Issue
3. 变更说明（What & Why）
4. 测试情况
5. 自审清单（打勾确认）
6. 截图/录屏（如有 UI 变更）

---

## 九、当前代码库专项审查基准

基于 2026-06-02 代码库全面体检，以下项目**在本次审查中优先关注**：

### P0 级（发现即打断合并）

| # | 检查项 | 说明 |
|---|---|---|
| 1 | 无硬编码路径 | 类似 `C:/Users/12572/Desktop/发票/...` 的路径不得出现 |
| 2 | 无裸 `except:` | 所有异常捕获必须指定 `Exception` 或其子类 |
| 3 | 依赖完整声明 | `requirements.txt` 必须包含所有 runtime 依赖（当前缺 `python-dateutil`） |
| 4 | App.vue 语法正确 | 无多余闭合大括号导致编译异常 |

### P1 级（必须修复或有合理解释）

| # | 检查项 | 说明 |
|---|---|---|
| 5 | 业务逻辑不入路由层 | Excel 导出、文件名解析等逻辑必须在 service 层 |
| 6 | 单函数不超过 120 行 | OCR 服务 `parse_invoice_from_ocr()` 需拆分 |
| 7 | 无调试日志残留 | `print("[DEBUG]")` 和 `console.log()` 全部替换 |
| 8 | 错误提示方式统一 | 全部使用 snackbar，禁止 `alert()` |
| 9 | 版本号唯一来源 | `.env.example` 与 `config.py` 版本号一致 |

---

## 十、审查沟通准则

1. **对事不对人**：评论针对代码而非作者。使用"这段逻辑……"而非"你写错了……"
2. **提出问题，也给出建议**：发现问题时，附上修改建议或参考代码
3. **区分严重等级**：在评论中标注 `[P0]` `[P1]` `[P2]` `[P3]`，让作者明确优先级
4. **及时响应**：作者修复后 2 小时内重新审查
5. **知识共享**：审查中发现的好模式或常见陷阱，记录到团队 Wiki 的"代码规范"页面

---

## 附录 A：审查常用命令

```bash
# 后端
cd backend
ruff check app/                      # Lint 检查
ruff format --check app/             # 格式检查（不修改）
ruff format app/                     # 自动格式化
pyright app/                         # 类型检查

# 前端
cd frontend
npm run lint                         # ESLint 检查
npm run format                       # Prettier 格式化
npm run type-check                   # TypeScript 类型检查（如已迁移 TS）

# 测试
cd backend && pytest --cov=app -v   # 后端测试 + 覆盖率
cd frontend && npm run test          # 前端测试
```
