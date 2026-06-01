import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/invoices',
    name: 'Invoices',
    component: () => import('@/views/InvoicesView.vue')
  },
  {
    path: '/invoices/new',
    name: 'NewInvoice',
    component: () => import('@/views/NewInvoiceView.vue')
  },
  {
    path: '/invoices/:id',
    name: 'InvoiceDetail',
    component: () => import('@/views/InvoiceDetailView.vue')
  },
  {
    path: '/invoices/:id/edit',
    name: 'EditInvoice',
    component: () => import('@/views/EditInvoiceView.vue')
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/UploadView.vue')
  },
  {
    path: '/categories',
    name: 'Categories',
    component: () => import('@/views/CategoriesView.vue')
  },
  {
    path: '/counterparts',
    name: 'Counterparts',
    component: () => import('@/views/CounterpartsView.vue')
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue')
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('@/views/AboutView.vue')
  },
  {
    path: '/summary',
    name: 'Summary',
    component: () => import('@/views/InvoiceSummaryView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router