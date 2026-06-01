<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-btn variant="text" icon @click="$router.push('/invoices')">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <span class="text-h5 ml-2">发票详情</span>
        <v-spacer></v-spacer>
        <v-btn color="warning" variant="outlined" class="mr-2" @click="editInvoice">
          <v-icon left>mdi-pencil</v-icon>
          编辑
        </v-btn>
        <v-btn color="error" variant="outlined" @click="confirmDelete">
          <v-icon left>mdi-delete</v-icon>
          删除
        </v-btn>
      </v-card-title>
    </v-card>

    <v-row v-if="invoice">
      <!-- 基本信息 -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>基本信息</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-receipt</v-icon>
                </template>
                <v-list-item-title>发票号码</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.invoice_number }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-barcode</v-icon>
                </template>
                <v-list-item-title>发票代码</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.invoice_code }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-tag</v-icon>
                </template>
                <v-list-item-title>发票类型</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.invoice_type }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-calendar</v-icon>
                </template>
                <v-list-item-title>开票日期</v-list-item-title>
                <v-list-item-subtitle>{{ formatDate(invoice.invoice_date) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-check-decagram</v-icon>
                </template>
                <v-list-item-title>校验码</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.check_code || '无' }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-office-building</v-icon>
                </template>
                <v-list-item-title>对方单位</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.counterpart?.name || '未指定' }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="primary">mdi-shape</v-icon>
                </template>
                <v-list-item-title>消费分类</v-list-item-title>
                <v-list-item-subtitle>{{ invoice.category?.name || '未分类' }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 金额信息 -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>金额信息</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-caption text-grey">不含税金额</div>
                  <div class="text-h5 mt-2">¥{{ formatAmount(invoice.total_amount) }}</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-caption text-grey">税额</div>
                  <div class="text-h5 mt-2">¥{{ formatAmount(invoice.tax_amount) }}</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-caption text-grey">含税总金额</div>
                  <div class="text-h5 mt-2">¥{{ formatAmount(invoice.total_with_tax) }}</div>
                </v-card>
              </v-col>
            </v-row>

            <v-divider class="my-4"></v-divider>

            <div class="text-body-1">
              <strong>备注：</strong>{{ invoice.remark || '无' }}
            </div>
            <div class="text-body-2 text-grey mt-4">
              创建时间：{{ formatDateTime(invoice.created_at) }}<br>
              修改时间：{{ formatDateTime(invoice.updated_at) }}
            </div>
          </v-card-text>
        </v-card>

        <!-- 文件管理 -->
        <v-card class="mt-4">
          <v-card-title>发票文件</v-card-title>
          <v-card-text>
            <div v-if="invoice.files && invoice.files.length > 0">
              <v-list>
                <v-list-item v-for="file in invoice.files" :key="file.id">
                  <template v-slot:prepend>
                    <v-icon :color="getFileIconColor(file.file_type)">
                      {{ getFileIcon(file.file_type) }}
                    </v-icon>
                  </template>
                  <v-list-item-title>{{ file.file_name }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}
                  </v-list-item-subtitle>
                  <template v-slot:append>
                    <v-btn icon variant="text" size="small" @click="downloadFile(file)">
                      <v-icon>mdi-download</v-icon>
                    </v-btn>
                    <v-btn icon variant="text" size="small" @click="deleteFile(file)">
                      <v-icon>mdi-delete</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-else class="text-center py-4">
              <v-icon size="48" color="grey">mdi-file-outline</v-icon>
              <div class="text-body-1 mt-2">暂无文件</div>
            </div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="uploadFile">
              <v-icon left>mdi-upload</v-icon>
              上传文件
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- 消费明细 -->
      <v-col cols="12">
        <v-card>
          <v-card-title>消费明细</v-card-title>
          <v-card-text>
            <v-data-table
              v-if="invoice.details && invoice.details.length > 0"
              :headers="detailHeaders"
              :items="invoice.details"
              hover
              hide-default-footer
            >
              <template v-slot:item.unit_price="{ item }">
                ¥{{ formatAmount(item.unit_price) }}
              </template>
              <template v-slot:item.amount="{ item }">
                ¥{{ formatAmount(item.amount) }}
              </template>
              <template v-slot:item.service_date="{ item }">
                {{ formatDate(item.service_date) }}
              </template>
            </v-data-table>
            <div v-else class="text-center py-4">
              <v-icon size="48" color="grey">mdi-format-list-bulleted</v-icon>
              <div class="text-body-1 mt-2">暂无消费明细</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 文件上传对话框 -->
    <v-dialog v-model="uploadDialog" max-width="400">
      <v-card>
        <v-card-title>上传发票文件</v-card-title>
        <v-card-text>
          <v-file-input
            v-model="newFiles"
            label="选择文件"
            accept=".pdf,.png,.jpg,.jpeg"
            prepend-icon="mdi-paperclip"
            variant="outlined"
          ></v-file-input>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="uploadDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleUpload" :loading="uploadingFile">
            上传
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { invoiceApi } from '@/api'

const route = useRoute()
const router = useRouter()

const invoice = ref(null)
const uploadDialog = ref(false)
const uploadingFile = ref(false)
const newFiles = ref([])

const detailHeaders = [
  { title: '品名', key: 'item_name', sortable: false },
  { title: '规格', key: 'spec', sortable: false },
  { title: '单位', key: 'unit', sortable: false },
  { title: '数量', key: 'quantity', sortable: false },
  { title: '单价', key: 'unit_price', sortable: false },
  { title: '金额', key: 'amount', sortable: false },
  { title: '税率', key: 'tax_rate', sortable: false },
  { title: '服务日期', key: 'service_date', sortable: false }
]

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '0.00'
  return Number(amount).toFixed(2)
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileIcon = (type) => {
  const icons = { 'pdf': 'mdi-file-pdf', 'png': 'mdi-file-image', 'jpg': 'mdi-file-image', 'jpeg': 'mdi-file-image' }
  return icons[type?.toLowerCase()] || 'mdi-file'
}

const getFileIconColor = (type) => {
  if (type?.toLowerCase() === 'pdf') return 'red'
  if (['png', 'jpg', 'jpeg'].includes(type?.toLowerCase())) return 'green'
  return 'grey'
}

const loadInvoice = async () => {
  try {
    invoice.value = await invoiceApi.getInvoice(route.params.id)
  } catch (error) {
    console.error('加载发票详情失败:', error)
    router.push('/invoices')
  }
}

const editInvoice = () => {
  router.push(`/invoices/${route.params.id}/edit`)
}

const confirmDelete = async () => {
  if (confirm('确定要删除这张发票吗？')) {
    try {
      await invoiceApi.deleteInvoice(route.params.id)
      router.push('/invoices')
    } catch (error) {
      console.error('删除发票失败:', error)
    }
  }
}

const uploadFile = () => {
  uploadDialog.value = true
  newFiles.value = []
}

const handleUpload = async () => {
  if (!newFiles.value.length) return

  uploadingFile.value = true
  try {
    for (const file of newFiles.value) {
      await invoiceApi.uploadFile(route.params.id, file)
    }
    await loadInvoice()
    uploadDialog.value = false
  } catch (error) {
    console.error('上传文件失败:', error)
    alert('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploadingFile.value = false
  }
}

const downloadFile = async (file) => {
  try {
    const response = await invoiceApi.downloadFile(route.params.id, file.id)
    const url = window.URL.createObjectURL(new Blob([response]))
    const a = document.createElement('a')
    a.href = url
    a.download = file.file_name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载文件失败:', error)
  }
}

const deleteFile = async (file) => {
  if (confirm(`确定要删除文件 "${file.file_name}" 吗？`)) {
    try {
      await invoiceApi.deleteFile(route.params.id, file.id)
      await loadInvoice()
    } catch (error) {
      console.error('删除文件失败:', error)
    }
  }
}

onMounted(() => {
  loadInvoice()
})
</script>