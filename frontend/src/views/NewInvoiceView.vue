<template>
  <v-card>
    <v-card-title class="text-h5">新建发票</v-card-title>
    <v-card-text>
      <v-form ref="formRef" @submit.prevent="submitForm">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.invoice_number"
              label="发票号码"
              required
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.invoice_code"
              label="发票代码"
              required
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              v-model="form.invoice_type"
              label="发票类型"
              :items="invoiceTypes"
              required
              variant="outlined"
              density="compact"
            ></v-select>
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.invoice_date"
              label="开票日期"
              type="date"
              required
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.check_code"
              label="校验码"
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.total_amount"
              label="不含税金额"
              type="number"
              step="0.01"
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.tax_amount"
              label="税额"
              type="number"
              step="0.01"
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="form.total_with_tax"
              label="含税总金额"
              type="number"
              step="0.01"
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="6">
            <v-select
              v-model="form.counterpart_id"
              label="对方单位"
              :items="counterparts"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              clearable
            ></v-select>
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="form.category_id"
              label="消费分类"
              :items="categories"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              clearable
            ></v-select>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.remark"
              label="备注"
              variant="outlined"
              density="compact"
              rows="2"
            ></v-textarea>
          </v-col>
        </v-row>

        <!-- 消费明细 -->
        <v-divider class="my-4"></v-divider>
        <div class="text-h6 mb-4">消费明细</div>
        <v-btn color="secondary" size="small" @click="addDetail" class="mb-4">
          <v-icon left>mdi-plus</v-icon>
          添加明细
        </v-btn>

        <v-card v-for="(detail, index) in form.details" :key="index" class="mb-4 pa-4">
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="detail.item_name"
                label="品名"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="12" md="2">
              <v-text-field
                v-model="detail.spec"
                label="规格"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-text-field
                v-model="detail.unit"
                label="单位"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-text-field
                v-model="detail.quantity"
                label="数量"
                type="number"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-text-field
                v-model="detail.unit_price"
                label="单价"
                type="number"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-text-field
                v-model="detail.amount"
                label="金额"
                type="number"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-text-field
                v-model="detail.tax_rate"
                label="税率"
                type="number"
                step="0.01"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
            <v-col cols="6" md="1">
              <v-btn icon variant="text" color="error" @click="removeDetail(index)">
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row>
            <v-col cols="12" md="3">
              <v-text-field
                v-model="detail.service_date"
                label="服务日期"
                type="date"
                variant="outlined"
                density="compact"
                hide-details
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card>

        <v-divider class="my-4"></v-divider>
        <v-row>
          <v-col cols="12">
            <v-btn color="primary" type="submit" block :loading="submitting">
              保存发票
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useInvoiceStore } from '@/stores/invoice'

const router = useRouter()
const route = useRoute()
const invoiceStore = useInvoiceStore()

const formRef = ref(null)
const submitting = ref(false)
const categories = ref([])
const counterparts = ref([])

const invoiceTypes = ['增值税专票', '增值税普票', '电子发票']

const form = reactive({
  invoice_number: '',
  invoice_code: '',
  invoice_type: '',
  invoice_date: new Date().toISOString().split('T')[0],
  total_amount: null,
  tax_amount: null,
  total_with_tax: null,
  check_code: '',
  counterpart_id: null,
  category_id: null,
  remark: '',
  details: []
})

const addDetail = () => {
  form.details.push({
    item_name: '',
    spec: '',
    unit: '',
    quantity: null,
    unit_price: null,
    amount: null,
    tax_rate: null,
    service_date: ''
  })
}

const removeDetail = (index) => {
  form.details.splice(index, 1)
}

const submitForm = async () => {
  if (!form.invoice_number || !form.invoice_type || !form.invoice_date) {
    alert('请填写必填字段')
    return
  }

  submitting.value = true
  try {
    const data = {
      ...form,
      total_amount: form.total_amount ? parseFloat(form.total_amount) : null,
      tax_amount: form.tax_amount ? parseFloat(form.tax_amount) : null,
      total_with_tax: form.total_with_tax ? parseFloat(form.total_with_tax) : null,
      details: form.details.map(d => ({
        ...d,
        quantity: d.quantity ? parseFloat(d.quantity) : null,
        unit_price: d.unit_price ? parseFloat(d.unit_price) : null,
        amount: d.amount ? parseFloat(d.amount) : null,
        tax_rate: d.tax_rate ? parseFloat(d.tax_rate) : null
      }))
    }

    const invoice = await invoiceStore.createInvoice(data)
    router.push(`/invoices/${invoice.id}`)
  } catch (error) {
    console.error('创建发票失败:', error)
    alert('创建失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await invoiceStore.fetchCategories()
  await invoiceStore.fetchCounterparts()
  categories.value = invoiceStore.categories
  counterparts.value = invoiceStore.counterparts

  // 从 OCR 上传页面传递的 query 参数预填表单
  const q = route.query
  if (q.invoice_number) form.invoice_number = q.invoice_number
  if (q.invoice_code) form.invoice_code = q.invoice_code
  if (q.invoice_type) form.invoice_type = q.invoice_type
  if (q.invoice_date) form.invoice_date = q.invoice_date.slice(0, 10)
  if (q.check_code) form.check_code = q.check_code
  if (q.total_amount) form.total_amount = parseFloat(q.total_amount)
  if (q.tax_amount) form.tax_amount = parseFloat(q.tax_amount)
  if (q.total_with_tax) form.total_with_tax = parseFloat(q.total_with_tax)
  if (q.remark) form.remark = q.remark

  // 根据销方单位名称自动匹配 counterpart_id
  if (q.counterpart_name) {
    const match = counterparts.value.find(
      c => c.name === q.counterpart_name
    )
    if (match) {
      form.counterpart_id = match.id
    }
  }
})
</script>