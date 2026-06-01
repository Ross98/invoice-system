<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span class="text-h5">发票管理</span>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="$router.push('/invoices/new')">
          <v-icon left>mdi-plus</v-icon>
          新建发票
        </v-btn>
      </v-card-title>
    </v-card>

    <!-- 搜索筛选 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row>
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
        <v-row>
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

    <!-- 发票列表 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="invoices"
          :loading="loading"
          :items-length="pagination.total"
          :page="pagination.page"
          :items-per-page="pagination.pageSize"
          :items-per-page-options="[10, 20, 50]"
          hover
          item-value="id"
          @click:row="goToDetail"
          @update:page="onPageChange"
          @update:items-per-page="onPageSizeChange"
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
            <v-checkbox
              :model-value="item.is_reimbursed"
              density="compact"
              hide-details
              @click.stop="toggleReimbursed(item)"
            ></v-checkbox>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn icon variant="text" size="small" @click.stop="editInvoice(item)">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon variant="text" size="small" @click.stop="confirmDelete(item)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除发票 {{ selectedInvoice?.invoice_number }} 吗？
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="deleteInvoice">删除</v-btn>
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
const deleteDialog = ref(false)
const selectedInvoice = ref(null)

const headers = [
  { title: '发票号码', key: 'invoice_number', sortable: true },
  { title: '发票代码', key: 'invoice_code', sortable: true },
  { title: '类型', key: 'invoice_type', sortable: true },
  { title: '开票日期', key: 'invoice_date', sortable: true },
  { title: '含税金额', key: 'total_with_tax', sortable: true },
  { title: '对方单位', key: 'counterpart', sortable: false },
  { title: '分类', key: 'category', sortable: false },
  { title: '是否报销', key: 'is_reimbursed', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

const typeOptions = [
  '增值税专票',
  '增值税普票',
  '电子发票'
]

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
    await invoiceStore.fetchInvoices({
      invoice_number: search.invoiceNumber || undefined,
      search_text: search.searchText || undefined,
      invoice_type: search.invoiceType || undefined,
      category_id: search.categoryId || undefined,
      start_date: search.startDate || undefined,
      end_date: search.endDate || undefined,
      min_amount: search.minAmount !== '' && search.minAmount != null ? search.minAmount : undefined,
      max_amount: search.maxAmount !== '' && search.maxAmount != null ? search.maxAmount : undefined
    })
    invoices.value = invoiceStore.invoices
  } catch (error) {
    console.error('加载发票列表失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  invoiceStore.setPage(1)
  loadInvoices()
}

const loadCategories = async () => {
  await invoiceStore.fetchCategories()
  categoryItems.value = invoiceStore.categories
}

const onPageChange = async (page) => {
  invoiceStore.setPage(page)
  await loadInvoices()
}

const onPageSizeChange = async (pageSize) => {
  invoiceStore.setPageSize(pageSize)
  await loadInvoices()
}

const goToDetail = (event, { item }) => {
  router.push(`/invoices/${item.id}`)
}

const editInvoice = (invoice) => {
  router.push(`/invoices/${invoice.id}/edit`)
}

const confirmDelete = (invoice) => {
  selectedInvoice.value = invoice
  deleteDialog.value = true
}

const deleteInvoice = async () => {
  if (selectedInvoice.value) {
    try {
      await invoiceStore.deleteInvoice(selectedInvoice.value.id)
      await loadInvoices()
    } catch (error) {
      console.error('删除发票失败:', error)
    }
  }
  deleteDialog.value = false
}

const toggleReimbursed = async (invoice) => {
  const newValue = !invoice.is_reimbursed
  // 乐观更新
  invoice.is_reimbursed = newValue
  try {
    await invoiceStore.updateInvoice(invoice.id, { is_reimbursed: newValue })
  } catch (error) {
    // 失败时回退
    invoice.is_reimbursed = !newValue
    console.error('更新报销状态失败:', error)
  }
}

onMounted(async () => {
  await loadCategories()
  await loadInvoices()
})
</script>