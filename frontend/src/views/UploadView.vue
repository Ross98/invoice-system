<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="text-h5">
        上传发票文件
      </v-card-title>
      <v-card-subtitle>支持 PDF、PNG、JPG 格式，自动 OCR 识别发票信息</v-card-subtitle>
    </v-card>

    <v-row>
      <!-- 文件上传区域 -->
      <v-col
        cols="12"
        md="6"
      >
        <v-card>
          <v-card-title>上传文件</v-card-title>
          <v-card-text>
            <v-file-input
              v-model="files"
              label="选择发票文件"
              multiple
              accept=".pdf,.png,.jpg,.jpeg"
              prepend-icon="mdi-paperclip"
              variant="outlined"
              @change="onFileSelect"
            />

            <v-divider class="my-4" />

            <!-- OCR 选项 -->
            <div class="text-h6 mb-2">
              OCR 设置
            </div>
            <v-select
              v-model="ocrLang"
              label="识别语言"
              :items="ocrLanguages"
              variant="outlined"
              density="compact"
            />
            <v-checkbox
              v-model="autoCreateInvoice"
              label="自动创建发票"
              density="compact"
            />
            <v-checkbox
              v-if="autoCreateInvoice"
              v-model="useCloudOcr"
              label="使用云端 OCR（更准确）"
              density="compact"
            />

            <v-btn
              color="primary"
              block
              :loading="uploading"
              :disabled="!files.length"
              class="mt-4"
              @click="uploadFiles"
            >
              <v-icon left>
                mdi-upload
              </v-icon>
              上传并识别
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 预览和结果区域 -->
      <v-col
        cols="12"
        md="6"
      >
        <v-card>
          <v-card-title>识别结果</v-card-title>
          <v-card-text>
            <div
              v-if="uploading"
              class="text-center py-4"
            >
              <v-progress-circular
                indeterminate
                color="primary"
              />
              <div class="mt-2">
                正在上传和识别...
              </div>
            </div>

            <div v-else-if="parsedInvoices.length > 0">
              <v-expansion-panels>
                <v-expansion-panel
                  v-for="(parsed, index) in parsedInvoices"
                  :key="index"
                >
                  <v-expansion-panel-title>
                    <v-list-item>
                      <template #prepend>
                        <v-icon :color="getFileIconColor(parsed.parsed.filename?.split('.').pop() || '')">
                          {{ getFileIcon(parsed.parsed.filename?.split('.').pop() || '') }}
                        </v-icon>
                      </template>
                      <v-list-item-title>{{ parsed.filename }}</v-list-item-title>
                      <v-list-item-subtitle>
                        {{ parsed.parsed.invoice_data?.invoice_number || '未识别' }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-card
                      variant="outlined"
                      class="pa-4"
                    >
                      <!-- 重复发票警告 -->
                      <v-alert
                        v-if="parsed.duplicate"
                        type="warning"
                        variant="tonal"
                        density="compact"
                        class="mb-3"
                        :text="parsed.duplicateMessage"
                      />
                      
                      <div class="text-body-2 font-weight-bold mb-2">
                        解析结果：
                      </div>
                      
                      <v-table density="compact">
                        <tbody>
                          <tr>
                            <td class="font-weight-bold">
                              发票号码
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.invoice_number || '未识别' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              发票代码
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.invoice_code || '未识别' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              发票类型
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.invoice_type || '未识别' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              开票日期
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.invoice_date || '未识别' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              金额
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.total_with_tax || '0.00' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              税额
                            </td>
                            <td>{{ parsed.parsed.invoice_data?.tax_amount || '0.00' }}</td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold">
                              销方单位
                            </td>
                            <td>{{ parsed.parsed.parsed?.counterpart_name || '未识别' }}</td>
                          </tr>
                        </tbody>
                      </v-table>

                      <div class="d-flex justify-end mt-4 gap-2">
                        <v-btn
                          v-if="!parsed.duplicate"
                          color="primary"
                          size="small"
                          :loading="importingIndex === index"
                          @click="importInvoice(parsed)"
                        >
                          <v-icon left>
                            mdi-check
                          </v-icon>
                          确认导入
                        </v-btn>
                        <v-btn
                          v-else
                          color="warning"
                          size="small"
                          disabled
                        >
                          <v-icon left>
                            mdi-alert-circle
                          </v-icon>
                          已存在
                        </v-btn>
                        <v-btn
                          color="secondary"
                          size="small"
                          @click="editInvoiceData(parsed)"
                        >
                          <v-icon left>
                            mdi-pencil
                          </v-icon>
                          编辑
                        </v-btn>
                      </div>
                    </v-card>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </div>

            <div
              v-else
              class="text-center py-8"
            >
              <v-icon
                size="64"
                color="grey"
              >
                mdi-file-upload-outline
              </v-icon>
              <div class="text-h6 mt-4">
                等待上传文件
              </div>
              <div class="text-body-1 mt-2">
                上传发票文件后，将自动进行 OCR 识别
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- OCR 状态提示 -->
    <v-alert
      v-if="ocrStatus"
      :type="ocrStatus.available ? 'success' : 'warning'"
      class="mt-4"
    >
      <div v-if="ocrStatus.available">
        <v-icon left>
          mdi-check-circle
        </v-icon>
        OCR 服务可用（{{ ocrStatus.engine }}）
      </div>
      <div v-else>
        <v-icon left>
          mdi-alert
        </v-icon>
        OCR 服务不可用：{{ ocrStatus.message }}
        <v-btn
          variant="text"
          size="small"
          class="ml-2"
          @click="checkOcrStatus"
        >
          重新检查
        </v-btn>
      </div>
    </v-alert>

    <!-- 全局提示 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="4000"
      location="top"
    >
      {{ snackbar.text }}
      <template #actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ocrApi } from "@/api";

const router = useRouter();

const files = ref([]);
const uploading = ref(false);
const ocrLang = ref("chi_sim+eng");
const autoCreateInvoice = ref(false);
const useCloudOcr = ref(false);
const ocrStatus = ref(null);
const parsedInvoices = ref([]);
const importingIndex = ref(-1);

// 全局提示
const snackbar = reactive({ show: false, text: "", color: "info" });
const notify = (text, color = "info") => {
  snackbar.text = text;
  snackbar.color = color;
  snackbar.show = true;
};

const ocrLanguages = [
  { title: "简体中文", value: "chi_sim" },
  { title: "简体中文 + 英文", value: "chi_sim+eng" },
  { title: "英文", value: "eng" },
];

const getFileIcon = (type) => {
  const icons = {
    "pdf": "mdi-file-pdf",
    "png": "mdi-file-image",
    "jpg": "mdi-file-image",
    "jpeg": "mdi-file-image",
  };
  return icons[type.toLowerCase()] || "mdi-file";
};

const getFileIconColor = (type) => {
  if (type.toLowerCase() === "pdf") return "red";
  if (["png", "jpg", "jpeg"].includes(type.toLowerCase())) return "green";
  return "grey";
};

const onFileSelect = (_event) => {
  // Vuetify 3 的 v-file-input @change 传递的是 File[]
};

const checkOcrStatus = async () => {
  try {
    ocrStatus.value = await ocrApi.getStatus();
  } catch {
    ocrStatus.value = {
      available: false,
      message: "检查 OCR 状态失败",
    };
  }
};

const uploadFiles = async () => {
  if (!files.value || !files.value.length) {
    notify("请先选择发票文件", "warning");
    return;
  }

  uploading.value = true;
  parsedInvoices.value = [];

  try {
    for (const file of files.value) {
      const result = await ocrApi.parseInvoice(file, ocrLang.value);
      const parsedItem = {
        filename: file.name,
        parsed: result,
        duplicate: false,
        duplicateMessage: "",
      };
      parsedInvoices.value.push(parsedItem);

      // 如果启用了自动创建发票，立即导入
      if (autoCreateInvoice.value) {
        try {
          const invoiceData = result.invoice_data;
          await ocrApi.importInvoice(invoiceData);
          // 从列表中移除已自动导入的项
          const index = parsedInvoices.value.indexOf(parsedItem);
          if (index > -1) {
            parsedInvoices.value.splice(index, 1);
          }
        } catch (importError) {
          console.error(`自动导入失败 (${file.name}):`, importError);
          // 标记为重复，在 UI 中显示警告
          if (importError.status === 409) {
            parsedItem.duplicate = true;
            parsedItem.duplicateMessage = importError.message || "该发票已存在，请勿重复导入";
          }
              // 自动导入失败时保留在列表中供用户查看
            }
          }
        }
      } catch (error) {
        console.error("发票解析失败:", error);
        notify("解析失败: " + (error.message || "未知错误"), "error");
      } finally {
        uploading.value = false;
      }
};

const importInvoice = async (parsed) => {
  const index = parsedInvoices.value.indexOf(parsed);
  importingIndex.value = index;

  try {
    const invoiceData = parsed.parsed.invoice_data;
    const result = await ocrApi.importInvoice(invoiceData);
    notify(`发票导入成功！发票号: ${result.invoice_number}`, "success");
    // 移除已导入的项
    parsedInvoices.value.splice(index, 1);
  } catch (error) {
    console.error("发票导入失败:", error);
    if (error.status === 409) {
      // 重复发票
      notify(error.message || "该发票已存在，请勿重复导入", "warning");
    } else {
      notify("导入失败: " + (error.message || "未知错误"), "error");
    }
  } finally {
    importingIndex.value = -1;
  }
};

const editInvoiceData = (parsed) => {
  const invoiceData = parsed.parsed.invoice_data;
  router.push({
    path: "/invoices/new",
    query: {
      invoice_number: invoiceData.invoice_number,
      invoice_code: invoiceData.invoice_code,
      invoice_date: invoiceData.invoice_date,
      invoice_type: invoiceData.invoice_type,
      total_with_tax: invoiceData.total_with_tax,
      total_amount: invoiceData.total_amount,
      tax_amount: invoiceData.tax_amount,
      check_code: invoiceData.check_code || "",
      counterpart_name: parsed.parsed.parsed?.counterpart_name || "",
      remark: invoiceData.remark || "",
    },
  });
};

onMounted(() => {
  checkOcrStatus();
});
</script>

<style scoped>
.ocr-text {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}
</style>