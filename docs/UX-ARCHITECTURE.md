# 发票管理系统 — 用户体验架构重构方案

> **版本**: v2.0 草案  
> **日期**: 2026-06-01  
> **作者**: ArchitectUX Agent  
> **状态**: 待审阅

---

## 目录

1. [现状诊断：六个核心断点](#1-现状诊断六个核心断点)
2. [信息架构重构](#2-信息架构重构)
3. [三大核心用户旅程](#3-三大核心用户旅程)
4. [页面组件层级规范](#4-页面组件层级规范)
5. [CSS 设计系统基础](#5-css-设计系统基础)
6. [实施路线图](#6-实施路线图)

---

## 1. 现状诊断：六个核心断点

### 🔴 断点一：导航扁平无层级

```
当前导航（8 项平铺）:
 首页 → 发票管理 → 发票汇总 → 上传发票 → 分类管理 → 单位管理 → 系统设置 → 关于系统
```

**问题**: 用户无法区分"主要操作"和"辅助管理"。发票入库的两种方式（手动新建 / OCR 上传）分散在不同菜单项中，心智模型不一致。

### 🔴 断点二：OCR 识别后流程分叉过多

```
当前 UploadView 识别完成后的出口:
  ├── "确认导入" → 直接入库（但看不到后续怎么办）
  ├── "编辑" → 跳转 /invoices/new（丢失 OCR 上下文）
  ├── "已存在" → 禁用状态（无引导）
  └── 什么都不做 → 数据丢失
```

**问题**: 4 个出口、无统一路径、用户需要在多个页面间跳转才能完成一次发票入库。

### 🔴 断点三：详情页职责过载

```
当前 InvoiceDetailView:
  ├── 发票基本信息展示
  ├── 金额统计卡片
  ├── 文件上传/下载/删除
  ├── 编辑按钮（跳转到独立编辑页）
  └── 删除按钮
```

**问题**: 信息查看、编辑操作、文件管理混在同一页面，页面滚动过长，编辑需要跳转到独立页面打断上下文。

### 🔴 断点四：汇总导出与发票管理割裂

```
当前路径:
  /invoices（浏览发票）→ 有导出需求 → /summary（汇总页）→ 再筛选 → 导出
```

**问题**: 用户在发票列表页产生"导出"意图时，需要导航到完全不同的页面重新筛选，流程割裂。

### 🔴 断点五：仪表盘缺乏行动入口

```
当前 HomeView: 系统状态卡片 + 最近操作列表
```

**问题**: 仪表盘只展示信息，不能直接发起操作。用户进入首页后不知道该做什么。

### 🔴 断点六：系统设置前端空壳

```
当前 SettingsView: OCR 配置表单均已展示，但后端 API 未实现
```

**问题**: 用户看到的设置项无法真正生效，产生预期落差。

---

## 2. 信息架构重构

### 2.1 新导航层级

```
┌─────────────────────────────────────────────────────┐
│  🏠 工作台 (Dashboard)          ← 默认首页           │
│  ├── 待办提醒: 本月未报销发票 N 张                   │
│  ├── 快捷入口: 上传发票 | 手动录入                   │
│  └── 数据概览: 本月/本年统计图表                     │
├─────────────────────────────────────────────────────┤
│  📋 发票管理 (Invoice Management)                    │
│  ├── 发票列表 (默认落地页)                           │
│  │   ├── 搜索/筛选/分页                              │
│  │   ├── 批量操作: 标记报销 / 导出 Excel / 删除      │
│  │   └── 单行操作: 查看详情 / 编辑 / 删除            │
│  ├── 发票详情 (子页面)                               │
│  │   ├── Tab: 基本信息 / 消费明细 / 原文件           │
│  │   └── 操作栏: 编辑 / 报销 / 导出 / 删除           │
│  └── 新建发票                                        │
│      ├── 手动录入 (表单)                             │
│      └── OCR 智能识别 (上传即识别→确认→入库)         │
├─────────────────────────────────────────────────────┤
│  📊 数据汇总 (Reports)                               │
│  ├── 发票汇总 (原有 summary 页升级)                  │
│  │   ├── 时间/分类/单位多维度筛选                     │
│  │   ├── 图表: 月度趋势 / 分类占比 / Top 消费单位     │
│  │   └── 导出 Excel / CSV                            │
│  └── 报销报表                                        │
│      ├── 已报销 / 未报销 分布                        │
│      └── 按时间段统计报销金额                         │
├─────────────────────────────────────────────────────┤
│  ⚙️ 基础数据 (Master Data)                          │
│  ├── 消费分类                                        │
│  └── 对方单位                                        │
├─────────────────────────────────────────────────────┤
│  🔧 系统设置                                         │
│  ├── OCR 配置                                        │
│  ├── 存储设置                                        │
│  └── 数据管理 (备份/恢复/重置)                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 面包屑策略

```yaml
面包屑规则:
  首页:                    🏠 工作台
  发票列表:                🏠 工作台 > 📋 发票管理
  发票详情:                🏠 工作台 > 📋 发票管理 > 发票详情: INV-2026-0001
  新建发票:                🏠 工作台 > 📋 发票管理 > 新建发票
  编辑发票:                🏠 工作台 > 📋 发票管理 > 编辑发票: INV-2026-0001
  汇总页:                  🏠 工作台 > 📊 数据汇总
  分类管理:                🏠 工作台 > ⚙️ 基础数据 > 消费分类
  单位管理:                🏠 工作台 > ⚙️ 基础数据 > 对方单位
  系统设置:                🏠 工作台 > 🔧 系统设置
```

### 2.3 路由结构重构

```javascript
// router/index.js 新结构
const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '工作台', icon: 'mdi-view-dashboard', group: 'main' }
  },
  // ── 发票管理组 ──
  {
    path: '/invoices',
    component: () => import('@/layouts/InvoiceLayout.vue'),  // ← 新增布局壳
    meta: { title: '发票管理', icon: 'mdi-receipt', group: 'invoices' },
    children: [
      {
        path: '',
        name: 'InvoiceList',
        component: () => import('@/views/InvoiceListView.vue'),
        meta: { title: '发票列表' }
      },
      {
        path: ':id',
        name: 'InvoiceDetail',
        component: () => import('@/views/InvoiceDetailView.vue'),
        meta: { title: '发票详情' }
      },
      {
        path: ':id/edit',
        name: 'InvoiceEdit',
        component: () => import('@/views/InvoiceEditView.vue'),
        meta: { title: '编辑发票' }
      },
      {
        path: 'new',
        name: 'InvoiceCreate',
        component: () => import('@/views/InvoiceCreateView.vue'),
        meta: { title: '新建发票' }
      }
    ]
  },
  // ── 数据汇总组 ──
  {
    path: '/reports',
    meta: { title: '数据汇总', icon: 'mdi-chart-bar', group: 'reports' },
    children: [
      {
        path: '',
        redirect: '/reports/invoice'
      },
      {
        path: 'invoice',
        name: 'InvoiceReport',
        component: () => import('@/views/InvoiceReportView.vue'),
        meta: { title: '发票汇总' }
      },
      {
        path: 'reimbursement',
        name: 'ReimbursementReport',
        component: () => import('@/views/ReimbursementReportView.vue'),
        meta: { title: '报销报表' }
      }
    ]
  },
  // ── 基础数据组 ──
  {
    path: '/master-data',
    meta: { title: '基础数据', icon: 'mdi-database', group: 'settings' },
    children: [
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/views/CategoriesView.vue'),
        meta: { title: '消费分类' }
      },
      {
        path: 'counterparts',
        name: 'Counterparts',
        component: () => import('@/views/CounterpartsView.vue'),
        meta: { title: '对方单位' }
      }
    ]
  },
  // ── 系统设置 ──
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '系统设置', icon: 'mdi-cog', group: 'settings' }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/AboutView.vue'),
    meta: { title: '关于系统', icon: 'mdi-information', group: 'settings' }
  }
]
```

### 2.4 新导航组件结构

```vue
<!-- App.vue 新结构 -->
<template>
  <v-app>
    <!-- 顶部导航栏 -->
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title>{{ appTitle }}</v-toolbar-title>
      <v-spacer />
      
      <!-- 全局搜索（新增） -->
      <v-text-field
        v-model="globalSearch"
        prepend-inner-icon="mdi-magnify"
        placeholder="搜索发票号码、单位..."
        hide-details
        density="compact"
        class="global-search"
        @keyup.enter="handleGlobalSearch"
      />
      <v-spacer />
      
      <!-- 主题切换 -->
      <v-btn icon @click="toggleTheme">
        <v-icon>{{ theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- 侧边导航（分组折叠） -->
    <v-navigation-drawer v-model="drawer" app width="260">
      <v-list density="compact" nav>
        <!-- 工作台 -->
        <v-list-item to="/" prepend-icon="mdi-view-dashboard" title="工作台" />
        
        <v-divider class="my-2" />
        
        <!-- 发票管理 分组 -->
        <v-list-group value="invoices">
          <template #activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-receipt" title="发票管理" />
          </template>
          <v-list-item to="/invoices" prepend-icon="mdi-format-list-bulleted" title="发票列表" />
          <v-list-item to="/invoices/new" prepend-icon="mdi-plus-circle" title="新建发票" />
        </v-list-group>
        
        <!-- 数据汇总 分组 -->
        <v-list-group value="reports">
          <template #activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-chart-bar" title="数据汇总" />
          </template>
          <v-list-item to="/reports/invoice" prepend-icon="mdi-file-table" title="发票汇总" />
          <v-list-item to="/reports/reimbursement" prepend-icon="mdi-check-circle" title="报销报表" />
        </v-list-group>
        
        <v-divider class="my-2" />
        
        <!-- 基础数据 分组 -->
        <v-list-group value="master-data">
          <template #activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-database" title="基础数据" />
          </template>
          <v-list-item to="/master-data/categories" prepend-icon="mdi-tag" title="消费分类" />
          <v-list-item to="/master-data/counterparts" prepend-icon="mdi-office-building" title="对方单位" />
        </v-list-group>
        
        <v-divider class="my-2" />
        
        <!-- 系统 -->
        <v-list-item to="/settings" prepend-icon="mdi-cog" title="系统设置" />
        <v-list-item to="/about" prepend-icon="mdi-information" title="关于系统" />
      </v-list>
    </v-navigation-drawer>

    <!-- 主内容区 -->
    <v-main>
      <!-- 面包屑（新增） -->
      <v-container fluid class="pa-4 pt-2">
        <v-breadcrumbs :items="breadcrumbs" density="compact">
          <template #divider>
            <v-icon size="small">mdi-chevron-right</v-icon>
          </template>
        </v-breadcrumbs>
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>
```

---

## 3. 三大核心用户旅程

### 3.1 旅程一：OCR 智能入库（高频核心路径）

```
┌──────────────────────────────────────────────────────────────────────┐
│  OCR 智能入库 — 统一工作流                                            │
│                                                                      │
│  [工作台]                                                             │
│     │ 点击 "上传发票" 或 "手动录入"                                    │
│     ▼                                                                │
│  [新建发票页] ← 合并上传 + 手动录入两个入口                           │
│     │                                                                │
│     ├─ Tab 1: "📷 智能识别"  ← 默认激活                              │
│     │   ├── 拖拽/选择文件（PDF / PNG / JPG）                          │
│     │   ├── 可选: OCR 语言 / 自动入库开关                             │
│     │   ├── 点击"开始识别" → 加载动画 + 进度提示                      │
│     │   ├── 识别完成 → 预览面板显示解析结果                           │
│     │   │   ├── 发票号码 / 代码 / 类型 / 日期                         │
│     │   │   ├── 金额汇总（不含税/税额/含税）                          │
│     │   │   ├── 销方单位名称                                          │
│     │   │   └── 消费明细（品名/数量/单价）                            │
│     │   ├── 用户可编辑任意字段（内联编辑）                            │
│     │   ├── 去重检测（如重复，显示"已存在发票 INV-xxx，是否查看？"）  │
│     │   └── 点击 "✅ 确认入库" → 成功提示 → 跳转详情页                │
│     │                                                                │
│     └─ Tab 2: "✏️ 手动录入"                                          │
│         ├── 标准发票表单                                              │
│         ├── 可添加/删除消费明细行                                     │
│         └── 保存 → 跳转详情页                                         │
│                                                                      │
│  关键改进:                                                            │
│  ✅ OCR 和手动录入合并在一个页面（Tab 切换），不用跳转                 │
│  ✅ 识别结果直接可编辑，不再需要"先识别→再跳转编辑页"                  │
│  ✅ 去重后提供"查看已存在发票"链接，不丢上下文                        │
│  ✅ 入库完成后直接进入详情页，显示"下一步"操作建议                     │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 旅程二：发票管理 → 批量报销 + 导出

```
┌──────────────────────────────────────────────────────────────────────┐
│  发票管理 → 批量报销 + 导出                                          │
│                                                                      │
│  [发票列表页]                                                        │
│     │                                                                │
│     ├── 筛选: 日期范围 / 分类 / 单位 / 报销状态 / 金额范围           │
│     ├── 搜索: 发票号码 / 备注关键词                                   │
│     │                                                                │
│     ├── 列表视图（表格 + 分页）                                       │
│     │   ├── ☐ 全选复选框                                             │
│     │   ├── 行: 号码 | 日期 | 类型 | 单位 | 金额 | 分类 | 报销状态   │
│     │   ├── 行操作: 详情 / 编辑 / 删除                                │
│     │   └── 报销状态内联切换（click toggle）                          │
│     │                                                                │
│     ├── 批量操作栏（选中 N 条时出现，固定在底部）                     │
│     │   ├── 🏷️ 标记已报销 → 确认弹窗                                 │
│     │   ├── 📥 导出选中 → 直接下载 Excel                              │
│     │   └── 🗑️ 批量删除 → 二次确认弹窗                               │
│     │                                                                │
│     └── 导出汇总（右上角常驻按钮）                                    │
│         └── 点击 → 弹出设置面板:                                      │
│             ├── 导出范围: 当前筛选结果 / 全部 / 选中                  │
│             ├── 导出格式: Excel (.xlsx) / CSV (.csv)                  │
│             ├── 按分类汇总: ☑                                       │
│             └── [取消] [导出]                                        │
│                                                                      │
│  关键改进:                                                            │
│  ✅ 发票列表页直接支持导出 → 不再需要跳转到 summary 页               │
│  ✅ 批量操作栏固定在底部 → 不打断浏览                                 │
│  ✅ 报销标记内联切换 → 减少页面跳转                                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3 旅程三：发票详情 → 文件管理 → 编辑

```
┌──────────────────────────────────────────────────────────────────────┐
│  发票详情页（Tab 化重构）                                            │
│                                                                      │
│  [发票详情: INV-2026-0001]                    [编辑] [标记报销] [···] │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  [基本信息]  [消费明细]  [原文件(3)]              ← Tab 导航    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                │  │
│  │  Tab 1: 基本信息                                                │  │
│  │  ┌──────────┬──────────┬──────────┬──────────┐                 │  │
│  │  │ 发票号码  │ 发票代码  │ 发票类型  │ 开票日期  │                 │  │
│  │  │ 12345678  │ 3100...  │ 增值税专票│ 2026-05-15│                 │  │
│  │  ├──────────┼──────────┼──────────┼──────────┤                 │  │
│  │  │ 不含税金额│ 税额     │ 含税总金额│ 校验码   │                 │  │
│  │  │ ¥8,547   │ ¥1,453   │ ¥10,000  │ ABC123   │                 │  │
│  │  └──────────┴──────────┴──────────┴──────────┘                 │  │
│  │  对方单位: 上海xxx科技有限公司                                   │  │
│  │  消费分类: 办公用品                                              │  │
│  │  备注: xxx                                                      │  │
│  │  报销状态: ✅ 已报销  创建时间: 2026-05-15  更新时间: 2026-05-20 │  │
│  │                                                                │  │
│  │  Tab 2: 消费明细                                                │  │
│  │  ┌─────┬──────┬────┬───┬─────┬──────┬────┐                    │  │
│  │  │ 品名 │ 规格 │单位│数量│ 单价 │ 金额 │税率│                    │  │
│  │  ├─────┼──────┼────┼───┼─────┼──────┼────┤                    │  │
│  │  │ A4纸│ 70g  │ 箱 │ 10│ ¥85 │ ¥850 │13% │                    │  │
│  │  └─────┴──────┴────┴───┴─────┴──────┴────┘                    │  │
│  │                                                                │  │
│  │  Tab 3: 原文件                                                  │  │
│  │  ┌─────────────────────────────────────────┐                   │  │
│  │  │ 📄 INV-2026-0001.pdf (1.2 MB)           │  [下载] [删除]    │  │
│  │  │ 📄 INV-2026-0001-detail.pdf (0.8 MB)    │  [下载] [删除]    │  │
│  │  │ 🖼️ INV-2026-0001-photo.jpg (2.1 MB)    │  [下载] [删除]    │  │
│  │  └─────────────────────────────────────────┘                   │  │
│  │  [+ 上传更多文件]                                               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  关键改进:                                                            │
│  ✅ Tab 化：基本信息/消费明细/原文件各占一个 Tab，结构清晰不滚动      │
│  ✅ 顶部固定操作栏：编辑/报销/更多菜单常驻可见                        │
│  ✅ 文件管理独立 Tab：上传/下载/删除更直观                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. 页面组件层级规范

### 4.1 页面模板规范

每一个功能页面遵循以下三层结构：

```
PageView.vue
├── PageToolbar        ← 页面工具栏（标题 + 主要操作按钮）
│   ├── 返回按钮（子页面）
│   ├── 页面标题
│   ├── 搜索框（可选）
│   └── 主操作按钮（新建/导出/保存等）
│
├── PageFilter         ← 筛选条件区（仅在列表页出现）
│   ├── 日期范围选择器
│   ├── 下拉筛选（分类/单位/状态）
│   ├── [展开更多筛选]
│   └── [重置筛选]
│
├── PageBody           ← 内容区（列表 / 表单 / 详情 / 图表）
│   ├── v-data-table（列表）
│   ├── v-form（表单）
│   ├── v-card-group（详情 / 仪表盘）
│   └── Chart 组件（汇总）
│
└── BatchActionBar     ← 批量操作栏（仅在列表页选中项时出现）
    ├── 已选 N 项 + 合计金额
    ├── 批量报销 / 批量导出 / 批量删除
    └── 取消选择
```

### 4.2 状态反馈规范

```yaml
加载状态:
  全页加载: v-progress-linear (顶部线性进度条，蓝色)
  区域加载: v-skeleton-loader (骨架屏，卡片/表格区域)
  按钮加载: v-btn :loading (按钮内 spinner)

空状态:
  无数据: 插图 + "暂无发票记录" + [立即创建] 按钮
  搜索无结果: 插图 + "没有找到匹配的发票" + [清除筛选] 按钮
  上传为空: 拖拽区域 + 占位文字

错误状态:
  网络错误: snackbar（底部弹出）+ "网络连接失败，请检查网络"
  服务错误: snackbar + 错误信息 + 错误码
  表单校验: 字段下方红色提示文字 + 聚焦到第一个错误字段

成功反馈:
  创建成功: snackbar（绿色，3秒）+ 自动跳转
  更新成功: snackbar（绿色，3秒）+ 原位停留
  删除成功: snackbar（绿色，3秒）+ 列表刷新
  导出成功: 浏览器下载提示

确认操作:
  删除: 对话框 "确定要删除发票 INV-xxx 吗？此操作不可撤销。"
  批量操作: 对话框 "确定要对 N 张发票标记为已报销吗？"
  数据库重置: 对话框 + 输入 "RESET" 确认
```

### 4.3 表单交互规范

```yaml
表单布局:
  单列表单: 最大宽度 720px，居中，左侧标签
  多列表单: CSS Grid 2-4 列，按语义分组
  动态列表: 每行一个项目 + [添加行] / [删除行] 按钮

字段校验:
  即时校验: blur 事件触发（用户离开字段时）
  提交校验: 点击提交时全量校验
  校验样式:
    未填写: 无样式
    校验中: 灰色边框
    校验通过: 绿色边框 + ✓ 图标
    校验失败: 红色边框 + 错误文字

必填字段: 标签后红色 * 号
禁用状态: 灰色背景 + not-allowed 光标
只读状态: 无边框 + 普通文字样式
```

---

## 5. CSS 设计系统基础

### 5.1 设计令牌

```css
/* ============================================
   发票管理系统 — Design Tokens
   基于 Vuetify 3 Material Design 3 扩展
   ============================================ */

:root {
  /* ── 品牌色 ── */
  --brand-primary: #1565C0;       /* Blue 800 — 主色 */
  --brand-primary-light: #1E88E5; /* Blue 600 — 悬停/高亮 */
  --brand-primary-dark: #0D47A1;  /* Blue 900 — 按压/深色 */
  --brand-accent: #FF6D00;        /* Orange 800 — 强调操作（报销/导出） */
  --brand-success: #2E7D32;       /* Green 800 — 成功/已报销 */
  --brand-warning: #F9A825;       /* Yellow 800 — 待处理 */
  --brand-error: #C62828;         /* Red 800 — 删除/错误 */
  --brand-info: #0277BD;          /* Light Blue 800 — 信息提示 */

  /* ── 中性色 ── */
  --neutral-50: #FAFAFA;
  --neutral-100: #F5F5F5;
  --neutral-200: #EEEEEE;
  --neutral-300: #E0E0E0;
  --neutral-400: #BDBDBD;
  --neutral-500: #9E9E9E;
  --neutral-600: #757575;
  --neutral-700: #616161;
  --neutral-800: #424242;
  --neutral-900: #212121;

  /* ── 排版层级 ── */
  --text-h1: clamp(1.5rem, 2.5vw, 2.125rem);  /* 34px 页面主标题 */
  --text-h2: clamp(1.25rem, 2vw, 1.5rem);      /* 24px 区块标题 */
  --text-h3: 1.125rem;                          /* 18px 卡片标题 */
  --text-body: 0.875rem;                        /* 14px 正文 */
  --text-caption: 0.75rem;                      /* 12px 辅助文字 */
  --text-label: 0.8125rem;                      /* 13px 标签 */
  
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;
  --line-height-tight: 1.2;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* ── 间距系统 (4px 基准) ── */
  --space-1: 0.25rem;   /* 4px  — 图标/标签间距 */
  --space-2: 0.5rem;    /* 8px  — 紧凑间距 */
  --space-3: 0.75rem;   /* 12px — 表单字段间距 */
  --space-4: 1rem;      /* 16px — 卡片内边距 */
  --space-6: 1.5rem;    /* 24px — 区块间距 */
  --space-8: 2rem;      /* 32px — 页面分区 */
  --space-12: 3rem;     /* 48px — 大区块 */
  --space-16: 4rem;     /* 64px — 页面级间距 */

  /* ── 圆角系统 ── */
  --radius-sm: 4px;     /* 按钮/标签/输入框 */
  --radius-md: 8px;     /* 卡片/对话框 */
  --radius-lg: 12px;    /* 大卡片/面板 */
  --radius-xl: 16px;    /* 模态框标签 */
  --radius-round: 9999px; /* 药丸/徽章 */

  /* ── 阴影系统 ── */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.08);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.1), 0 10px 10px rgba(0,0,0,0.04);

  /* ── 过渡动画 ── */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);

  /* ── 布局容器 ── */
  --container-max: 1280px;
  --container-form: 720px;
  --sidebar-width: 260px;
  --appbar-height: 64px;
  --batch-bar-height: 56px;
}

/* ── 暗色主题覆盖 ── */
[data-theme="dark"] {
  --neutral-50: #121212;
  --neutral-100: #1E1E1E;
  --neutral-200: #2D2D2D;
  --neutral-300: #3D3D3D;
  --neutral-400: #5C5C5C;
  /* ... others adapt via Vuetify */
}
```

### 5.2 通用组件样式

```css
/* ============================================
   发票管理系统 — 组件样式基类
   ============================================ */

/* ── 页面工具栏 ── */
.page-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--neutral-200);
  margin-bottom: var(--space-6);
}
.page-toolbar__title {
  font-size: var(--text-h1);
  font-weight: var(--font-weight-bold);
  flex: 1;
}

/* ── 筛选区域 ── */
.page-filter {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--neutral-50);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-4);
}

/* ── 批量操作栏 ── */
.batch-action-bar {
  position: fixed;
  bottom: 0;
  left: var(--sidebar-width);
  right: 0;
  height: var(--batch-bar-height);
  background: var(--brand-primary);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 var(--space-6);
  gap: var(--space-4);
  z-index: 10;
  box-shadow: var(--shadow-lg);
  transform: translateY(100%);
  transition: transform var(--transition-base);
}
.batch-action-bar--visible {
  transform: translateY(0);
}

/* ── 空状态插画 ── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-4);
  color: var(--neutral-500);
  text-align: center;
  gap: var(--space-4);
}

/* ── 状态徽章 ── */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px 10px;
  border-radius: var(--radius-round);
  font-size: var(--text-caption);
  font-weight: var(--font-weight-medium);
}
.status-badge--reimbursed {
  background: #E8F5E9;
  color: #2E7D32;
}
.status-badge--pending {
  background: #FFF8E1;
  color: #F57F17;
}

/* ── 金额数字格式 ── */
.amount {
  font-variant-numeric: tabular-nums;  /* 等宽数字 */
  font-weight: var(--font-weight-medium);
  text-align: right;
}
.amount--positive { color: var(--brand-success); }
.amount--with-tax { font-size: var(--text-h2); font-weight: var(--font-weight-bold); }

/* ── 响应式断点 ── */
@media (max-width: 960px) {
  :root {
    --sidebar-width: 0px;
  }
  .page-filter {
    flex-direction: column;
  }
  .batch-action-bar {
    left: 0;
  }
}
```

---

## 6. 实施路线图

### Phase 1: 导航与信息架构（优先级最高）

| 任务 | 工作量 | 依赖 |
|---|---|---|
| 1.1 重构 App.vue：分组导航 + 面包屑 | 0.5 天 | — |
| 1.2 重构路由结构：嵌套路由 + meta 字段 | 0.5 天 | 1.1 |
| 1.3 新增 InvoiceLayout.vue（发票管理布局壳） | 0.5 天 | 1.2 |
| 1.4 将所有现有页面适配新路由 | 1 天 | 1.2 |

### Phase 2: 核心流程重构

| 任务 | 工作量 | 依赖 |
|---|---|---|
| 2.1 合并 Upload + NewInvoice → InvoiceCreateView（Tab: 智能识别 / 手动录入） | 1.5 天 | Phase 1 |
| 2.2 重构 InvoiceDetailView：Tab 化（基本信息 / 消费明细 / 原文件） | 1 天 | Phase 1 |
| 2.3 重构 InvoiceListView：批量操作栏 + 内联报销切换 + 内联导出面板 | 1 天 | 1.4 |
| 2.4 新增全局搜索功能 | 0.5 天 | 1.4 |

### Phase 3: 仪表盘与汇总

| 任务 | 工作量 | 依赖 |
|---|---|---|
| 3.1 重构 DashboardView：快捷入口面板 + 统计图表 | 1 天 | Phase 1 |
| 3.2 重构汇总页为 InvoiceReportView（增强图表 + 多维度筛选） | 1 天 | Phase 1 |
| 3.3 新增 ReimbursementReportView（报销追踪视图） | 0.5 天 | 3.1 |

### Phase 4: 交互细节打磨

| 任务 | 工作量 | 依赖 |
|---|---|---|
| 4.1 全局状态反馈（骨架屏 / 空状态 / 错误处理） | 1 天 | Phase 2 |
| 4.2 表单即时校验 + 字段级错误提示 | 0.5 天 | Phase 2 |
| 4.3 键盘快捷键（Ctrl+K 搜索 / Ctrl+N 新建 / Esc 关闭弹窗） | 0.5 天 | Phase 1 |
| 4.4 过渡动画（页面切换 / 列表过滤 / 弹窗进出） | 0.5 天 | Phase 2 |

### Phase 5: 后端补全

| 任务 | 工作量 | 依赖 |
|---|---|---|
| 5.1 实现系统设置页的 API（OCR 配置读写 / 备份 / 恢复） | 1 天 | — |
| 5.2 添加统计汇总 API（月度趋势 / 分类占比 / 报销统计） | 0.5 天 | — |
| 5.3 添加全局搜索 API | 0.5 天 | — |

---

## 附录 A: 页面状态矩阵

| 页面 | 加载中 | 空数据 | 错误 | 正常 | 批量操作 |
|---|---|---|---|---|---|
| 工作台 | ✅ 骨架屏 | ✅ 引导创建 | ✅ 重试按钮 | ✅ 统计卡片 | — |
| 发票列表 | ✅ 表格骨架 | ✅ 空状态 | ✅ 重试 | ✅ 数据表格 | ✅ 底部操作栏 |
| 发票详情 | ✅ 详情骨架 | ✅ 404 页面 | ✅ 重试 | ✅ Tab 面板 | — |
| 新建发票 | — | ✅ 空表单 | ✅ 保存失败 | ✅ 表单 | — |
| 发票汇总 | ✅ 图表骨架 | ✅ 无数据提示 | ✅ 重试 | ✅ 图表+表格 | ✅ 导出面板 |
| 分类/单位管理 | ✅ 表格骨架 | ✅ 引导创建 | ✅ 重试 | ✅ 数据表格 | — |
| 系统设置 | ✅ 面板骨架 | — | ✅ 保存失败 | ✅ 配置表单 | — |

## 附录 B: 关键交互时序

```
发票列表搜索：
  输入关键词 → debounce 300ms → 更新 query → API 请求 → 表格刷新
  筛选变更：选择 → 即时 query 更新 → API 请求 → 表格刷新

OCR 识别：
  选择文件 → 前端预览 → 点击识别 → progress linear → API 请求
  → 轮询状态（如需要） → 返回结果 → 渲染预览面板

批量报销：
  选中行 → 批量操作栏展开 → 点击"标记已报销"
  → 确认对话框 → API 请求（乐观更新） → 成功 snackbar

导出 Excel：
  点击导出 → 设置面板 → 确认 → API 请求 → Blob 下载
  → 成功 snackbar（"已导出 15 条发票记录"）
```

---

> **下一步**: 请审阅以上方案，确认后按 Phase 顺序逐步实施。每个 Phase 完成后进行一轮验收测试。
