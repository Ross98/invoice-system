<template>
  <v-app>
    <v-app-bar app color="primary" dark>
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>发票管理系统</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn icon @click="toggleTheme">
        <v-icon>{{ themeIcon }}</v-icon>
      </v-btn>
      <v-btn icon @click="refreshData">
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" app temporary>
      <v-list>
        <v-list-item to="/" prepend-icon="mdi-home" title="首页"></v-list-item>
        <v-list-item to="/invoices" prepend-icon="mdi-receipt" title="发票管理"></v-list-item>
        <v-list-item to="/summary" prepend-icon="mdi-file-table" title="发票汇总"></v-list-item>
        <v-list-item to="/upload" prepend-icon="mdi-upload" title="上传发票"></v-list-item>
        <v-list-item to="/categories" prepend-icon="mdi-tag" title="分类管理"></v-list-item>
        <v-list-item to="/counterparts" prepend-icon="mdi-office-building" title="单位管理"></v-list-item>
        <v-divider></v-divider>
        <v-list-item to="/settings" prepend-icon="mdi-cog" title="系统设置"></v-list-item>
        <v-list-item to="/about" prepend-icon="mdi-information" title="关于系统"></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid>
        <router-view></router-view>
      </v-container>
    </v-main>

    <v-footer app color="primary" dark>
      <v-spacer></v-spacer>
      <span>&copy; 2026 发票管理系统 v1.0.0</span>
      <v-spacer></v-spacer>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useTheme } from 'vuetify'

const drawer = ref(false)
const theme = useTheme()

const themeIcon = computed(() => theme.global.current.value.dark ? 'mdi-weather-sunny' : 'mdi-weather-night')

const toggleTheme = () => {
  theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
}

const refreshData = () => {
  window.location.reload()
}
</script>

<style>
.v-application {
  font-family: 'Roboto', 'Noto Sans SC', sans-serif;
}
</style>