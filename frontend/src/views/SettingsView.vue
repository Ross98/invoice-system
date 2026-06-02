<template>
  <div>
    <!-- 全局反馈 -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3500" location="top">
      {{ snackbar.message }}
      <template #actions>
        <v-btn variant="text" @click="snackbar.show = false">关闭</v-btn>
      </template>
    </v-snackbar>

    <!-- OCR 设置 -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card :loading="savingOcr">
          <template #loader>
            <v-progress-linear indeterminate color="primary" />
          </template>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-text-recognition</v-icon>
            OCR 设置
          </v-card-title>
          <v-card-text>
            <v-alert :type="ocrStatus?.available ? 'success' : 'warning'" variant="tonal" class="mb-4" density="compact">
              <div v-if="ocrStatus?.available" class="d-flex align-center">
                <v-icon class="mr-2">mdi-check-circle</v-icon>
                OCR 服务可用（{{ ocrStatus.engine }}）
              </div>
              <div v-else>
                <v-icon class="mr-2">mdi-alert</v-icon>
                OCR 服务不可用：{{ ocrStatus?.message || '请检查 Tesseract 安装' }}
              </div>
            </v-alert>

            <v-select
              v-model="ocrForm.lang"
              label="默认识别语言"
              :items="ocrLanguages"
              variant="outlined"
              density="compact"
              class="mb-4"
            />

            <v-text-field
              v-model="ocrForm.tesseract_path"
              label="Tesseract 路径"
              variant="outlined"
              density="compact"
              hint="留空则自动从 runtime/ 目录或系统 PATH 查找"
              persistent-hint
              class="mb-4"
            />

            <v-checkbox
              v-model="ocrForm.use_cloud"
              label="启用云端 OCR 备用"
              density="compact"
              class="mb-2"
            />

            <v-expand-transition>
              <div v-if="ocrForm.use_cloud">
                <v-select
                  v-model="ocrForm.cloud_provider"
                  label="服务提供商"
                  :items="cloudProviders"
                  variant="outlined"
                  density="compact"
                  class="mb-2"
                />
                <v-text-field
                  v-model="ocrForm.cloud_api_key"
                  label="云端 API Key"
                  variant="outlined"
                  density="compact"
                  type="password"
                />
              </div>
            </v-expand-transition>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="saveOcrSettings" :loading="savingOcr">
              保存 OCR 设置
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- 存储设置 -->
      <v-col cols="12" md="6">
        <v-card :loading="savingStorage">
          <template #loader>
            <v-progress-linear indeterminate color="primary" />
          </template>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-folder-cog</v-icon>
            文件存储设置
          </v-card-title>
          <v-card-text>
            <v-text-field
              v-model="storageForm.upload_path"
              label="上传文件存储路径"
              variant="outlined"
              density="compact"
              hint="发票原文件存储位置（只读）"
              persistent-hint
              readonly
              class="mb-4"
            />

            <v-text-field
              v-model="storageForm.file_size_threshold_mb"
              label="文件大小阈值 (MB)"
              type="number"
              variant="outlined"
              density="compact"
              hint="小于此值的文件存入数据库，大于此值的存本地文件"
              persistent-hint
              class="mb-4"
            />

            <v-checkbox
              v-model="storageForm.auto_cleanup"
              label="自动清理临时文件"
              density="compact"
              class="mb-2"
            />

            <v-text-field
              v-if="storageForm.auto_cleanup"
              v-model="storageForm.cleanup_days"
              label="清理天数"
              type="number"
              variant="outlined"
              density="compact"
              hint="清理多少天前的临时文件"
              persistent-hint
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn color="primary" @click="saveStorageSettings" :loading="savingStorage">
              保存存储设置
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 数据库管理 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-database-cog</v-icon>
            数据库管理
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4" color="success">
                  <div class="text-h6">数据库状态</div>
                  <v-icon size="48" color="success" class="my-4">mdi-database-check</v-icon>
                  <div class="text-body-1">连接正常</div>
                  <div class="text-caption text-medium-emphasis mt-1">
                    {{ dbInfo }}
                  </div>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card variant="outlined" class="text-center pa-4">
                  <div class="text-h6">备份</div>
                  <v-icon size="48" color="info" class="my-4">mdi-backup-restore</v-icon>
                  <div class="text-body-1 mb-4">下载数据库备份文件</div>
                  <v-btn color="info" block @click="backupDatabase" :loading="backingUp">
                    <v-icon start>mdi-download</v-icon>
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
                    <v-icon start>mdi-delete</v-icon>
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
        <v-card-title class="text-error">⚠️ 警告：重置数据库</v-card-title>
        <v-card-text>
          <v-alert type="error" variant="tonal" class="mb-4">
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
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="resetDialog = false">取消</v-btn>
          <v-btn
            color="error"
            @click="resetDatabase"
            :disabled="confirmText !== 'RESET'"
            :loading="resetting"
          >
            确认重置
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { settingsApi, ocrApi } from '@/api'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── 状态 ──
const savingOcr = ref(false)
const savingStorage = ref(false)
const backingUp = ref(false)
const resetting = ref(false)
const resetDialog = ref(false)
const confirmText = ref('')
const dbInfo = ref('')

const ocrStatus = ref(null)
const ocrForm = reactive({
  lang: 'chi_sim+eng',
  tesseract_path: '',
  use_cloud: false,
  cloud_api_key: '',
  cloud_provider: 'baidu',
})

const storageForm = reactive({
  upload_path: '',
  file_size_threshold_mb: 1,
  auto_cleanup: true,
  cleanup_days: 30,
})

const snackbar = reactive({ show: false, message: '', color: 'success' })

const showSnackbar = (message, color = 'success') => {
  snackbar.message = message
  snackbar.color = color
  snackbar.show = true
}

const ocrLanguages = [
  { title: '简体中文', value: 'chi_sim' },
  { title: '简体中文 + 英文', value: 'chi_sim+eng' },
  { title: '英文', value: 'eng' },
]

const cloudProviders = [
  { title: '百度云 OCR', value: 'baidu' },
  { title: '腾讯云 OCR', value: 'tencent' },
]

// ── 加载 ──
onMounted(async () => {
  await Promise.all([loadSettings(), loadOcrStatus()])
})

const loadSettings = async () => {
  try {
    const data = await settingsApi.getSettings()
    ocrForm.lang = data.ocr.lang
    ocrForm.tesseract_path = data.ocr.tesseract_path
    ocrForm.use_cloud = data.ocr.use_cloud
    ocrForm.cloud_api_key = data.ocr.cloud_api_key
    ocrForm.cloud_provider = data.ocr.cloud_provider

    storageForm.upload_path = data.storage.upload_path
    storageForm.file_size_threshold_mb = data.storage.file_size_threshold_mb
    storageForm.auto_cleanup = data.storage.auto_cleanup
    storageForm.cleanup_days = data.storage.cleanup_days

    dbInfo.value = `${data.app.title} v${data.app.version}`
  } catch (err) {
    console.error('加载设置失败:', err)
    showSnackbar('加载设置失败', 'error')
  }
}

const loadOcrStatus = async () => {
  try {
    ocrStatus.value = await ocrApi.getStatus()
  } catch (err) {
    ocrStatus.value = { available: false, message: '检测失败' }
  }
}

// ── 保存 ──
const saveOcrSettings = async () => {
  savingOcr.value = true
  try {
    await settingsApi.saveOcrSettings({
      ocr_lang: ocrForm.lang,
      tesseract_path: ocrForm.tesseract_path,
      use_cloud_ocr: ocrForm.use_cloud,
      cloud_api_key: ocrForm.cloud_api_key,
      cloud_provider: ocrForm.cloud_provider,
    })
    showSnackbar('OCR 设置已保存')
  } catch (err) {
    showSnackbar('保存失败: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    savingOcr.value = false
  }
}

const saveStorageSettings = async () => {
  savingStorage.value = true
  try {
    await settingsApi.saveStorageSettings({
      file_size_threshold_mb: storageForm.file_size_threshold_mb,
      auto_cleanup: storageForm.auto_cleanup,
      cleanup_days: storageForm.cleanup_days,
    })
    showSnackbar('存储设置已保存')
  } catch (err) {
    showSnackbar('保存失败: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    savingStorage.value = false
  }
}

// ── 备份 ──
const backupDatabase = async () => {
  backingUp.value = true
  try {
    const blob = await settingsApi.backupDatabase()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `invoice_backup_${new Date().toISOString().split('T')[0]}.db`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    showSnackbar('数据库备份已下载')
  } catch (err) {
    showSnackbar('备份失败: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    backingUp.value = false
  }
}

// ── 重置 ──
const confirmReset = () => {
  resetDialog.value = true
  confirmText.value = ''
}

const resetDatabase = async () => {
  if (confirmText.value !== 'RESET') return

  resetting.value = true
  try {
    await settingsApi.resetDatabase()
    resetDialog.value = false
    showSnackbar('数据库已重置')
    setTimeout(() => {
      router.push('/')
    }, 1500)
  } catch (err) {
    showSnackbar('重置失败: ' + (err.response?.data?.detail || err.message), 'error')
  } finally {
    resetting.value = false
  }
}
</script>
