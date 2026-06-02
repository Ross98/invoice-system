<template>
  <div>
    <!-- 页面标题 -->
    <div class="d-flex align-center mb-4">
      <h2 class="text-h4 font-weight-bold">工作台</h2>
      <v-spacer />
      <span class="text-caption text-medium-emphasis">{{ currentMonthLabel }}</span>
    </div>

    <!-- 加载骨架屏 -->
    <template v-if="loading">
      <v-row class="mb-6">
        <v-col v-for="n in 4" :key="n" cols="12" sm="6" lg="3">
          <v-skeleton-loader type="card" />
        </v-col>
      </v-row>
      <v-row class="mb-6">
        <v-col cols="12" lg="4">
          <v-skeleton-loader type="card" height="200" />
        </v-col>
        <v-col cols="12" lg="8">
          <v-skeleton-loader type="card" height="200" />
        </v-col>
      </v-row>
      <v-row class="mb-6">
        <v-col cols="12" md="7">
          <v-skeleton-loader type="card" height="280" />
        </v-col>
        <v-col cols="12" md="5">
          <v-skeleton-loader type="card" height="280" />
        </v-col>
      </v-row>
    </template>

    <!-- 正常内容 -->
    <template v-else>

    <!-- 统计卡片 -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card" border flat>
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-2">
              <v-avatar size="42" color="primary" variant="tonal" class="mr-3">
                <v-icon size="22">mdi-receipt</v-icon>
              </v-avatar>
              <div>
                <div class="text-caption text-medium-emphasis">本月发票</div>
                <div class="text-h4 font-weight-bold">{{ stats.month.total_count }}</div>
              </div>
            </div>
            <div class="text-caption text-medium-emphasis">
              全年累计 {{ stats.overall.total_count }} 张
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card" border flat>
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-2">
              <v-avatar size="42" color="success" variant="tonal" class="mr-3">
                <v-icon size="22">mdi-cash-multiple</v-icon>
              </v-avatar>
              <div>
                <div class="text-caption text-medium-emphasis">本月金额</div>
                <div class="text-h4 font-weight-bold">¥{{ fmtAmount(stats.month.total_amount) }}</div>
              </div>
            </div>
            <div class="text-caption text-medium-emphasis">
              税额 ¥{{ fmtAmount(stats.month.total_tax) }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card" border flat>
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-2">
              <v-avatar size="42" color="info" variant="tonal" class="mr-3">
                <v-icon size="22">mdi-check-circle</v-icon>
              </v-avatar>
              <div>
                <div class="text-caption text-medium-emphasis">报销率</div>
                <div class="text-h4 font-weight-bold">{{ reimbursementRate }}%</div>
              </div>
            </div>
            <v-progress-linear
              :model-value="reimbursementRate"
              color="info"
              height="6"
              rounded
            />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card" border flat>
          <v-card-text class="pa-4">
            <div class="d-flex align-center mb-2">
              <v-avatar size="42" color="warning" variant="tonal" class="mr-3">
                <v-icon size="22">mdi-clock-outline</v-icon>
              </v-avatar>
              <div>
                <div class="text-caption text-medium-emphasis">待报销</div>
                <div class="text-h4 font-weight-bold">{{ stats.month.pending_count }}</div>
              </div>
            </div>
            <div class="text-caption text-medium-emphasis">
              已报销 {{ stats.month.reimbursed_count }} 张
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 快捷入口 + 月度趋势 -->
    <v-row class="mb-6">
      <v-col cols="12" lg="4">
        <v-card class="h-100" border flat>
          <v-card-title class="text-subtitle-1 font-weight-bold">快捷入口</v-card-title>
          <v-card-text>
            <div class="d-flex flex-column ga-3">
              <v-btn
                block
                size="large"
                color="primary"
                variant="tonal"
                prepend-icon="mdi-camera-plus"
                @click="$router.push('/invoices/new')"
              >
                智能识别上传发票
              </v-btn>
              <v-btn
                block
                size="large"
                color="secondary"
                variant="tonal"
                prepend-icon="mdi-pencil-plus"
                @click="$router.push('/invoices/new?tab=manual')"
              >
                手动录入发票
              </v-btn>
              <v-btn
                block
                size="large"
                variant="text"
                prepend-icon="mdi-format-list-bulleted"
                @click="$router.push('/invoices')"
              >
                浏览全部发票
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" lg="8">
        <v-card class="h-100" border flat>
          <v-card-title class="text-subtitle-1 font-weight-bold">
            月度趋势（近12个月）
            <v-spacer />
            <v-chip size="small" label variant="flat">发票数量</v-chip>
          </v-card-title>
          <v-card-text class="pa-4">
            <div v-if="stats.monthly_trend.length > 0" class="trend-chart">
              <div
                v-for="item in stats.monthly_trend"
                :key="item.label"
                class="trend-bar-wrapper"
              >
                <div class="text-caption text-medium-emphasis mb-1">{{ item.count }}</div>
                <div
                  class="trend-bar"
                  :style="{ height: barHeight(item.count) + 'px' }"
                  :title="`${item.label}: ${item.count}张, ¥${fmtAmount(item.amount)}`"
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

    <!-- 分类占比 + Top单位 -->
    <v-row class="mb-6">
      <v-col cols="12" md="7">
        <v-card border flat>
          <v-card-title class="text-subtitle-1 font-weight-bold">
            分类占比（{{ currentYear }}年）
          </v-card-title>
          <v-card-text>
            <div v-if="stats.category_distribution.length > 0">
              <div
                v-for="(cat, i) in stats.category_distribution.slice(0, 6)"
                :key="cat.name"
                class="mb-3"
              >
                <div class="d-flex justify-space-between mb-1">
                  <span class="text-body-2">{{ cat.name }}</span>
                  <span class="text-body-2 font-weight-medium">¥{{ fmtAmount(cat.amount) }}</span>
                </div>
                <v-progress-linear
                  :model-value="catPct(cat.amount)"
                  :color="catColors[i % catColors.length]"
                  height="8"
                  rounded
                />
              </div>
            </div>
            <div v-else class="text-center py-6 text-medium-emphasis">
              暂无数据
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card border flat class="h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">
            Top 消费单位（{{ currentYear }}年）
          </v-card-title>
          <v-card-text>
            <div v-if="stats.top_counterparts.length > 0">
              <v-list density="compact">
                <v-list-item
                  v-for="(cp, i) in stats.top_counterparts"
                  :key="cp.name"
                  :prepend-icon="rankIcon(i)"
                >
                  <template #prepend>
                    <v-avatar :color="rankColor(i)" size="28" class="mr-2">
                      <span class="text-white text-caption font-weight-bold">{{ i + 1 }}</span>
                    </v-avatar>
                  </template>
                  <v-list-item-title class="text-body-2">{{ cp.name }}</v-list-item-title>
                  <template #append>
                    <span class="text-body-2 font-weight-medium">¥{{ fmtAmount(cp.amount) }}</span>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-else class="text-center py-6 text-medium-emphasis">
              暂无数据
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 最近发票 -->
    <v-card border flat>
      <v-card-title class="d-flex align-center">
        <span class="text-subtitle-1 font-weight-bold">最近发票</span>
        <v-spacer />
        <v-btn variant="text" size="small" @click="$router.push('/invoices')">
          查看全部
          <v-icon end>mdi-arrow-right</v-icon>
        </v-btn>
      </v-card-title>
      <v-card-text>
        <div v-if="stats.recent_invoices.length > 0">
          <v-table density="compact">
            <thead>
              <tr>
                <th class="text-caption">发票号码</th>
                <th class="text-caption">日期</th>
                <th class="text-caption">类型</th>
                <th class="text-caption">金额</th>
                <th class="text-caption">状态</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="inv in stats.recent_invoices"
                :key="inv.id"
                style="cursor: pointer"
                @click="$router.push(`/invoices/${inv.id}`)"
              >
                <td class="text-body-2 font-weight-medium">{{ inv.invoice_number }}</td>
                <td class="text-body-2">{{ inv.invoice_date }}</td>
                <td>
                  <v-chip size="x-small" variant="flat">{{ inv.invoice_type }}</v-chip>
                </td>
                <td class="text-body-2 font-weight-medium">¥{{ fmtAmount(inv.total_with_tax) }}</td>
                <td>
                  <v-chip
                    :color="inv.is_reimbursed ? 'success' : 'warning'"
                    size="x-small"
                    variant="flat"
                  >
                    {{ inv.is_reimbursed ? '已报销' : '待报销' }}
                  </v-chip>
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>
        <div v-else class="text-center py-6">
          <v-icon size="48" color="grey-lighten-1">mdi-receipt-text-outline</v-icon>
          <div class="text-body-1 mt-2 text-medium-emphasis">暂无发票记录</div>
          <v-btn
            variant="text"
            color="primary"
            class="mt-2"
            @click="$router.push('/invoices/new')"
          >
            创建第一张发票
          </v-btn>
        </div>
      </v-card-text>
    </v-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsApi } from '@/api'

const loading = ref(true)
const stats = ref({
  month: { year: 0, month: 0, total_count: 0, total_amount: 0, total_tax: 0, reimbursed_count: 0, pending_count: 0 },
  overall: { total_count: 0, total_amount: 0, total_reimbursed: 0 },
  year: { year: 0, total_amount: 0 },
  monthly_trend: [],
  category_distribution: [],
  top_counterparts: [],
  recent_invoices: [],
})

const now = new Date()
const currentYear = computed(() => stats.value.month.year || now.getFullYear())
const currentMonthLabel = computed(() => {
  const m = stats.value.month.month || (now.getMonth() + 1)
  return `${currentYear.value}年${m}月`
})

const reimbursementRate = computed(() => {
  const total = stats.value.month.total_count
  if (total === 0) return 0
  return Math.round((stats.value.month.reimbursed_count / total) * 100)
})

const catColors = ['primary', 'success', 'warning', 'error', 'info', 'secondary']
const maxCatAmount = computed(() => {
  const arr = stats.value.category_distribution
  if (arr.length === 0) return 1
  return Math.max(...arr.map(c => c.amount))
})

function catPct(amount) {
  return maxCatAmount.value > 0 ? (amount / maxCatAmount.value) * 100 : 0
}

function fmtAmount(val) {
  if (val == null || isNaN(val)) return '0'
  return Number(val).toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

const maxTrendCount = computed(() => {
  const arr = stats.value.monthly_trend
  if (arr.length === 0) return 1
  return Math.max(...arr.map(i => i.count), 1)
})

function barHeight(count) {
  const minH = 8
  const maxH = 120
  return maxTrendCount.value > 0
    ? Math.max(minH, (count / maxTrendCount.value) * maxH)
    : minH
}

function rankColor(i) {
  const colors = ['#FF6D00', '#757575', '#795548', '#9E9E9E', '#BDBDBD']
  return colors[i] || '#BDBDBD'
}

function rankIcon(i) {
  return i === 0 ? 'mdi-trophy' : 'mdi-pound'
}

onMounted(async () => {
  try {
    const data = await statsApi.getDashboard()
    stats.value = data
  } catch (err) {
    console.error('加载仪表盘数据失败:', err)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card {
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

.trend-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  height: 200px;
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
  background: linear-gradient(180deg, #1565C0 0%, #1E88E5 100%);
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease, opacity 0.2s ease;
  cursor: pointer;
}
.trend-bar:hover {
  opacity: 0.8;
}
</style>
