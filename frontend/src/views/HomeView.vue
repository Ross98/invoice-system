<template>
  <div>
    <v-row class="mb-6">
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h4 text-center py-8">
            <v-icon size="48" class="mr-4" color="primary">mdi-receipt</v-icon>
            发票管理系统
          </v-card-title>
          <v-card-subtitle class="text-h6 text-center">
            本地部署的企业发票管理解决方案
          </v-card-subtitle>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card class="text-center" height="200" @click="$router.push('/invoices')">
          <v-card-text class="pa-6">
            <v-icon size="64" color="primary">mdi-receipt</v-icon>
            <div class="text-h5 mt-4">发票管理</div>
            <div class="text-body-1 mt-2">录入、查询、管理发票信息</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="text-center" height="200" @click="$router.push('/upload')">
          <v-card-text class="pa-6">
            <v-icon size="64" color="green">mdi-upload</v-icon>
            <div class="text-h5 mt-4">上传发票</div>
            <div class="text-body-1 mt-2">支持 PDF/图片，OCR 自动识别</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="text-center" height="200" @click="$router.push('/categories')">
          <v-card-text class="pa-6">
            <v-icon size="64" color="orange">mdi-tag</v-icon>
            <div class="text-h5 mt-4">分类管理</div>
            <div class="text-body-1 mt-2">管理消费分类和统计</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-6">
      <v-col cols="12">
        <v-card>
          <v-card-title>快速开始</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-title>1. 添加消费分类</v-list-item-title>
                <v-list-item-subtitle>在"分类管理"中创建办公用品、差旅费等分类</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>2. 添加对方单位</v-list-item-title>
                <v-list-item-subtitle>在"单位管理"中录入常用供应商信息</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>3. 录入或上传发票</v-list-item-title>
                <v-list-item-subtitle>通过表单录入或上传发票文件自动识别</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>4. 查询和统计</v-list-item-title>
                <v-list-item-subtitle>按时间、分类、金额等条件筛选分析</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-6">
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>系统状态</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item>
                <v-list-item-title>后端 API</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip :color="apiStatus ? 'success' : 'error'" size="small">
                    {{ apiStatus ? '运行中' : '未连接' }}
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>OCR 服务</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip :color="ocrStatus ? 'success' : 'warning'" size="small">
                    {{ ocrStatus ? '可用' : '未配置' }}
                  </v-chip>
                </v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>数据库</v-list-item-title>
                <v-list-item-subtitle>
                  <v-chip color="success" size="small">已连接</v-chip>
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>最近操作</v-card-title>
          <v-card-text>
            <v-list v-if="recentInvoices.length > 0">
              <v-list-item v-for="invoice in recentInvoices" :key="invoice.id">
                <v-list-item-title>{{ invoice.invoice_number }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ formatDate(invoice.invoice_date) }} - ¥{{ invoice.total_with_tax }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <div v-else class="text-center py-4">
              <v-icon size="48" color="grey">mdi-information-outline</v-icon>
              <div class="text-body-1 mt-2">暂无发票记录</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useInvoiceStore } from '@/stores/invoice'
import { ocrApi } from '@/api'

const invoiceStore = useInvoiceStore()
const apiStatus = ref(false)
const ocrStatus = ref(false)
const recentInvoices = ref([])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

const checkApiStatus = async () => {
  try {
    const response = await fetch('/health')
    apiStatus.value = response.ok
  } catch {
    apiStatus.value = false
  }
}

const checkOcrStatus = async () => {
  try {
    const status = await ocrApi.getStatus()
    ocrStatus.value = status.available
  } catch {
    ocrStatus.value = false
  }
}

const loadRecentInvoices = async () => {
  try {
    const invoices = await invoiceStore.fetchInvoices({ limit: 5 })
    recentInvoices.value = invoices
  } catch (error) {
    console.error('加载最近发票失败:', error)
  }
}

onMounted(async () => {
  await checkApiStatus()
  await checkOcrStatus()
  await loadRecentInvoices()
})
</script>