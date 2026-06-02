<template>
  <div>
    <!-- 顶部标题 + 操作按钮 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span class="text-h5">发票管理</span>
        <v-spacer></v-spacer>
        <v-btn color="secondary" variant="tonal" class="mr-2" @click="exportDialog = true">
          <v-icon left>mdi-file-export</v-icon>
          导出
        </v-btn>
        <v-btn color="primary" @click="$router.push('/invoices/new')">
          <v-icon left>mdi-plus</v-icon>
          新建发票
        </v-btn>
      </v-card-title>
    </v-card>

    <!-- 搜索筛选 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="search.invoiceNumber"
              label="发票号码"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="search.searchText"
              label="全文搜索"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="search.invoiceType"
              label="发票类型"
              :items="typeOptions"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-select>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="search.categoryId"
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
          <v-col cols="12" md="2">
            <v-btn color="primary" block @click="handleSearch">查询</v-btn>
          </v-col>
        </v-row>
        <v-row dense>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="search.startDate"
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
              v-model="search.endDate"
              label="结束日期"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="search.minAmount"
              label="最低金额"
              type="number"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field
              v-model="search.maxAmount"
              label="最高金额"
              type="number"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            ></v-text-field>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 发票表格 -->
    <v-card>
      <v-card-text class="pa-0">
        <v-data-table
          v-model="selectedItems"
          :headers="headers"
          :items="invoices"
          :loading="loading"
          :items-length="pagination.total"
          :page="pagination.page"
          :items-per-page="pagination.pageSize"
          :items-per-page-options="[10, 20, 50]"
          :show-select="true"
          item-value="id"
          hover
          return-object
          @update:page="onPageChange"
          @update:items-per-page="onPageSizeChange"
        >
          <template v-slot:item.invoice_date="{ item }">
            {{ formatDate(item.invoice_date) }}
          </template>
          <template v-slot:item.total_with_tax="{ item }">
            <span class="font-weight-bold">¥{{ formatAmount(item.total_with_tax) }}</span>
          </template>
          <template v-slot:item.counterpart="{ item }">
            {{ item.counterpart?.name || '-' }}
          </template>
          <template v-slot:item.category="{ item }">
            <v-chip size="x-small" variant="tonal" :color="item.category?.color || 'grey'">
              {{ item.category?.name || '-' }}
            </v-chip>
          </template>
          <template v-slot:item.is_reimbursed="{ item }">
            <v-chip
              :color="item.is_reimbursed ? 'success' : 'warning'"
              size="small"
              variant="tonal"
              class="cursor-pointer"
              @click.stop="toggleReimbursed(item)"
            >
              {{ item.is_reimbursed ? '已报销' : '未报销' }}
            </v-chip>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              icon
              variant="text"
              size="small"
              @click.stop="$router.push(`/invoices/${item.id}`)"
              title="查看详情"
            >
              <v-icon>mdi-eye</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              @click.stop="$router.push(`/invoices/${item.id}/edit`)"
              title="编辑"
            >
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              size="small"
              color="error"
              @click.stop="confirmDelete(item)"
              title="删除"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 批量操作栏（固定在底部） -->
    <v-slide-y-reverse-transition>
      <v-card
        v-if="selectedItems.length > 0"
        class="batch-action-bar"
        color="primary"
        variant="tonal"
        elevation="8"
      >
        <v-card-text class="d-flex align-center pa-3">
          <v-icon class="mr-2">mdi-checkbox-multiple-marked</v-icon>
          <span class="text-body-1 mr-4">已选 {{ selectedItems.length }} 项</span>
          <v-spacer></v-spacer>
          <v-btn
            color="success"
            variant="elevated"
            size="small"
            class="mr-2"
            @click="batchToggleReimbursed(true)"
          >
            <v-icon left size="18">mdi-check-circle</v-icon>
            标记已报销
          </v-btn>
          <v-btn
            color="secondary"
            variant="elevated"
            size="small"
            class="mr-2"
            @click="batchExport"
          >
            <v-icon left size="18">mdi-file-export</v-icon>
            导出选中
          </v-btn>
          <v-btn
            color="error"
            variant="tonal"
            size="small"
            @click="batchDeleteConfirm"
          >
            <v-icon left size="18">mdi-delete</v-icon>
            删除
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            class="ml-2"
            @click="selectedItems = []"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-text>
      </v-card>
    </v-slide-y-reverse-transition>

    <!-- 导出对话框 -->
    <v-dialog v-model="exportDialog" max-width="480">
      <v-card>
        <v-card-title class="text-h6">导出发票数据</v-card-title>
        <v-card-text>
          <v-select
            v-model="exportScope"
            label="导出范围"
            :items="exportScopes"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          <v-select
            v-model="exportFormat"
            label="导出格式"
            :items="exportFormats"
            variant="outlined"
            density="compact"
            class="mb-3"
          ></v-select>
          <v-checkbox
            v-model="exportSummarize"
            label="按分类汇总"
            density="compact"
            hide-details
          ></v-checkbox>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="exportDialog = false">取消</v-btn>
          <v-btn color="primary" :loading="exporting" @click="doExport">
            <v-icon left>mdi-download</v-icon>
            导出
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量删除确认 -->
    <v-dialog v-model="batchDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h6">批量删除确认</v-card-title>
        <v-card-text>
          确定要删除选中的 {{ batchDeleteTarget.length }} 张发票吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="batchDeleteDialog = false">取消</v-btn>
          <v-btn color="error" :loading="batchDeleting" @click="doBatchDelete">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useInvoiceStore } from '@/stores/invoice'

const router = useRouter()
const invoiceStore = useInvoiceStore()

const loading = ref(false)
const invoices = ref([])
const selectedItems = ref([])

const headers = [
  { title: '发票号码', key: 'invoice_number', sortable: true },
  { title: '发票代码', key: 'invoice_code', sortable: true },
  { title: '类型', key: 'invoice_type', sortable: true },
  { title: '开票日期', key: 'invoice_date', sortable: true },
  { title: '含税金额', key: 'total_with_tax', sortable: true },
  { title: '对方单位', key: 'counterpart', sortable: false },
  { title: '分类', key: 'category', sortable: false },
  { title: '报销状态', key: 'is_reimbursed', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

const typeOptions = ['增值税专票', '增值税普票', '电子发票']
const categoryItems = ref([])

const search = reactive({
  invoiceNumber: '',
  searchText: '',
  invoiceType: '',
  categoryId: null,
  startDate: '',
  endDate: '',
  minAmount: '',
  maxAmount: ''
})

const pagination = computed(() => ({
  page: invoiceStore.pagination.page,
  pageSize: invoiceStore.pagination.pageSize,
  total: invoiceStore.pagination.total
}))

// ── 导出 ──
const exportDialog = ref(false)
const exporting = ref(false)
const exportScope = ref('current')
const exportFormat = ref('xlsx')
const exportSummarize = ref(false)

const exportScopes = [
  { title: '当前筛选结果', value: 'current' },
  { title: '全部发票', value: 'all' },
  { title: '已报销', value: 'reimbursed' },
  { title: '未报销', value: 'unreimbursed' }
]
const exportFormats = [
  { title: 'Excel (.xlsx)', value: 'xlsx' },
  { title: 'CSV (.csv)', value: 'csv' }
]

// ── 批量操作 ──
const batchDeleteDialog = ref(false)
const batchDeleting = ref(false)
const batchDeleteTarget = ref([])

const formatDate = (d) => d ? new Date(d).toLocaleDateString('zh-CN') : ''
const formatAmount = (v) => (v != null) ? Number(v).toFixed(2) : '0.00'

// ── 数据加载 ──
const buildParams = () => ({
  invoice_number: search.invoiceNumber || undefined,
  search_text: search.searchText || undefined,
  invoice_type: search.invoiceType || undefined,
  category_id: search.categoryId || undefined,
  start_date: search.startDate || undefined,
  end_date: search.endDate || undefined,
  min_amount: search.minAmount !== '' && search.minAmount != null ? search.minAmount : undefined,
  max_amount: search.maxAmount !== '' && search.maxAmount != null ? search.maxAmount : undefined
})

const loadInvoices = async () => {
  loading.value = true
  try {
    await invoiceStore.fetchInvoices(buildParams())
    invoices.value = invoiceStore.invoices
  } catch (e) {
    console.error('加载发票列表失败:', e)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  await invoiceStore.fetchCategories()
  categoryItems.value = invoiceStore.categories
}

const handleSearch = () => {
  selectedItems.value = []
  invoiceStore.setPage(1)
  loadInvoices()
}

const onPageChange = (page) => {
  invoiceStore.setPage(page)
  selectedItems.value = []
  loadInvoices()
}

const onPageSizeChange = (size) => {
  invoiceStore.setPageSize(size)
  selectedItems.value = []
  loadInvoices()
}

// ── 单条操作 ──
const toggleReimbursed = async (invoice) => {
  const newVal = !invoice.is_reimbursed
  invoice.is_reimbursed = newVal
  try {
    await invoiceStore.updateInvoice(invoice.id, { is_reimbursed: newVal })
  } catch {
    invoice.is_reimbursed = !newVal
  }
}

const confirmDelete = async (invoice) => {
  if (!confirm(`确定要删除发票 "${invoice.invoice_number}" 吗？`)) return
  try {
    await invoiceStore.deleteInvoice(invoice.id)
    await loadInvoices()
  } catch (e) {
    console.error('删除失败:', e)
  }
}

// ── 批量操作 ──
const batchToggleReimbursed = async (val) => {
  const ids = selectedItems.value.map(i => i.id)
  for (const item of selectedItems.value) {
    item.is_reimbursed = val
  }
  try {
    // 逐条更新（后端没有批量接口，后续可加）
    for (const id of ids) {
      await invoiceStore.updateInvoice(id, { is_reimbursed: val })
    }
    selectedItems.value = []
  } catch {
    // 回退
    for (const item of selectedItems.value) {
      item.is_reimbursed = !val
    }
  }
}

const batchExport = () => {
  const ids = selectedItems.value.map(i => i.id)
  const params = new URLSearchParams()
  params.set('format', 'xlsx')
  params.set('summarize', exportSummarize.value.toString())
  ids.forEach(id => params.append('ids', id))
  window.open(`/api/invoices/export?${params.toString()}`, '_blank')
}

const batchDeleteConfirm = () => {
  batchDeleteTarget.value = [...selectedItems.value]
  batchDeleteDialog.value = true
}

const doBatchDelete = async () => {
  batchDeleting.value = true
  try {
    for (const item of batchDeleteTarget.value) {
      await invoiceStore.deleteInvoice(item.id)
    }
    batchDeleteDialog.value = false
    selectedItems.value = []
    await loadInvoices()
  } catch (e) {
    console.error('批量删除失败:', e)
    alert('删除失败: ' + (e.message || '未知错误'))
  } finally {
    batchDeleting.value = false
  }
}

// ── 导出对话框 ──
const doExport = async () => {
  exporting.value = true
  try {
    const params = new URLSearchParams()
    params.set('format', exportFormat.value)
    params.set('summarize', exportSummarize.value.toString())
    if (exportScope.value === 'current') {
      Object.entries(buildParams()).forEach(([k, v]) => {
        if (v !== undefined && v !== '') params.set(k, v)
      })
    } else if (exportScope.value === 'reimbursed') {
      params.set('is_reimbursed', 'true')
    } else if (exportScope.value === 'unreimbursed') {
      params.set('is_reimbursed', 'false')
    }
    window.open(`/api/invoices/export?${params.toString()}`, '_blank')
    exportDialog.value = false
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await loadCategories()
  await loadInvoices()
})
</script>

<style scoped>
.batch-action-bar {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 32px);
  max-width: 900px;
  z-index: 100;
  border-radius: 12px;
}
.cursor-pointer {
  cursor: pointer;
}
</style>
