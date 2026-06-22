import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import * as api from '@/api'
import { useInvoiceStore } from '../invoice'

vi.mock('@/api', () => ({
  invoiceApi: {
    getInvoices: vi.fn(),
    getInvoice: vi.fn(),
    createInvoice: vi.fn(),
    updateInvoice: vi.fn(),
    deleteInvoice: vi.fn(),
    uploadFile: vi.fn(),
    getFiles: vi.fn(),
    downloadFile: vi.fn(),
    deleteFile: vi.fn()
  },
  categoryApi: {
    getCategories: vi.fn(),
    createCategory: vi.fn(),
    updateCategory: vi.fn(),
    deleteCategory: vi.fn()
  },
  counterpartApi: {
    getCounterparts: vi.fn(),
    createCounterpart: vi.fn(),
    updateCounterpart: vi.fn(),
    deleteCounterpart: vi.fn()
  },
  ocrApi: {},
  statsApi: {},
  searchApi: {},
  settingsApi: {}
}))

const mockedApi = api

describe('useInvoiceStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useInvoiceStore()
    vi.clearAllMocks()
    // 抑制 store 内部 console.error 输出,避免测试噪音
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  // ===== P2-08 修复: fetchInvoices 响应格式适配 =====
  describe('fetchInvoices - 响应格式适配 (P2-08)', () => {
    it('数组格式响应: invoices 应为该数组,total 为数组长度', async () => {
      const arr = [{ id: 1, invoice_no: 'A001' }, { id: 2, invoice_no: 'A002' }]
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockResolvedValue(arr)

      await store.fetchInvoices()

      expect(store.invoices).toEqual(arr)
      expect(store.pagination.total).toBe(arr.length)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('对象格式响应: invoices 应为 items,total 取自 total 字段', async () => {
      const obj = { items: [{ id: 10, invoice_no: 'B001' }], total: 100 }
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockResolvedValue(obj)

      await store.fetchInvoices()

      expect(store.invoices).toEqual(obj.items)
      expect(store.pagination.total).toBe(100)
    })

    it('空数组响应: total 应为 0,不应崩溃', async () => {
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockResolvedValue([])

      await store.fetchInvoices()

      expect(store.invoices).toEqual([])
      expect(store.pagination.total).toBe(0)
    })

    it('防御: API 抛错不应让 store 进入无效状态', async () => {
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockRejectedValue(
        new Error('网络失败')
      )

      await store.fetchInvoices()

      expect(store.error).toBe('网络失败')
      expect(store.loading).toBe(false)
      // 后续 getter 应仍可访问,不抛错
      expect(() => store.totalPages).not.toThrow()
      expect(() => store.hasNextPage).not.toThrow()
      expect(() => store.hasPrevPage).not.toThrow()
    })

    it('防御: 异常类型响应 (字符串) 不应让后续 filter/reduce 崩溃', async () => {
      // 模拟后端返回畸形响应(非数组非对象有 items 的东西)
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockResolvedValue('bad response')

      await store.fetchInvoices()

      // 即使是非预期响应,store 不应抛错
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
      // 后续链式操作不应崩溃
      expect(() => {
        // 模拟组件中可能的 reduce/filter
        if (Array.isArray(store.invoices)) {
          store.invoices.filter(i => i.id)
        }
      }).not.toThrow()
    })

    it('分页参数: 应正确计算 skip/limit 并与 params 合并', async () => {
      vi.mocked(mockedApi.invoiceApi.getInvoices).mockResolvedValue({ items: [], total: 0 })

      store.setPageSize(50)
      store.setPage(3)
      await store.fetchInvoices({ keyword: 'test' })

      expect(mockedApi.invoiceApi.getInvoices).toHaveBeenCalledWith({
        skip: 100, // (3-1) * 50
        limit: 50,
        keyword: 'test'
      })
    })
  })

  // ===== pagination getter =====
  describe('pagination getters', () => {
    it('totalPages: 向上取整', () => {
      store.pagination.total = 45
      store.pagination.pageSize = 20
      expect(store.totalPages).toBe(3) // ceil(45/20) = 3

      store.pagination.total = 40
      expect(store.totalPages).toBe(2)

      store.pagination.total = 0
      expect(store.totalPages).toBe(0)
    })

    it('hasNextPage: 当前页小于总页数时为 true', () => {
      store.pagination.total = 45
      store.pagination.pageSize = 20
      store.pagination.page = 1
      expect(store.hasNextPage).toBe(true)

      store.pagination.page = 3
      expect(store.hasNextPage).toBe(false)
    })

    it('hasPrevPage: 当前页大于 1 时为 true', () => {
      store.pagination.page = 1
      expect(store.hasPrevPage).toBe(false)

      store.pagination.page = 2
      expect(store.hasPrevPage).toBe(true)
    })
  })

  // ===== createInvoice =====
  describe('createInvoice', () => {
    it('成功: API 返回新发票,应插入到 invoices 头部', async () => {
      const existing = [{ id: 2, invoice_no: 'X002' }]
      store.invoices = existing
      const newInv = { id: 1, invoice_no: 'X001', amount: 100 }
      vi.mocked(mockedApi.invoiceApi.createInvoice).mockResolvedValue(newInv)

      const result = await store.createInvoice({ invoice_no: 'X001', amount: 100 })

      expect(result).toEqual(newInv)
      expect(store.invoices[0]).toEqual(newInv)
      expect(store.invoices).toHaveLength(2)
      expect(store.loading).toBe(false)
      expect(store.error).toBeNull()
    })

    it('失败: API 抛错,应设置 error 并 rethrow', async () => {
      const err = new Error('创建失败')
      vi.mocked(mockedApi.invoiceApi.createInvoice).mockRejectedValue(err)

      await expect(store.createInvoice({})).rejects.toThrow('创建失败')

      expect(store.error).toBe('创建失败')
      expect(store.loading).toBe(false)
    })
  })

  // ===== deleteInvoice =====
  describe('deleteInvoice', () => {
    it('成功: 从 invoices 中移除,并清空 currentInvoice(若 id 匹配)', async () => {
      store.invoices = [
        { id: 1, invoice_no: 'A' },
        { id: 2, invoice_no: 'B' },
        { id: 3, invoice_no: 'C' }
      ]
      store.currentInvoice = { id: 2, invoice_no: 'B' }
      vi.mocked(mockedApi.invoiceApi.deleteInvoice).mockResolvedValue(undefined)

      await store.deleteInvoice(2)

      expect(store.invoices).toHaveLength(2)
      expect(store.invoices.find(i => i.id === 2)).toBeUndefined()
      expect(store.currentInvoice).toBeNull()
      expect(store.error).toBeNull()
    })

    it('失败: API 抛错,应设置 error 并 rethrow', async () => {
      const err = new Error('删除失败')
      vi.mocked(mockedApi.invoiceApi.deleteInvoice).mockRejectedValue(err)

      await expect(store.deleteInvoice(1)).rejects.toThrow('删除失败')

      expect(store.error).toBe('删除失败')
    })
  })

  // ===== updateInvoice =====
  describe('updateInvoice', () => {
    it('成功: 更新 list 中对应项 + currentInvoice', async () => {
      store.invoices = [
        { id: 1, invoice_no: 'A', amount: 100 },
        { id: 2, invoice_no: 'B', amount: 200 }
      ]
      store.currentInvoice = { id: 1, invoice_no: 'A', amount: 100 }
      const updated = { id: 1, invoice_no: 'A', amount: 999 }
      vi.mocked(mockedApi.invoiceApi.updateInvoice).mockResolvedValue(updated)

      const result = await store.updateInvoice(1, { amount: 999 })

      expect(result).toEqual(updated)
      expect(store.invoices[0]).toEqual(updated)
      expect(store.currentInvoice).toEqual(updated)
      expect(store.error).toBeNull()
    })

    it('成功: 仅更新 list,不影响 currentInvoice(若 id 不匹配)', async () => {
      store.invoices = [{ id: 1, invoice_no: 'A' }]
      store.currentInvoice = { id: 99, invoice_no: 'Z' }
      const updated = { id: 1, invoice_no: 'A-new' }
      vi.mocked(mockedApi.invoiceApi.updateInvoice).mockResolvedValue(updated)

      await store.updateInvoice(1, { invoice_no: 'A-new' })

      expect(store.invoices[0]).toEqual(updated)
      expect(store.currentInvoice).toEqual({ id: 99, invoice_no: 'Z' })
    })

    it('失败: API 抛错,应设置 error 并 rethrow', async () => {
      const err = new Error('更新失败')
      vi.mocked(mockedApi.invoiceApi.updateInvoice).mockRejectedValue(err)

      await expect(store.updateInvoice(1, {})).rejects.toThrow('更新失败')

      expect(store.error).toBe('更新失败')
    })
  })
})
