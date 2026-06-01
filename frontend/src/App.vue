<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-toolbar-title>发票管理系统</v-toolbar-title>
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

        <router-view />
      </v-container>
    </v-main>

    <!-- 底部信息 -->
    <v-footer app color="primary" dark height="36">
      <v-spacer />
      <span class="text-caption">&copy; 2026 发票管理系统 v1.0.1</span>
      <v-spacer />
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTheme } from 'vuetify'
import { useRoute } from 'vue-router'

const drawer = ref(false)
const theme = useTheme()
const route = useRoute()

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
</script>

<style>
.v-application {
  font-family: 'Roboto', 'Noto Sans SC', sans-serif;
}

/* 子导航组缩进动画 */
.nav-sub-group {
  overflow: hidden;
}
</style>
