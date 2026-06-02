<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span class="text-h5">对方单位管理</span>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="showDialog = true">
          <v-icon left>mdi-plus</v-icon>
          添加单位
        </v-btn>
      </v-card-title>
    </v-card>

    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="counterparts"
          :loading="loading"
          hover
        >
          <template #item.actions="{ item }">
            <v-btn icon variant="text" size="small" @click="editItem(item)">
              <v-icon>mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon variant="text" size="small" @click="confirmDelete(item)">
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 添加/编辑对话框 -->
    <v-dialog v-model="showDialog" max-width="500">
      <v-card>
        <v-card-title>
          {{ editing ? '编辑单位' : '添加单位' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="saveItem">
            <v-text-field
              v-model="form.name"
              label="单位名称"
              required
              variant="outlined"
              density="compact"
              class="mb-4"
            ></v-text-field>
            <v-text-field
              v-model="form.tax_id"
              label="统一社会信用代码 / 纳税人识别号"
              variant="outlined"
              density="compact"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelEdit">取消</v-btn>
          <v-btn color="primary" @click="saveItem" :loading="saving">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除单位 "{{ selected?.name }}" 吗？
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="deleteItem" :loading="deleting">删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { counterpartApi } from '@/api'

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const showDialog = ref(false)
const deleteDialog = ref(false)
const editing = ref(false)
const counterparts = ref([])
const selected = ref(null)
const formRef = ref(null)

const headers = [
  { title: '单位名称', key: 'name', sortable: true },
  { title: '税号', key: 'tax_id', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

const form = reactive({ name: '', tax_id: '' })

const loadItems = async () => {
  loading.value = true
  try {
    counterparts.value = await counterpartApi.getCounterparts()
  } catch (error) {
    console.error('加载单位列表失败:', error)
  } finally {
    loading.value = false
  }
}

const editItem = (item) => {
  editing.value = true
  form.name = item.name
  form.tax_id = item.tax_id || ''
  selected.value = item
  showDialog.value = true
}

const saveItem = async () => {
  if (!form.name.trim()) {
    alert('请输入单位名称')
    return
  }

  saving.value = true
  try {
    if (editing.value && selected.value) {
      await counterpartApi.updateCounterpart(selected.value.id, form)
    } else {
      await counterpartApi.createCounterpart(form)
    }
    await loadItems()
    cancelEdit()
  } catch (error) {
    console.error('保存单位失败:', error)
    alert('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const confirmDelete = (item) => {
  selected.value = item
  deleteDialog.value = true
}

const deleteItem = async () => {
  if (!selected.value) return
  deleting.value = true
  try {
    await counterpartApi.deleteCounterpart(selected.value.id)
    await loadItems()
    deleteDialog.value = false
  } catch (error) {
    console.error('删除单位失败:', error)
    alert('删除失败: ' + (error.message || '未知错误'))
  } finally {
    deleting.value = false
  }
}

const cancelEdit = () => {
  showDialog.value = false
  editing.value = false
  selected.value = null
  form.name = ''
  form.tax_id = ''
}

onMounted(() => {
  loadItems()
})
</script>