import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data } = error.response
      let message = data?.detail || '请求失败'
      
      if (status === 401) {
        message = '未授权，请重新登录'
      } else if (status === 403) {
        message = '权限不足'
      } else if (status === 404) {
        message = '资源不存在'
      } else if (status === 409) {
        message = data?.detail || '数据冲突：发票已存在'
      } else if (status >= 500) {
        message = data?.detail || '服务器错误'
      }
      
      return Promise.reject({ message, status, data })
    } else if (error.request) {
      return Promise.reject({ message: '网络连接失败' })
    } else {
      return Promise.reject({ message: error.message })
    }
  }
)

// 发票相关 API
export const invoiceApi = {
  // 获取发票列表
  getInvoices(params) {
    return api.get('/invoices', { params })
  },
  
  // 获取单张发票
  getInvoice(id) {
    return api.get(`/invoices/${id}`)
  },
  
  // 创建发票
  createInvoice(data) {
    return api.post('/invoices', data)
  },
  
  // 更新发票
  updateInvoice(id, data) {
    return api.put(`/invoices/${id}`, data)
  },
  
  // 删除发票
  deleteInvoice(id) {
    return api.delete(`/invoices/${id}`)
  },
  
  // 上传文件
  uploadFile(invoiceId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/invoices/${invoiceId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 获取文件列表
  getFiles(invoiceId) {
    return api.get(`/invoices/${invoiceId}/files`)
  },
  
  // 下载文件
  downloadFile(invoiceId, fileId) {
    return api.get(`/invoices/${invoiceId}/files/${fileId}/download`, {
      responseType: 'blob'
    })
  },
  
  // 删除文件
  deleteFile(invoiceId, fileId) {
    return api.delete(`/invoices/${invoiceId}/files/${fileId}`)
  }
}

// OCR 相关 API
export const ocrApi = {
  // 检查 OCR 状态
  getStatus() {
    return api.get('/ocr/status')
  },
  
  // OCR 识别文件
  recognizeFile(file, lang = 'chi_sim+eng') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('lang', lang)
    return api.post('/ocr/recognize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // OCR 识别并关联到发票
  recognizeAndAssociate(invoiceId, file, lang = 'chi_sim+eng') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('lang', lang)
    return api.post(`/ocr/recognize/${invoiceId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 解析发票信息
  parseInvoice(file, lang = 'chi_sim+eng') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('lang', lang)
    return api.post('/ocr/parse', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 导入发票
  importInvoice(invoiceData) {
    return api.post('/ocr/import', invoiceData)
  }
}

// 分类管理 API
export const categoryApi = {
  getCategories() {
    return api.get('/categories')
  },
  
  createCategory(data) {
    return api.post('/categories', data)
  },
  
  updateCategory(id, data) {
    return api.put(`/categories/${id}`, data)
  },
  
  deleteCategory(id) {
    return api.delete(`/categories/${id}`)
  }
}

// 对方单位管理 API
export const counterpartApi = {
  getCounterparts() {
    return api.get('/counterparts')
  },
  
  createCounterpart(data) {
    return api.post('/counterparts', data)
  },
  
  updateCounterpart(id, data) {
    return api.put(`/counterparts/${id}`, data)
  },
  
  deleteCounterpart(id) {
    return api.delete(`/counterparts/${id}`)
  }
}

export default api