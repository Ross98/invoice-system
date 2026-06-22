<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-btn
        variant="text"
        icon
        @click="$router.push('/invoices')"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <span class="text-h5 ml-2">新建发票</span>
    </v-card-title>

    <!-- 全局反馈 -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      timeout="3500"
      location="top"
    >
      {{ snackbar.message }}
      <template #actions>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          关闭
        </v-btn>
      </template>
    </v-snackbar>

    <!-- 统一 Tab: 智能识别 / 手动录入 -->
    <v-tabs
      v-model="activeTab"
      class="px-4"
      color="primary"
    >
      <v-tab value="ocr">
        <v-icon
          left
          size="20"
        >
          mdi-camera
        </v-icon>
        智能识别
      </v-tab>
      <v-tab value="manual">
        <v-icon
          left
          size="20"
        >
          mdi-pencil
        </v-icon>
        手动录入
      </v-tab>
    </v-tabs>

    <v-divider />

    <v-card-text>
      <!-- ===== Tab 1: 智能识别 ===== -->
      <v-tabs-window v-model="activeTab">
        <v-tabs-window-item value="ocr">
          <v-row>
            <!-- 左: 文件上传区 -->
            <v-col
              cols="12"
              md="5"
            >
              <v-card variant="outlined">
                <v-card-text class="pa-6">
                  <div class="text-h6 mb-4">
                    📎 上传发票文件
                  </div>

                  <!-- 拖拽区域 -->
                  <v-file-input
                    v-model="ocrFiles"
                    label="拖拽或点击选择文件"
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg"
                    prepend-icon="mdi-cloud-upload"
                    variant="outlined"
                    class="mb-4"
                    @update:model-value="onOcrFilesChanged"
                  />

                  <div class="text-caption text-grey mb-4">
                    支持 PDF、PNG、JPG 格式，可一次选择多个文件
                  </div>

                  <!-- OCR 设置折叠 -->
                  <v-expansion-panels
                    variant="accordion"
                    class="mb-4"
                  >
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <v-icon
                          left
                          size="small"
                          class="mr-2"
                        >
                          mdi-tune
                        </v-icon>
                        OCR 识别设置
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-select
                          v-model="ocrLang"
                          label="识别语言"
                          :items="ocrLanguages"
                          variant="outlined"
                          density="compact"
                          class="mb-3"
                        />
                        <v-checkbox
                          v-model="autoCreateInvoice"
                          label="识别后自动入库"
                          density="compact"
                          hide-details
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

                  <v-btn
                    color="primary"
                    size="large"
                    block
                    :loading="ocrProcessing"
                    :disabled="!ocrFiles.length"
                    @click="startOcr"
                  >
                    <v-icon left>
                      mdi-magnify-scan
                    </v-icon>
                    开始识别
                  </v-btn>

                  <!-- OCR 服务状态 -->
                  <v-alert
                    v-if="ocrStatus"
                    :type="ocrStatus.available ? 'success' : 'warning'"
                    variant="tonal"
                    density="compact"
                    class="mt-3"
                  >
                    <span v-if="ocrStatus.available">
                      ✅ OCR 服务可用（{{ ocrStatus.engine }}）
                    </span>
                    <span v-else>
                      ⚠️ {{ ocrStatus.message }}
                    </span>
                  </v-alert>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- 右: 识别结果 -->
            <v-col
              cols="12"
              md="7"
            >
              <v-card variant="outlined">
                <v-card-text>
                  <div class="text-h6 mb-4">
                    📋 识别结果
                  </div>

                  <!-- 识别中 -->
                  <div
                    v-if="ocrProcessing"
                    class="text-center py-8"
                  >
                    <v-progress-circular
                      indeterminate
                      color="primary"
                      size="48"
                    />
                    <div class="mt-3 text-body-1">
                      正在识别中<span class="dots">...</span>
                    </div>
                  </div>

                  <!-- 结果列表 -->
                  <div v-else-if="ocrResults.length > 0">
                    <v-expansion-panels
                      v-model="expandedResults"
                      multiple
                    >
                      <v-expansion-panel
                        v-for="(item, idx) in ocrResults"
                        :key="idx"
                        :value="idx"
                      >
                        <v-expansion-panel-title>
                          <template #default="{ expanded }">
                            <v-list-item
                              class="pa-0"
                              :class="{ 'bg-grey-lighten-4': expanded }"
                            >
                              <template #prepend>
                                <v-icon
                                  :color="item.imported ? 'success' : 'primary'"
                                  size="20"
                                >
                                  {{ item.imported ? 'mdi-check-circle' : 'mdi-file-document' }}
                                </v-icon>
                              </template>
                              <v-list-item-title class="text-body-2">
                                {{ item.filename }}
                              </v-list-item-title>
                              <v-list-item-subtitle
                                v-if="!item.imported"
                                class="text-caption"
                              >
                                {{ item.data?.invoice_number || '等待确认' }}
                              </v-list-item-subtitle>
                            </v-list-item>
                          </template>
                        </v-expansion-panel-title>
                        <v-expansion-panel-text v-if="!item.imported">
                          <!-- 重复警告 -->
                          <v-alert
                            v-if="item.duplicate"
                            type="warning"
                            variant="tonal"
                            density="compact"
                            class="mb-3"
                            :text="item.duplicateMessage"
                          />

                          <!-- 解析结果可编辑预览 -->
                          <v-table
                            density="compact"
                            class="mb-3"
                          >
                            <tbody>
                              <tr>
                                <td
                                  class="font-weight-bold text-caption"
                                  width="100"
                                >
                                  发票号码
                                </td>
                                <td class="text-body-2">
                                  {{ item.data?.invoice_number || '-' }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  发票代码
                                </td>
                                <td class="text-body-2">
                                  {{ item.data?.invoice_code || '-' }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  发票类型
                                </td>
                                <td class="text-body-2">
                                  {{ item.data?.invoice_type || '-' }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  开票日期
                                </td>
                                <td class="text-body-2">
                                  {{ item.data?.invoice_date || '-' }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  含税金额
                                </td>
                                <td class="text-body-2 font-weight-bold">
                                  ¥{{ formatAmount(item.data?.total_with_tax) }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  税额
                                </td>
                                <td class="text-body-2">
                                  ¥{{ formatAmount(item.data?.tax_amount) }}
                                </td>
                              </tr>
                              <tr>
                                <td class="font-weight-bold text-caption">
                                  销方单位
                                </td>
                                <td class="text-body-2">
                                  {{ item.counterpartName || '-' }}
                                </td>
                              </tr>
                            </tbody>
                          </v-table>

                          <div class="d-flex justify-end gap-2">
                            <v-btn
                              v-if="!item.duplicate"
                              color="primary"
                              size="small"
                              variant="tonal"
                              :loading="item.importing"
                              @click="confirmImport(idx)"
                            >
                              <v-icon
                                left
                                size="18"
                              >
                                mdi-check
                              </v-icon>
                              确认入库
                            </v-btn>
                            <v-btn
                              color="secondary"
                              size="small"
                              variant="tonal"
                              @click="editOcrResult(idx)"
                            >
                              <v-icon
                                left
                                size="18"
                              >
                                mdi-pencil
                              </v-icon>
                              编辑后录入
                            </v-btn>
                          </div>
                        </v-expansion-panel-text>
                        <!-- 已导入 -->
                        <v-expansion-panel-text v-else>
                          <v-alert
                            type="success"
                            variant="tonal"
                            density="compact"
                            class="mb-2"
                          >
                            已成功导入：{{ item.importedNumber }}
                          </v-alert>
                          <v-btn
                            size="small"
                            variant="text"
                            color="primary"
                            @click="$router.push(`/invoices/${item.importedId}`)"
                          >
                            查看详情 →
                          </v-btn>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </div>

                  <!-- 空状态 -->
                  <div
                    v-else
                    class="text-center py-8"
                  >
                    <v-icon
                      size="64"
                      color="grey-lighten-1"
                    >
                      mdi-file-upload-outline
                    </v-icon>
                    <div class="text-body-1 mt-3 text-grey">
                      上传发票文件后将自动进行 OCR 识别
                    </div>
                    <div class="text-caption text-grey mt-1">
                      或切换到「手动录入」标签直接填表
                    </div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-tabs-window-item>

        <!-- ===== Tab 2: 手动录入 ===== -->
        <v-tabs-window-item value="manual">
          <v-form
            ref="manualFormRef"
            validate-on="blur lazy"
            @submit.prevent="submitManual"
          >
            <v-row>
              <v-col
                cols="12"
                md="6"
              >
                <v-text-field
                  v-model="manualForm.invoice_number"
                  label="发票号码 *"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col
                cols="12"
                md="6"
              >
                <v-text-field
                  v-model="manualForm.invoice_code"
                  label="发票代码 *"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col
                cols="12"
                md="4"
              >
                <v-select
                  v-model="manualForm.invoice_type"
                  label="发票类型 *"
                  :items="invoiceTypes"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col
                cols="12"
                md="4"
              >
                <v-text-field
                  v-model="manualForm.invoice_date"
                  label="开票日期 *"
                  type="date"
                  :rules="[rules.required]"
                  required
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col
                cols="12"
                md="4"
              >
                <v-text-field
                  v-model="manualForm.check_code"
                  label="校验码"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col
                cols="12"
                md="4"
              >
                <v-text-field
                  v-model="manualForm.total_amount"
                  label="不含税金额"
                  type="number"
                  step="0.01"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col
                cols="12"
                md="4"
              >
                <v-text-field
                  v-model="manualForm.tax_amount"
                  label="税额"
                  type="number"
                  step="0.01"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col
                cols="12"
                md="4"
              >
                <v-text-field
                  v-model="manualForm.total_with_tax"
                  label="含税总金额"
                  type="number"
                  step="0.01"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col
                cols="12"
                md="6"
              >
                <v-select
                  v-model="manualForm.counterpart_id"
                  label="对方单位"
                  :items="counterparts"
                  item-title="name"
                  item-value="id"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
              <v-col
                cols="12"
                md="6"
              >
                <v-select
                  v-model="manualForm.category_id"
                  label="消费分类"
                  :items="categories"
                  item-title="name"
                  item-value="id"
                  variant="outlined"
                  density="compact"
                  clearable
                />
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="12">
                <v-textarea
                  v-model="manualForm.remark"
                  label="备注"
                  variant="outlined"
                  density="compact"
                  rows="2"
                />
              </v-col>
            </v-row>

            <!-- 消费明细 -->
            <v-divider class="my-4" />
            <div class="d-flex align-center mb-3">
              <span class="text-h6">消费明细</span>
              <v-spacer />
              <v-btn
                color="secondary"
                size="small"
                variant="tonal"
                @click="addManualDetail"
              >
                <v-icon
                  left
                  size="18"
                >
                  mdi-plus
                </v-icon>
                添加明细行
              </v-btn>
            </div>

            <v-card
              v-for="(detail, index) in manualForm.details"
              :key="index"
              variant="outlined"
              class="mb-3 pa-3"
            >
              <v-row dense>
                <v-col
                  cols="12"
                  md="4"
                >
                  <v-text-field
                    v-model="detail.item_name"
                    label="品名"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="2"
                >
                  <v-text-field
                    v-model="detail.spec"
                    label="规格"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-text-field
                    v-model="detail.unit"
                    label="单位"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-text-field
                    v-model="detail.quantity"
                    label="数量"
                    type="number"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-text-field
                    v-model="detail.unit_price"
                    label="单价"
                    type="number"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-text-field
                    v-model="detail.amount"
                    label="金额"
                    type="number"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-text-field
                    v-model="detail.tax_rate"
                    label="税率%"
                    type="number"
                    step="0.01"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
                <v-col
                  cols="6"
                  md="1"
                >
                  <v-btn
                    icon
                    variant="text"
                    size="small"
                    color="error"
                    @click="removeManualDetail(index)"
                  >
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
              <v-row dense>
                <v-col
                  cols="12"
                  md="3"
                >
                  <v-text-field
                    v-model="detail.service_date"
                    label="服务日期"
                    type="date"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>
              </v-row>
            </v-card>

            <div
              v-if="manualForm.details.length === 0"
              class="text-center py-3"
            >
              <span class="text-caption text-grey">暂无消费明细，可点击上方按钮添加</span>
            </div>

            <v-divider class="my-4" />
            <v-btn
              color="primary"
              size="large"
              block
              type="submit"
              :loading="manualSubmitting"
            >
              <v-icon left>
                mdi-check
              </v-icon>
              保存发票
            </v-btn>
          </v-form>
        </v-tabs-window-item>
      </v-tabs-window>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useInvoiceStore } from "@/stores/invoice";
import { ocrApi } from "@/api";

const router = useRouter();
const route = useRoute();
const invoiceStore = useInvoiceStore();

// ── Tab 状态 ──
const activeTab = ref("ocr");

// ── OCR Tab 数据 ──
const ocrFiles = ref([]);
const ocrLang = ref("chi_sim+eng");
const autoCreateInvoice = ref(false);
const ocrProcessing = ref(false);
const ocrStatus = ref(null);
const ocrResults = ref([]);
const expandedResults = ref([]);

const ocrLanguages = [
  { title: "简体中文", value: "chi_sim" },
  { title: "简体中文 + 英文", value: "chi_sim+eng" },
  { title: "英文", value: "eng" },
];

// ── 手动录入 Tab 数据 ──
const manualFormRef = ref(null);
const manualSubmitting = ref(false);
const categories = ref([]);
const counterparts = ref([]);
const invoiceTypes = ["增值税专票", "增值税普票", "电子发票"];

// 表单校验规则
const rules = {
  required: (v) => !!v || "此字段为必填项",
  number: (v) => !v || !isNaN(v) || "请输入有效数字",
  positiveNumber: (v) => !v || parseFloat(v) > 0 || "必须大于0",
};

// 全局反馈
const snackbar = reactive({ show: false, message: "", color: "success" });

const showSnackbar = (message, color = "success") => {
  snackbar.message = message;
  snackbar.color = color;
  snackbar.show = true;
};

// ── 组件卸载守卫：防止异步操作在卸载后 resolve/reject 造成内存泄露 ──
let cancelled = false;
onUnmounted(() => { cancelled = true; });

const manualForm = reactive({
  invoice_number: "",
  invoice_code: "",
  invoice_type: "",
  invoice_date: new Date().toISOString().split("T")[0],
  total_amount: null,
  tax_amount: null,
  total_with_tax: null,
  check_code: "",
  counterpart_id: null,
  category_id: null,
  remark: "",
  details: [],
});

const makeManualDetail = () => ({
  item_name: "",
  spec: "",
  unit: "",
  quantity: null,
  unit_price: null,
  amount: null,
  tax_rate: null,
  service_date: "",
});

// ── 辅助方法 ──
const formatAmount = (v) => {
  if (v === null || v === undefined) return "0.00";
  return Number(v).toFixed(2);
};

const toNum = (v) => (v !== "" && v != null) ? parseFloat(v) : null;

// ── OCR 操作 ──
const checkOcrStatus = async () => {
  try {
    ocrStatus.value = await ocrApi.getStatus();
  } catch {
    ocrStatus.value = { available: false, message: "无法连接 OCR 服务" };
  }
};

const onOcrFilesChanged = () => {
  // 文件变更时清除旧结果
  if (ocrFiles.value.length === 0) {
    ocrResults.value = [];
  }
};

const startOcr = async () => {
  if (!ocrFiles.value.length) return;
  ocrProcessing.value = true;
  const newResults = [];

  for (const file of ocrFiles.value) {
    if (cancelled) break;
    try {
      const result = await ocrApi.parseInvoice(file, ocrLang.value);
      if (cancelled) return;
      const item = {
        filename: file.name,
        data: result.invoice_data,
        counterpartName: result.parsed?.counterpart_name || "",
        duplicate: false,
        duplicateMessage: "",
        imported: false,
        importedId: null,
        importedNumber: "",
        importing: false,
      };

      // 自动入库模式
      if (autoCreateInvoice.value) {
        try {
          const importResult = await ocrApi.importInvoice(result.invoice_data);
          if (cancelled) return;
          item.imported = true;
          item.importedId = importResult.id;
          item.importedNumber = importResult.invoice_number;
        } catch (e) {
          if (cancelled) return;
          if (e.status === 409) {
            item.duplicate = true;
            item.duplicateMessage = e.message || "该发票已存在";
          }
        }
      }

      newResults.push(item);
    } catch (e) {
      if (cancelled) return;
      console.error(`OCR 解析失败 (${file.name}):`, e);
      newResults.push({
        filename: file.name,
        data: {},
        counterpartName: "",
        duplicate: false,
        duplicateMessage: "",
        imported: false,
        importedId: null,
        importedNumber: "",
        importing: false,
        error: e.message || "解析失败",
        errorItem: true,
      });
    }
  }

  if (cancelled) return;
  ocrResults.value = newResults;
  // 自动展开全部结果
  expandedResults.value = newResults.map((_, i) => i);
  ocrProcessing.value = false;
  ocrFiles.value = [];
};

const confirmImport = async (idx) => {
  const item = ocrResults.value[idx];
  item.importing = true;
  try {
    const result = await ocrApi.importInvoice(item.data);
    item.imported = true;
    item.importedId = result.id;
    item.importedNumber = result.invoice_number;
    item.importing = false;
  } catch (e) {
    item.importing = false;
    alert(e.message || "导入失败");
  }
};

// 编辑 OCR 结果 → 切换到 Tab 2 并预填表单
const editOcrResult = (idx) => {
  const item = ocrResults.value[idx];
  const d = item.data || {};

  manualForm.invoice_number = d.invoice_number || "";
  manualForm.invoice_code = d.invoice_code || "";
  manualForm.invoice_type = d.invoice_type || "";
  manualForm.invoice_date = d.invoice_date ? d.invoice_date.slice(0, 10) : new Date().toISOString().split("T")[0];
  manualForm.check_code = d.check_code || "";
  manualForm.total_amount = d.total_amount ? toNum(d.total_amount) : null;
  manualForm.tax_amount = d.tax_amount ? toNum(d.tax_amount) : null;
  manualForm.total_with_tax = d.total_with_tax ? toNum(d.total_with_tax) : null;
  manualForm.remark = d.remark || "";

  // 自动匹配对方单位
  if (item.counterpartName) {
    const match = counterparts.value.find(c => c.name === item.counterpartName);
    manualForm.counterpart_id = match ? match.id : null;
  } else {
    manualForm.counterpart_id = null;
  }

  manualForm.category_id = null;
  manualForm.details = d.details?.map(detail => ({
    item_name: detail.item_name || "",
    spec: detail.spec || "",
    unit: detail.unit || "",
    quantity: detail.quantity ? toNum(detail.quantity) : null,
    unit_price: detail.unit_price ? toNum(detail.unit_price) : null,
    amount: detail.amount ? toNum(detail.amount) : null,
    tax_rate: detail.tax_rate ? toNum(detail.tax_rate) : null,
    service_date: detail.service_date || "",
  })) || [];

  activeTab.value = "manual";
};

// ── 手动录入操作 ──
const addManualDetail = () => {
  manualForm.details.push(makeManualDetail());
};

const removeManualDetail = (index) => {
  manualForm.details.splice(index, 1);
};

const submitManual = async () => {
  // v-form 校验
  const { valid } = await manualFormRef.value.validate();
  if (!valid) {
    showSnackbar("请修正表单中的错误", "error");
    // 聚焦第一个错误字段
    setTimeout(() => {
      const firstError = document.querySelector(".v-input--error input, .v-input--error .v-field__input");
      if (firstError) firstError.focus();
    }, 100);
    return;
  }

  manualSubmitting.value = true;
  try {
    const data = {
      invoice_number: manualForm.invoice_number,
      invoice_code: manualForm.invoice_code,
      invoice_type: manualForm.invoice_type,
      invoice_date: manualForm.invoice_date,
      check_code: manualForm.check_code,
      total_amount: toNum(manualForm.total_amount),
      tax_amount: toNum(manualForm.tax_amount),
      total_with_tax: toNum(manualForm.total_with_tax),
      counterpart_id: manualForm.counterpart_id || null,
      category_id: manualForm.category_id || null,
      remark: manualForm.remark,
      details: manualForm.details.map(d => ({
        item_name: d.item_name,
        spec: d.spec,
        unit: d.unit,
        quantity: toNum(d.quantity),
        unit_price: toNum(d.unit_price),
        amount: toNum(d.amount),
        tax_rate: toNum(d.tax_rate),
        service_date: d.service_date || null,
      })),
    };

    const invoice = await invoiceStore.createInvoice(data);
    showSnackbar(`发票 ${invoice.invoice_number} 创建成功`, "success");
    setTimeout(() => router.push(`/invoices/${invoice.id}`), 800);
  } catch (error) {
    console.error("创建发票失败:", error);
    showSnackbar("创建失败: " + (error.message || "未知错误"), "error");
  } finally {
    manualSubmitting.value = false;
  }
};

// ── 从旧 UploadView 的 query 参数预填 ──
const prefillFromQuery = () => {
  const q = route.query;
  if (!q.invoice_number) return;

  manualForm.invoice_number = q.invoice_number || "";
  manualForm.invoice_code = q.invoice_code || "";
  manualForm.invoice_type = q.invoice_type || "";
  manualForm.invoice_date = q.invoice_date ? q.invoice_date.slice(0, 10) : new Date().toISOString().split("T")[0];
  manualForm.check_code = q.check_code || "";
  manualForm.total_amount = q.total_amount ? toNum(q.total_amount) : null;
  manualForm.tax_amount = q.tax_amount ? toNum(q.tax_amount) : null;
  manualForm.total_with_tax = q.total_with_tax ? toNum(q.total_with_tax) : null;
  manualForm.remark = q.remark || "";

  if (q.counterpart_name) {
    const match = counterparts.value.find(c => c.name === q.counterpart_name);
    if (match) manualForm.counterpart_id = match.id;
  }

  activeTab.value = "manual";
};

onMounted(async () => {
  await invoiceStore.fetchCategories();
  await invoiceStore.fetchCounterparts();
  categories.value = invoiceStore.categories;
  counterparts.value = invoiceStore.counterparts;

  checkOcrStatus();
  prefillFromQuery();
});
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
</style>
