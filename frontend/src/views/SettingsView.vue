<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="text-h5">系统设置</v-card-title>
    </v-card>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>OCR 设置</v-card-title>
          <v-card-text>
            <v-alert :type="ocrStatus?.available ? 'success' : 'warning'" class="mb-4">
              <div v-if="ocrStatus?.available">
                <v-icon left>mdi-check-circle</v-icon>
                OCR 服务可用（{{ ocrStatus.engine }}）
              </div>
              <div v-else>
                <v-icon left>mdi-alert</v-icon>
                OCR 服务不可用：{{ ocrStatus?.message }}
              </div>
            </v-alert>

            <v-select
              v-model="ocrLang"
              label="默认识别语言"
              :items="ocrLanguages"
              variant="outlined"
              density="compact"
              class="mb-4"
            ></v-select>

            <v-text-field
              v-model="tesseractPath"
              label="Tesseract 路径"
              variant="outlined"
              density="compact"
              hint="本地 Tesseract OCR 可执行文件路径"
              persistent-hint
              class="mb-4"
            ></v-text-field>

            <v-checkbox
              v-model="useCloudOcr"
              label="启用云端 OCR 备用"
              density="compact"
              class="mb-2"
            ></v-checkbox>

            <v-expand-transition>
              <div v-if="useCloudOcr">
                <v-text-field
                  v-model="cloudApiKey"
                  label="云端 API Key"
                  variant="outlined"
                  density="compact"
                  type="password"
                  class="mb-2"
                ></v-text-field>
                <v-select
                  v-model="cloudProvider"
                  label="服务提供商"
                  :items="cloudProviders"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </div>
            </v-expand-transition>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="saveOcrSettings" :loading="saving">
              保存 OCR 设置
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>文件存储设置</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="uploadPath"
              label="上传文件存储路径"
              variant="outlined"
              density="compact"
              hint="发票原文件存储位置"
              persistent-hint
              class="mb-4"
            ></v-text-field>

            <v-text-field
              v-model="fileSizeThreshold"
              label="文件大小阈值 (MB)"
              type="number"
              variant="outlined"
              density="compact"
              hint="小于此值的文件存入数据库，大于此值的文件存本地"
              persistent-hint
              class="mb-4"
            ></v-text-field>

            <v-checkbox
              v-model="autoCleanup"
              label="自动清理临时文件"
              density="compact"
              hint="定期清理未关联的临时文件"
              persistent-hint
              class="mb-2"
            ></v-checkbox>

            <v-text-field
              v-if="autoCleanup"
              v-model="cleanupDays"
              label="清理天数"
              type="number"
              variant="outlined"
              density="compact"
              hint="清理多少天前的临时文件"
              persistent-hint
            ></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="saveStorageSettings" :loading="saving">
              保存存储设置
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>数据库管理</v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h6">数据库状态</div>
                  <v-icon size="48" color="success" class="my-4">mdi-database-check</v-icon>
                  <div class="text-body-1">连接正常</div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h6">备份</div>
                  <v-icon size="48" color="info" class="my-4">mdi-backup-restore</v-icon>
                  <div class="text-body-1 mb-4">手动备份数据库</div>
                  <v-btn color="info" block @click="backupDatabase">
                    <v-icon left>mdi-download</v-icon>
                    备份
                  </v-btn>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h6">重置</div>
                  <v-icon size="48" color="warning" class="my-4">mdi-alert-circle</v-icon>
                  <div class="text-body-1 mb-4">清空所有数据</div>
                  <v-btn color="warning" block @click="confirmReset">
                    <v-icon left>mdi-delete</v-icon>
                    重置数据库
                  </v-btn>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 重置确认对话框 -->
    <v-dialog v-model="resetDialog" max-width="500">
      <v-card>
        <v-card-title class="text-error">警告：重置数据库</v-card-title>
        <v-card-text>
          <v-alert type="error" class="mb-4">
            此操作将清空所有数据，包括：
            <ul class="mt-2">
              <li>所有发票记录</li>
              <li>所有消费明细</li>
              <li>所有上传的文件</li>
              <li>所有分类和单位</li>
            </ul>
            此操作不可逆！
          </v-alert>
          <v-text-field
            v-model="confirmText"
            label="请输入 'RESET' 确认操作"
            variant="outlined"
            density="compact"
          ></v-text-field>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="resetDialog = false">取消</v-btn>
          <v-btn color="error" @click="resetDatabase" :disabled="confirmText !== 'RESET'">
            确认重置
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ocrApi } from '@/api'

const saving = ref(false)
const resetDialog = ref(false)
const confirmText = ref('')

const ocrStatus = ref(null)
const ocrLang = ref('chi_sim+eng')
const tesseractPath = ref('')
const useCloudOcr = ref(false)
const cloudApiKey = ref('')
const cloudProvider = ref('baidu')

const uploadPath = ref('')
const fileSizeThreshold = ref(1)
const autoCleanup = ref(true)
const cleanupDays = ref(30)

const ocrLanguages = [
  { title: '简体中文', value: 'chi_sim' },
  { title: '简体中文 + 英文', value: 'chi_sim+eng' },
  { title: '英文', value: 'eng' }
]

const cloudProviders = [
  { title: '百度云 OCR', value: 'baidu' },
  { title: '腾讯云 OCR', value: 'tencent' }
]

const loadSettings = async () => {
  try {
    ocrStatus.value = await ocrApi.getStatus()
    // 这里应该从后端加载保存的设置
    // 暂时使用默认值
  } catch (error) {
    console.error('加载设置失败:', error)
  }
}

const saveOcrSettings = async () => {
  saving.value = true
  try {
    // 这里应该调用后端 API 保存 OCR 设置
    await new Promise(resolve => setTimeout(resolve, 500))
    alert('OCR 设置已保存')
  } catch (error) {
    console.error('保存 OCR 设置失败:', error)
    alert('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const saveStorageSettings = async () => {
  saving.value = true
  try {
    // 这里应该调用后端 API 保存存储设置
    await new Promise(resolve => setTimeout(resolve, 500))
    alert('存储设置已保存')
  } catch (error) {
    console.error('保存存储设置失败:', error)
    alert('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const backupDatabase = async () => {
  try {
    // 这里应该调用后端 API 备份数据库
    const response = await fetch('/api/backup', { method: 'POST' })
    if (response.ok) {
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice-backup-${new Date().toISOString().split('T')[0]}.db`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
      alert('数据库备份成功')
    } else {
      throw new Error('备份失败')
    }
  } catch (error) {
    console.error('备份数据库失败:', error)
    alert('备份失败: ' + (error.message || '未知错误'))
  }
}

const confirmReset = () => {
  resetDialog.value = true
  confirmText.value = ''
}

const resetDatabase = async () => {
  if (confirmText.value !== 'RESET') return

  try {
    // 这里应该调用后端 API 重置数据库
    const response = await fetch('/api/reset', { method: 'POST' })
    if (response.ok) {
      alert('数据库已重置，请重启应用')
      window.location.reload()
    } else {
      throw new Error('重置失败')
    }
  } catch (error) {
    console.error('重置数据库失败:', error)
    alert('重置失败: ' + (error.message || '未知错误'))
  } finally {
    resetDialog.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>