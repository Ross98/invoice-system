import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // ── 工作台 ──
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { title: '工作台', icon: 'mdi-view-dashboard', group: 'dashboard' }
  },

  // ── 发票管理组（嵌套，保留 InvoiceLayout 壳） ──
  {
    path: '/invoices',
    component: () => import('@/layouts/InvoiceLayout.vue'),
    meta: { title: '发票管理', icon: 'mdi-receipt', group: 'invoices' },
    children: [
      {
        path: '',
        name: 'InvoiceList',
        component: () => import('@/views/InvoicesView.vue'),
        meta: { title: '发票列表' }
      },
      {
        path: 'new',
        name: 'InvoiceCreate',
        component: () => import('@/views/InvoiceCreateView.vue'),
        meta: { title: '新建发票' }
      },
      {
        path: ':id/edit',
        name: 'InvoiceEdit',
        component: () => import('@/views/EditInvoiceView.vue'),
        meta: { title: '编辑发票' }
      },
      {
        path: ':id',
        name: 'InvoiceDetail',
        component: () => import('@/views/InvoiceDetailView.vue'),
        meta: { title: '发票详情' }
      }
    ]
  },

  // ── 数据汇总组（扁平，无父壳组件） ──
  {
    path: '/reports/invoice',
    name: 'InvoiceReport',
    component: () => import('@/views/InvoiceSummaryView.vue'),
    meta: { title: '发票汇总', icon: 'mdi-file-table', group: 'reports', parentTitle: '数据汇总' }
  },
  {
    path: '/reports/reimbursement',
    name: 'ReimbursementReport',
    component: () => import('@/views/ReimbursementReportView.vue'),
    meta: { title: '报销报表', icon: 'mdi-check-circle', group: 'reports', parentTitle: '数据汇总' }
  },

  // ── 基础数据组（扁平，无父壳组件） ──
  {
    path: '/master-data/categories',
    name: 'Categories',
    component: () => import('@/views/CategoriesView.vue'),
    meta: { title: '消费分类', icon: 'mdi-tag', group: 'master-data', parentTitle: '基础数据' }
  },
  {
    path: '/master-data/counterparts',
    name: 'Counterparts',
    component: () => import('@/views/CounterpartsView.vue'),
    meta: { title: '对方单位', icon: 'mdi-office-building', group: 'master-data', parentTitle: '基础数据' }
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
  },

  // ── 向后兼容重定向 ──
  { path: '/upload',    redirect: '/invoices/new' },
  { path: '/summary',   redirect: '/reports/invoice' },
  { path: '/categories', redirect: '/master-data/categories' },
  { path: '/counterparts', redirect: '/master-data/counterparts' },
  { path: '/reports',   redirect: '/reports/invoice' },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
