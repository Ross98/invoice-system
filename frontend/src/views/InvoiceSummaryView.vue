<template>
  <div>
    <!-- 标题 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span class="text-h5">发票汇总</span>
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          :disabled="selectedIds.length === 0"
          :loading="exporting"
          @click="exportExcel"
        >
          <v-icon left>mdi-file-excel</v-icon>
          导出 Excel ({{ selectedIds.length }})
        </v-btn>
      </v-card-title>
    </v-card>

    <!-- 筛选条件 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.startDate"
              label="开始日期"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="filters.endDate"
              label="结束日期"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="filters.categoryId"
              label="消费分类"
              :items="categoryItems"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" md="3">
            <v-btn color="primary" block @click="loadInvoices">查询</v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 操作栏 -->
    <v-card class="mb-4">
      <v-card-text class="d-flex align-center py-2">
        <v-btn variant="text" size="small" @click="selectAll">全选</v-btn>
        <v-btn variant="text" size="small" @click="deselectAll">取消全选</v-btn>
        <v-divider vertical class="mx-2"></v-divider>
        <span class="text-body-2 text-grey">
          已选择 {{ selectedIds.length }} / {{ invoices.length }} 张发票，
          合计金额：¥{{ totalSelectedAmount.toFixed(2) }}
        </span>
      </v-card-text>
    </v-card>

    <!-- 发票列表 -->
    <v-card>
      <v-card-text>
        <v-data-table
          v-model="selectedIds"
          :headers="headers"
          :items="invoices"
          :loading="loading"
          show-select
          item-value="id"
          hover
          @click:row="toggleSelect"
        >
          <template v-slot:item.invoice_date="{ item }">
            {{ formatDate(item.invoice_date) }}
          </template>
          <template v-slot:item.total_with_tax="{ item }">
            ¥{{ formatAmount(item.total_with_tax) }}
          </template>
          <template v-slot:item.counterpart="{ item }">
            {{ item.counterpart?.name || '-' }}
          </template>
          <template v-slot:item.category="{ item }">
            {{ item.category?.name || '-' }}
          </template>
          <template v-slot:item.is_reimbursed="{ item }">
            <v-chip :color="item.is_reimbursed ? 'success' : 'grey'" size="small" variant="tonal">
              {{ item.is_reimbursed ? '已报销' : '未报销' }}
            </v-chip>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useInvoiceStore } from '@/stores/invoice'
import api from '@/api'

const invoiceStore = useInvoiceStore()
const loading = ref(false)
const exporting = ref(false)
const invoices = ref([])
const selectedIds = ref([])
const categoryItems = ref([])

const headers = [
  { title: '发票号码', key: 'invoice_number', sortable: true },
  { title: '类型', key: 'invoice_type', sortable: true },
  { title: '开票日期', key: 'invoice_date', sortable: true },
  { title: '含税金额', key: 'total_with_tax', sortable: true },
  { title: '对方单位', key: 'counterpart', sortable: false },
  { title: '分类', key: 'category', sortable: false },
  { title: '报销状态', key: 'is_reimbursed', sortable: false },
]

const filters = reactive({
  startDate: '',
  endDate: '',
  categoryId: null,
})

const totalSelectedAmount = computed(() => {
  return invoices.value
    .filter(inv => selectedIds.value.includes(inv.id))
    .reduce((sum, inv) => sum + (Number(inv.total_with_tax) || 0), 0)
})

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '0.00'
  return Number(amount).toFixed(2)
}

const loadInvoices = async () => {
  loading.value = true
  try {
    const res = await api.get('/invoices', {
      params: {
        start_date: filters.startDate || undefined,
        end_date: filters.endDate || undefined,
        category_id: filters.categoryId || undefined,
        limit: 200,
      }
    })
    invoices.value = res.items || []
    selectedIds.value = []
  } catch (err) {
    console.error('加载发票列表失败:', err)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  await invoiceStore.fetchCategories()
  categoryItems.value = invoiceStore.categories
}

const selectAll = () => {
  selectedIds.value = invoices.value.map(inv => inv.id)
}

const deselectAll = () => {
  selectedIds.value = []
}

const toggleSelect = (event, { item }) => {
  const idx = selectedIds.value.indexOf(item.id)
  if (idx >= 0) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(item.id)
  }
}

const exportExcel = async () => {
  if (selectedIds.value.length === 0) return
  exporting.value = true
  try {
    const response = await api.post('/invoices/export', selectedIds.value, {
      responseType: 'blob',
    })
    // 创建下载链接
    const url = window.URL.createObjectURL(response)
    const link = document.createElement('a')
    link.href = url
    link.download = '费用报销汇总.xlsx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('导出失败:', err)
    alert('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await loadCategories()
  await loadInvoices()
})
</script>
