import axios from "axios";

export const TIMEOUT_DEFAULT = 10000;
export const TIMEOUT_LONG = 60000;

const api = axios.create({
  baseURL: "/api",
  timeout: TIMEOUT_DEFAULT,
  headers: {
    "Content-Type": "application/json",
  },
});

// 长操作 axios 实例(OCR 大文件、导出等)
export const axiosLong = axios.create({
  baseURL: "/api",
  timeout: TIMEOUT_LONG,
  headers: {
    "Content-Type": "application/json",
  },
})

// 请求拦截器
;[api, axiosLong].forEach(instance => {
  instance.interceptors.request.use(
    config => {
      // 可以在这里添加 token 等
      return config;
    },
    error => {
      return Promise.reject(error);
    },
  );

  instance.interceptors.response.use(
    response => response.data,
    error => {
      if (error.response) {
        const { status, data } = error.response;
        let message = data?.detail || "请求失败";

        if (status === 401) {
          message = "未授权，请重新登录";
        } else if (status === 403) {
          message = "权限不足";
        } else if (status === 404) {
          message = "资源不存在";
        } else if (status === 409) {
          message = data?.detail || "数据冲突：发票已存在";
        } else if (status >= 500) {
          message = data?.detail || "服务器错误";
        }

        return Promise.reject({ message, status, data });
      } else if (error.request) {
        return Promise.reject({ message: "网络连接失败" });
      } else {
        return Promise.reject({ message: error.message });
      }
    },
  );
});

// 发票相关 API
export const invoiceApi = {
  // 获取发票列表
  getInvoices(params) {
    return api.get("/invoices", { params });
  },
  
  // 获取单张发票
  getInvoice(id) {
    return api.get(`/invoices/${id}`);
  },
  
  // 创建发票
  createInvoice(data) {
    return api.post("/invoices", data);
  },
  
  // 更新发票
  updateInvoice(id, data) {
    return api.put(`/invoices/${id}`, data);
  },
  
  // 删除发票
  deleteInvoice(id) {
    return api.delete(`/invoices/${id}`);
  },
  
  // 上传文件
  uploadFile(invoiceId, file) {
    const formData = new FormData();
    formData.append("file", file);
    return axiosLong.post(`/invoices/${invoiceId}/files`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  
  // 获取文件列表
  getFiles(invoiceId) {
    return api.get(`/invoices/${invoiceId}/files`);
  },
  
  // 下载文件
  downloadFile(invoiceId, fileId) {
    return api.get(`/invoices/${invoiceId}/files/${fileId}/download`, {
      responseType: "blob",
    });
  },
  
  // 删除文件
  deleteFile(invoiceId, fileId) {
    return api.delete(`/invoices/${invoiceId}/files/${fileId}`);
  },
};

// OCR 相关 API
export const ocrApi = {
  // 检查 OCR 状态
  getStatus() {
    return api.get("/ocr/status");
  },
  
  // OCR 识别文件
  recognizeFile(file, lang = "chi_sim+eng") {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lang", lang);
    return axiosLong.post("/ocr/recognize", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // OCR 识别并关联到发票
  recognizeAndAssociate(invoiceId, file, lang = "chi_sim+eng") {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lang", lang);
    return axiosLong.post(`/ocr/recognize/${invoiceId}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 解析发票信息
  parseInvoice(file, lang = "chi_sim+eng") {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("lang", lang);
    return axiosLong.post("/ocr/parse", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // 导入发票
  importInvoice(invoiceData) {
    return axiosLong.post("/ocr/import", invoiceData);
  },
};

// 分类管理 API
export const categoryApi = {
  getCategories() {
    return api.get("/categories");
  },
  
  createCategory(data) {
    return api.post("/categories", data);
  },
  
  updateCategory(id, data) {
    return api.put(`/categories/${id}`, data);
  },
  
  deleteCategory(id) {
    return api.delete(`/categories/${id}`);
  },
};

// 对方单位管理 API
export const counterpartApi = {
  getCounterparts() {
    return api.get("/counterparts");
  },
  
  createCounterpart(data) {
    return api.post("/counterparts", data);
  },
  
  updateCounterpart(id, data) {
    return api.put(`/counterparts/${id}`, data);
  },
  
  deleteCounterpart(id) {
    return api.delete(`/counterparts/${id}`);
  },
};

// 统计汇总 API
export const statsApi = {
  getDashboard(year, month) {
    return api.get("/stats/dashboard", { params: { year, month } });
  },
};

// 全局搜索 API
export const searchApi = {
  search(query, limit = 20) {
    return api.get("/search", { params: { q: query, limit } });
  },
};

// 系统设置 API
export const settingsApi = {
  getSettings() {
    return api.get("/settings");
  },

  saveOcrSettings(data) {
    return api.put("/settings/ocr", data);
  },

  saveStorageSettings(data) {
    return api.put("/settings/storage", data);
  },

  backupDatabase() {
    return axiosLong.post("/settings/backup", {}, { responseType: "blob" });
  },

  resetDatabase() {
    return api.post("/settings/reset");
  },
};

export default api;