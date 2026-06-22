<template>
  <div>
    <!-- 页面标题 -->
    <div class="d-flex align-center mb-4">
      <h2 class="text-h4 font-weight-bold">
        发票汇总
      </h2>
      <v-spacer />
      <v-progress-linear
        v-if="loading"
        indeterminate
        color="primary"
        class="flex-grow-0 mx-4"
        style="max-width: 200px"
      />
      <v-btn
        color="primary"
        variant="tonal"
        prepend-icon="mdi-file-excel"
        :loading="exporting"
        :disabled="selectedIds.length === 0"
        @click="exportExcel"
      >
        导出 Excel ({{ selectedIds.length }})
      </v-btn>
    </div>

    <!-- 统计概览行 -->
    <v-row class="mb-4">
      <v-col
        cols="12"
        sm="4"
      >
        <v-card
          border
          flat
        >
          <v-card-text class="pa-3 d-flex align-center">
            <v-avatar
              size="36"
              color="primary"
              variant="tonal"
              class="mr-3"
            >
              <v-icon size="18">
                mdi-receipt
              </v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-medium-emphasis">
                筛选结果
              </div>
              <div class="text-h6 font-weight-bold">
                {{ invoices.length }} 张
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col
        cols="12"
        sm="4"
      >
        <v-card
          border
          flat
        >
          <v-card-text class="pa-3 d-flex align-center">
            <v-avatar
              size="36"
              color="success"
              variant="tonal"
              class="mr-3"
            >
              <v-icon size="18">
                mdi-cash
              </v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-medium-emphasis">
                总金额
              </div>
              <div class="text-h6 font-weight-bold">
                ¥{{ fmtAmount(totalAmount) }}
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col
        cols="12"
        sm="4"
      >
        <v-card
          border
          flat
        >
          <v-card-text class="pa-3 d-flex align-center">
            <v-avatar
              size="36"
              color="warning"
              variant="tonal"
              class="mr-3"
            >
              <v-icon size="18">
                mdi-clock-outline
              </v-icon>
            </v-avatar>
            <div>
              <div class="text-caption text-medium-emphasis">
                待报销
              </div>
              <div class="text-h6 font-weight-bold">
                {{ pendingCount }} 张
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 筛选条件 -->
    <v-card
      class="mb-4"
      border
      flat
    >
      <v-card-text class="pb-0">
        <v-row>
          <v-col
            cols="12"
            sm="4"
            md="2"
          >
            <v-text-field
              v-model="filters.startDate"
              label="开始日期"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col
            cols="12"
            sm="4"
            md="2"
          >
            <v-text-field
              v-model="filters.endDate"
              label="结束日期"
              type="date"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col
            cols="12"
            sm="4"
            md="2"
          >
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
            />
          </v-col>
          <v-col
            cols="6"
            sm="3"
            md="2"
          >
            <v-select
              v-model="filters.counterpartId"
              label="对方单位"
              :items="counterpartItems"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col
            cols="6"
            sm="3"
            md="2"
          >
            <v-select
              v-model="filters.reimbursed"
              label="报销状态"
              :items="[{ title: '全部', value: null }, { title: '已报销', value: 'yes' }, { title: '待报销', value: 'no' }]"
              variant="outlined"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col
            cols="6"
            sm="3"
            md="2"
          >
            <v-btn
              color="primary"
              block
              variant="tonal"
              @click="loadInvoices"
            >
              查询
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 分类占比预览条 -->
    <v-card
      v-if="categoryBars.length > 0"
      class="mb-4"
      border
      flat
    >
      <v-card-title class="text-subtitle-2 font-weight-bold py-2">
        分类占比
      </v-card-title>
      <v-card-text class="py-0">
        <div
          class="category-bar-stack mb-2"
          style="height: 24px; border-radius: 12px; overflow: hidden; display: flex;"
        >
          <div
            v-for="(bar, i) in categoryBars"
            :key="bar.name"
            :style="{
              width: bar.pct + '%',
              background: catColor(i),
              minWidth: bar.pct > 0 ? '4px' : '0',
            }"
            :title="`${bar.name}: ¥${fmtAmount(bar.amount)}`"
          ></div>
        </div>
        <div class="d-flex flex-wrap ga-3 pb-2">
          <div
            v-for="(bar, i) in categoryBars.slice(0, 8)"
            :key="bar.name"
            class="d-flex align-center"
          >
            <div
              :style="{
                width: '10px', height: '10px', borderRadius: '2px',
                background: catColor(i), marginRight: '4px',
              }"
            ></div>
            <span class="text-caption">{{ bar.name }} ¥{{ fmtAmount(bar.amount) }}</span>
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 操作栏 -->
    <v-card
      v-if="selectedIds.length > 0"
      class="mb-4"
      border
      flat
    >
      <v-card-text class="d-flex align-center py-2">
        <v-btn
          variant="text"
          size="small"
          @click="selectAll"
        >
          全选
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          @click="deselectAll"
        >
          取消全选
        </v-btn>
        <v-divider
          vertical
          class="mx-2"
        />
        <span class="text-body-2 text-grey">
          已选择 {{ selectedIds.length }} / {{ invoices.length }} 张，
          合计金额：¥{{ fmtAmount(totalSelectedAmount) }}
        </span>
      </v-card-text>
    </v-card>

    <!-- 发票列表 -->
    <v-card
      border
      flat
    >
      <v-data-table-server
        v-model="selectedIds"
        :headers="headers"
        :items="invoices"
        :loading="loading"
        :items-length="totalCount"
        :page="page"
        :items-per-page="pageSize"
        :items-per-page-options="[20, 50, 100, 200]"
        show-select
        item-value="id"
        hover
        density="compact"
        @update:page="onPageChange"
        @update:items-per-page="onPageSizeChange"
      >
        <template #item.invoice_date="{ item }">
          {{ formatDate(item.invoice_date) }}
        </template>
        <template #item.total_with_tax="{ item }">
          <span class="font-weight-medium">¥{{ fmtAmount(item.total_with_tax) }}</span>
        </template>
        <template #item.counterpart="{ item }">
          {{ item.counterpart?.name || '-' }}
        </template>
        <template #item.category="{ item }">
          <v-chip
            size="x-small"
            variant="flat"
          >
            {{ item.category?.name || '-' }}
          </v-chip>
        </template>
        <template #item.is_reimbursed="{ item }">
          <v-chip
            :color="item.is_reimbursed ? 'success' : 'warning'"
            size="x-small"
            variant="flat"
          >
            {{ item.is_reimbursed ? '已报销' : '待报销' }}
          </v-chip>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useInvoiceStore } from "@/stores/invoice";
import api from "@/api";

const invoiceStore = useInvoiceStore();
const loading = ref(false);
const exporting = ref(false);
const invoices = ref([]);
const selectedIds = ref([]);
const categoryItems = ref([]);
const counterpartItems = ref([]);

// 分页状态
const page = ref(1);
const pageSize = ref(50);
const totalCount = ref(0);

const headers = [
  { title: "发票号码", key: "invoice_number", sortable: true },
  { title: "类型", key: "invoice_type", sortable: true },
  { title: "开票日期", key: "invoice_date", sortable: true },
  { title: "含税金额", key: "total_with_tax", sortable: true },
  { title: "对方单位", key: "counterpart" },
  { title: "分类", key: "category" },
  { title: "报销状态", key: "is_reimbursed" },
];

const filters = reactive({
  startDate: "",
  endDate: "",
  categoryId: null,
  counterpartId: null,
  reimbursed: null,
});

const totalAmount = computed(() =>
  invoices.value.reduce((s, i) => s + (Number(i.total_with_tax) || 0), 0),
);

const pendingCount = computed(() =>
  invoices.value.filter(i => !i.is_reimbursed).length,
);

const totalSelectedAmount = computed(() =>
  invoices.value
    .filter(inv => selectedIds.value.includes(inv.id))
    .reduce((sum, inv) => sum + (Number(inv.total_with_tax) || 0), 0),
);

const categoryBars = computed(() => {
  const map = {};
  invoices.value.forEach(inv => {
    const name = inv.category?.name || "其他";
    map[name] = (map[name] || 0) + (Number(inv.total_with_tax) || 0);
  });
  const max = Math.max(...Object.values(map), 1);
  return Object.entries(map)
    .map(([name, amount]) => ({ name, amount: Math.round(amount * 100) / 100, pct: Math.round((amount / max) * 100) }))
    .sort((a, b) => b.amount - a.amount);
});

const catColors = [
  "#1565C0", "#2E7D32", "#F57F17", "#C62828", "#6A1B9A",
  "#00838F", "#4E342E", "#37474F", "#AD1457", "#283593",
];
function catColor(i) { return catColors[i % catColors.length]; }

function fmtAmount(val) {
  if (val == null || isNaN(val)) return "0";
  return Number(val).toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatDate(d) {
  if (!d) return "";
  return new Date(d).toLocaleDateString("zh-CN");
}

async function loadInvoices() {
  loading.value = true;
  try {
    const params = {
      skip: (page.value - 1) * pageSize.value,
      limit: pageSize.value,
    };
    if (filters.startDate) params.start_date = filters.startDate;
    if (filters.endDate) params.end_date = filters.endDate;
    if (filters.categoryId) params.category_id = filters.categoryId;
    if (filters.counterpartId) params.counterpart_id = filters.counterpartId;
    if (filters.reimbursed === "yes") params.is_reimbursed = "true";
    else if (filters.reimbursed === "no") params.is_reimbursed = "false";
    const res = await api.get("/invoices", { params });
    invoices.value = res.items || [];
    totalCount.value = res.total != null ? res.total : (res.items?.length || 0);
    selectedIds.value = [];
  } catch (err) {
    console.error("加载失败:", err);
  } finally {
    loading.value = false;
  }
}

function onPageChange(newPage) {
  page.value = newPage;
  loadInvoices();
}

function onPageSizeChange(newSize) {
  pageSize.value = newSize;
  page.value = 1;
  loadInvoices();
}

async function loadMeta() {
  await invoiceStore.fetchCategories();
  categoryItems.value = invoiceStore.categories;
  try {
    const parts = await api.get("/counterparts");
    counterpartItems.value = parts || [];
  } catch { /* counterpart fetch is optional */ }
}

function selectAll() { selectedIds.value = invoices.value.map(i => i.id); }
function deselectAll() { selectedIds.value = []; }

async function exportExcel() {
  if (selectedIds.value.length === 0) return;
  exporting.value = true;
  try {
    const blob = await api.post("/invoices/export", selectedIds.value, { responseType: "blob" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "费用报销汇总.xlsx"; document.body.appendChild(a);
    a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("导出失败:", err);
  } finally {
    exporting.value = false;
  }
}

onMounted(async () => {
  await loadMeta();
  await loadInvoices();
});
</script>
