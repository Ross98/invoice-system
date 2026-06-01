<template>
  <div>
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center">
        <span class="text-h5">消费分类管理</span>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="showAddDialog = true">
          <v-icon left>mdi-plus</v-icon>
          添加分类
        </v-btn>
      </v-card-title>
    </v-card>

    <!-- 分类列表 -->
    <v-card>
      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="categories"
          :loading="loading"
          hover
        >
          <template v-slot:item.actions="{ item }">
            <v-btn icon variant="text" size="small" @click="editCategory(item)">
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
    <v-dialog v-model="showAddDialog" max-width="500">
      <v-card>
        <v-card-title>
          {{ editingCategory ? '编辑分类' : '添加分类' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="saveCategory">
            <v-text-field
              v-model="categoryForm.name"
              label="分类名称"
              required
              variant="outlined"
              density="compact"
              class="mb-4"
            ></v-text-field>
            
            <v-select
              v-model="categoryForm.parent_id"
              label="父分类"
              :items="parentCategoryOptions"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              clearable
              hint="留空表示一级分类"
              persistent-hint
            ></v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="cancelEdit">取消</v-btn>
          <v-btn color="primary" @click="saveCategory" :loading="saving">
            保存
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>确认删除</v-card-title>
        <v-card-text>
          确定要删除分类 "{{ selectedCategory?.name }}" 吗？
          <v-alert v-if="hasChildCategories" type="warning" class="mt-2">
            该分类下有子分类，删除后所有子分类将变为一级分类
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="deleteDialog = false">取消</v-btn>
          <v-btn color="error" @click="deleteCategory" :loading="deleting">
            删除
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useInvoiceStore } from '@/stores/invoice'

const invoiceStore = useInvoiceStore()

const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const showAddDialog = ref(false)
const deleteDialog = ref(false)
const categories = ref([])
const selectedCategory = ref(null)
const editingCategory = ref(null)
const formRef = ref(null)

const headers = [
  { title: '分类名称', key: 'name', sortable: true },
  { title: '父分类', key: 'parent_name', sortable: true },
  { title: '创建时间', key: 'created_at', sortable: true },
  { title: '操作', key: 'actions', sortable: false }
]

const categoryForm = reactive({
  name: '',
  parent_id: null
})

const parentCategoryOptions = computed(() => {
  return categories.value.filter(cat => !cat.parent_id)
})

const hasChildCategories = computed(() => {
  if (!selectedCategory.value) return false
  return categories.value.some(cat => cat.parent_id === selectedCategory.value.id)
})

const loadCategories = async () => {
  loading.value = true
  try {
    await invoiceStore.fetchCategories()
    categories.value = invoiceStore.categories.map(cat => ({
      ...cat,
      parent_name: cat.parent_id ? 
        categories.value.find(p => p.id === cat.parent_id)?.name || '未知' : 
        '-'
    }))
  } catch (error) {
    console.error('加载分类失败:', error)
  } finally {
    loading.value = false
  }
}

const editCategory = (category) => {
  editingCategory.value = category
  categoryForm.name = category.name
  categoryForm.parent_id = category.parent_id
  showAddDialog.value = true
}

const saveCategory = async () => {
  if (!categoryForm.name.trim()) {
    alert('请输入分类名称')
    return
  }

  saving.value = true
  try {
    if (editingCategory.value) {
      await invoiceStore.updateCategory(editingCategory.value.id, categoryForm)
    } else {
      await invoiceStore.createCategory(categoryForm)
    }
    
    await loadCategories()
    cancelEdit()
  } catch (error) {
    console.error('保存分类失败:', error)
    alert('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

const confirmDelete = (category) => {
  selectedCategory.value = category
  deleteDialog.value = true
}

const deleteCategory = async () => {
  if (!selectedCategory.value) return

  deleting.value = true
  try {
    await invoiceStore.deleteCategory(selectedCategory.value.id)
    await loadCategories()
  } catch (error) {
    console.error('删除分类失败:', error)
    alert('删除失败: ' + (error.message || '未知错误'))
  } finally {
    deleting.value = false
    deleteDialog.value = false
    selectedCategory.value = null
  }
}

const cancelEdit = () => {
  showAddDialog.value = false
  editingCategory.value = null
  categoryForm.name = ''
  categoryForm.parent_id = null
}

onMounted(async () => {
  await loadCategories()
})
</script>