<template>
  <div class="agent-list">
    <div class="agent-header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="showCreateDialog">创建 Agent</el-button>
    </div>

    <!-- 状态筛选 -->
    <div class="agent-filter">
      <el-radio-group v-model="store.statusFilter" @change="handleFilterChange">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="draft">草稿</el-radio-button>
        <el-radio-button value="active">已激活</el-radio-button>
        <el-radio-button value="inactive">已停用</el-radio-button>
      </el-radio-group>
    </div>

    <!-- Agent 列表 -->
    <el-table :data="store.agents" v-loading="store.loading" stripe>
      <el-table-column prop="name" label="名称" min-width="120" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="model_name" label="关联 Model" width="150">
        <template #default="{ row }">{{ row.model_name || '-' }}</template>
      </el-table-column>
      <el-table-column prop="prompt_title" label="关联 Prompt" min-width="150">
        <template #default="{ row }">{{ row.prompt_title || '-' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 'draft' || row.status === 'inactive'" type="success" size="small" @click="handleActivate(row)">激活</el-button>
          <el-button v-if="row.status === 'active'" type="warning" size="small" @click="handleDeactivate(row)">停用</el-button>
          <el-button v-if="row.status === 'inactive'" type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 创建 Agent 对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建 Agent" width="500px" destroy-on-close>
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="关联 Model">
          <el-select v-model="createForm.model_id" placeholder="选择 Model（可选）" clearable style="width: 100%">
            <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联 Prompt">
          <el-select v-model="createForm.prompt_id" placeholder="选择 Prompt（可选）" clearable style="width: 100%">
            <el-option v-for="p in prompts" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAgentStore } from '../stores/agent'
import { ElMessageBox } from 'element-plus'
import api from '../api'

const store = useAgentStore()

const models = ref([])
const prompts = ref([])
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createFormRef = ref(null)

const createForm = ref({
  name: '',
  description: '',
  model_id: null,
  prompt_id: null,
})

const createRules = {
  name: [{ required: true, message: '请输入 Agent 名称', trigger: 'blur' }],
}

function statusTagType(status) {
  const map = { draft: 'warning', active: 'success', inactive: 'info' }
  return map[status] || 'info'
}

function statusLabel(status) {
  const map = { draft: '草稿', active: '已激活', inactive: '已停用' }
  return map[status] || status
}

function handleFilterChange(val) {
  store.fetchAgents(val || undefined)
}

function showCreateDialog() {
  createForm.value = { name: '', description: '', model_id: null, prompt_id: null }
  createDialogVisible.value = true
}

async function loadOptions() {
  const [modelsRes, promptsRes] = await Promise.all([
    api.get('/api/v1/models/'),
    api.get('/api/v1/prompts/'),
  ])
  models.value = modelsRes.data || []
  prompts.value = promptsRes.data || []
}

async function handleCreate() {
  await createFormRef.value.validate()
  createLoading.value = true
  try {
    await store.createAgent(createForm.value)
    createDialogVisible.value = false
  } finally {
    createLoading.value = false
  }
}

function handleActivate(row) {
  ElMessageBox.confirm(
    `确定要激活 Agent「${row.name}」吗？激活后该 Agent 将可运行。`,
    '确认激活',
    { confirmButtonText: '激活', cancelButtonText: '取消', type: 'info' },
  ).then(() => {
    store.changeStatus(row.id, 'active')
  }).catch(() => {})
}

function handleDeactivate(row) {
  ElMessageBox.confirm(
    `确定要停用 Agent「${row.name}」吗？停用后 Agent 将暂停运行，关联 Skill 将不可用。`,
    '确认停用',
    { confirmButtonText: '停用', cancelButtonText: '取消', type: 'warning' },
  ).then(() => {
    store.changeStatus(row.id, 'inactive')
  }).catch(() => {})
}

function handleDelete(row) {
  ElMessageBox.confirm(
    `确定要删除 Agent「${row.name}」吗？此操作不可恢复。`,
    '确认删除',
    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'error' },
  ).then(() => {
    store.deleteAgentById(row.id)
  }).catch(() => {})
}

onMounted(async () => {
  await Promise.all([store.fetchAgents(), loadOptions()])
})
</script>

<style scoped>
.agent-list {
  padding: 20px;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.agent-filter {
  margin-bottom: 16px;
}
</style>
