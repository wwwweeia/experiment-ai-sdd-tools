<template>
  <div class="agent-list">
    <div class="header">
      <h2>Agent 管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">新建 Agent</el-button>
    </div>

    <!-- 状态筛选 -->
    <el-tabs v-model="activeTab" class="status-tabs" @tab-change="handleFilterChange">
      <el-tab-pane label="全部" name="" />
      <el-tab-pane label="草稿" name="draft" />
      <el-tab-pane label="已激活" name="active" />
      <el-tab-pane label="已停用" name="inactive" />
    </el-tabs>

    <!-- Agent 表格 -->
    <el-table v-loading="agentStore.loading" :data="agentStore.agents" style="width: 100%">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="名称" min-width="120" show-overflow-tooltip />
      <el-table-column prop="description" label="描述" min-width="160" show-overflow-tooltip />
      <el-table-column label="关联模型" width="120">
        <template #default="{ row }">
          {{ row.model_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="关联提示词" width="140">
        <template #default="{ row }">
          {{ row.prompt_name || '-' }}
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="agentStore.statusTagType[row.status]" size="small">
            {{ agentStore.statusLabel[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button
            v-if="row.status === 'draft' || row.status === 'inactive'"
            type="success"
            size="small"
            @click="handleActivate(row)"
          >
            激活
          </el-button>
          <el-button
            v-if="row.status === 'active'"
            type="warning"
            size="small"
            @click="handleDeactivate(row)"
          >
            停用
          </el-button>
          <el-button
            v-if="row.status === 'inactive'"
            type="danger"
            size="small"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        :page-size="agentStore.pagination.limit"
        :total="agentStore.pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 新建 Agent 弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建 Agent" width="500px" @close="resetForm">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="请输入 Agent 名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="可选" />
        </el-form-item>
        <el-form-item label="关联模型">
          <el-select v-model="createForm.model_id" placeholder="选择模型（激活前必选）" clearable style="width: 100%">
            <el-option v-for="m in modelOptions" :key="m.id" :label="m.name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联提示词">
          <el-select v-model="createForm.prompt_id" placeholder="选择提示词（激活前必选）" clearable style="width: 100%">
            <el-option v-for="p in promptOptions" :key="p.id" :label="p.title" :value="p.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAgentStore } from '../stores/agent'
import { fetchPrompts } from '../api/prompts'
import api from '../api'

const agentStore = useAgentStore()

const activeTab = ref('')
const showCreateDialog = ref(false)
const submitting = ref(false)
const modelOptions = ref([])
const promptOptions = ref([])

const createForm = ref({
  name: '',
  description: '',
  model_id: null,
  prompt_id: null,
})

const currentPage = computed({
  get: () => Math.floor(agentStore.pagination.skip / agentStore.pagination.limit) + 1,
  set: () => {},
})

async function loadOptions() {
  const [modelRes, promptRes] = await Promise.all([
    api.get('/api/v1/models/'),
    fetchPrompts(),
  ])
  modelOptions.value = modelRes.data || []
  promptOptions.value = promptRes.data || []
}

function handleFilterChange(status) {
  agentStore.setFilter(status)
  agentStore.fetchAgents()
}

function handlePageChange(page) {
  agentStore.setPage((page - 1) * agentStore.pagination.limit)
  agentStore.fetchAgents()
}

function handleActivate(row) {
  ElMessageBox.confirm(
    `确定要激活 Agent「${row.name}」吗？激活后将可被系统调用。`,
    '激活确认',
    { type: 'info', confirmButtonText: '确定激活', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.changeStatus(row.id, 'active').catch(() => {})
  }).catch(() => {})
}

function handleDeactivate(row) {
  ElMessageBox.confirm(
    `确定要停用 Agent「${row.name}」吗？停用后该 Agent 将不再接受请求。`,
    '停用确认',
    { type: 'warning', confirmButtonText: '确定停用', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.changeStatus(row.id, 'inactive').catch(() => {})
  }).catch(() => {})
}

function handleDelete(row) {
  ElMessageBox.confirm(
    `确定要删除 Agent「${row.name}」吗？此操作不可恢复。`,
    '删除确认',
    { type: 'error', confirmButtonText: '确定删除', cancelButtonText: '取消' },
  ).then(() => {
    agentStore.deleteAgent(row.id).then(() => {
      ElMessage.success('删除成功')
    }).catch(() => {})
  }).catch(() => {})
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入 Agent 名称')
    return
  }
  submitting.value = true
  try {
    await agentStore.createAgent(createForm.value)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
  } catch {
    // 错误由拦截器处理
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  createForm.value = { name: '', description: '', model_id: null, prompt_id: null }
}

onMounted(() => {
  agentStore.fetchAgents()
  loadOptions()
})
</script>

<style scoped>
.agent-list {
  padding: 20px;
  background: #fff;
  min-height: calc(100vh - 60px);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h2 {
  margin: 0;
  font-size: 20px;
}

.status-tabs {
  margin-bottom: 16px;
}

.pagination-wrapper {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
