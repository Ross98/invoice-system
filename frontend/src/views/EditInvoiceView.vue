<template>
  <v-card>
    <v-card-title class="text-h5">编辑发票</v-card-title>
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
              更新发票
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useInvoiceStore } from '@/stores/invoice'

const route = useRoute()
const router = useRouter()
const invoiceStore = useInvoiceStore()

const formRef = ref(null)
const submitting = ref(false)
const categories = ref([])
const counterparts = ref([])
const invoiceId = ref(null)

const invoiceTypes = ['增值税专票', '增值税普票', '电子发票']

const form = reactive({
  invoice_number: '',
  invoice_code: '',
  invoice_type: '',
  invoice_date: '',
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

const loadInvoice = async () => {
  try {
    let invoice = await invoiceStore.getInvoice(invoiceId.value)
    // 安全兜底：如果 getInvoice 没返回值，直接从 store 读取
    if (!invoice) {
      invoice = invoiceStore.currentInvoice
    }
    if (!invoice || !invoice.id) {
      throw new Error('发票数据加载失败')
    }
    // 填充表单数据
    form.invoice_number = invoice.invoice_number
    form.invoice_code = invoice.invoice_code
    form.invoice_type = invoice.invoice_type
    form.invoice_date = invoice.invoice_date
    form.total_amount = invoice.total_amount
    form.tax_amount = invoice.tax_amount
    form.total_with_tax = invoice.total_with_tax
    form.check_code = invoice.check_code
    form.counterpart_id = invoice.counterpart?.id || null
    form.category_id = invoice.category?.id || null
    form.remark = invoice.remark
    form.details = invoice.details || []
  } catch (error) {
    console.error('加载发票失败:', error)
    router.push('/invoices')
  }
}

const submitForm = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return

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

    await invoiceStore.updateInvoice(invoiceId.value, data)
    router.push(`/invoices/${invoiceId.value}`)
  } catch (error) {
    console.error('更新发票失败:', error)
    alert('更新失败: ' + (error.message || '未知错误'))
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  invoiceId.value = route.params.id
  await invoiceStore.fetchCategories()
  await invoiceStore.fetchCounterparts()
  categories.value = invoiceStore.categories
  counterparts.value = invoiceStore.counterparts
  await loadInvoice()
})
</script>