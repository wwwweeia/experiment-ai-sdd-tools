<template>
  <div class="agent-list">
    <!-- 操作栏 -->
    <div class="search-area">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="状态筛选">
          <el-select
            v-model="filterStatus"
            placeholder="全部状态"
            clearable
            style="width: 160px"
            @change="handleStatusFilterChange"
          >
            <el-option label="全部" :value="null" />
            <el-option label="DRAFT" value="draft" />
            <el-option label="ACTIVE" value="active" />
            <el-option label="INACTIVE" value="inactive" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-button type="primary" @click="openCreateDialog">创建 Agent</el-button>
    </div>

    <!-- 表格 -->
    <el-table
      v-loading="agentStore.loading"
      :data="agentStore.agents"
      style="width: 100%"
      empty-text="暂无数据"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="关联模型" min-width="120">
        <template #default="{ row }">
          {{ row.model_name || '未关联' }}
        </template>
      </el-table-column>
      <el-table-column label="关联提示词" min-width="120">
        <template #default="{ row }">
          {{ row.prompt_name || '未关联' }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'draft'" type="primary" size="small" @click="handleActivate(row)">激活</el-button>
          <el-button v-if="row.status === 'active'" type="warning" size="small" @click="handleDeactivate(row)">停用</el-button>
          <template v-if="row.status === 'inactive'">
            <el-button type="primary" size="small" @click="handleActivate(row)">激活</el-button>
            <el-button v-if="row.status === 'inactive'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="agentStore.currentPage"
        v-model:page-size="agentStore.pageSize"
        layout="prev, pager, next"
        @current-change="agentStore.setCurrentPage"
      />
    </div>

    <!-- 创建对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="创建 Agent"
      width="500px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createFormRules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            placeholder="请输入描述（选填）"
          />
        </el-form-item>
        <el-form-item label="关联模型" prop="model_id">
          <el-select
            v-model="createForm.model_id"
            placeholder="请选择模型"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in models"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联提示词" prop="prompt_id">
          <el-select
            v-model="createForm.prompt_id"
            placeholder="请选择提示词"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in prompts"
              :key="item.id"
              :label="item.title"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">暂不创建</el-button>
        <el-button type="primary" @click="submitCreate">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useAgentStore } from '../stores/agent'
import { ElMessageBox } from 'element-plus'
import api from '../api/index'

const agentStore = useAgentStore()

// 创建对话框状态
const createDialogVisible = ref(false)
const createFormRef = ref(null)
const models = ref([])
const prompts = ref([])

const createForm = reactive({
  name: '',
  description: '',
  model_id: null,
  prompt_id: null,
})

const createFormRules = {
  name: [{ required: true, message: '请输入 Agent 名称', trigger: 'blur' }],
}

// 状态筛选（组件本地状态，同步到 store）
const filterStatus = ref(null)

function handleStatusFilterChange(val) {
  agentStore.setStatusFilter(val)
}

// 状态标签辅助函数
function statusTagType(status) {
  const map = { draft: 'info', active: 'success', inactive: 'warning' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { draft: 'DRAFT', active: 'ACTIVE', inactive: 'INACTIVE' }
  return map[status] || status?.toUpperCase() || status
}

// 激活 Agent
function handleActivate(row) {
  const msg = row.status === 'inactive'
    ? `确认重新激活 Agent「${row.name}」？系统将重新验证关联的 Model 和 Prompt。`
    : `确认激活 Agent「${row.name}」？激活前系统将验证关联的 Model 和 Prompt 是否有效。`
  ElMessageBox.confirm(msg, '激活确认', { type: 'warning' })
    .then(() => agentStore.updateStatus(row.id, 'active'))
    .catch(() => {})
}

// 停用 Agent
function handleDeactivate(row) {
  ElMessageBox.confirm(
    `确认停用 Agent「${row.name}」？停用后关联的 Skill 将标记为不可用。`,
    '停用确认',
    { type: 'warning' }
  )
    .then(() => agentStore.updateStatus(row.id, 'inactive'))
    .catch(() => {})
}

// 删除 Agent
function handleDelete(row) {
  ElMessageBox.confirm(
    `确认删除 Agent「${row.name}」？此操作不可撤销。`,
    '删除确认',
    { type: 'error' }
  )
    .then(() => agentStore.deleteAgent(row.id))
    .catch(() => {})
}

// 创建对话框 — 懒加载下拉选项
async function openCreateDialog() {
  createDialogVisible.value = true
  try {
    const [modelsRes, promptsRes] = await Promise.all([
      api.get('/api/v1/models/'),
      api.get('/api/v1/prompts/'),
    ])
    models.value = modelsRes.data || []
    prompts.value = promptsRes.data || []
  } catch (e) {
    console.error('[AgentList] 加载下拉选项失败:', e)
  }
}

// 提交创建
function submitCreate() {
  createFormRef.value.validate((valid) => {
    if (!valid) return
    agentStore.createAgent({ ...createForm })
    createDialogVisible.value = false
    resetCreateForm()
  })
}

// 重置表单
function resetCreateForm() {
  createForm.name = ''
  createForm.description = ''
  createForm.model_id = null
  createForm.prompt_id = null
  createFormRef.value?.resetFields()
}

// 对话框关闭时重置表单
watch(createDialogVisible, (val) => {
  if (!val) resetCreateForm()
})

onMounted(() => { agentStore.loadAgents() })
</script>

<style scoped>
.agent-list {
  padding: 24px;
  background: #fff;
  min-height: calc(100vh - 60px);
}

.search-area {
  margin-bottom: 20px;
  padding: 16px 20px;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
</style>
