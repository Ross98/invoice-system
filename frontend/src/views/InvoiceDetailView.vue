<template>
  <div>
    <!-- 顶部操作栏 -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <v-btn
          variant="text"
          icon
          @click="$router.push('/invoices')"
        >
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <span class="text-h5 ml-2">发票详情</span>
        <v-chip
          v-if="invoice"
          :color="invoice.is_reimbursed ? 'success' : 'warning'"
          size="small"
          class="ml-3"
        >
          {{ invoice.is_reimbursed ? '已报销' : '未报销' }}
        </v-chip>
        <v-spacer />
        <v-btn
          v-if="invoice && !invoice.is_reimbursed"
          color="success"
          variant="tonal"
          class="mr-2"
          @click="toggleReimbursed"
        >
          <v-icon left>
            mdi-check-circle
          </v-icon>
          标记已报销
        </v-btn>
        <v-btn
          v-if="invoice && invoice.is_reimbursed"
          color="warning"
          variant="tonal"
          class="mr-2"
          @click="toggleReimbursed"
        >
          <v-icon left>
            mdi-undo
          </v-icon>
          取消报销
        </v-btn>
        <v-btn
          color="primary"
          variant="tonal"
          class="mr-2"
          @click="editInvoice"
        >
          <v-icon left>
            mdi-pencil
          </v-icon>
          编辑
        </v-btn>
        <v-btn
          color="error"
          variant="outlined"
          @click="confirmDelete"
        >
          <v-icon left>
            mdi-delete
          </v-icon>
          删除
        </v-btn>
      </v-card-title>
    </v-card>

    <!-- 加载骨架屏 -->
    <div v-if="!invoice">
      <div class="text-center py-3 mb-2">
        <v-progress-linear
          indeterminate
          color="primary"
        />
      </div>
      <v-row>
        <v-col
          cols="12"
          md="8"
        >
          <v-skeleton-loader type="table" />
        </v-col>
        <v-col
          cols="12"
          md="4"
        >
          <v-skeleton-loader
            type="card"
            class="mb-3"
          />
          <v-skeleton-loader
            type="card"
            class="mb-3"
          />
          <v-skeleton-loader type="card" />
        </v-col>
      </v-row>
    </div>

    <template v-else>
      <!-- Tab 导航 -->
      <v-card>
        <v-tabs
          v-model="activeTab"
          color="primary"
          class="px-2"
        >
          <v-tab value="info">
            <v-icon
              left
              size="20"
            >
              mdi-card-text
            </v-icon>
            基本信息
          </v-tab>
          <v-tab value="details">
            <v-icon
              left
              size="20"
            >
              mdi-format-list-bulleted
            </v-icon>
            消费明细
            <v-chip
              v-if="invoice.details?.length"
              size="x-small"
              class="ml-1"
              color="primary"
              variant="tonal"
            >
              {{ invoice.details.length }}
            </v-chip>
          </v-tab>
          <v-tab value="files">
            <v-icon
              left
              size="20"
            >
              mdi-file-document
            </v-icon>
            原文件
            <v-chip
              v-if="invoice.files?.length"
              size="x-small"
              class="ml-1"
              color="primary"
              variant="tonal"
            >
              {{ invoice.files.length }}
            </v-chip>
          </v-tab>
        </v-tabs>

        <v-divider />

        <v-card-text>
          <v-tabs-window v-model="activeTab">
            <!-- ===== Tab 1: 基本信息 ===== -->
            <v-tabs-window-item value="info">
              <v-row>
                <!-- 发票标识 -->
                <v-col
                  cols="12"
                  md="8"
                >
                  <v-card variant="outlined">
                    <v-card-text>
                      <div class="text-subtitle-1 font-weight-bold mb-4">
                        发票信息
                      </div>
                      <v-table density="compact">
                        <tbody>
                          <tr>
                            <td
                              class="font-weight-bold text-caption"
                              width="120"
                            >
                              发票号码
                            </td>
                            <td class="text-body-2">
                              {{ invoice.invoice_number }}
                            </td>
                            <td
                              class="font-weight-bold text-caption"
                              width="120"
                            >
                              发票代码
                            </td>
                            <td class="text-body-2">
                              {{ invoice.invoice_code }}
                            </td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold text-caption">
                              发票类型
                            </td>
                            <td class="text-body-2">
                              {{ invoice.invoice_type }}
                            </td>
                            <td class="font-weight-bold text-caption">
                              开票日期
                            </td>
                            <td class="text-body-2">
                              {{ formatDate(invoice.invoice_date) }}
                            </td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold text-caption">
                              校验码
                            </td>
                            <td class="text-body-2">
                              {{ invoice.check_code || '无' }}
                            </td>
                            <td class="font-weight-bold text-caption">
                              对方单位
                            </td>
                            <td class="text-body-2">
                              {{ invoice.counterpart?.name || '未指定' }}
                            </td>
                          </tr>
                          <tr>
                            <td class="font-weight-bold text-caption">
                              消费分类
                            </td>
                            <td class="text-body-2">
                              {{ invoice.category?.name || '未分类' }}
                            </td>
                            <td class="font-weight-bold text-caption">
                              备注
                            </td>
                            <td class="text-body-2">
                              {{ invoice.remark || '无' }}
                            </td>
                          </tr>
                        </tbody>
                      </v-table>
                    </v-card-text>
                  </v-card>
                </v-col>

                <!-- 金额卡片 -->
                <v-col
                  cols="12"
                  md="4"
                >
                  <v-card
                    variant="outlined"
                    class="text-center pa-4 mb-3"
                  >
                    <div class="text-caption text-grey">
                      含税总金额
                    </div>
                    <div class="text-h4 mt-2 text-primary">
                      ¥{{ formatAmount(invoice.total_with_tax) }}
                    </div>
                  </v-card>
                  <v-card
                    variant="outlined"
                    class="text-center pa-4 mb-3"
                  >
                    <div class="text-caption text-grey">
                      不含税金额
                    </div>
                    <div class="text-h5 mt-1">
                      ¥{{ formatAmount(invoice.total_amount) }}
                    </div>
                  </v-card>
                  <v-card
                    variant="outlined"
                    class="text-center pa-4"
                  >
                    <div class="text-caption text-grey">
                      税额
                    </div>
                    <div class="text-h5 mt-1">
                      ¥{{ formatAmount(invoice.tax_amount) }}
                    </div>
                  </v-card>
                </v-col>
              </v-row>

              <!-- 时间信息 -->
              <v-row class="mt-2">
                <v-col cols="12">
                  <div class="text-caption text-grey">
                    创建时间：{{ formatDateTime(invoice.created_at) }}
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    修改时间：{{ formatDateTime(invoice.updated_at) }}
                  </div>
                </v-col>
              </v-row>
            </v-tabs-window-item>

            <!-- ===== Tab 2: 消费明细 ===== -->
            <v-tabs-window-item value="details">
              <v-data-table
                v-if="invoice.details && invoice.details.length > 0"
                :headers="detailHeaders"
                :items="invoice.details"
                hover
                hide-default-footer
                density="comfortable"
              >
                <template #item.unit_price="{ item }">
                  ¥{{ formatAmount(item.unit_price) }}
                </template>
                <template #item.amount="{ item }">
                  ¥{{ formatAmount(item.amount) }}
                </template>
                <template #item.tax_rate="{ item }">
                  {{ item.tax_rate ? item.tax_rate + '%' : '-' }}
                </template>
                <template #item.service_date="{ item }">
                  {{ formatDate(item.service_date) }}
                </template>
              </v-data-table>

              <div
                v-else
                class="text-center py-8"
              >
                <v-icon
                  size="64"
                  color="grey-lighten-1"
                >
                  mdi-format-list-bulleted
                </v-icon>
                <div class="text-body-1 mt-3 text-grey">
                  暂无消费明细
                </div>
              </div>
            </v-tabs-window-item>

            <!-- ===== Tab 3: 原文件 ===== -->
            <v-tabs-window-item value="files">
              <div v-if="invoice.files && invoice.files.length > 0">
                <v-list lines="two">
                  <v-list-item
                    v-for="file in invoice.files"
                    :key="file.id"
                  >
                    <template #prepend>
                      <v-icon
                        :color="fileIconColor(file.file_type)"
                        size="28"
                      >
                        {{ fileIcon(file.file_type) }}
                      </v-icon>
                    </template>
                    <v-list-item-title class="text-body-2">
                      {{ file.file_name }}
                    </v-list-item-title>
                    <v-list-item-subtitle class="text-caption">
                      {{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}
                    </v-list-item-subtitle>
                    <template #append>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        @click="previewFile(file)"
                      >
                        <v-icon>mdi-eye</v-icon>
                      </v-btn>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        @click="downloadFile(file)"
                      >
                        <v-icon>mdi-download</v-icon>
                      </v-btn>
                      <v-btn
                        icon
                        variant="text"
                        size="small"
                        color="error"
                        @click="deleteFile(file)"
                      >
                        <v-icon>mdi-delete</v-icon>
                      </v-btn>
                    </template>
                  </v-list-item>
                </v-list>
              </div>

              <div
                v-else
                class="text-center py-8"
              >
                <v-icon
                  size="64"
                  color="grey-lighten-1"
                >
                  mdi-file-outline
                </v-icon>
                <div class="text-body-1 mt-3 text-grey">
                  暂无发票文件
                </div>
                <div class="text-caption text-grey mt-1">
                  点击下方按钮上传发票原文件
                </div>
              </div>

              <div class="d-flex justify-end mt-4">
                <v-btn
                  color="primary"
                  variant="tonal"
                  @click="openUpload"
                >
                  <v-icon left>
                    mdi-upload
                  </v-icon>
                  上传文件
                </v-btn>
              </div>
            </v-tabs-window-item>
          </v-tabs-window>
        </v-card-text>
      </v-card>
    </template>

    <!-- 文件上传对话框 -->
    <v-dialog
      v-model="uploadDialog"
      max-width="400"
    >
      <v-card>
        <v-card-title>上传发票文件</v-card-title>
        <v-card-text>
          <v-file-input
            v-model="newFiles"
            label="选择文件"
            multiple
            accept=".pdf,.png,.jpg,.jpeg"
            prepend-icon="mdi-paperclip"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="uploadDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="primary"
            :loading="uploadingFile"
            @click="handleUpload"
          >
            上传
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认 -->
    <v-dialog
      v-model="deleteDialog"
      max-width="400"
    >
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除发票 "{{ invoice?.invoice_number }}" 吗？此操作不可撤销。
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="deleteDialog = false"
          >
            取消
          </v-btn>
          <v-btn
            color="error"
            @click="doDelete"
          >
            确认删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { invoiceApi } from "@/api";
import { useInvoiceStore } from "@/stores/invoice";

const route = useRoute();
const router = useRouter();
const invoiceStore = useInvoiceStore();

const invoice = ref(null);
const activeTab = ref("info");

// 文件上传
const uploadDialog = ref(false);
const uploadingFile = ref(false);
const newFiles = ref([]);

// 删除
const deleteDialog = ref(false);

const detailHeaders = [
  { title: "品名", key: "item_name" },
  { title: "规格", key: "spec" },
  { title: "单位", key: "unit" },
  { title: "数量", key: "quantity" },
  { title: "单价", key: "unit_price" },
  { title: "金额", key: "amount" },
  { title: "税率", key: "tax_rate" },
  { title: "服务日期", key: "service_date" },
];

const formatDate = (d) => d ? new Date(d).toLocaleDateString("zh-CN") : "-";
const formatDateTime = (d) => d ? new Date(d).toLocaleString("zh-CN") : "-";
const formatAmount = (v) => (v != null) ? Number(v).toFixed(2) : "0.00";
const formatFileSize = (b) => {
  if (!b) return "0 B";
  const k = 1024, sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(b) / Math.log(k));
  return parseFloat((b / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};
const fileIcon = (t) => ({ pdf: "mdi-file-pdf", png: "mdi-file-image", jpg: "mdi-file-image", jpeg: "mdi-file-image" }[t?.toLowerCase()] || "mdi-file");
const fileIconColor = (t) => {
  if (t?.toLowerCase() === "pdf") return "red";
  if (["png", "jpg", "jpeg"].includes(t?.toLowerCase())) return "green";
  return "grey";
};

// ── 数据加载 ──
const loadInvoice = async () => {
  try {
    invoice.value = await invoiceApi.getInvoice(route.params.id);
  } catch (error) {
    console.error("加载发票详情失败:", error);
    router.push("/invoices");
  }
};

// ── 操作 ──
const editInvoice = () => router.push(`/invoices/${route.params.id}/edit`);
const confirmDelete = () => { deleteDialog.value = true; };
const doDelete = async () => {
  try {
    await invoiceApi.deleteInvoice(route.params.id);
    router.push("/invoices");
  } catch (e) {
    console.error("删除失败:", e);
    alert("删除失败: " + (e.message || "未知错误"));
  }
  deleteDialog.value = false;
};

const toggleReimbursed = async () => {
  const newVal = !invoice.value.is_reimbursed;
  invoice.value.is_reimbursed = newVal;
  try {
    await invoiceStore.updateInvoice(invoice.value.id, { is_reimbursed: newVal });
  } catch (e) {
    invoice.value.is_reimbursed = !newVal;
    console.error("更新失败:", e);
  }
};

// ── 文件操作 ──
const openUpload = () => {
  uploadDialog.value = true;
  newFiles.value = [];
};

const handleUpload = async () => {
  if (!newFiles.value.length) return;
  uploadingFile.value = true;
  try {
    for (const file of newFiles.value) {
      await invoiceApi.uploadFile(route.params.id, file);
    }
    await loadInvoice();
    uploadDialog.value = false;
    activeTab.value = "files";
  } catch (e) {
    alert("上传失败: " + (e.message || "未知错误"));
  } finally {
    uploadingFile.value = false;
  }
};

const previewFile = (file) => {
  // 在新标签页预览
  window.open(`/api/invoices/${route.params.id}/files/${file.id}/download`, "_blank");
};

const downloadFile = async (file) => {
  try {
    const response = await invoiceApi.downloadFile(route.params.id, file.id);
    const url = window.URL.createObjectURL(new Blob([response]));
    const a = document.createElement("a");
    a.href = url; a.download = file.file_name;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error("下载失败:", e);
  }
};

const deleteFile = async (file) => {
  if (!confirm(`确定要删除文件 "${file.file_name}" 吗？`)) return;
  try {
    await invoiceApi.deleteFile(route.params.id, file.id);
    await loadInvoice();
  } catch (e) {
    console.error("删除文件失败:", e);
  }
};

onMounted(() => loadInvoice());
</script>
