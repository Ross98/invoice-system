<template>
  <div>
    <!-- 页面标题 -->
    <div class="d-flex align-center mb-4">
      <h2 class="text-h4 font-weight-bold">报销报表</h2>
      <v-spacer />
      <v-btn
        variant="tonal"
        color="primary"
        prepend-icon="mdi-file-excel"
        :loading="exportLoading"
        @click="exportReport"
      >
        导出 Excel
      </v-btn>
    </div>

    <!-- 统计概览 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card border flat>
          <v-card-text class="pa-4 text-center">
            <v-icon size="36" color="primary" class="mb-2">mdi-receipt</v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.overall.total_count }}</div>
            <div class="text-caption text-medium-emphasis">发票总数</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card border flat>
          <v-card-text class="pa-4 text-center">
            <v-icon size="36" color="success" class="mb-2">mdi-check-circle</v-icon>
            <div class="text-h4 font-weight-bold">{{ stats.overall.total_reimbursed }}</div>
            <div class="text-caption text-medium-emphasis">已报销</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card border flat>
          <v-card-text class="pa-4 text-center">
            <v-icon size="36" color="warning" class="mb-2">mdi-clock-outline</v-icon>
            <div class="text-h4 font-weight-bold">{{ pendingCount }}</div>
            <div class="text-caption text-medium-emphasis">待报销</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card border flat>
          <v-card-text class="pa-4 text-center">
            <v-icon size="36" color="info" class="mb-2">mdi-cash</v-icon>
            <div class="text-h4 font-weight-bold">¥{{ fmtAmount(stats.overall.total_amount) }}</div>
            <div class="text-caption text-medium-emphasis">总金额</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 报销状态分布 + 月度趋势 -->
    <v-row class="mb-6">
      <v-col cols="12" md="5">
        <v-card border flat>
          <v-card-title class="text-subtitle-1 font-weight-bold">报销状态分布</v-card-title>
          <v-card-text class="pa-4">
            <div class="d-flex align-center justify-center py-4">
              <!-- 环形图用纯 CSS/SVG -->
              <svg viewBox="0 0 200 200" width="180" height="180">
                <circle cx="100" cy="100" r="80" fill="none" stroke="#E0E0E0" stroke-width="24" />
                <!-- 已报销弧 -->
                <circle
                  cx="100" cy="100" r="80" fill="none"
                  stroke="#2E7D32"
                  stroke-width="24"
                  :stroke-dasharray="`${(reimbPct * 5.027).toFixed(1)} ${(502.7 - reimbPct * 5.027).toFixed(1)}`"
                  stroke-dashoffset="0"
                  stroke-linecap="round"
                  transform="rotate(-90 100 100)"
                />
                <text x="100" y="95" text-anchor="middle" class="text-h4 font-weight-bold" fill="#2E7D32">
                  {{ reimbPct }}%
                </text>
                <text x="100" y="120" text-anchor="middle" class="text-caption" fill="#757575">
                  已报销 {{ stats.overall.total_reimbursed }} / {{ stats.overall.total_count }}
                </text>
              </svg>
            </div>
            <div class="d-flex justify-center ga-6">
              <div class="d-flex align-center">
                <v-icon size="16" color="success" class="mr-1">mdi-square</v-icon>
                <span class="text-caption">已报销</span>
              </div>
              <div class="d-flex align-center">
                <v-icon size="16" color="warning" class="mr-1">mdi-square</v-icon>
                <span class="text-caption">待报销</span>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="7">
        <v-card border flat>
          <v-card-title class="text-subtitle-1 font-weight-bold">月度报销趋势</v-card-title>
          <v-card-text class="pa-4">
            <div v-if="stats.monthly_trend.length > 0" class="trend-chart">
              <div
                v-for="item in stats.monthly_trend"
                :key="item.label"
                class="trend-bar-wrapper"
              >
                <div class="text-caption font-weight-medium mb-1" style="color: #2E7D32">
                  {{ item.count }}
                </div>
                <div
                  class="trend-bar"
                  :style="{ height: barH(item.count) + 'px' }"
                  :title="`${item.label}: ¥${fmtAmount(item.amount)}`"
                />
                <div class="text-caption text-medium-emphasis mt-1">{{ item.label }}</div>
              </div>
            </div>
            <div v-else class="text-center py-6 text-medium-emphasis">
              暂无数据
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 逐年汇总 -->
    <v-card border flat class="mb-6">
      <v-card-title class="text-subtitle-1 font-weight-bold">
        年度汇总
      </v-card-title>
      <v-card-text>
        <v-table density="compact">
          <thead>
            <tr>
              <th class="text-caption">年份</th>
              <th class="text-caption">发票数</th>
              <th class="text-caption">总金额</th>
              <th class="text-caption">已报销</th>
              <th class="text-caption">报销率</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="text-body-1 font-weight-bold">{{ currentYear }}年</td>
              <td class="text-body-2">{{ stats.overall.total_count }}</td>
              <td class="text-body-2 font-weight-medium">¥{{ fmtAmount(stats.year.total_amount) }}</td>
              <td>
                <v-chip size="x-small" color="success" variant="flat">
                  {{ stats.overall.total_reimbursed }}
                </v-chip>
              </td>
              <td>
                <v-progress-linear
                  :model-value="reimbPct"
                  color="success"
                  height="6"
                  rounded
                  style="max-width: 120px"
                />
                <span class="text-caption ml-2">{{ reimbPct }}%</span>
              </td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '@/api'

const stats = ref({
  month: { year: 0, month: 0, total_count: 0, total_amount: 0, total_tax: 0, reimbursed_count: 0, pending_count: 0 },
  overall: { total_count: 0, total_amount: 0, total_reimbursed: 0 },
  year: { year: 0, total_amount: 0 },
  monthly_trend: [],
  category_distribution: [],
  top_counterparts: [],
  recent_invoices: [],
})

const exportLoading = ref(false)
const now = new Date()
const currentYear = computed(() => stats.value.month.year || now.getFullYear())

const pendingCount = computed(() => stats.value.overall.total_count - stats.value.overall.total_reimbursed)

const reimbPct = computed(() => {
  if (stats.value.overall.total_count === 0) return 0
  return Math.round((stats.value.overall.total_reimbursed / stats.value.overall.total_count) * 100)
})

function fmtAmount(val) {
  if (val == null || isNaN(val)) return '0'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const maxTrendCount = computed(() => {
  const arr = stats.value.monthly_trend
  if (arr.length === 0) return 1
  return Math.max(...arr.map(i => i.count), 1)
})

function barH(count) {
  const minH = 8
  const maxH = 100
  return maxTrendCount.value > 0 ? Math.max(minH, (count / maxTrendCount.value) * maxH) : minH
}

function exportReport() {
  exportLoading.value = true
  // 使用发票列表导出功能 — 这里暂用简单提示
  setTimeout(() => {
    exportLoading.value = false
  }, 500)
}

onMounted(async () => {
  try {
    const data = await statsApi.getDashboard()
    stats.value = data
  } catch (err) {
    console.error('加载报销数据失败:', err)
  }
})
</script>

<style scoped>
.trend-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  height: 160px;
  padding: 8px 0;
}

.trend-bar-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
}

.trend-bar {
  width: 28px;
  max-width: 100%;
  min-height: 8px;
  background: linear-gradient(180deg, #2E7D32 0%, #43A047 100%);
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease;
}
</style>
