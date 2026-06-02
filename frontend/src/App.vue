<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title>发票管理系统</v-toolbar-title>
      <v-spacer />
      <!-- 全局搜索 -->
      <v-text-field
        ref="searchField"
        v-model="globalSearchQuery"
        prepend-inner-icon="mdi-magnify"
        placeholder="搜索发票…"
        variant="solo-filled"
        density="compact"
        hide-details
        single-line
        flat
        class="global-search-field mx-4"
        @keyup.enter="openSearchDialog"
        @focus="searchFocused = true"
        @blur="searchFocused = false"
      >
        <template #append-inner>
          <kbd class="search-shortcut" v-if="!searchFocused">Ctrl+K</kbd>
        </template>
      </v-text-field>
      <v-spacer />
      <v-btn icon @click="toggleTheme">
        <v-icon>{{ themeIcon }}</v-icon>
      </v-btn>
      <v-btn icon @click="refreshData">
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- 侧边导航（手动控制折叠） -->
    <v-navigation-drawer v-model="drawer" app temporary width="260">
      <v-list density="compact" nav>
        <!-- 工作台 -->
        <v-list-item
          to="/"
          prepend-icon="mdi-view-dashboard"
          title="工作台"
          :active="route.path === '/'"
          color="primary"
        />

        <v-divider class="my-2" />

        <!-- 发票管理 分组（手动折叠） -->
        <v-list-item
          prepend-icon="mdi-receipt"
          :append-icon="isGroupOpen('invoices') ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          title="发票管理"
          @click="toggleGroup('invoices')"
        />
        <div v-show="isGroupOpen('invoices')" class="nav-sub-group">
          <v-list-item
            to="/invoices"
            prepend-icon="mdi-format-list-bulleted"
            title="发票列表"
            :active="route.path === '/invoices'"
            class="pl-8"
            color="primary"
          />
          <v-list-item
            to="/invoices/new"
            prepend-icon="mdi-plus-circle"
            title="新建发票"
            :active="route.path === '/invoices/new'"
            class="pl-8"
            color="primary"
          />
        </div>

        <!-- 数据汇总 分组（手动折叠） -->
        <v-list-item
          prepend-icon="mdi-chart-bar"
          :append-icon="isGroupOpen('reports') ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          title="数据汇总"
          @click="toggleGroup('reports')"
        />
        <div v-show="isGroupOpen('reports')" class="nav-sub-group">
          <v-list-item
            to="/reports/invoice"
            prepend-icon="mdi-file-table"
            title="发票汇总"
            :active="route.path === '/reports/invoice'"
            class="pl-8"
            color="primary"
          />
          <v-list-item
            to="/reports/reimbursement"
            prepend-icon="mdi-check-circle"
            title="报销报表"
            :active="route.path === '/reports/reimbursement'"
            class="pl-8"
            color="primary"
          />
        </div>

        <v-divider class="my-2" />

        <!-- 基础数据 分组（手动折叠） -->
        <v-list-item
          prepend-icon="mdi-database"
          :append-icon="isGroupOpen('master-data') ? 'mdi-chevron-up' : 'mdi-chevron-down'"
          title="基础数据"
          @click="toggleGroup('master-data')"
        />
        <div v-show="isGroupOpen('master-data')" class="nav-sub-group">
          <v-list-item
            to="/master-data/categories"
            prepend-icon="mdi-tag"
            title="消费分类"
            :active="route.path === '/master-data/categories'"
            class="pl-8"
            color="primary"
          />
          <v-list-item
            to="/master-data/counterparts"
            prepend-icon="mdi-office-building"
            title="对方单位"
            :active="route.path === '/master-data/counterparts'"
            class="pl-8"
            color="primary"
          />
        </div>

        <v-divider class="my-2" />

        <!-- 系统 -->
        <v-list-item
          to="/settings"
          prepend-icon="mdi-cog"
          title="系统设置"
          :active="route.path === '/settings'"
          color="primary"
        />
        <v-list-item
          to="/about"
          prepend-icon="mdi-information"
          title="关于系统"
          :active="route.path === '/about'"
          color="primary"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- 主内容区 -->
    <v-main>
      <v-container fluid class="pa-4 pt-2">
        <!-- 面包屑导航 -->
        <v-breadcrumbs
          v-if="breadcrumbs.length > 1"
          :items="breadcrumbs"
          density="compact"
          class="px-0 pt-0 text-caption"
        >
          <template #divider>
            <v-icon size="small" class="mx-1">mdi-chevron-right</v-icon>
          </template>
          <template #item="{ item, index }">
            <v-breadcrumbs-item
              :disabled="index === breadcrumbs.length - 1"
              :to="index < breadcrumbs.length - 1 ? item.to : undefined"
              exact
            >
              {{ item.title }}
            </v-breadcrumbs-item>
          </template>
        </v-breadcrumbs>

        <v-slide-x-transition mode="out-in">
          <router-view />
        </v-slide-x-transition>
      </v-container>
    </v-main>

    <!-- 底部信息 -->
    <v-footer app color="primary" dark height="36">
      <v-spacer />
      <span class="text-caption">&copy; 2026 发票管理系统 v2.0.0</span>
      <v-spacer />
    </v-footer>

    <!-- 全局搜索对话框 -->
    <v-dialog v-model="searchDialog" max-width="600">
      <v-card>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="searchDialogQuery"
            placeholder="输入发票号码 / 单位名称 / 备注关键词…"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="compact"
            hide-details
            autofocus
            clearable
            :loading="searchLoading"
            @keyup.enter="performSearch"
            @update:model-value="debouncedSearch"
          >
            <template #append-inner>
              <v-btn variant="text" size="small" @click="searchDialog = false" icon="mdi-close" />
            </template>
          </v-text-field>
        </v-card-text>

        <v-divider></v-divider>

        <!-- 搜索结果 -->
        <v-list v-if="searchResults.length > 0" lines="two" max-height="400" class="overflow-y-auto">
          <v-list-item
            v-for="item in searchResults"
            :key="item.id"
            :to="`/invoices/${item.id}`"
            @click="searchDialog = false"
          >
            <template v-slot:prepend>
              <v-icon color="primary">mdi-receipt</v-icon>
            </template>
            <v-list-item-title class="text-body-2">
              {{ item.invoice_number }}
              <v-chip size="x-small" class="ml-2" variant="tonal" :color="item.is_reimbursed ? 'success' : 'warning'">
                {{ item.is_reimbursed ? '已报销' : '未报销' }}
              </v-chip>
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption">
              {{ item.invoice_type }} · ¥{{ fmt(item.total_with_tax) }}
              &nbsp;|&nbsp; {{ item.counterpart?.name || '未知单位' }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <div v-else-if="searchDialogQuery && !searchLoading" class="text-center py-6">
          <v-icon size="40" color="grey">mdi-file-search-outline</v-icon>
          <div class="text-body-2 mt-2 text-grey">未找到匹配的发票</div>
        </div>

        <div v-else-if="!searchDialogQuery" class="text-center py-6">
          <v-icon size="40" color="grey-lighten-1">mdi-magnify</v-icon>
          <div class="text-body-2 mt-2 text-grey">输入关键词搜索发票</div>
          <div class="text-caption text-grey mt-1">支持发票号码 / 单位名称 / 备注</div>
        </div>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useTheme } from 'vuetify'
import { useRoute, useRouter } from 'vue-router'
import { invoiceApi } from '@/api'

const drawer = ref(false)
const theme = useTheme()
const route = useRoute()
const router = useRouter()

// ── 主题切换 ──
const themeIcon = computed(() =>
  theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night'
)

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

const refreshData = () => {
  window.location.reload()
}

// ── 导航分组手动折叠 ──
const openGroups = ref(new Set())

// 根据当前路由自动初始化展开组
watch(
  () => route.path,
  (path) => {
    const next = new Set(openGroups.value)
    if (path.startsWith('/invoices')) next.add('invoices')
    if (path.startsWith('/reports')) next.add('reports')
    if (path.startsWith('/master-data')) next.add('master-data')
    openGroups.value = next
  },
  { immediate: true, deep: false }
)

const isGroupOpen = (key) => openGroups.value.has(key)

const toggleGroup = (key) => {
  const next = new Set(openGroups.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  openGroups.value = next
}

// ── 面包屑 ──
const breadcrumbs = computed(() => {
  const items = route.matched
    .filter((r) => r.meta.title)
    .map((r) => ({ title: r.meta.title, to: r.path }))

  // Flat routes: prepend parentTitle if set (e.g. "基础数据 > 消费分类")
  const parent = route.meta.parentTitle
  if (parent && items.length === 1) {
    items.unshift({ title: parent, to: '#' })
  }
  return items
})

// ── 全局搜索 ──
const searchField = ref(null)
const globalSearchQuery = ref('')
const searchFocused = ref(false)
const searchDialog = ref(false)
const searchDialogQuery = ref('')
const searchResults = ref([])
const searchLoading = ref(false)
const searchTimer = ref(null)

const fmt = (v) => (v != null) ? Number(v).toFixed(2) : '0.00'

const openSearchDialog = () => {
  searchDialogQuery.value = globalSearchQuery.value
  searchDialog.value = true
  if (searchDialogQuery.value) performSearch()
}

const performSearch = async () => {
  if (!searchDialogQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchLoading.value = true
  try {
    const result = await invoiceApi.getInvoices({
      search_text: searchDialogQuery.value.trim(),
      limit: 20
    })
    searchResults.value = result.items || result
  } catch (e) {
    console.error('搜索失败:', e)
    searchResults.value = []
  } finally {
    searchLoading.value = false
  }
}

const debouncedSearch = () => {
  clearTimeout(searchTimer.value)
  searchTimer.value = setTimeout(() => {
    if (searchDialogQuery.value.trim()) {
      performSearch()
    } else {
      searchResults.value = []
    }
  }, 300)
}

// 全局快捷键
const onKeyDown = (e) => {
  // 跳过输入框内的按键
  const tag = e.target.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

  // Ctrl+K — 打开搜索
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    searchDialog.value = true
    setTimeout(() => {
      const input = document.querySelector('.v-dialog .v-field__input input')
      if (input) input.focus()
    }, 100)
    return
  }

  // Ctrl+N — 快速新建发票
  if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
    e.preventDefault()
    router.push('/invoices/new')
    return
  }

  // Esc — 关闭弹窗/搜索/抽屉
  if (e.key === 'Escape') {
    if (searchDialog.value) {
      searchDialog.value = false
    } else if (drawer.value) {
      drawer.value = false
    }
  }
}

// 注册/移除全局快捷键
onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style>
.v-application {
  font-family: 'Roboto', 'Noto Sans SC', sans-serif;
}

/* 子导航组缩进动画 */
.nav-sub-group {
  overflow: hidden;
}

/* 全局搜索 */
.global-search-field {
  max-width: 300px;
}
.search-shortcut {
  background: rgba(255,255,255,0.2);
  border: 1px solid rgba(255,255,255,0.3);
  border-radius: 4px;
  padding: 1px 6px;
  font-size: 11px;
  font-family: monospace;
  color: rgba(255,255,255,0.7);
}
</style>
