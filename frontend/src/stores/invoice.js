import { defineStore } from 'pinia'
import { invoiceApi, categoryApi, counterpartApi } from '@/api'

export const useInvoiceStore = defineStore('invoice', {
  state: () => ({
    invoices: [],
    currentInvoice: null,
    categories: [],
    counterparts: [],
    loading: false,
    error: null,
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0
    }
  }),

  getters: {
    totalPages: (state) => Math.ceil(state.pagination.total / state.pagination.pageSize),
    hasNextPage: (state) => state.pagination.page < Math.ceil(state.pagination.total / state.pagination.pageSize),
    hasPrevPage: (state) => state.pagination.page > 1
  },

  actions: {
    async fetchInvoices(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await invoiceApi.getInvoices({
          skip: (this.pagination.page - 1) * this.pagination.pageSize,
          limit: this.pagination.pageSize,
          ...params
        })
        this.invoices = response.items || response
        this.pagination.total = response.total || response.length
      } catch (err) {
        this.error = err.message
        console.error('获取发票列表失败:', err)
      } finally {
        this.loading = false
      }
    },

    async getInvoice(id) {
      this.loading = true
      this.error = null
      try {
        this.currentInvoice = await invoiceApi.getInvoice(id)
        return this.currentInvoice
      } catch (err) {
        this.error = err.message
        console.error('获取发票详情失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async createInvoice(invoiceData) {
      this.loading = true
      this.error = null
      try {
        const newInvoice = await invoiceApi.createInvoice(invoiceData)
        this.invoices.unshift(newInvoice)
        return newInvoice
      } catch (err) {
        this.error = err.message
        console.error('创建发票失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateInvoice(id, invoiceData) {
      this.loading = true
      this.error = null
      try {
        const updatedInvoice = await invoiceApi.updateInvoice(id, invoiceData)
        const index = this.invoices.findIndex(i => i.id === id)
        if (index !== -1) {
          this.invoices[index] = updatedInvoice
        }
        if (this.currentInvoice?.id === id) {
          this.currentInvoice = updatedInvoice
        }
        return updatedInvoice
      } catch (err) {
        this.error = err.message
        console.error('更新发票失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteInvoice(id) {
      this.loading = true
      this.error = null
      try {
        await invoiceApi.deleteInvoice(id)
        this.invoices = this.invoices.filter(i => i.id !== id)
        if (this.currentInvoice?.id === id) {
          this.currentInvoice = null
        }
      } catch (err) {
        this.error = err.message
        console.error('删除发票失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async uploadFile(invoiceId, file) {
      this.loading = true
      this.error = null
      try {
        const fileRecord = await invoiceApi.uploadFile(invoiceId, file)
        if (this.currentInvoice?.id === invoiceId) {
          this.currentInvoice.files = this.currentInvoice.files || []
          this.currentInvoice.files.push(fileRecord)
        }
        return fileRecord
      } catch (err) {
        this.error = err.message
        console.error('上传文件失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchCategories() {
      try {
        this.categories = await categoryApi.getCategories()
      } catch (err) {
        console.error('获取分类失败:', err)
      }
    },

    async createCategory(data) {
      this.loading = true
      try {
        const cat = await categoryApi.createCategory(data)
        this.categories.push(cat)
        return cat
      } catch (err) {
        this.error = err.message
        console.error('创建分类失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async updateCategory(id, data) {
      this.loading = true
      try {
        const updated = await categoryApi.updateCategory(id, data)
        const idx = this.categories.findIndex(c => c.id === id)
        if (idx !== -1) this.categories[idx] = updated
        return updated
      } catch (err) {
        this.error = err.message
        console.error('更新分类失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async deleteCategory(id) {
      this.loading = true
      try {
        await categoryApi.deleteCategory(id)
        this.categories = this.categories.filter(c => c.id !== id)
      } catch (err) {
        this.error = err.message
        console.error('删除分类失败:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async fetchCounterparts() {
      try {
        this.counterparts = await counterpartApi.getCounterparts()
      } catch (err) {
        console.error('获取对方单位失败:', err)
      }
    },

    setPage(page) {
      this.pagination.page = page
    },

    setPageSize(size) {
      this.pagination.pageSize = size
      this.pagination.page = 1
    },

    clearCurrentInvoice() {
      this.currentInvoice = null
    }
  }
})